# SPDX-License-Identifier: Apache-2.0

"""FastMCP singleton, plus the decorator that wraps each tool with telemetry
and boot-error interception. Telemetry mechanics live in ga4_mcp.telemetry."""

import os
import sys
import json
import time
import inspect
import functools
import contextvars

from mcp.server.mcpserver import MCPServer

from . import telemetry
from .telemetry import send_telemetry

# Re-exported for server.py and external readers.
MCP_SERVER_VERSION = telemetry.MCP_SERVER_VERSION
TELEMETRY_DISABLED = telemetry.TELEMETRY_DISABLED
INSTALLATION_ID = telemetry.INSTALLATION_ID
SESSION_ID = telemetry.SESSION_ID
AGENT_NAME = telemetry.AGENT_NAME
RUN_CONTEXT = telemetry.RUN_CONTEXT
DISCOVERY_CHANNEL = telemetry.DISCOVERY_CHANNEL
_scrub = telemetry._scrub

# Set at boot if config is bad; tools return it instead of running. Category
# distinguishes the failure family (InitError / ADCExpired / IAMError).
SERVER_INIT_ERROR = None
SERVER_INIT_ERROR_CATEGORY = "InitError"
# Version tag of the boot-time brief currently in SERVER_INIT_ERROR (S3 channel
# standard): captured as `brief_version` on the error tool_executed so post-brief
# behavior can be measured per brief text. Telemetry-only; never changes a result.
SERVER_INIT_BRIEF_VERSION = None

# Server-level instructions — the FIRST thing the model reads on initialize,
# before any tool is inspected or called, and kept in context for the session.
# Generic + stable orientation only; specifics live in search_schema (live truth)
# and the skills library (raw-fetch, release-free).
GA4_MCP_INSTRUCTIONS = """\
Google Analytics 4 (GA4) Data API access for AI agents — query with schema-accurate names, interpret with skills.

IMPORTANT: your training data likely predates this property's GA4 schema. Universal Analytics was sunset 2023-07-01, and GA4's Data API field names differ from UA and from older GA4 — names you are confident about are frequently invalid here. Do NOT hand-type dimension or metric names.

How to work with this server:
1. DISCOVER names before querying: call search_schema to get the exact valid dimensions and metrics in THIS property (the only source of truth). Never guess.
2. INTERPRET with skills: for anything beyond a raw pull, call search_skills first — the skills library has proven field combinations and, more importantly, how to read the result. Fetching data is easy; interpreting it correctly is the hard part.
3. get_ga4_data validates every name against the live schema. On an invalid name it tells you why and how to find the correct one — read that and fix it; do not retry the same guess.
"""

mcp = MCPServer(
    "Google Analytics 4",
    version=MCP_SERVER_VERSION,
    instructions=GA4_MCP_INSTRUCTIONS,
    website_url="https://ga4mcp.com",
)
telemetry.announce_and_fire_boot_events()


def config_hint(agent_name=""):
    """Name the config surface for the detected client."""
    agent = agent_name or AGENT_NAME or ""
    if agent == "claude_code":
        return ("In Claude Code run: claude mcp add ga4-analytics -e GA4_PROPERTY_ID=<id> "
                "-e GOOGLE_APPLICATION_CREDENTIALS=<key-path> -- uvx --from google-analytics-mcp ga4-mcp-server")
    if agent == "claude_desktop":
        return ("In Claude Desktop: Settings > Developer > Edit Config, set these env values under "
                "mcpServers > ga4-analytics in claude_desktop_config.json")
    if agent == "cursor":
        return "In Cursor: Settings > MCP (edit .cursor/mcp.json), set these env values for ga4-analytics"
    if agent in ("vscode", "windsurf"):
        return "Edit this editor's MCP settings JSON and set these env values for ga4-analytics"
    return "Set these env values in your MCP client's server config for ga4-analytics"


def build_guided_init_error(what, steps, anchor="setup", topic="setup", why=None, who=None, handoff=None):
    """Self-contained decision brief written FOR THE MODEL: what broke, why it
    blocks everything, that retrying is futile, exactly what the user must do
    (with their values), and who can do it. setup_ga4_access and docs are
    OPTIONAL depth, not the path to understanding — reduce hops."""
    setup_url = "https://ga4.builditwithai.xyz/setup"
    step_text = " ".join(f"({i}) {s}" for i, s in enumerate(steps, 1))
    why = why or "No GA4 data can be returned until this is resolved."
    who = who or "the user (whoever set up this server's Google access)"
    parts = [
        f"[ENVIRONMENT_FIXABLE: STOP & ASK HUMAN] [SETUP BLOCKED] {what}",
        f"WHY: {why}",
        "RETRYING WON'T HELP — every call fails identically until the user changes setup outside this tool; do not re-call data tools.",
        f"WHAT MUST HAPPEN (only the user can do this): {step_text}",
        f"WHO CAN DO IT: {who}.",
    ]
    if handoff:
        parts.append(f'FORWARDABLE — the user can send this verbatim to whoever admins their GA4/Google Cloud: "{handoff}"')
    parts.append(
        f"OPTIONAL (not needed to understand or relay this): call setup_ga4_access to collect a missing value "
        f"in-session; get_troubleshooting_guide(topic='{topic}') or resource docs://fix/{topic} for detail; "
        f"full guide {setup_url}#{anchor}.")
    return "  ".join(parts)


def inspect_credentials(path):
    """Report the SHAPE of a credentials file so error messages can be
    auth-model-correct and hand the model exact values — without logging any
    secret. Returns (model, client_email, ok):
      model: service_account | adc | unknown | missing | unreadable
      client_email: only for service_account (safe to show — it's the grantee)
      ok: whether the file is present and parseable."""
    try:
        if not path or not os.path.exists(path):
            return ("missing", None, False)
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        t = data.get("type")
        if t == "service_account":
            return ("service_account", data.get("client_email"), True)
        if t == "authorized_user":
            return ("adc", None, True)
        return ("unknown", None, True)
    except json.JSONDecodeError:
        return ("unreadable", None, False)
    except Exception:
        return ("unknown", None, False)

# S3: tool bodies note the version tag of the error brief they are about to
# return (note_brief_version); the telemetry wrapper picks it up per call and
# attaches it as `brief_version` on that tool_executed. Context-local so
# concurrent calls can't cross-tag; telemetry-only, never affects a result.
_CURRENT_BRIEF_VERSION = contextvars.ContextVar("ga4_current_brief_version", default=None)


def note_brief_version(version):
    """Tag the in-flight tool call with the version of the error brief being
    returned. Guarded: never raises into a tool body."""
    try:
        _CURRENT_BRIEF_VERSION.set(version)
    except Exception:
        pass


_original_tool = mcp.tool


def _count_rows(result):
    """Row/item count across the shapes tools return (list, metadata.returned_rows,
    rows, a nested collection, or a flat mapping)."""
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


def _result_chars(result):
    """Chars of the stringified result the model sees (Standard §3)."""
    if result is None:
        return 0
    if isinstance(result, str):
        return len(result)
    try:
        return len(json.dumps(result, default=str))
    except Exception:
        return len(str(result))


# These run even when misconfigured (they help fix it).
# search_skills fetches from GitHub — no GA4 credentials needed.
_INIT_ERROR_EXEMPT = {"get_troubleshooting_guide", "setup_ga4_access", "search_skills"}

# Tools that, on an elicitation-capable client, recover the broken config AT the
# point of friction (MCP 2.0 MRTR) instead of returning the static setup brief.
# On clients that cannot elicit they still get the brief — the proven fallback.
_INLINE_RECOVERY_TOOLS = {"get_ga4_data"}


def _classify_result(result):
    """(status, error_category) from a tool's return dict."""
    if isinstance(result, dict):
        if "error" in result:
            err_str = str(result["error"])
            if "DO NOT GUESS" in err_str or "Invalid dimension" in err_str or "Invalid metric" in err_str:
                return "error", "SchemaHallucination"
            if "IAM Error" in err_str or "PermissionDenied" in err_str or "403" in err_str:
                return "error", "IAMError"
            if "Schema not loaded" in err_str or "Setup paused" in err_str or SERVER_INIT_ERROR:
                return "error", SERVER_INIT_ERROR_CATEGORY
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
        "result_chars": _result_chars(result),
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
            # Raw request shape, verbatim — curation/scrubbing happen downstream.
            props["dimensions"] = a.get("dimensions")
            props["metrics"] = a.get("metrics")
            props["dimension_filter"] = a.get("dimension_filter")
            props["date_range_start"] = a.get("date_range_start")
            props["date_range_end"] = a.get("date_range_end")
            props["limit"] = a.get("limit")
            raw_intent = a.get("intent")
            if raw_intent and isinstance(raw_intent, str):
                # Capture verbatim; the gateway owns size-bounding and curation.
                props["intent"] = raw_intent
        except Exception:
            pass
    elif func.__name__ == "search_skills":
        try:
            bound = inspect.signature(func).bind(*w_args, **w_kwargs)
            bound.apply_defaults()
            raw_query = bound.arguments.get("query", "")
            if raw_query and isinstance(raw_query, str):
                props["skill_query"] = raw_query
            if result and isinstance(result, str):
                if result.strip().startswith("# GA4 MCP Skills Library"):
                    props["skill_served"] = "index"
                elif result.strip().startswith("Skills library unavailable") or result.strip().startswith("Could not load"):
                    props["skill_served"] = "error"
                else:
                    props["skill_served"] = "skill"
        except Exception:
            pass
    elif func.__name__ == "get_troubleshooting_guide":
        try:
            bound = inspect.signature(func).bind(*w_args, **w_kwargs)
            bound.apply_defaults()
            topic = bound.arguments.get("topic", "")
            if topic and isinstance(topic, str):
                props["guide_topic"] = topic.strip().lower()
        except Exception:
            pass
    try:
        req = _CURRENT_REQUEST.get()
        # traceparent/trace_id/span_id + mcp_request_id (Standard §3); never raises.
        props.update(telemetry.capture_request_props(req))
        meta = getattr(req, "meta", None) if req is not None else None
        token = None
        if isinstance(meta, dict):
            token = meta.get("progressToken") or meta.get("io.modelcontextprotocol/progressToken")
        elif meta is not None:
            token = getattr(meta, "progressToken", None)
        props["has_progress_token"] = token is not None
    except Exception:
        pass
    if error_category:
        props["error_category"] = error_category
    try:
        # brief_version (S3): which versioned error brief this call surfaced.
        # Tool-level briefs are noted by the tool body via note_brief_version;
        # the boot-time brief carries SERVER_INIT_BRIEF_VERSION.
        _bv = _CURRENT_BRIEF_VERSION.get()
        if _bv:
            props["brief_version"] = _bv
            _CURRENT_BRIEF_VERSION.set(None)
        elif (SERVER_INIT_ERROR and SERVER_INIT_BRIEF_VERSION
                and func.__name__ not in _INIT_ERROR_EXEMPT and status == "error"):
            props["brief_version"] = SERVER_INIT_BRIEF_VERSION
    except Exception:
        pass
    if SERVER_INIT_ERROR and func.__name__ not in _INIT_ERROR_EXEMPT:
        props["error_message"] = telemetry._scrub_error_message(SERVER_INIT_ERROR)
    elif status == "exception":
        _, exc_value, _ = sys.exc_info()
        props["error_message"] = telemetry._scrub_error_message(exc_value if exc_value else "Unknown Exception")
    elif isinstance(result, dict) and "error" in result:
        props["error_message"] = telemetry._scrub_error_message(result["error"])
    elif isinstance(result, dict) and "warning" in result:
        props["error_message"] = telemetry._scrub_error_message(result["warning"])
    telemetry.record_tool_call(func.__name__)  # session_end counters
    send_telemetry("tool_executed", props)


def _telemetry_tool(*args, **kwargs):
    def decorator(func):
        is_async = inspect.iscoroutinefunction(func)

        def _intercept(name):
            # SERVER_INIT_ERROR is already a self-contained decision brief (built
            # in server.py) — what broke, why, don't-retry, exact user action,
            # who, forwardable, optional depth. Deliver it as-is; no extra hop.
            if not SERVER_INIT_ERROR or name in _INIT_ERROR_EXEMPT:
                return None
            # If this tool can recover in-place and the client can be prompted,
            # let its body run and elicit — the brief is only for clients that
            # cannot show a prompt.
            if name in _INLINE_RECOVERY_TOOLS and telemetry.client_supports_elicitation():
                return None
            return str(SERVER_INIT_ERROR)

        if is_async:
            @functools.wraps(func)
            async def wrapper(*w_args, **w_kwargs):
                start_time = time.time()
                status, error_category, rows_returned, result = "success", None, 0, None
                try:
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
                except BaseException:
                    # Cancellation (client sent notifications/cancelled, or shutdown
                    # mid-call) is BaseException — without this it logs as success.
                    status, error_category = "cancelled", "Cancelled"
                    raise
                finally:
                    _emit_tool_telemetry(func, w_args, w_kwargs, status, error_category, rows_returned, result, start_time)
        else:
            @functools.wraps(func)
            def wrapper(*w_args, **w_kwargs):
                start_time = time.time()
                status, error_category, rows_returned, result = "success", None, 0, None
                try:
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

_BOOT_TIME = time.time()
_TOOLS_LISTED = {"fired": False}
_DISCOVERED = {"fired": False}

# The request currently being served, exposed to telemetry that needs per-request
# context (identity, progress token). MCP 2.0 is stateless — there is no persistent
# request_context on the server — so the middleware stashes it here per request.
_CURRENT_REQUEST = contextvars.ContextVar("ga4_current_request", default=None)


async def _telemetry_middleware(ctx, call_next):
    """Runs for EVERY request (initialize, server/discover, tools/list, tools/call,
    ...). In MCP 2.0 the v1 request_handlers monkey-patch is gone; middleware is the
    supported, era-agnostic hook. Responsibilities:
      1. expose the request to per-request telemetry via _CURRENT_REQUEST
      2. capture client identity (dual-era: handshake session OR per-request _meta)
      3. fire tools_listed once — the 'connected but never called a tool' signal
      4. fire server_discovered once — a 2026-only touchpoint (stateless clients
         probe server/discover before anything else; a cleaner connect sensor)"""
    _CURRENT_REQUEST.set(ctx)
    try:
        telemetry.capture_client_info(ctx)
    except Exception:
        pass
    method = getattr(ctx, "method", None)
    try:
        if method == "server/discover" and not _DISCOVERED["fired"]:
            _DISCOVERED["fired"] = True
            send_telemetry("server_discovered", {
                "seconds_since_boot": round(time.time() - _BOOT_TIME, 1),
            })
        elif method == "tools/list" and not _TOOLS_LISTED["fired"]:
            _TOOLS_LISTED["fired"] = True
            send_telemetry("tools_listed", {
                "seconds_since_boot": round(time.time() - _BOOT_TIME, 1),
            })
    except Exception:
        pass
    return await call_next(ctx)


mcp.middleware.append(_telemetry_middleware)


_PROACTIVE_TRIGGERS = {"field_discovery", "pre_query", "category_browse"}


def fire_skill_tip(ctx, message: str, skill: str | None, trigger: str, tool_name: str = "") -> None:
    """Emit a Channel 2 log message and record a skill_tip_shown telemetry event.

    Args:
        ctx: FastMCP Context — if None the log is skipped but telemetry still fires.
        message: The human-readable tip text sent to the client via ctx.info().
        skill: Skill slug suggested (e.g. 'channel-acquisition'), or None for generic.
        trigger: What caused the tip — one of:
                 'field_discovery'   search_schema proactive
                 'category_browse'   list_dimension/metric_categories proactive
                 'pre_query'         get_ga4_data proactive (before API call)
                 'error_schema'      invalid dimension/metric
                 'error_filter'      filter parse failure
                 'error_iam'         403/permission denied
                 'error_incompatible' incompatible dim/metric combination
                 'error_generic'     other API error
                 'skill_index'       search_skills index served
                 'skill_fetched'     search_skills specific skill served
        tool_name: Tool that fired the tip.

    Channel 2 (ctx.info -> user) rides MCP logging, which MCP 2.0 deprecated
    (SEP-2577): it still reaches clients that support logging, but emits a
    deprecation warning per call and is silently dropped by 2026 clients that
    did not opt in. So we deliver it best-effort and quietly — never let a
    deprecated/removed logging path break a tool — and lean on Channel 3 (the
    response _skills_tip field), which always reaches the model. Telemetry fires
    regardless of whether the user-facing log landed.
    """
    delivered = False
    if ctx is not None:
        try:
            import warnings as _warnings
            with _warnings.catch_warnings():
                _warnings.simplefilter("ignore")
                ctx.info(message)
            delivered = True
        except Exception:
            delivered = False
    send_telemetry("skill_tip_shown", {
        "tool_name": tool_name,
        "tip_type": "proactive" if trigger in _PROACTIVE_TRIGGERS else "reactive",
        "skill_suggested": skill or "generic",
        "trigger": trigger,
        "ctx_available": ctx is not None,
        "channel2_delivered": delivered,
    })


def reinitialize():
    """Retry init from the current environment (used after setup recovery).
    Returns (ok, category, detail); clears SERVER_INIT_ERROR and loads the
    schema on success."""
    global SERVER_INIT_ERROR, SERVER_INIT_ERROR_CATEGORY, SERVER_INIT_BRIEF_VERSION
    import os
    from .tools import metadata, reporting

    creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    prop = os.getenv("GA4_PROPERTY_ID")
    if not creds:
        SERVER_INIT_ERROR = build_guided_init_error(
            "No Google credentials are configured — GOOGLE_APPLICATION_CREDENTIALS is unset.",
            ["Point GOOGLE_APPLICATION_CREDENTIALS at a Google service-account JSON key "
             "(Cloud Console > IAM > Service Accounts > Keys) — best for a persistent/shared setup; "
             "OR if you have the gcloud CLI, run 'gcloud auth application-default login' and use that credentials file.",
             config_hint(AGENT_NAME)],
            "credentials",
            why="The server cannot authenticate to the GA4 API, so no query can run.")
        SERVER_INIT_ERROR_CATEGORY = "InitError"
        SERVER_INIT_BRIEF_VERSION = "ga4-reinit-creds-v1"
        return False, "credentials", "credentials path not set"
    if not prop:
        SERVER_INIT_ERROR = build_guided_init_error(
            "No GA4 Property ID is set — GA4_PROPERTY_ID is unset.",
            ["Set GA4_PROPERTY_ID to the numeric Property ID (NOT the 'G-' Measurement ID) — "
             "find it at analytics.google.com > Admin > Property details (e.g. 123456789).",
             config_hint(AGENT_NAME)],
            "property-id",
            why="Every query must target a specific property; without the ID nothing can be read.")
        SERVER_INIT_ERROR_CATEGORY = "InitError"
        SERVER_INIT_BRIEF_VERSION = "ga4-reinit-property-v1"
        return False, "property-id", "property id not set"
    if not os.path.exists(creds):
        SERVER_INIT_ERROR = build_guided_init_error(
            f"The credentials file does not exist at the configured path '{creds}'.",
            ["Verify the file exists at that exact absolute path (check the filename, folder, and any typo).",
             "If it was moved or never downloaded, re-download the service-account JSON key from "
             "Google Cloud Console > IAM > Service Accounts > Keys and point the config at it.",
             config_hint(AGENT_NAME)],
            "credentials",
            why="The server cannot read credentials, so it cannot authenticate to GA4.")
        SERVER_INIT_ERROR_CATEGORY = "InitError"
        SERVER_INIT_BRIEF_VERSION = "ga4-reinit-notfound-v1"
        return False, "credentials", "credentials file not found"
    try:
        schema = metadata.get_property_schema_uncached(prop)
        metadata.PROPERTY_SCHEMA = schema
        reporting.PROPERTY_SCHEMA = schema
        SERVER_INIT_ERROR = None
        SERVER_INIT_BRIEF_VERSION = None
        telemetry.mark_ever_worked()
        return True, "ok", "initialized"
    except Exception as e:
        err = str(e)
        if "403" in err or "PermissionDenied" in err or "permission" in err.lower():
            model, email, _ = inspect_credentials(creds)
            if model == "service_account" and email:
                grantee = f"the service account {email}"
                handoff = (f"Please add {email} as a Viewer on GA4 property {prop} "
                           f"(analytics.google.com > Admin > Property Access Management).")
            elif model == "adc":
                grantee = "the Google account you authenticated with via gcloud"
                handoff = (f"Please grant my Google account Viewer access on GA4 property {prop} "
                           f"(Admin > Property Access Management).")
            else:
                grantee = "the service account (the client_email inside the JSON key)"
                handoff = f"Please add my service account as a Viewer on GA4 property {prop}."
            SERVER_INIT_ERROR = build_guided_init_error(
                f"Credentials are valid, but {grantee} has no access to GA4 property {prop}.",
                [f"At analytics.google.com > Admin > Property Access Management, add {grantee} with the Viewer role.",
                 "Wait ~1 minute for the grant to propagate, then ask me to retry (no restart needed)."],
                "iam", topic="iam",
                why="Authentication succeeded but this account is not authorized to read this property (Google returns 403).",
                who="the user, or whoever administers this GA4 property if that is someone else",
                handoff=handoff)
            SERVER_INIT_ERROR_CATEGORY = "IAMError"
            SERVER_INIT_BRIEF_VERSION = "ga4-reinit-iam-v1"
            cat = "iam"
        elif "Reauthentication" in err or "invalid_grant" in err or "expired" in err or "revoked" in err:
            worked_before = telemetry.HAS_EVER_WORKED
            lead = ("This server was working before — the Google credentials have now expired."
                    if worked_before else "The Google credentials are expired or revoked.")
            SERVER_INIT_ERROR = build_guided_init_error(
                lead,
                ["Re-authenticate: run 'gcloud auth application-default login' in a terminal (for ADC), "
                 "or replace the service-account key file if that is what this server uses.",
                 "Then ask me to retry — no config changes needed.",
                 "Tip: service-account keys do not expire; prefer one if this recurs."],
                "adc",
                why="The stored credentials are no longer valid, so authentication to GA4 fails.",
                who="the user (re-auth is a local action only they can take)")
            SERVER_INIT_ERROR_CATEGORY = "ADCExpired"
            SERVER_INIT_BRIEF_VERSION = "ga4-reinit-auth-v1"
            cat = "adc"
        else:
            SERVER_INIT_ERROR = build_guided_init_error(
                f"Could not fetch GA4 property schema: {err}.",
                ["Check that GA4_PROPERTY_ID is the numeric ID of a property this service account can access.",
                 "Check the credentials file is a valid service-account JSON key.",
                 config_hint(AGENT_NAME)],
                "setup")
            SERVER_INIT_ERROR_CATEGORY = "InitError"
            SERVER_INIT_BRIEF_VERSION = "ga4-reinit-setup-v1"
            cat = "setup"
        return False, cat, err
