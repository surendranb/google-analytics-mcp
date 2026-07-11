# SPDX-License-Identifier: Apache-2.0

"""Anonymous usage telemetry: identity, environment signals, and transport to
the gateway (workers/install-telemetry/). Opt-out and privacy: see README."""

import os
import re
import sys
import time
import json
import uuid
import atexit
import platform
import threading
import subprocess
import urllib.request
from pathlib import Path

GATEWAY_URL = "https://ga4.builditwithai.xyz/e"
SCHEMA_VERSION = 1

try:
    import importlib.metadata
    MCP_SERVER_VERSION = importlib.metadata.version("google-analytics-mcp")
except Exception:
    MCP_SERVER_VERSION = "unknown"


# Any disable flag wins over GA_MCP_TELEMETRY=true.
def _telemetry_disabled() -> bool:
    if os.getenv("GA_MCP_TELEMETRY", "true").lower() in ("false", "0", "off"):
        return True
    for var in ("DISABLE_TELEMETRY", "DO_NOT_TRACK", "NO_TELEMETRY"):
        if os.getenv(var, "").lower() in ("1", "true", "yes", "on"):
            return True
    return False


TELEMETRY_DISABLED = _telemetry_disabled()

# Set only by our own CI/dev runs, to tag them traffic_class=internal.
INTERNAL_RUN = os.getenv("GA4_MCP_INTERNAL", "").lower() in ("1", "true", "yes")


def _init_anonymous_identity():
    """Random installation UUID in ~/.ga4_mcp/; created on first run, reset by
    deleting the folder. Returns (installation_id, is_first_install)."""
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
        # filesystem not writable: fall back to a non-persistent id
        return f"anon_{uuid.uuid4()}", False


INSTALLATION_ID, IS_FIRST_INSTALL = _init_anonymous_identity()
SESSION_ID = f"sess_{uuid.uuid4()}"  # one per process

IN_VIRTUAL_ENV = sys.prefix != sys.base_prefix
CPU_ARCH = platform.machine()
TIMEZONE_OFFSET = -time.timezone if (time.localtime().tm_isdst == 0) else -time.altzone


# GA4_MCP_SOURCE, set in install snippets; raw value + low-cardinality bucket.
_KNOWN_SOURCES = {
    "readme", "glama", "mcpso", "pulsemcp", "ga4mcp", "setup",
    "cursor_button", "vscode_button", "installer",
}


def _install_source():
    raw = (os.getenv("GA4_MCP_SOURCE") or "").strip().lower()
    if not raw:
        return None, None
    return raw, (raw if raw in _KNOWN_SOURCES else "other")


INSTALL_SOURCE_RAW, INSTALL_SOURCE = _install_source()


# Redaction applied to every outgoing string.
_REDACTIONS = [
    (re.compile(r"\bhttps?://\S+"), "<url>"),
    (re.compile(r"(?:file://)?[A-Za-z]:[\\/](?:[^\\/:*?\"<>|\r\n]+[\\/])+[^\\/:*?\"<>|\r\n ]*"), "<path>"),
    (re.compile(r"(?:file://)?/(?:[\w.@()~+-]+/)+[\w.@()~+-]*"), "<path>"),
    (re.compile(r"(?:[\w.@()~+-]+/){2,}[\w.@()~+-]+"), "<path>"),
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"), "<email>"),
    (re.compile(r"AIza[0-9A-Za-z_\-]{35}"), "<google_key>"),
    (re.compile(r"properties/\d+"), "properties/<id>"),
    # User-defined GA4 field names can carry business context — mask the name
    (re.compile(r"custom(Event|User|Item)?:[\w.-]+"), r"custom\1:<redacted>"),
]


def _scrub(value):
    if isinstance(value, str):
        s = value
        for pattern, replacement in _REDACTIONS:
            s = pattern.sub(replacement, s)
        return s
    if isinstance(value, dict):
        return {k: _scrub(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_scrub(v) for v in value]
    return value


# Map a handshake clientInfo.name to a known bucket.
def _normalize_client_name(raw):
    n = (raw or "").strip().lower()
    if not n or n == "unknown":
        return None
    buckets = [
        ("local-agent-mode", "claude_cowork"),
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
    """Parent-process command names (the agent sits above uvx/python)."""
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
    """Where the server runs, by priority: ci > cloud > terminal > desktop > headless."""
    env = os.environ
    if env.get("GITHUB_ACTIONS", "").lower() == "true" or env.get("CI", "").lower() in ("true", "1"):
        return "ci"
    if ("KUBERNETES_SERVICE_HOST" in env or "AWS_EXECUTION_ENV" in env
            or "ECS_CONTAINER_METADATA_URI" in env or "ECS_CONTAINER_METADATA_URI_V4" in env
            or os.path.exists("/.dockerenv")):
        return "cloud"
    if "TERM_PROGRAM" in env or "SSH_TTY" in env or "SSH_CONNECTION" in env or sys.stdin.isatty():
        return "terminal"
    # macOS GUI apps strip TERM_PROGRAM but set a bundle id
    if env.get("__CFBundleIdentifier"):
        return "desktop"
    if "DISPLAY" in env or "WAYLAND_DISPLAY" in env or env.get("XDG_SESSION_TYPE") in ("x11", "wayland"):
        return "desktop"
    if platform.system() == "Windows" and env.get("SESSIONNAME", "").lower() == "console":
        return "desktop"
    return "headless"


RUN_CONTEXT = _detect_run_context()


def _detect_agent_name() -> str:
    """Best-effort agent from env-var presence, bundle id, and parent processes;
    used before the handshake clientInfo is available."""
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

    bundle = env.get("__CFBundleIdentifier", "").lower()
    if "claudefordesktop" in bundle or "claude-desktop" in bundle:
        return "claude_desktop"
    if "cursor" in bundle:
        return "cursor"
    if "windsurf" in bundle:
        return "windsurf"

    # Before the VSCODE_* check: Cursor/Windsurf also set those vars.
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


def _detect_discovery_channel() -> str:
    """How the package was launched: uvx / homebrew / pip_venv / direct_python.
    (Launch mechanism, not discovery — kept under the old name for query
    continuity; sent as launch_channel too.)"""
    argv_str = " ".join(sys.argv).lower()
    if "uvx" in argv_str or "uv" in sys.executable:
        return "uvx"
    if "brew" in sys.executable or "homebrew" in sys.executable:
        return "homebrew"
    if IN_VIRTUAL_ENV:
        return "pip_venv"
    return "direct_python"


DISCOVERY_CHANNEL = _detect_discovery_channel()


def _raw_env_signals() -> dict:
    """The raw signals run_context/agent_name are derived from, sent alongside
    the labels so they can be re-derived in a query. Flags and short ids only."""
    env = os.environ
    return {
        "term_program": env.get("TERM_PROGRAM"),
        "stdin_tty": sys.stdin.isatty(),
        "has_ssh": ("SSH_TTY" in env or "SSH_CONNECTION" in env),
        "cfbundle_id": env.get("__CFBundleIdentifier"),
        "has_display": ("DISPLAY" in env or "WAYLAND_DISPLAY" in env),
        "container": (os.path.exists("/.dockerenv") or "KUBERNETES_SERVICE_HOST" in env
                      or "AWS_EXECUTION_ENV" in env or "ECS_CONTAINER_METADATA_URI" in env),
        "ci": (env.get("CI", "").lower() in ("true", "1") or env.get("GITHUB_ACTIONS", "").lower() == "true"),
        "has_claudecode": ("CLAUDECODE" in env or "CLAUDE_CODE" in env or any(k.startswith("CLAUDE_CODE_") for k in env)),
        "has_cursor": any(k in env for k in ("CURSOR_TRACE_ID", "CURSOR_TRACE", "CURSOR_VERSION", "CURSOR_SESSION_ID")),
        "has_gemini": ("GEMINI_CLI" in env or "GEMINI_EXTENSION" in env),
        "has_windsurf": ("WINDSURF_VERSION" in env or any(k.startswith("CODEIUM_") for k in env)),
        "has_antigravity": ("ANTIGRAVITY" in env or "AGY_SESSION" in env),
        "has_vscode": ("VSCODE_PID" in env or "VSCODE_IPC_HOOK" in env or "VSCODE_CWD" in env),
        "parent_procs": _process_ancestor_names(),
    }


ENV_SIGNALS = _raw_env_signals()

# Handshake clientInfo, populated on the first tool call (handshake is post-boot).
_RUNTIME_CLIENT = {
    "name": None, "version": None, "agent": None, "title": None,
    "description": None, "protocol_version": None, "caps": None, "caps_raw": None,
}


def capture_client_info(mcp_server):
    """Read clientInfo, protocol version, and capability flags from the handshake."""
    if _RUNTIME_CLIENT["name"] is not None:
        return
    try:
        ctx = mcp_server._mcp_server.request_context
        params = ctx.session.client_params if (ctx and ctx.session) else None
        if not params or not params.clientInfo:
            return
        info = params.clientInfo
        _RUNTIME_CLIENT["name"] = str(info.name)
        _RUNTIME_CLIENT["version"] = str(info.version)
        _RUNTIME_CLIENT["agent"] = _normalize_client_name(info.name)
        title = getattr(info, "title", None)
        _RUNTIME_CLIENT["title"] = str(title) if title else None
        desc = getattr(info, "description", None)
        _RUNTIME_CLIENT["description"] = str(desc) if desc else None
        pv = getattr(params, "protocolVersion", None)
        _RUNTIME_CLIENT["protocol_version"] = str(pv) if pv else None
        caps = getattr(params, "capabilities", None)
        if caps is not None:
            _RUNTIME_CLIENT["caps"] = {
                "client_supports_sampling": getattr(caps, "sampling", None) is not None,
                "client_supports_roots": getattr(caps, "roots", None) is not None,
                "client_supports_elicitation": getattr(caps, "elicitation", None) is not None,
                "client_has_experimental_caps": bool(getattr(caps, "experimental", None)),
            }
            # Raw capabilities verbatim (incl. experimental keys) — the booleans
            # above are a convenience, this is the record.
            try:
                _RUNTIME_CLIENT["caps_raw"] = caps.model_dump(mode="json", exclude_none=True)
            except Exception:
                pass
    except Exception:
        pass


def client_supports_url_elicitation() -> bool:
    """True if the handshake advertised URL-mode elicitation (elicitation.url).
    Read from the raw capabilities we capture; used to offer guided-navigation
    recovery only to clients that can open a URL."""
    caps = _RUNTIME_CLIENT.get("caps_raw")
    if not isinstance(caps, dict):
        return False
    elicit = caps.get("elicitation")
    return isinstance(elicit, dict) and "url" in elicit


# In-flight sender threads, drained briefly at exit — short-lived sessions
# (a large share of real boots) otherwise lose their events to process death.
_PENDING_SENDS = []


def _drain_pending_sends(deadline_seconds=2.0):
    end = time.time() + deadline_seconds
    for th in list(_PENDING_SENDS):
        remaining = end - time.time()
        if remaining <= 0:
            break
        try:
            th.join(remaining)
        except Exception:
            pass


atexit.register(_drain_pending_sends)


def send_telemetry(event: str, properties: dict = None):
    """Fire-and-forget event to the gateway on a daemon thread (joined briefly
    at exit). No-op when opted out; never raises."""
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
                "agent_name": _RUNTIME_CLIENT["agent"] or AGENT_NAME,
                "run_context": RUN_CONTEXT,
                "discovery_channel": DISCOVERY_CHANNEL,
                "launch_channel": DISCOVERY_CHANNEL,
                "raw_env": ENV_SIGNALS,  # the raw clues behind run_context/agent_name
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
            if _RUNTIME_CLIENT["title"]:
                props.setdefault("mcp_client_title", _RUNTIME_CLIENT["title"])
            if _RUNTIME_CLIENT["description"]:
                props.setdefault("mcp_client_description", _RUNTIME_CLIENT["description"])
            if _RUNTIME_CLIENT["protocol_version"]:
                props.setdefault("mcp_protocol_version", _RUNTIME_CLIENT["protocol_version"])
            if _RUNTIME_CLIENT["caps"]:
                for k, v in _RUNTIME_CLIENT["caps"].items():
                    props.setdefault(k, v)
            if _RUNTIME_CLIENT["caps_raw"] is not None:
                props.setdefault("client_capabilities", _RUNTIME_CLIENT["caps_raw"])
            props = _scrub(props)
            props["$process_person_profile"] = False  # no person profiles
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
            pass

    th = threading.Thread(target=_send, daemon=True)
    th.start()
    _PENDING_SENDS.append(th)
    if len(_PENDING_SENDS) > 8:
        _PENDING_SENDS[:] = [t for t in _PENDING_SENDS if t.is_alive()]


def _track_version_change():
    """Emit package_download once per version (PyPI has no install hook)."""
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
