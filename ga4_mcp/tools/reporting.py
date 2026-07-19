# SPDX-License-Identifier: Apache-2.0

"""The core reporting tool for fetching GA4 data."""

import os
import sys
import json
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange, Dimension, Metric, RunReportRequest, Filter, FilterExpression, FilterExpressionList,
    OrderBy, MetricAggregation
)
from mcp.types import ToolAnnotations
from mcp.server.fastmcp import Context
from ga4_mcp.coordinator import mcp, fire_skill_tip

_READ_ONLY = ToolAnnotations(readOnlyHint=True)

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

def _should_aggregate(dimensions, metrics):
    """Detect when server-side aggregation would be beneficial."""
    return len(dimensions) == 0 or "date" not in dimensions


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
def get_ga4_data(
    dimensions: list[str] = ["date"],
    metrics: list[str] = ["totalUsers", "newUsers", "sessions"],
    date_range_start: str = "7daysAgo",
    date_range_end: str = "yesterday",
    dimension_filter: dict = None,
    limit: int = 1000,
    estimate_only: bool = False,
    proceed_with_large_dataset: bool = False,
    enable_aggregation: bool = True,
    intent: str = None,
    ctx: Context = None,
):
    """
    Retrieve GA4 data with built-in intelligence for better and safer results.

    Returns on success: {"data": [...], "metadata": {...}, "_skills_tip": "..."}
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
        enable_aggregation: If True, uses server-side aggregation when no date dimension. Default True.
        intent: Short plain-English description of what the user is trying to learn.
                E.g. "which channels drive most signups", "bot traffic audit for last month".
    """
    if not PROPERTY_SCHEMA:
        return {"error": "Schema not loaded. Please check server startup logs."}

    try:
        # --- Input Parsing and Validation ---
        parsed_dimensions = dimensions if isinstance(dimensions, list) else [d.strip() for d in dimensions.split(',')]
        parsed_metrics = metrics if isinstance(metrics, list) else [m.strip() for m in metrics.split(',')]

        # Transparently translate common aliases (e.g. conversions -> keyEvents)
        parsed_metrics = [METRIC_ALIASES.get(m, m) for m in parsed_metrics]
        parsed_dimensions = [DIMENSION_ALIASES.get(d, d) for d in parsed_dimensions]

        if not parsed_metrics:
            return {"error": "Metrics list cannot be empty."}

        valid_dims = PROPERTY_SCHEMA["dimensions"].keys()
        valid_mets = PROPERTY_SCHEMA["metrics"].keys()
        for dim in parsed_dimensions:
            if dim not in valid_dims:
                fire_skill_tip(ctx, "💡 Skill tip: search_skills('common-metric-names') has the correct GA4 field names and UA→GA4 name mapping. search_skills('custom-dimensions') covers customEvent:/customUser: syntax.", skill="common-metric-names", trigger="error_schema", tool_name="get_ga4_data")
                return {"error": f"Invalid dimension: '{dim}' — not present in this property's live GA4 schema. WHY: GA4 Data API field names often differ from names in model training data — many are Universal Analytics (sunset 2023-07-01) or older-GA4 artifacts that no longer exist — so a name you are confident about can be out of date. The current names live outside your training: call search_schema('<keyword>') to read THIS property's live schema (also finds custom dimensions), or search_skills('ua-to-ga4') for the maintained UA→GA4 name mapping. Do NOT retry '{dim}' or guess a variant."}
        for met in parsed_metrics:
            if met not in valid_mets:
                fire_skill_tip(ctx, "💡 Skill tip: search_skills('common-metric-names') has the correct GA4 metric names. Common wrong guesses: 'conversions'→'keyEvents', 'users'→'totalUsers', 'uniquePageviews'→'screenPageViews'.", skill="common-metric-names", trigger="error_schema", tool_name="get_ga4_data")
                return {"error": f"Invalid metric: '{met}' — not present in this property's live GA4 schema. WHY: GA4 Data API metric names often differ from names in model training data — many are Universal Analytics (sunset 2023-07-01) or metrics renamed since your training, so a name you are confident about can be out of date. The current names live outside your training: call search_schema('<keyword>') to read THIS property's live schema, or search_skills('common-metric-names') for the maintained name mapping. Do NOT retry '{met}' or guess a variant."}

        # --- Filter Expression Building ---
        filter_expression = None
        if dimension_filter:
            try:
                # Recursively translate camelCase keys to snake_case for proto-plus
                # compatibility, then repair known wrong shapes models send
                snake_filter = _repair_filter_shape(_convert_keys_to_snake(dimension_filter))
                filter_expression = FilterExpression(snake_filter)
            except Exception as e:
                fire_skill_tip(ctx, "💡 Skill tip: search_skills('filter-structures') has copy-paste templates for every filter type — single field, AND, OR, NOT, IN LIST.", skill="filter-structures", trigger="error_filter", tool_name="get_ga4_data")
                return {"error": f"Invalid dimension_filter structure: {e}. WHY: the GA4 filter shape and field names often differ from filter formats in model training data — field names are camelCase (eventName, not event_name) inside a specific nested structure. The current templates live outside your training: call search_skills('filter-structures') for copy-paste examples of every filter type, or search_schema to confirm a field name. Do NOT retry the same shape."}

        # Channel 2: proactive — fires before the API call, while query is in-flight
        skill = _suggest_skill(parsed_dimensions, parsed_metrics, intent)
        if skill:
            fire_skill_tip(ctx, f"💡 Skill available: search_skills('{skill}') has the full analytical methodology for this query type — proven field combinations, filters, and interpretation guidance.", skill=skill, trigger="pre_query", tool_name="get_ga4_data")
        else:
            fire_skill_tip(ctx, "💡 GA4 Skills: 15 analytical recipes available. Call search_skills() to find the proven pattern for traffic, ecommerce, attribution, content, geo, and more.", skill=None, trigger="pre_query", tool_name="get_ga4_data")

        # --- API Client and Request Objects ---
        client = BetaAnalyticsDataClient()
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
                estimation_res = client.run_report(request=estimation_req)
                estimated_rows = estimation_res.row_count

                if estimate_only:
                    return {"estimated_rows": estimated_rows}

                if int(estimated_rows or 0) > 2500:
                    return {
                        "warning": "Query will return a large dataset.",
                        "estimated_rows": estimated_rows,
                        "suggestions": [
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
        response = client.run_report(request=request)

        # --- Response Formatting ---
        result = []
        for row in response.rows:
            data_row = {}
            for i, dim_header in enumerate(response.dimension_headers):
                data_row[dim_header.name] = row.dimension_values[i].value
            for i, met_header in enumerate(response.metric_headers):
                data_row[met_header.name] = row.metric_values[i].value
            result.append(data_row)

        # Channel 3: embed skill tip in response for model to relay to user
        response_payload = {
            "data": result,
            "metadata": {
                "total_rows_in_source": response.row_count,
                "returned_rows": len(result),
            },
        }
        if skill:
            response_payload["_skills_tip"] = f"For deeper analysis, call search_skills('{skill}') — it has the full pattern for this query type including interpretation guidance."
        else:
            response_payload["_skills_tip"] = "Call search_skills() to explore 15 analytical recipes that provide proven query patterns and interpretation guidance."

        return response_payload

    except Exception as e:
        error_message = f"Error fetching GA4 data: {str(e)}"
        print(error_message, file=sys.stderr)
        if hasattr(e, 'details'):
            details_val = e.details() if callable(getattr(e, 'details', None)) else getattr(e, 'details')
            error_message += f" Details: {details_val}"

        if "incompatible" in error_message.lower() or "dimensions & metrics" in error_message.lower():
            fire_skill_tip(ctx, "💡 Skill tip: search_skills('compatible-combinations') explains which dimension/metric scopes can be paired. Session dims need session metrics; event dims need event metrics.", skill="compatible-combinations", trigger="error_incompatible", tool_name="get_ga4_data")
            error_message += " SYSTEM DIRECTIVE: Call search_skills('compatible-combinations') to learn which dimensions and metrics can be combined."

        elif "403" in error_message or "PermissionDenied" in error_message or "permission" in error_message.lower():
            fire_skill_tip(ctx, "💡 Permission error detected. Call get_troubleshooting_guide(topic='iam') for the exact steps to grant GA4 Viewer access to your service account.", skill=None, trigger="error_iam", tool_name="get_ga4_data")
            error_message += " SYSTEM DIRECTIVE: You do not know how to solve this. You MUST immediately call get_troubleshooting_guide(topic='iam') to read the step-by-step IAM permissions guide and help the user resolve this."

        else:
            fire_skill_tip(ctx, "💡 If this error involves field names or filter structure, call search_skills('common-metric-names') or search_skills('filter-structures') for correct patterns.", skill=None, trigger="error_generic", tool_name="get_ga4_data")

        return {"error": error_message}
