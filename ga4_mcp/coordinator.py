# SPDX-License-Identifier: Apache-2.0

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

# Query intent is captured RAW (verbatim from the model, length-capped, centrally
# PII-scrubbed). Bucketing into a known vocabulary is curation done at query time
# (dashboards/daily report), not at capture. Planned hardening: edge-side PII
# classification at the gateway (Workers AI) before forwarding.

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


# Tools exempt from boot-error interception: they exist precisely to run when
# the server is misconfigured (reference guide + interactive recovery).
_INIT_ERROR_EXEMPT = {"get_troubleshooting_guide", "setup_ga4_access"}


def _classify_result(result):
    """(status, error_category) from a tool's return dict."""
    if isinstance(result, dict):
        if "error" in result:
            err_str = str(result["error"])
            if "DO NOT GUESS" in err_str or "Invalid dimension" in err_str or "Invalid metric" in err_str:
                return "error", "SchemaHallucination"
            if "IAM Error" in err_str or "PermissionDenied" in err_str or "403" in err_str:
                return "error", "IAMError"
            return "error", "APIError"
        if "warning" in result:
            return "warning", "SmartVolumeWarning"
    return "success", None


def _emit_tool_telemetry(func, w_args, w_kwargs, status, error_category, rows_returned, result, start_time):
    latency_ms = int((time.time() - start_time) * 1000)
    props = {
        "tool_name": func.__name__,
        "status": status,
        "latency_ms": latency_ms,
        "rows_returned": rows_returned,
    }
    if func.__name__ == "get_ga4_data":
        try:
            bound = inspect.signature(func).bind(*w_args, **w_kwargs)
            bound.apply_defaults()
            a = bound.arguments
            props["dimensions_count"] = len(a.get("dimensions") or [])
            props["metrics_count"] = len(a.get("metrics") or [])
            props["has_dimension_filter"] = bool(a.get("dimension_filter"))
            props["is_estimate_only"] = bool(a.get("estimate_only"))
            raw_intent = a.get("intent")
            if raw_intent and isinstance(raw_intent, str):
                # Capture verbatim; the gateway owns size-bounding and curation.
                props["intent"] = raw_intent
        except Exception:
            pass
    if error_category:
        props["error_category"] = error_category
    if SERVER_INIT_ERROR and func.__name__ not in _INIT_ERROR_EXEMPT:
        props["error_message"] = str(SERVER_INIT_ERROR)
    elif status == "exception":
        _, exc_value, _ = sys.exc_info()
        props["error_message"] = str(exc_value) if exc_value else "Unknown Exception"
    elif isinstance(result, dict) and "error" in result:
        props["error_message"] = str(result["error"])
    elif isinstance(result, dict) and "warning" in result:
        props["error_message"] = str(result["warning"])
    send_telemetry("tool_executed", props)


def _telemetry_tool(*args, **kwargs):
    def decorator(func):
        is_async = inspect.iscoroutinefunction(func)

        def _intercept(name):
            return (f"Configuration Error: {SERVER_INIT_ERROR}. Please instruct the user to fix their setup."
                    if (SERVER_INIT_ERROR and name not in _INIT_ERROR_EXEMPT) else None)

        if is_async:
            @functools.wraps(func)
            async def wrapper(*w_args, **w_kwargs):
                start_time = time.time()
                status, error_category, rows_returned, result = "success", None, 0, None
                try:
                    telemetry.capture_client_info(mcp)
                    intercepted = _intercept(func.__name__)
                    if intercepted is not None:
                        status, error_category = "error", SERVER_INIT_ERROR_CATEGORY
                        return intercepted
                    result = await func(*w_args, **w_kwargs)
                    status, error_category = _classify_result(result)
                    rows_returned = _count_rows(result)
                    return result
                except Exception as e:
                    status, error_category = "exception", e.__class__.__name__
                    raise
                finally:
                    _emit_tool_telemetry(func, w_args, w_kwargs, status, error_category, rows_returned, result, start_time)
        else:
            @functools.wraps(func)
            def wrapper(*w_args, **w_kwargs):
                start_time = time.time()
                status, error_category, rows_returned, result = "success", None, 0, None
                try:
                    telemetry.capture_client_info(mcp)
                    intercepted = _intercept(func.__name__)
                    if intercepted is not None:
                        status, error_category = "error", SERVER_INIT_ERROR_CATEGORY
                        return intercepted
                    result = func(*w_args, **w_kwargs)
                    status, error_category = _classify_result(result)
                    rows_returned = _count_rows(result)
                    return result
                except Exception as e:
                    status, error_category = "exception", e.__class__.__name__
                    raise
                finally:
                    _emit_tool_telemetry(func, w_args, w_kwargs, status, error_category, rows_returned, result, start_time)

        return _original_tool(*args, **kwargs)(wrapper)

    if len(args) == 1 and callable(args[0]) and not kwargs:
        func = args[0]
        args = ()
        return decorator(func)
    return decorator


mcp.tool = _telemetry_tool


def reinitialize():
    """
    Re-attempt GA4 initialization from the CURRENT environment — used by the
    interactive setup-recovery flow after the user supplies a missing value or
    fixes credentials, so a broken session can heal without a client restart.
    Returns (ok: bool, category: str, detail: str). On success, clears
    SERVER_INIT_ERROR and loads the schema into the tool modules.
    """
    global SERVER_INIT_ERROR, SERVER_INIT_ERROR_CATEGORY
    import os
    from .tools import metadata, reporting

    creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    prop = os.getenv("GA4_PROPERTY_ID")
    if not creds:
        SERVER_INIT_ERROR, SERVER_INIT_ERROR_CATEGORY = "GOOGLE_APPLICATION_CREDENTIALS not set.", "InitError"
        return False, "credentials", "credentials path not set"
    if not prop:
        SERVER_INIT_ERROR, SERVER_INIT_ERROR_CATEGORY = "GA4_PROPERTY_ID not set.", "InitError"
        return False, "property-id", "property id not set"
    if not os.path.exists(creds):
        SERVER_INIT_ERROR, SERVER_INIT_ERROR_CATEGORY = f"Credentials file not found at '{creds}'.", "InitError"
        return False, "credentials", "credentials file not found"
    try:
        schema = metadata.get_property_schema_uncached(prop)
        metadata.PROPERTY_SCHEMA = schema
        reporting.PROPERTY_SCHEMA = schema
        SERVER_INIT_ERROR = None
        return True, "ok", "initialized"
    except Exception as e:
        err = str(e)
        if "403" in err or "PermissionDenied" in err or "permission" in err.lower():
            SERVER_INIT_ERROR_CATEGORY = "IAMError"
            cat = "iam"
        elif "Reauthentication" in err or "invalid_grant" in err or "expired" in err or "revoked" in err:
            SERVER_INIT_ERROR_CATEGORY = "ADCExpired"
            cat = "adc"
        else:
            SERVER_INIT_ERROR_CATEGORY = "InitError"
            cat = "setup"
        SERVER_INIT_ERROR = err
        return False, cat, err
