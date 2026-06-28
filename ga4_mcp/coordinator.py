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
import time
import json
import uuid
import platform
import threading
import functools
import urllib.request
from mcp.server.fastmcp import FastMCP

# PostHog configuration
POSTHOG_API_KEY = "phc_Aik6H3pf5P9dPBrWLjd6N3wzsVAD6tJnmmEhFwW8Pzsi"
POSTHOG_HOST = "https://us.i.posthog.com"

# Generate a session ID (random UUID per process run)
SESSION_ID = str(uuid.uuid4())

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
            try:
                result = func(*w_args, **w_kwargs)
                # GA4 MCP often returns {"error": ...} on handled errors
                if isinstance(result, dict) and "error" in result:
                    status = "error"
                return result
            except Exception:
                status = "exception"
                raise
            finally:
                latency_ms = int((time.time() - start_time) * 1000)
                send_telemetry("tool_executed", {
                    "tool_name": func.__name__,
                    "status": status,
                    "latency_ms": latency_ms
                })
                
        # Register the wrapped function using the original tool decorator
        return _original_tool(*args, **kwargs)(wrapper)
    return decorator

mcp.tool = _telemetry_tool
