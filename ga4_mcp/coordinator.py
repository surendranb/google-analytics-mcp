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

# Generate a session ID (random UUID per process run)
SESSION_ID = str(uuid.uuid4())

# Environment Context
IN_VIRTUAL_ENV = sys.prefix != sys.base_prefix
CPU_ARCH = platform.machine()
TIMEZONE_OFFSET = -time.timezone if (time.localtime().tm_isdst == 0) else -time.altzone

def send_telemetry(event: str, properties: dict = None):
    """
    Fire-and-forget anonymous telemetry.
    ponytail: We swallow all exceptions to ensure telemetry never crashes the user's MCP.
    """
    if os.getenv("GA_MCP_TELEMETRY", "true").lower() == "false":
        return

    def _send():
        try:
            payload = {
                "api_key": POSTHOG_API_KEY,
                "event": event,
                "distinct_id": SESSION_ID,
                "properties": {
                    "$os": platform.system(),
                    "python_version": platform.python_version(),
                    "mcp_server_version": MCP_SERVER_VERSION,
                    "cpu_arch": CPU_ARCH,
                    "in_virtual_env": IN_VIRTUAL_ENV,
                    "timezone_offset": TIMEZONE_OFFSET,
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
                # Intercept tool calls if the server failed to initialize properly
                if SERVER_INIT_ERROR:
                    status = "error"
                    error_category = "InitError"
                    return f"Configuration Error: {SERVER_INIT_ERROR}. Please instruct the user to fix their setup."

                result = func(*w_args, **w_kwargs)
                
                # Analyze result dictionaries for specific error/warning types
                if isinstance(result, dict):
                    if "error" in result:
                        status = "error"
                        err_str = str(result["error"])
                        if "DO NOT GUESS" in err_str or "Invalid dimension" in err_str or "Invalid metric" in err_str:
                            error_category = "SchemaHallucination"
                        elif "IAM Error" in err_str or "PermissionDenied" in err_str or "403" in err_str:
                            error_category = "IAMError"
                        else:
                            error_category = "APIError"
                    elif "warning" in result:
                        status = "warning"
                        error_category = "SmartVolumeWarning"
                    elif "metadata" in result:
                        rows_returned = result.get("metadata", {}).get("returned_rows", 0)
                        
                return result
            except Exception as e:
                status = "exception"
                error_category = e.__class__.__name__
                raise
            finally:
                latency_ms = int((time.time() - start_time) * 1000)
                
                # Extract client info and CI environment
                client_name = "unknown"
                client_version = "unknown"
                try:
                    ctx = mcp._mcp_server.request_context
                    if ctx and ctx.session and ctx.session.client_params and ctx.session.client_params.clientInfo:
                        client_name = ctx.session.client_params.clientInfo.name
                        client_version = ctx.session.client_params.clientInfo.version
                except Exception as e:
                    import sys
                    print(f"Error extracting telemetry context: {e}", file=sys.stderr)
                
                is_ci = os.getenv("CI", "false").lower() == "true" or os.getenv("GITHUB_ACTIONS", "false").lower() == "true"
                tz_name = time.tzname[0] if hasattr(time, "tzname") and time.tzname else "unknown"

                props = {
                    "tool_name": func.__name__,
                    "status": status,
                    "latency_ms": latency_ms,
                    "mcp_client_name": client_name,
                    "mcp_client_version": client_version,
                    "is_ci": is_ci,
                    "timezone": tz_name,
                    "rows_returned": rows_returned
                }
                
                # Extract behavioral metadata for reporting tool
                if func.__name__ == "get_ga4_data":
                    try:
                        sig = inspect.signature(func)
                        bound = sig.bind(*w_args, **w_kwargs)
                        bound.apply_defaults()
                        args_dict = bound.arguments
                        
                        props["dimensions_count"] = len(args_dict.get("dimensions") or [])
                        props["metrics_count"] = len(args_dict.get("metrics") or [])
                        props["has_dimension_filter"] = bool(args_dict.get("dimension_filter"))
                        props["is_estimate_only"] = bool(args_dict.get("estimate_only"))
                    except Exception as e:
                        pass
                        
                if error_category:
                    props["error_category"] = error_category
                    
                # Capture specific error messages based on the state
                if SERVER_INIT_ERROR:
                    props["error_message"] = str(SERVER_INIT_ERROR)
                elif error_category == "exception" or status == "exception":
                    import sys
                    _, exc_value, _ = sys.exc_info()
                    props["error_message"] = str(exc_value) if exc_value else "Unknown Exception"
                elif isinstance(result, dict) and "error" in result:
                    props["error_message"] = str(result["error"])
                elif isinstance(result, dict) and "warning" in result:
                    props["error_message"] = str(result["warning"])
                    
                send_telemetry("tool_executed", props)
                
        # Register the wrapped function using the original tool decorator
        return _original_tool(*args, **kwargs)(wrapper)
    return decorator

mcp.tool = _telemetry_tool
