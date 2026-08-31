# SPDX-License-Identifier: Apache-2.0

"""The core reporting tool for fetching GA4 data across single or multiple properties."""

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
from ga4_mcp.coordinator import mcp, fire_skill_tip, note_brief_version
from ga4_mcp.telemetry import client_supports_elicitation
from ga4_mcp.sites import registry, PropertyInfo
from ga4_mcp.schema_cache import schema_cache
from ga4_mcp.client_pool import client_pool

# S3: version tags for the field-proven error briefs below.
BRIEF_INVALID_DIMENSION = "ga4-schema-dim-v1"
BRIEF_INVALID_METRIC = "ga4-schema-met-v1"
BRIEF_FILTER_SHAPE = "ga4-filter-v1"
BRIEF_INCOMPATIBLE = "ga4-incompatible-v1"
BRIEF_IAM_QUERY = "ga4-iam-query-v1"

# get_ga4_data hits the external GA4 Data API: open world, read-only, idempotent.
_READ_ONLY = ToolAnnotations(read_only_hint=True, idempotent_hint=True, open_world_hint=True)

# Legacy global schema holder for backward compatibility
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
    """Request GA4 server-side metric totals whenever a dimension splits the
    metrics across rows (a time series like ['date'] or any breakdown)."""
    return len(dimensions) >= 1 and len(metrics) >= 1

def _extract_totals(response):
    """Pull GA4's server-side totals into a metric->value map."""
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
    """Format a GA4 RunReportResponse into the tool payload."""
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
    if isinstance(d, list):
        return [_repair_filter_shape(x, parent_key) for x in d]
    if not isinstance(d, dict):
        return d
    repaired = {}
    for k, v in d.items():
        nk = _FILTER_KEY_SYNONYMS.get(k, k)
        repaired[nk] = _repair_filter_shape(v, nk)
    if parent_key == "string_filter" and "exact" in repaired and "value" not in repaired:
        repaired["value"] = repaired.pop("exact")
        repaired.setdefault("match_type", "EXACT")
    is_leaf_bearing = bool(repaired.keys() & _FILTER_LEAF_KEYS)
    if parent_key == "filter" or (parent_key in (None, "expressions", "not_expression") and is_leaf_bearing
                                  and not (repaired.keys() & _FILTER_EXPR_KEYS)):
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
    dimension_filter: dict = None,
    limit: int = 1000,
    estimate_only: bool = False,
    proceed_with_large_dataset: bool = False,
    enable_aggregation: bool = True,
    intent: str = None,
    property: str = None,
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

    CRITICAL WORKFLOW:
    1. DISCOVER SITES & FIELDS: Call `list_properties` to see all accessible sites.
       Call `search_schema` to verify exact dimension/metric names for that property.
    2. DISCOVER PATTERN: Call `search_skills('<topic>')` BEFORE querying for proven combinations.
    3. RETRIEVE: Call get_ga4_data with verified fields and optional `property='...'`.

    Args:
        dimensions: GA4 dimension names (verified via schema tools, e.g. ["date", "city"]).
        metrics: GA4 metric names (verified via schema tools, e.g. ["totalUsers", "sessions"]).
        date_range_start: Start date — 'YYYY-MM-DD' or '7daysAgo', '30daysAgo', 'yesterday'.
        date_range_end: End date — 'YYYY-MM-DD' or 'yesterday', 'today'.
        dimension_filter: Optional FilterExpression dict. camelCase and snake_case both accepted.
        limit: Max rows to return. Defaults to 1000.
        estimate_only: If True, returns only estimated row count without fetching data.
        proceed_with_large_dataset: Set True to bypass the 2500-row volume warning.
        enable_aggregation: If True, asks GA4 for server-side metric totals. Default True.
        intent: Short plain-English description of what the user is trying to learn.
        property: Optional property name, alias, or numeric Property ID. Defaults to active property.
    """
    # --- Resolve Target Property and Schema ---
    prop_info, err = registry.resolve(property)
    active_schema = None

    if err or not prop_info:
        # Check if born-broken and elicit-capable
        from ga4_mcp import coordinator as _coordinator
        if ctx is not None and _coordinator.SERVER_INIT_ERROR and client_supports_elicitation():
            from ga4_mcp.setup_flow import run_inline_recovery
            recovered, message = await run_inline_recovery(ctx)
            if not recovered:
                return {"error": message}
            prop_info, err = registry.resolve(property)

        if not prop_info:
            # Fallback to legacy PROPERTY_SCHEMA if populated
            if PROPERTY_SCHEMA:
                active_schema = PROPERTY_SCHEMA
                legacy_id = os.getenv("GA4_PROPERTY_ID", "")
                prop_info = PropertyInfo(property_id=legacy_id, display_name=f"Property {legacy_id}")
            else:
                return {"error": err or "No accessible GA4 property resolved. Call list_properties to view available sites."}

    if not active_schema:
        try:
            active_schema = schema_cache.get_schema(prop_info)
        except Exception as e:
            if PROPERTY_SCHEMA:
                active_schema = PROPERTY_SCHEMA
            else:
                return {"error": f"Could not load schema for property '{prop_info.display_name}' ({prop_info.property_id}): {e}"}

    try:
        # --- Input Parsing and Validation ---
        parsed_dimensions = dimensions if isinstance(dimensions, list) else [d.strip() for d in dimensions.split(',')]
        parsed_metrics = metrics if isinstance(metrics, list) else [m.strip() for m in metrics.split(',')]

        parsed_metrics = [METRIC_ALIASES.get(m, m) for m in parsed_metrics]
        parsed_dimensions = [DIMENSION_ALIASES.get(d, d) for d in parsed_dimensions]

        if not parsed_metrics:
            return {"error": "Metrics list cannot be empty."}

        valid_dims = active_schema["dimensions"].keys()
        valid_mets = active_schema["metrics"].keys()
        for dim in parsed_dimensions:
            if dim not in valid_dims:
                fire_skill_tip(ctx, "💡 Skill tip: search_skills('common-metric-names') has the correct GA4 field names.", skill="common-metric-names", trigger="error_schema", tool_name="get_ga4_data")
                note_brief_version(BRIEF_INVALID_DIMENSION)
                return {"error": f"Invalid dimension: '{dim}' — not present in property '{prop_info.display_name}' live GA4 schema. Call search_schema('<keyword>') to verify names for this property."}
        for met in parsed_metrics:
            if met not in valid_mets:
                fire_skill_tip(ctx, "💡 Skill tip: search_skills('common-metric-names') has the correct GA4 metric names.", skill="common-metric-names", trigger="error_schema", tool_name="get_ga4_data")
                note_brief_version(BRIEF_INVALID_METRIC)
                return {"error": f"Invalid metric: '{met}' — not present in property '{prop_info.display_name}' live GA4 schema. Call search_schema('<keyword>') to verify names for this property."}

        # --- Filter Expression Building ---
        filter_expression = None
        if dimension_filter:
            try:
                snake_filter = _repair_filter_shape(_convert_keys_to_snake(dimension_filter))
                filter_expression = FilterExpression(snake_filter)
            except Exception as e:
                fire_skill_tip(ctx, "💡 Skill tip: search_skills('filter-structures') has copy-paste templates for every filter type.", skill="filter-structures", trigger="error_filter", tool_name="get_ga4_data")
                note_brief_version(BRIEF_FILTER_SHAPE)
                return {"error": f"Invalid dimension_filter structure: {e}. Call search_skills('filter-structures') for templates."}

        # Channel 2: proactive tip
        skill = _suggest_skill(parsed_dimensions, parsed_metrics, intent)
        if skill:
            fire_skill_tip(ctx, f"💡 Skill available: search_skills('{skill}') has the full analytical methodology for this query type.", skill=skill, trigger="pre_query", tool_name="get_ga4_data")
        else:
            fire_skill_tip(ctx, "💡 GA4 Skills: 15 analytical recipes available. Call search_skills() to find the proven pattern.", skill=None, trigger="pre_query", tool_name="get_ga4_data")

        # --- API Client and Request Objects ---
        client = client_pool.get_data_client(prop_info.credentials_path)
        property_target = f"properties/{prop_info.property_id}"
        dimension_objects = [Dimension(name=d) for d in parsed_dimensions]
        metric_objects = [Metric(name=m) for m in parsed_metrics]
        date_range_object = DateRange(start_date=date_range_start, end_date=date_range_end)

        # --- Row Count Estimation ---
        if not proceed_with_large_dataset or estimate_only:
            try:
                estimation_req = RunReportRequest(
                    property=property_target,
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
            property=property_target,
            dimensions=dimension_objects,
            metrics=metric_objects,
            date_ranges=[date_range_object],
            dimension_filter=filter_expression,
            limit=limit,
            order_bys=_get_smart_sorting(parsed_dimensions, parsed_metrics),
            metric_aggregations=[MetricAggregation.TOTAL] if enable_aggregation and _should_aggregate(parsed_dimensions, parsed_metrics) else None
        )
        response = await asyncio.to_thread(client.run_report, request=request)

        # --- Response Formatting ---
        return _build_report_payload(response, skill)

    except Exception as e:
        error_message = f"Error fetching GA4 data for property '{prop_info.display_name}' ({prop_info.property_id}): {str(e)}"
        print(error_message, file=sys.stderr)
        if hasattr(e, 'details'):
            details_val = e.details() if callable(getattr(e, 'details', None)) else getattr(e, 'details')
            error_message += f" Details: {details_val}"

        if "incompatible" in error_message.lower() or "dimensions & metrics" in error_message.lower():
            fire_skill_tip(ctx, "💡 Skill tip: search_skills('compatible-combinations') explains which dimension/metric scopes can be paired.", skill="compatible-combinations", trigger="error_incompatible", tool_name="get_ga4_data")
            error_message += " SYSTEM DIRECTIVE: Call search_skills('compatible-combinations') to learn which dimensions and metrics can be combined."
            note_brief_version(BRIEF_INCOMPATIBLE)

        elif "403" in error_message or "PermissionDenied" in error_message or "permission" in error_message.lower():
            fire_skill_tip(ctx, "💡 Permission error detected. Verify that your credentials have Viewer access on this GA4 property.", skill=None, trigger="error_iam", tool_name="get_ga4_data")
            error_message += " SYSTEM DIRECTIVE: Call get_troubleshooting_guide(topic='iam') to read the IAM permissions guide."
            note_brief_version(BRIEF_IAM_QUERY)

        else:
            fire_skill_tip(ctx, "💡 If this error involves field names or filter structure, call search_skills('common-metric-names') or search_skills('filter-structures').", skill=None, trigger="error_generic", tool_name="get_ga4_data")

        return {"error": error_message}
