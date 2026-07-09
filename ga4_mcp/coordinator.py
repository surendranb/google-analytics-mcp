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
MCP server wiring: creates the FastMCP singleton and wraps every registered
tool with telemetry and boot-error interception. All telemetry mechanics
(identity, detection, scrubbing, transport) live in ga4_mcp.telemetry.
"""

import sys
import time
import inspect
import functools

from mcp.server.fastmcp import FastMCP

from . import telemetry
from .telemetry import send_telemetry  # re-exported; imported from here by server.py

# Backward-compatible re-exports (server.py and external code read these here)
MCP_SERVER_VERSION = telemetry.MCP_SERVER_VERSION
TELEMETRY_DISABLED = telemetry.TELEMETRY_DISABLED
INSTALLATION_ID = telemetry.INSTALLATION_ID
SESSION_ID = telemetry.SESSION_ID
AGENT_NAME = telemetry.AGENT_NAME
RUN_CONTEXT = telemetry.RUN_CONTEXT
ACTOR_TYPE = telemetry.ACTOR_TYPE
DISCOVERY_CHANNEL = telemetry.DISCOVERY_CHANNEL
_scrub = telemetry._scrub

# Global state to capture boot-time configuration errors without crashing the
# server. CATEGORY separates config-failure families (InitError, ADCExpired,
# IAMError) so each can be measured and fixed independently.
SERVER_INIT_ERROR = None
SERVER_INIT_ERROR_CATEGORY = "InitError"

# Fixed vocabulary for the model-declared query intent (never free text)
_INTENT_VALUES = {
    "traffic_overview", "acquisition", "content_performance", "ecommerce_revenue",
    "user_behavior", "geography_devices", "campaign_analysis", "seo", "debugging", "other",
}

# Creates the singleton mcp object that is imported by all other modules.
mcp = FastMCP("Google Analytics 4")

# First-run disclosure + install/version events (no-op when opted out)
telemetry.announce_and_fire_boot_events()

# Monkey-patch mcp.tool to automatically wrap all registered tools with telemetry
_original_tool = mcp.tool


def _count_rows(result):
    """
    Rows/items returned by a tool, shape-aware. Reporting tools carry
    metadata.returned_rows or rows; discovery tools return either a dict with
    one nested collection (search_schema, categories) or a flat mapping.
    """
    if isinstance(result, list):
        return len(result)
    if not isinstance(result, dict):
        return 0
    if "metadata" in result:
        return result.get("metadata", {}).get("returned_rows", 0)
    if "rows" in result:
        return len(result.get("rows", []))
    if any(k in result for k in ("error", "warning", "message")):
        return 0
    nested = [v for v in result.values() if isinstance(v, (dict, list))]
    if nested:
        return sum(len(v) for v in nested)
    return len(result)


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
                telemetry.capture_client_info(mcp)

                # Intercept tool calls if the server failed to initialize properly
                if SERVER_INIT_ERROR and func.__name__ != "get_troubleshooting_guide":
                    status = "error"
                    error_category = SERVER_INIT_ERROR_CATEGORY
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

                rows_returned = _count_rows(result)

                return result
            except Exception as e:
                status = "exception"
                error_category = e.__class__.__name__
                raise
            finally:
                latency_ms = int((time.time() - start_time) * 1000)

                props = {
                    "tool_name": func.__name__,
                    "status": status,
                    "latency_ms": latency_ms,
                    "rows_returned": rows_returned,
                }

                # Behavioral metadata for the reporting tool (shape only, never values)
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
                        # Model-declared query intent: fixed vocabulary only, never free text
                        raw_intent = args_dict.get("intent")
                        if raw_intent:
                            props["intent"] = raw_intent if raw_intent in _INTENT_VALUES else "other"
                    except Exception:
                        pass

                if error_category:
                    props["error_category"] = error_category

                # Error messages are PII-scrubbed centrally in send_telemetry
                if SERVER_INIT_ERROR:
                    props["error_message"] = str(SERVER_INIT_ERROR)
                elif status == "exception":
                    _, exc_value, _ = sys.exc_info()
                    props["error_message"] = str(exc_value) if exc_value else "Unknown Exception"
                elif isinstance(result, dict) and "error" in result:
                    props["error_message"] = str(result["error"])
                elif isinstance(result, dict) and "warning" in result:
                    props["error_message"] = str(result["warning"])

                send_telemetry("tool_executed", props)

        # Register the wrapped function using the original tool decorator
        return _original_tool(*args, **kwargs)(wrapper)

    # Support bare @mcp.tool usage (no parentheses)
    if len(args) == 1 and callable(args[0]) and not kwargs:
        func = args[0]
        args = ()
        return decorator(func)
    return decorator


mcp.tool = _telemetry_tool
