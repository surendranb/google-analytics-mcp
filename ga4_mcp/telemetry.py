# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Anonymous usage telemetry for google-analytics-mcp.

Everything telemetry lives here: opt-out handling, anonymous identity,
environment detection, PII scrubbing, and transport. Events are sent to the
project's own gateway (a Cloudflare Worker whose source is in this repo under
workers/install-telemetry/), which strips IPs, stamps coarse geo, and forwards
to PostHog. See 'Telemetry & Privacy' in the README.

Identity contract (frozen, schema_version 1): the only identity is a random,
resettable installation UUID stored in ~/.ga4_mcp/. Never hardware-derived,
never fingerprinted. Deleting ~/.ga4_mcp resets it entirely.
"""

import os
import re
import sys
import time
import json
import uuid
import platform
import threading
import subprocess
import urllib.request
from pathlib import Path

# Central gateway (source: workers/install-telemetry/ in this repo).
# The gateway strips IPs, stamps coarse geo, and forwards to the analytics
# store. No vendor keys ship in this client.
GATEWAY_URL = "https://ga4.builditwithai.xyz/e"

# Version of the telemetry event contract. Additive-only evolution: properties
# may be added under the same version; renames/removals require a bump and a
# deprecation window where both shapes are emitted.
SCHEMA_VERSION = 1

# Extract the package version so it can be stamped on all telemetry
try:
    import importlib.metadata
    MCP_SERVER_VERSION = importlib.metadata.version("google-analytics-mcp")
except Exception:
    MCP_SERVER_VERSION = "unknown"


# Telemetry Opt-Out
# Honors every flag we have ever documented (README used to say DISABLE_TELEMETRY)
# plus the cross-tool DO_NOT_TRACK convention (consoledonottrack.com).
# Precedence: any disable flag wins over any enable value — the most
# privacy-protective signal always takes priority.
def _telemetry_disabled() -> bool:
    if os.getenv("GA_MCP_TELEMETRY", "true").lower() in ("false", "0", "off"):
        return True
    for var in ("DISABLE_TELEMETRY", "DO_NOT_TRACK", "NO_TELEMETRY"):
        if os.getenv(var, "").lower() in ("1", "true", "yes", "on"):
            return True
    return False


TELEMETRY_DISABLED = _telemetry_disabled()

# Marker set by this project's own CI/dev environments so our runs can be
# tagged (traffic_class=internal) instead of polluting adoption metrics.
# User CI stays first-class data — only OUR runs carry this.
INTERNAL_RUN = os.getenv("GA4_MCP_INTERNAL", "").lower() in ("1", "true", "yes")


# Persistent Anonymous Installation ID & First-Run Detection
def _init_anonymous_identity():
    """
    Manages a purely random anonymous installation UUID stored locally.
    Contains NO PII (no usernames, hostnames, IP addresses, or path names).
    Deleting ~/.ga4_mcp resets the identity entirely.
    """
    try:
        config_dir = Path.home() / ".ga4_mcp"
        config_dir.mkdir(parents=True, exist_ok=True)

        id_file = config_dir / "installation_id"
        if id_file.exists():
            installation_id = id_file.read_text(encoding="utf-8").strip()
            is_first_install = False
        else:
            installation_id = f"inst_{uuid.uuid4()}"
            id_file.write_text(installation_id, encoding="utf-8")
            is_first_install = True

        flag_file = config_dir / "installed_v2"
        if not flag_file.exists():
            is_first_install = True
            flag_file.write_text("1", encoding="utf-8")

        return installation_id, is_first_install
    except Exception:
        # Fallback to random session ID if filesystem access is restricted
        return f"anon_{uuid.uuid4()}", False


INSTALLATION_ID, IS_FIRST_INSTALL = _init_anonymous_identity()

# Per-process session ID: one server process == one agent session (stdio transport)
SESSION_ID = f"sess_{uuid.uuid4()}"

# Environment Context
IN_VIRTUAL_ENV = sys.prefix != sys.base_prefix
CPU_ARCH = platform.machine()
TIMEZONE_OFFSET = -time.timezone if (time.localtime().tm_isdst == 0) else -time.altzone


# Install-source attribution: self-declared channel marker baked into install
# snippets (e.g. the 1-line installer writes GA4_MCP_SOURCE into the config).
# Raw value is kept (capture), a low-cardinality bucket is added (curation).
_KNOWN_SOURCES = {
    "readme", "glama", "mcpso", "pulsemcp", "ga4mcp", "setup",
    "cursor_button", "vscode_button", "installer",
}


def _install_source():
    raw = (os.getenv("GA4_MCP_SOURCE") or "").strip().lower()[:64]
    if not raw:
        return None, None
    return raw, (raw if raw in _KNOWN_SOURCES else "other")


INSTALL_SOURCE_RAW, INSTALL_SOURCE = _install_source()


# PII Scrubbing
# Every outgoing string property passes through this, so no call site can leak
# paths, emails, keys, or GA4 property IDs — including future call sites.
_REDACTIONS = [
    (re.compile(r"\bhttps?://\S+"), "<url>"),
    (re.compile(r"(?:file://)?[A-Za-z]:[\\/](?:[^\\/:*?\"<>|\r\n]+[\\/])+[^\\/:*?\"<>|\r\n ]*"), "<path>"),
    (re.compile(r"(?:file://)?/(?:[\w.@()~+-]+/)+[\w.@()~+-]*"), "<path>"),
    (re.compile(r"(?:[\w.@()~+-]+/){2,}[\w.@()~+-]+"), "<path>"),
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"), "<email>"),
    (re.compile(r"AIza[0-9A-Za-z_\-]{35}"), "<google_key>"),
    (re.compile(r"properties/\d+"), "properties/<id>"),
]


def _scrub(value):
    if isinstance(value, str):
        s = value
        for pattern, replacement in _REDACTIONS:
            s = pattern.sub(replacement, s)
        return s[:500]
    if isinstance(value, dict):
        return {k: _scrub(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_scrub(v) for v in value]
    return value


# Agent Identity
# Ground truth is the MCP handshake clientInfo (captured on first tool call).
# Env-var detection is only a fallback for events fired before the handshake
# (server_first_install, mcp_started). Env var VALUES are never collected.
def _normalize_client_name(raw):
    n = (raw or "").strip().lower()
    if not n or n == "unknown":
        return None
    buckets = [
        ("claude-code", "claude_code"),
        ("claude_code", "claude_code"),
        ("claude code", "claude_code"),
        ("claudeai", "claude_desktop"),
        ("claude-ai", "claude_desktop"),
        ("claude desktop", "claude_desktop"),
        ("cursor", "cursor"),
        ("codex", "codex"),
        ("gemini", "gemini_cli"),
        ("windsurf", "windsurf"),
        ("opencode", "opencode"),
        ("kiro", "kiro"),
        ("antigravity", "antigravity"),
        ("copilot", "github_copilot"),
        ("cline", "cline"),
        ("zed", "zed"),
        ("visual studio code", "vscode"),
        ("vscode", "vscode"),
        ("inspector", "mcp_inspector"),
    ]
    for needle, bucket in buckets:
        if needle in n:
            return bucket
    return "other"


def _process_ancestor_names(max_depth=4):
    """Command names of parent processes (uvx sits between the agent and us)."""
    names = []
    try:
        if platform.system() not in ("Darwin", "Linux"):
            return names
        pid = os.getppid()
        for _ in range(max_depth):
            if not pid or pid <= 1:
                break
            out = subprocess.check_output(
                ["ps", "-p", str(pid), "-o", "ppid=,comm="], text=True, timeout=1
            ).strip()
            if not out:
                break
            parts = out.split(None, 1)
            names.append(parts[1].lower() if len(parts) > 1 else "")
            pid = int(parts[0])
    except Exception:
        pass
    return names


def _detect_run_context() -> str:
    """
    Single deterministic answer to WHERE the server is running, by priority:
    ci > cloud/container > terminal (attended) > desktop GUI app (attended) > headless.
    Presence-based env checks only; no values are collected.
    """
    env = os.environ
    if env.get("GITHUB_ACTIONS", "").lower() == "true" or env.get("CI", "").lower() in ("true", "1"):
        return "ci"
    if ("KUBERNETES_SERVICE_HOST" in env or "AWS_EXECUTION_ENV" in env
            or "ECS_CONTAINER_METADATA_URI" in env or "ECS_CONTAINER_METADATA_URI_V4" in env
            or os.path.exists("/.dockerenv")):
        return "cloud"
    if "TERM_PROGRAM" in env or "SSH_TTY" in env or "SSH_CONNECTION" in env or sys.stdin.isatty():
        return "terminal"
    # GUI apps strip TERM_PROGRAM but stamp their own identity on the process
    if env.get("__CFBundleIdentifier"):
        return "desktop"
    if "DISPLAY" in env or "WAYLAND_DISPLAY" in env or env.get("XDG_SESSION_TYPE") in ("x11", "wayland"):
        return "desktop"
    if platform.system() == "Windows" and env.get("SESSIONNAME", "").lower() == "console":
        return "desktop"
    return "headless"


RUN_CONTEXT = _detect_run_context()


def _detect_agent_name() -> str:
    """
    Detects the AI agent client from env-var PRESENCE and parent process names.
    Claude Code sets CLAUDECODE / CLAUDE_CODE_* (verified); Cursor sets
    CURSOR_TRACE_ID. Zero PII collected — values are never read except CI/GITHUB_ACTIONS booleans.
    """
    env = os.environ
    if "CLAUDECODE" in env or "CLAUDE_CODE" in env or any(k.startswith("CLAUDE_CODE_") for k in env):
        return "claude_code"
    if any(k in env for k in ("CURSOR_TRACE_ID", "CURSOR_TRACE", "CURSOR_VERSION", "CURSOR_SESSION_ID")):
        return "cursor"
    if "GEMINI_CLI" in env or "GEMINI_EXTENSION" in env:
        return "gemini_cli"
    if "WINDSURF_VERSION" in env or any(k.startswith("CODEIUM_") for k in env):
        return "windsurf"
    if "ANTIGRAVITY" in env or "AGY_SESSION" in env:
        return "antigravity"

    # macOS GUI spawns carry the host app's bundle id (third identity signal)
    bundle = env.get("__CFBundleIdentifier", "").lower()
    if "claudefordesktop" in bundle or "claude-desktop" in bundle:
        return "claude_desktop"
    if "cursor" in bundle:
        return "cursor"
    if "windsurf" in bundle:
        return "windsurf"

    # Parent-process walk runs before the VS Code check because VS Code forks
    # (Cursor, Windsurf) also set VSCODE_* in their terminals.
    for comm in _process_ancestor_names():
        for needle, bucket in (
            ("claude", "claude_code"),
            ("cursor", "cursor"),
            ("gemini", "gemini_cli"),
            ("windsurf", "windsurf"),
            ("codex", "codex"),
        ):
            if needle in comm:
                return bucket

    if "VSCODE_PID" in env or "VSCODE_IPC_HOOK" in env or "VSCODE_CWD" in env:
        return "vscode"
    if env.get("GITHUB_ACTIONS", "").lower() == "true" or env.get("CI", "").lower() in ("true", "1"):
        return "ci_runner"

    return "generic_agent" if not sys.stdin.isatty() else "human_terminal"


AGENT_NAME = _detect_agent_name()


def _detect_actor_type() -> str:
    """Autonomous AI agent environment vs human shell. No PII collected."""
    if not sys.stdin.isatty():
        return "ai_agent"
    if AGENT_NAME not in ("human_terminal", "generic_agent", "ci_runner"):
        return "ai_agent"
    return "human"


def _detect_discovery_channel() -> str:
    """Detects package execution harness channel (uvx, pip, brew, npx, direct)."""
    argv_str = " ".join(sys.argv).lower()
    if "uvx" in argv_str or "uv" in sys.executable:
        return "uvx"
    if "brew" in sys.executable or "homebrew" in sys.executable:
        return "homebrew"
    if "npx" in argv_str or "node" in argv_str:
        return "npx"
    if IN_VIRTUAL_ENV:
        return "pip_venv"
    return "direct_python"


ACTOR_TYPE = _detect_actor_type()
DISCOVERY_CHANNEL = _detect_discovery_channel()

# Ground-truth client identity from the MCP initialize handshake.
# Populated lazily on the first tool call (the handshake happens after boot).
_RUNTIME_CLIENT = {"name": None, "version": None, "agent": None}


def capture_client_info(mcp_server):
    """Capture clientInfo from the MCP handshake (raw name kept, bucket added)."""
    if _RUNTIME_CLIENT["name"] is not None:
        return
    try:
        ctx = mcp_server._mcp_server.request_context
        if ctx and ctx.session and ctx.session.client_params and ctx.session.client_params.clientInfo:
            info = ctx.session.client_params.clientInfo
            _RUNTIME_CLIENT["name"] = str(info.name)[:100]
            _RUNTIME_CLIENT["version"] = str(info.version)[:50]
            _RUNTIME_CLIENT["agent"] = _normalize_client_name(info.name)
    except Exception:
        pass


def send_telemetry(event: str, properties: dict = None):
    """
    Fire-and-forget 100% anonymous telemetry via the project gateway.
    Respects opt-out flags: GA_MCP_TELEMETRY=false, DISABLE_TELEMETRY=1,
    DO_NOT_TRACK=1, NO_TELEMETRY=1 — nothing is sent anywhere when set.
    All string properties are PII-scrubbed centrally before sending.
    Swallows all network errors so MCP operation is never impacted.
    """
    if TELEMETRY_DISABLED:
        return

    def _send():
        try:
            props = {
                "schema_version": SCHEMA_VERSION,
                "mcp_server_name": "google-analytics",
                "$os": platform.system(),
                "python_version": platform.python_version(),
                "mcp_server_version": MCP_SERVER_VERSION,
                "cpu_arch": CPU_ARCH,
                "in_virtual_env": IN_VIRTUAL_ENV,
                "timezone_offset": TIMEZONE_OFFSET,
                "actor_type": ACTOR_TYPE,
                "agent_name": _RUNTIME_CLIENT["agent"] or AGENT_NAME,
                "run_context": RUN_CONTEXT,
                "discovery_channel": DISCOVERY_CHANNEL,
                "session_id": SESSION_ID,
                **(properties or {}),
            }
            if INTERNAL_RUN:
                props["internal_run"] = True
            if INSTALL_SOURCE:
                props.setdefault("install_source", INSTALL_SOURCE)
                props.setdefault("install_source_raw", INSTALL_SOURCE_RAW)
            if _RUNTIME_CLIENT["name"]:
                props.setdefault("mcp_client_name", _RUNTIME_CLIENT["name"])
                props.setdefault("mcp_client_version", _RUNTIME_CLIENT["version"])
            props = _scrub(props)
            # Anonymous events: no person profiles are created in the store.
            props["$process_person_profile"] = False
            payload = {
                "event": event,
                "distinct_id": INSTALLATION_ID,
                "properties": props,
            }
            req = urllib.request.Request(
                GATEWAY_URL,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    # Product UA: default library UAs are rejected at the edge
                    "User-Agent": f"google-analytics-mcp/{MCP_SERVER_VERSION}",
                },
            )
            urllib.request.urlopen(req, timeout=3)
        except Exception:
            pass  # Silently fail on network issues or timeouts

    # Run in a daemon thread so it doesn't block execution or shutdown
    threading.Thread(target=_send, daemon=True).start()


def _track_version_change():
    """
    Emit package_download on the first run of each new version — PyPI has no
    install hooks, so this is the install/upgrade funnel signal (one event per
    version per installation).
    """
    try:
        version_file = Path.home() / ".ga4_mcp" / "last_run_version"
        previous = version_file.read_text(encoding="utf-8").strip() if version_file.exists() else None
        if previous == MCP_SERVER_VERSION:
            return
        send_telemetry("package_download", {
            "version": MCP_SERVER_VERSION,
            "previous_version": previous,
            "first_download": previous is None,
        })
        version_file.write_text(MCP_SERVER_VERSION, encoding="utf-8")
    except Exception:
        pass


def announce_and_fire_boot_events():
    """First-run disclosure BEFORE the first event, then install/version events."""
    if TELEMETRY_DISABLED:
        return
    if IS_FIRST_INSTALL:
        print(
            "google-analytics-mcp collects anonymous usage telemetry (no PII, no GA4 data, "
            "no paths — see 'Telemetry & Privacy' in the README). "
            "Opt out any time with DISABLE_TELEMETRY=1 or DO_NOT_TRACK=1.",
            file=sys.stderr,
        )
        send_telemetry("server_first_install", {"first_install_version": MCP_SERVER_VERSION})
    _track_version_change()
