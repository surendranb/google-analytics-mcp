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

import os
import sys
import time
import json
import uuid
import platform
import threading
import functools
import inspect
import urllib.request
from pathlib import Path
from mcp.server.fastmcp import FastMCP

# PostHog configuration
POSTHOG_API_KEY = "phc_Aik6H3pf5P9dPBrWLjd6N3wzsVAD6tJnmmEhFwW8Pzsi"
POSTHOG_HOST = "https://us.i.posthog.com"

# Extract the package version so it can be stamped on all telemetry
try:
    import importlib.metadata
    MCP_SERVER_VERSION = importlib.metadata.version("google-analytics-mcp")
except Exception:
    MCP_SERVER_VERSION = "unknown"

# Persistent Anonymous Installation ID & First-Run Detection
def _init_anonymous_identity():
    """
    Manages a purely random anonymous installation UUID stored locally.
    Contains NO PII (no usernames, hostnames, IP addresses, or path names).
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

# Environment Context & Actor Detection
IN_VIRTUAL_ENV = sys.prefix != sys.base_prefix
CPU_ARCH = platform.machine()
TIMEZONE_OFFSET = -time.timezone if (time.localtime().tm_isdst == 0) else -time.altzone

def _detect_actor_type() -> str:
    """
    Determines if the server is running in an autonomous AI agent environment vs human shell.
    No PII collected.
    """
    if not sys.stdin.isatty():
        return "ai_agent"
    if any(k in os.environ for k in ["CLAUDE_CODE", "CURSOR_TRACE", "GEMINI_CLI", "ANTIGRAVITY"]):
        return "ai_agent"
    return "human"

def _detect_discovery_channel() -> str:
    """
    Detects package execution harness channel (uvx, pip, brew, npx, direct).
    """
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

def send_telemetry(event: str, properties: dict = None):
    """
    Fire-and-forget 100% anonymous telemetry.
    Strictly respects opt-out flags: GA_MCP_TELEMETRY=false, DO_NOT_TRACK=1, NO_TELEMETRY=1.
    Swallows all network errors so MCP operation is never impacted.
    """
    # Strict Opt-Out Check
    if os.getenv("GA_MCP_TELEMETRY", "true").lower() in ("false", "0", "off"):
        return
    if os.getenv("DO_NOT_TRACK", "0").lower() in ("true", "1") or os.getenv("NO_TELEMETRY", "0").lower() in ("true", "1"):
        return

    def _send():
        try:
            payload = {
                "api_key": POSTHOG_API_KEY,
                "event": event,
                "distinct_id": INSTALLATION_ID,
                "properties": {
                    "mcp_server_name": "google-analytics",
                    "$os": platform.system(),
                    "python_version": platform.python_version(),
                    "mcp_server_version": MCP_SERVER_VERSION,
                    "cpu_arch": CPU_ARCH,
                    "in_virtual_env": IN_VIRTUAL_ENV,
                    "timezone_offset": TIMEZONE_OFFSET,
                    "actor_type": ACTOR_TYPE,
                    "discovery_channel": DISCOVERY_CHANNEL,
                    **(properties or {})
                }
            }
            req = urllib.request.Request(
                f"{POSTHOG_HOST}/capture/",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            urllib.request.urlopen(req, timeout=3)
        except Exception:
            pass  # Silently fail on network issues or timeouts

    # Run in a daemon thread so it doesn't block execution or shutdown
    threading.Thread(target=_send, daemon=True).start()

# Fire First-Install Telemetry Event on First Machine Run
if IS_FIRST_INSTALL:
    send_telemetry("server_first_install", {
        "first_install_version": MCP_SERVER_VERSION
    })

# Global state to capture boot-time configuration errors without crashing the server
SERVER_INIT_ERROR = None

# Creates the singleton mcp object that is imported by all other modules.
mcp = FastMCP("Google Analytics 4")

# Monkey-patch mcp.tool to automatically wrap all registered tools with telemetry
_original_tool = mcp.tool

def _telemetry_tool(*args, **kwargs):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*w_args, **w_kwargs):
            start_time = time.time()
            status = "success"
            error_category = None
            rows_returned = 0
            result = None

            try:
                result = func(*w_args, **w_kwargs)
                if isinstance(result, list):
                    rows_returned = len(result)
                elif isinstance(result, dict) and "rows" in result:
                    rows_returned = len(result.get("rows", []))
                return result
            except Exception as e:
                status = "error"
                error_category = type(e).__name__
                raise e
            finally:
                latency_ms = int((time.time() - start_time) * 1000)
                send_telemetry("tool_executed", {
                    "tool_name": func.__name__,
                    "latency_ms": latency_ms,
                    "status": status,
                    "error_category": error_category,
                    "rows_returned": rows_returned
                })

        return _original_tool(*args, **kwargs)(wrapper)

    if len(args) == 1 and callable(args[0]):
        return decorator(args[0])
    return decorator

mcp.tool = _telemetry_tool
