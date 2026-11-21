# SPDX-License-Identifier: Apache-2.0

"""The core reporting tool for fetching GA4 data."""

import os
import sys
import json
import asyncio
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange, Dimension, Metric, RunReportRequest, Filter, FilterExpression, FilterExpressionList,
    OrderBy, MetricAggregation
)
from mcp.types import ToolAnnotations
from mcp.server.mcpserver import Context
from ga4_mcp.coordinator import mcp, fire_skill_tip, note_brief_version, classify_setup_failure, build_transient_error
from ga4_mcp.tools import metadata
from ga4_mcp.telemetry import client_supports_elicitation

# S3: version tags for the field-proven error briefs below. The brief TEXT is
# unchanged — these tags ride telemetry only (`brief_version` on that error's
# tool_executed) so post-brief behavior can be measured per brief revision.
BRIEF_INVALID_DIMENSION = "ga4-schema-dim-v1"
BRIEF_INVALID_METRIC = "ga4-schema-met-v1"
BRIEF_FILTER_SHAPE = "ga4-filter-v1"
BRIEF_INCOMPATIBLE = "ga4-incompatible-v1"
BRIEF_FIELD_UNAVAILABLE = "ga4-gsc-field-v1"
BRIEF_TRANSIENT = "ga4-transient-v1"
BRIEF_FIELD_SHAPE = "ga4-field-shape-v1"

# get_ga4_data hits the external GA4 Data API: open world, read-only, idempotent.
_READ_ONLY = ToolAnnotations(read_only_hint=True, idempotent_hint=True, open_world_hint=True)

# This global variable will be populated by the server on startup.
PROPERTY_SCHEMA = None

def _camel_to_snake(name: str) -> str:
    import re
    return re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()

def _convert_keys_to_snake(d):
    if isinstance(d, dict):
        new_d = {}
        for k, v in d.items():
            snake_k = _camel_to_snake(k)
            if snake_k in ("filter_expressions", "filterexpressions"):
                snake_k = "expressions"
            new_d[snake_k] = _convert_keys_to_snake(v)
        return new_d
    elif isinstance(d, list):
        return [_convert_keys_to_snake(x) for x in d]
    return d

def _get_smart_sorting(dimensions, metrics):
    """Determine optimal sorting strategy for relevance."""
    order_bys = []
    if "date" in dimensions:
        order_bys.append(OrderBy(dimension=OrderBy.DimensionOrderBy(dimension_name="date"), desc=True))
    if metrics:
        order_bys.append(OrderBy(metric=OrderBy.MetricOrderBy(metric_name=metrics[0]), desc=True))
    return order_bys

# Upstream GA4 failures that retry cleanly (429/503/504 + transport spellings)
# are detected and formatted in ga4_mcp.coordinator — one status test, one
# transient brief, so the boot path and this path cannot disagree.
from ga4_mcp.coordinator import is_transient_error as _is_transient


def _should_aggregate(dimensions, metrics):
    """Request GA4 server-side metric totals whenever a dimension splits the
    metrics across rows (a time series like ['date'] or any breakdown). With no
    dimensions GA4 already returns a single aggregate row, so a totals row would
    be redundant. This is what lets a 7-day pull come back with the period figure
    computed server-side, not left for the model to sum."""
    return len(dimensions) >= 1 and len(metrics) >= 1


def _extract_totals(response):
    """Pull GA4's server-side totals (present when metric_aggregations=[TOTAL]
    was requested) into a metric->value map. Returns None if absent."""
    totals_rows = getattr(response, "totals", None) or []
    if not totals_rows:
        return None
    headers = [h.name for h in response.metric_headers]
    row = totals_rows[0]
    out = {}
    for i, name in enumerate(headers):
        try:
            out[name] = row.metric_values[i].value
        except (IndexError, AttributeError):
            continue
    return out or None


def _build_report_payload(response, skill):
    """Format a GA4 RunReportResponse into the tool payload: data rows, metadata,
    server-side totals (with a coaching note), and the Channel-3 skills tip. Pure
    (no network), so it is unit-tested against a response stub."""
    result = []
    for row in response.rows:
        data_row = {}
        for i, dim_header in enumerate(response.dimension_headers):
            data_row[dim_header.name] = row.dimension_values[i].value
        for i, met_header in enumerate(response.metric_headers):
            data_row[met_header.name] = row.metric_values[i].value
        result.append(data_row)

    payload = {
        "data": result,
        "metadata": {
            "total_rows_in_source": getattr(response, "row_count", len(result)),
            "returned_rows": len(result),
        },
    }

    # Coaching: on a multi-row pull (time series or breakdown), GA4's own totals
    # let the model state the period figure without summing rows itself — a known
    # LLM error mode. A single row already IS the aggregate, so skip it there.
    if len(result) > 1:
        totals = _extract_totals(response)
        if totals:
            payload["totals"] = totals
            payload["metadata"]["aggregation_note"] = (
                f"`totals` are GA4 server-side aggregates across all {len(result)} "
                "rows — use them for the period figure instead of summing rows "
                "yourself. Additive metrics (users, sessions, pageviews) sum; "
                "rate/ratio metrics are period-computed by GA4."
            )

    # Channel 3: model-to-user relay — the tip rides in the response so the model
    # can weave it into its answer to the human.
    if skill:
        payload["_skills_tip"] = f"For deeper analysis, call search_skills('{skill}') — it has the full pattern for this query type including interpretation guidance."
    else:
        payload["_skills_tip"] = "Call search_skills() to explore 15 analytical recipes that provide proven query patterns and interpretation guidance."

    return payload


_SKILL_HINTS = [
    (["chatgpt", "claude", "perplexity", "gemini", "openai", "ai referral", "ai traffic", "llm"], "ai-referral-analysis"),
    (["bot", "spam", "scraper", "crawler", "fake traffic"], "bot-traffic-detection"),
    (["purchase", "revenue", "ecommerce", "cart", "checkout", "transaction", "ecommercepurchases"], "ecommerce-analysis"),
    (["firstusersource", "firstusermedium", "firstuser", "attribution", "first touch", "last click", "user acquisition"], "attribution-scope"),
    (["sessiondefaultchannelgroup", "sessionsource", "sessionmedium", "sessioncampaignname", "channel acquisition", "where users come from"], "channel-acquisition"),
    (["pagepath", "pagetitle", "content performance", "top pages", "blog", "article", "landing page", "scroll"], "content-performance"),
    (["country", "city", "region", "devicecategory", "geo", "mobile vs", "by device", "by country"], "geo-device-segmentation"),
    (["spike", "drop", "anomaly", "why did", "traffic fell", "traffic rose", "diagnos", "investigate"], "traffic-diagnosis"),
    (["customevent:", "customuser:", "custom dimension", "custom event", "event parameter"], "custom-dimensions"),
    (["incompatible", "compatible", "scope", "session metric", "event metric", "dimensions & metrics"], "compatible-combinations"),
]

def _suggest_skill(dimensions: list, metrics: list, intent: str | None) -> str | None:
    """Return the most relevant skill slug for this query context, or None."""
    dims = [d.lower() for d in (dimensions or [])]
    mets = [m.lower() for m in (metrics or [])]
    all_text = " ".join(dims + mets + [(intent or "").lower()])
    for keywords, skill in _SKILL_HINTS:
        if any(kw in all_text for kw in keywords):
            return skill
    return None


# Common LLM metric aliases (e.g., legacy GA metric names -> GA4 Data API names)
# Extend from telemetry: recurring SchemaHallucination field names get an alias.
METRIC_ALIASES = {
    "conversions": "keyEvents",
    "conversion_rate": "sessionKeyEventRate",
    "user_conversion_rate": "userKeyEventRate",
    "bounce_rate": "bounceRate",
    "users": "totalUsers",
    "itemViews": "itemsViewed",
    "purchases": "ecommercePurchases",
}

DIMENSION_ALIASES = {
    "sessionDefaultChannelGrouping": "sessionDefaultChannelGroup",
    "defaultChannelGrouping": "defaultChannelGroup",
}

# Filter-shape repairs for structures models actually send (from telemetry).
# Applied AFTER camel->snake conversion; valid shapes pass through untouched.
_FILTER_KEY_SYNONYMS = {
    "or_filter": "or_group",
    "and_filter": "and_group",
    "not_filter": "not_expression",
    "field": "field_name",
    "filters": "expressions",
}
_FILTER_LEAF_KEYS = {"field_name", "string_filter", "in_list_filter", "numeric_filter", "between_filter"}


_FILTER_EXPR_KEYS = {"filter", "and_group", "or_group", "not_expression", "expressions"}


def _repair_filter_shape(d, parent_key=None):
    """
    Map known wrong keys to proto names, wrap bare leaf filters sent without
    their {"filter": {...}} wrapper, and drop decorative keys models invent at
    the Filter leaf (e.g. "type"). Dicts under a "filter" key ARE the leaf
    (proto Filter), so they are never wrapped again.
    """
    if isinstance(d, list):
        return [_repair_filter_shape(x, parent_key) for x in d]
    if not isinstance(d, dict):
        return d
    repaired = {}
    for k, v in d.items():
        nk = _FILTER_KEY_SYNONYMS.get(k, k)
        repaired[nk] = _repair_filter_shape(v, nk)
    # Models invent {"stringFilter": {"exact": "x"}} — translate to the proto form
    if parent_key == "string_filter" and "exact" in repaired and "value" not in repaired:
        repaired["value"] = repaired.pop("exact")
        repaired.setdefault("match_type", "EXACT")
    is_leaf_bearing = bool(repaired.keys() & _FILTER_LEAF_KEYS)
    if parent_key == "filter" or (parent_key in (None, "expressions", "not_expression") and is_leaf_bearing
                                  and not (repaired.keys() & _FILTER_EXPR_KEYS)):
        # At (or wrapping into) a Filter leaf: strip decorative junk keys
        cleaned = {k: v for k, v in repaired.items() if k in _FILTER_LEAF_KEYS}
        if parent_key == "filter":
            return cleaned if cleaned else repaired
        return {"filter": cleaned if cleaned else repaired}
    return repaired

@mcp.tool(annotations=_READ_ONLY)
async def get_ga4_data(
    dimensions: list[str] = ["date"],
    metrics: list[str] = ["totalUsers", "newUsers", "sessions"],
    date_range_start: str = "7daysAgo",
    date_range_end: str = "yesterday",
    dimension_filter: dict | None = None,
    limit: int = 1000,
    estimate_only: bool = False,
    proceed_with_large_dataset: bool = False,
    enable_aggregation: bool = True,
    intent: str = "",
    ctx: Context = None,
):
    """
    Retrieve GA4 data with built-in intelligence for better and safer results.

    Returns on success: {"data": [...], "metadata": {...}, "_skills_tip": "..."}.
      For multi-row pulls (a time series like ['date'], or any breakdown) the
      result also carries "totals": {metric: value} — GA4 server-side aggregates
      across all rows. Read the period figure from "totals"; do NOT sum the rows
      yourself. (Additive metrics sum; rate metrics are period-computed by GA4.)
    Returns on volume warning: {"warning": "...", "estimated_rows": N, "suggestions": [...]}
    Returns on error: {"error": "..."}

    CRITICAL WORKFLOW — follow this sequence every time:

    1. DISCOVER FIELDS: NEVER guess dimension or metric names. Call `search_schema`,
       `list_dimension_categories`, or `list_metric_categories` FIRST to verify exact
       API names for this property. Guessing costs you a failed round-trip.

    2. DISCOVER PATTERN: For any domain-specific analysis, call `search_skills('<topic>')`
       BEFORE querying to get the proven methodology — correct dimensions, metrics,
       filters, and how to interpret the result. One extra call prevents multiple failures.
       Use for: traffic diagnosis, attribution, ecommerce, channel acquisition, content
       performance, geo/device segmentation, AI referrals, bot detection.

    3. RETRIEVE: Call get_ga4_data with the verified fields and the skill's pattern.

    4. TROUBLESHOOT: On schema error, invalid field, or filter parse error — do NOT
       retry by guessing. Your training may predate current GA4 (UA was sunset
       2023-07-01). Call `search_schema('<keyword>')` to find the current name in
       THIS property, or `search_skills('ua-to-ga4' | 'common-metric-names' |
       'filter-structures')` for the mapping.

    FIELD NAMES — GA4 API names vs common wrong guesses:
    - 'screenPageViews'       not 'uniquePageviews' or 'pageViews'
    - 'totalUsers'            not 'users'
    - 'keyEvents'             not 'conversions' or 'goalCompletionsAll'
    - 'sessionKeyEventRate'   not 'sessionConversionRate' or 'conversionRate' (GA4 renamed conversions→key events, 2024)
    - 'userEngagementDuration' not 'timeOnPage' or 'avgTimeOnPage'
    - 'averageSessionDuration' not 'avgSessionDuration'
    - 'itemsViewed'           not 'itemViews'
    - 'ecommercePurchases'    not 'purchases'
    - 'sessionDefaultChannelGroup'  not 'sessionDefaultChannelGrouping'
    - 'sessionSource'/'sessionMedium'  not 'source'/'medium'
    - All names are camelCase — never snake_case (page_path → pagePath, event_name → eventName)
    - 'bounceRate' and 'newUsers' are correct as-is

    DATE RANGES:
    - Format: 'YYYY-MM-DD' or relative strings: '7daysAgo', '30daysAgo', 'yesterday', 'today'
    - 'NdaysAgo' counts back from today, excluding today. 'yesterday' = last complete day.
    - Period comparison (YoY, WoW): run two separate queries with different date ranges,
      then compare the results. The API does not support multi-period in one call.

    SCOPE RULES — incompatible combinations return a 400 error:
    - Session dims (sessionSource, sessionMedium, sessionCampaignName) → use with
      sessions, bounceRate, sessionKeyEventRate. NOT with eventCount.
    - Event dims (eventName) → use with eventCount. NOT with sessions.
    - User dims (firstUserSource, firstUserMedium) → use with totalUsers, newUsers. NOT sessions.
    - Safe with any metric: date, deviceCategory, country, city, pagePath, pageTitle.

    FILTER STRUCTURE:
    - Simple: {"filter": {"fieldName": "sessionSource", "stringFilter": {"value": "google", "matchType": "CONTAINS"}}}
    - AND:    {"andGroup": {"expressions": [{"filter": {...}}, {"filter": {...}}]}}
    - OR:     {"orGroup":  {"expressions": [{"filter": {...}}, {"filter": {...}}]}}
    - NOT:    {"notExpression": {"filter": {...}}}
    - Wrong keys that break filters: and_filter→andGroup, or_filter→orGroup,
      not_filter→notExpression, filters→expressions, field→fieldName

    Args:
        dimensions: GA4 dimension names (verified via schema tools, e.g. ["date", "city"]).
        metrics: GA4 metric names (verified via schema tools, e.g. ["totalUsers", "sessions"]).
        date_range_start: Start date — 'YYYY-MM-DD' or '7daysAgo', '30daysAgo', 'yesterday'.
        date_range_end: End date — 'YYYY-MM-DD' or 'yesterday', 'today'.
        dimension_filter: Optional FilterExpression dict. camelCase and snake_case both accepted.
        limit: Max rows to return. Defaults to 1000.
        estimate_only: If True, returns only estimated row count without fetching data.
        proceed_with_large_dataset: Set True to bypass the 2500-row volume warning.
        enable_aggregation: If True, asks GA4 for server-side metric totals whenever a
            dimension splits the data across rows (e.g. a 7-day ['date'] pull), returned
            in a "totals" block so the model needn't sum rows. Default True.
        intent: Short plain-English description of what the user is trying to learn.
                E.g. "which channels drive most signups", "bot traffic audit for last month".
    """
    if not PROPERTY_SCHEMA:
        # Born-broken, but if the client can be prompted, recover the missing
        # config AT this call (MCP 2.0 MRTR) instead of bouncing to a separate
        # tool. Clients that cannot elicit never reach here — the coordinator
        # returns the setup brief for them (the proven fallback).
        from ga4_mcp import coordinator as _coordinator
        if ctx is not None and _coordinator.SERVER_INIT_ERROR and client_supports_elicitation():
            from ga4_mcp.setup_flow import run_inline_recovery
            recovered, message = await run_inline_recovery(ctx)
            if not recovered:
                return {"error": message}
            # reinitialize() repopulated the module schema global; fall through.
        if not PROPERTY_SCHEMA:
            return {"error": "Schema not loaded. Please check server startup logs."}

    try:
        # --- Input Parsing and Validation ---
        parsed_dimensions = dimensions if isinstance(dimensions, list) else [d.strip() for d in dimensions.split(',')]
        parsed_metrics = metrics if isinstance(metrics, list) else [m.strip() for m in metrics.split(',')]

        # Transparently translate common aliases (e.g. conversions -> keyEvents)
        parsed_metrics = [METRIC_ALIASES.get(m, m) for m in parsed_metrics]
        parsed_dimensions = [DIMENSION_ALIASES.get(d, d) for d in parsed_dimensions]

        # GA4 400s on a repeated field ("Found duplicate dimensions/metrics").
        # Order-preserving dedupe keeps the caller's intent, same answer, no
        # round-trip spent.
        parsed_dimensions = list(dict.fromkeys(parsed_dimensions))
        parsed_metrics = list(dict.fromkeys(parsed_metrics))

        if not parsed_metrics:
            return {"error": "Metrics list cannot be empty."}

        # Fields this property cannot serve at all (removed from the allowlist at
        # schema load) fail locally, naming the field and where the number lives.
        unservable = metadata.unavailable_fields()
        for met in parsed_metrics:
            if met in unservable:
                fire_skill_tip(ctx, f"💡 '{met}' is a Search Console metric, not a GA4 one — read it from the Google Search Console API instead.", skill="ga4-limitations", trigger="error_schema", tool_name="get_ga4_data")
                note_brief_version(BRIEF_FIELD_UNAVAILABLE)
                return {"error": f"'{met}' cannot be read from this property: GA4's Search Console metrics require an active Search Console link, and this property has none — every request for them returns 400 upstream, so none was sent. The same number lives in the Google Search Console API as '{unservable[met]}' (searchanalytics.query, dimensions=['date'], type='web'). Do NOT retry '{met}' or try a dimension variant. For organic search traffic, use a Google Search Console tool; for on-site behaviour in GA4, use search_schema('<keyword>') for the GA4 names this property does have."}

        valid_dims = PROPERTY_SCHEMA["dimensions"].keys()
        valid_mets = PROPERTY_SCHEMA["metrics"].keys()
        for dim in parsed_dimensions:
            if dim not in valid_dims:
                fire_skill_tip(ctx, "💡 Skill tip: search_skills('common-metric-names') has the correct GA4 field names and UA→GA4 name mapping. search_skills('custom-dimensions') covers customEvent:/customUser: syntax.", skill="common-metric-names", trigger="error_schema", tool_name="get_ga4_data")
                note_brief_version(BRIEF_INVALID_DIMENSION)
                return {"error": f"Invalid dimension: '{dim}' — not present in this property's live GA4 schema. WHY: GA4 Data API field names often differ from names in model training data — many are Universal Analytics (sunset 2023-07-01) or older-GA4 artifacts that no longer exist — so a name you are confident about can be out of date. The current names live outside your training: call search_schema('<keyword>') to read THIS property's live schema (also finds custom dimensions), or search_skills('ua-to-ga4') for the maintained UA→GA4 name mapping. Do NOT retry '{dim}' or guess a variant."}
        for met in parsed_metrics:
            if met not in valid_mets:
                fire_skill_tip(ctx, "💡 Skill tip: search_skills('common-metric-names') has the correct GA4 metric names. Common wrong guesses: 'conversions'→'keyEvents', 'users'→'totalUsers', 'uniquePageviews'→'screenPageViews'.", skill="common-metric-names", trigger="error_schema", tool_name="get_ga4_data")
                note_brief_version(BRIEF_INVALID_METRIC)
                return {"error": f"Invalid metric: '{met}' — not present in this property's live GA4 schema. WHY: GA4 Data API metric names often differ from names in model training data — many are Universal Analytics (sunset 2023-07-01) or metrics renamed since your training, so a name you are confident about can be out of date. The current names live outside your training: call search_schema('<keyword>') to read THIS property's live schema, or search_skills('common-metric-names') for the maintained name mapping. Do NOT retry '{met}' or guess a variant."}

        # --- Filter Expression Building ---
        filter_expression = None
        if dimension_filter:
            try:
                # If passed as stringified JSON, parse it first
                if isinstance(dimension_filter, str):
                    try:
                        dimension_filter = json.loads(dimension_filter)
                    except Exception:
                        pass
                # Recursively translate camelCase keys to snake_case for proto-plus
                # compatibility, then repair known wrong shapes models send
                snake_filter = _repair_filter_shape(_convert_keys_to_snake(dimension_filter))
                if isinstance(snake_filter, list):
                    if len(snake_filter) == 1:
                        filter_expression = FilterExpression(snake_filter[0])
                    elif len(snake_filter) > 1:
                        exprs = [FilterExpression(f) if isinstance(f, dict) else f for f in snake_filter]
                        filter_expression = FilterExpression(and_group=FilterExpressionList(expressions=exprs))
                elif isinstance(snake_filter, dict):
                    filter_expression = FilterExpression(snake_filter)
            except Exception as e:
                fire_skill_tip(ctx, "💡 Skill tip: search_skills('filter-structures') has copy-paste templates for every filter type — single field, AND, OR, NOT, IN LIST.", skill="filter-structures", trigger="error_filter", tool_name="get_ga4_data")
                note_brief_version(BRIEF_FILTER_SHAPE)
                return {"error": f"Invalid dimension_filter structure: {e}. WHY: the GA4 filter shape and field names often differ from filter formats in model training data — field names are camelCase (eventName, not event_name) inside a specific nested structure. The current templates live outside your training: call search_skills('filter-structures') for copy-paste examples of every filter type, or search_schema to confirm a field name. Do NOT retry the same shape."}

        # Channel 2: proactive — fires before the API call, while query is in-flight
        skill = _suggest_skill(parsed_dimensions, parsed_metrics, intent)
        if skill:
            fire_skill_tip(ctx, f"💡 Skill available: search_skills('{skill}') has the full analytical methodology for this query type — proven field combinations, filters, and interpretation guidance.", skill=skill, trigger="pre_query", tool_name="get_ga4_data")
        else:
            fire_skill_tip(ctx, "💡 GA4 Skills: 15 analytical recipes available. Call search_skills() to find the proven pattern for traffic, ecommerce, attribution, content, geo, and more.", skill=None, trigger="pre_query", tool_name="get_ga4_data")

        # --- API Client and Request Objects ---
        from ..coordinator import get_data_client
        client = get_data_client()
        property_id = os.getenv("GA4_PROPERTY_ID")
        dimension_objects = [Dimension(name=d) for d in parsed_dimensions]
        metric_objects = [Metric(name=m) for m in parsed_metrics]
        date_range_object = DateRange(start_date=date_range_start, end_date=date_range_end)

        # --- Row Count Estimation ---
        if not proceed_with_large_dataset or estimate_only:
            try:
                estimation_req = RunReportRequest(
                    property=f"properties/{property_id}",
                    dimensions=dimension_objects,
                    metrics=metric_objects,
                    date_ranges=[date_range_object],
                    dimension_filter=filter_expression,
                    limit=1
                )
                estimation_res = await asyncio.to_thread(client.run_report, request=estimation_req)
                estimated_rows = estimation_res.row_count

                if estimate_only:
                    return {"estimated_rows": estimated_rows}

                if int(estimated_rows or 0) > 2500 and (limit is None or limit > 2500):
                    return {
                        "warning": f"Query would return ~{estimated_rows} rows (exceeding safety threshold of 2,500).",
                        "estimated_rows": estimated_rows,
                        "suggestions": [
                            "If you only need a sample, re-run with limit <= 2500 (e.g. limit=100).",
                            "Reduce the date range.",
                            "Add or refine the dimension_filter.",
                            "Use fewer dimensions.",
                            "Or, re-run with proceed_with_large_dataset=True to fetch the data anyway."
                        ]
                    }
            except Exception as e:
                print(f"DEBUG: Row count estimation failed: {e}", file=sys.stderr)

        # --- Main GA4 API Call ---
        request = RunReportRequest(
            property=f"properties/{property_id}",
            dimensions=dimension_objects,
            metrics=metric_objects,
            date_ranges=[date_range_object],
            dimension_filter=filter_expression,
            limit=limit,
            order_bys=_get_smart_sorting(parsed_dimensions, parsed_metrics),
            metric_aggregations=[MetricAggregation.TOTAL] if enable_aggregation and _should_aggregate(parsed_dimensions, parsed_metrics) else None
        )
        response = await asyncio.to_thread(client.run_report, request=request)

        # --- Response Formatting (pure, unit-tested) ---
        # Surfaces GA4 server-side totals + Channel-3 skills tip.
        return _build_report_payload(response, skill)

    except Exception as e:
        upstream = str(e)
        error_message = f"Error fetching GA4 data: {upstream}"
        print(error_message, file=sys.stderr)
        if hasattr(e, 'details'):
            details_val = e.details() if callable(getattr(e, 'details', None)) else getattr(e, 'details')
            upstream += f" Details: {details_val}"
            error_message += f" Details: {details_val}"

        # Upstream STATUS beats text matching. A recoverable blip is not a setup
        # problem: 2.12.0 sent 503s to the IAM/ADC briefs because their text
        # carried 'expired'/'permission', telling the model to stop when one
        # retry would have worked.
        if _is_transient(error_message):
            fire_skill_tip(ctx, "💡 Upstream GA4 API is briefly unavailable — the query itself is valid.", skill=None, trigger="error_transient", tool_name="get_ga4_data")
            note_brief_version(BRIEF_TRANSIENT)
            return {"error": build_transient_error("running this report", upstream)}

        elif "incompatible" in error_message.lower() or "dimensions & metrics" in error_message.lower():
            fire_skill_tip(ctx, "💡 Skill tip: search_skills('compatible-combinations') explains which dimension/metric scopes can be paired. Session dims need session metrics; event dims need event metrics.", skill="compatible-combinations", trigger="error_incompatible", tool_name="get_ga4_data")
            error_message += " SYSTEM DIRECTIVE: Call search_skills('compatible-combinations') to learn which dimensions and metrics can be combined."
            note_brief_version(BRIEF_INCOMPATIBLE)

        else:
            # Setup-class failures (401 family, 403) get at runtime what boot
            # gives them — one classifier, one brief formatter, no library string.
            category, brief_version, brief = classify_setup_failure(
                e, os.getenv("GA4_PROPERTY_ID") or "", os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or "")
            if category in ("IAMError", "ADCExpired"):
                fire_skill_tip(ctx, "💡 Auth failure — the setup brief in this error names the fix and who can do it.", skill=None,
                               trigger="error_iam" if category == "IAMError" else "error_auth", tool_name="get_ga4_data")
                note_brief_version(brief_version)
                return {"error": brief}

            # Nothing left may reach the model as a raw library string: the
            # residual 400/field-shape class names its causes and the next call.
            fire_skill_tip(ctx, "💡 Skill tip: search_schema() has this property's live field names; search_skills('compatible-combinations') has the pairing rules.", skill="compatible-combinations", trigger="error_generic", tool_name="get_ga4_data")
            note_brief_version(BRIEF_FIELD_SHAPE)
            return {"error": (
                "GA4 rejected this request — the fields, their pairing, or their shape do not match what this property accepts.  "
                "WHY: the GA4 Data API rejects (400) a field name it does not know, a dimension/metric pairing drawn from "
                "different scopes (session dimensions need session metrics; event dimensions need event metrics), or a field "
                "this property cannot serve at all.  "
                "LIKELY CAUSES: (1) an invalid dimension or metric name — GA4 names differ from Universal Analytics and from "
                "older-GA4 names in model training data; (2) an incompatible dimension-metric pairing; (3) an unsupported "
                "field for this property.  "
                "NEXT CALL: search_schema('<keyword>') for this property's live field names, search_skills('compatible-combinations') "
                "for pairing rules, or search_skills('filter-structures') if a filter was involved. Do NOT resend this exact request — "
                "change the field or the pairing.  "
                f"UPSTREAM SAID: {upstream}"
            )}

        return {"error": error_message}
