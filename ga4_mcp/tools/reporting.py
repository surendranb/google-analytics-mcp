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
from ga4_mcp.coordinator import mcp

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


# Common LLM metric aliases (e.g., legacy GA metric names -> GA4 Data API names)
# Extend from telemetry: recurring SchemaHallucination field names get an alias.
METRIC_ALIASES = {
    "conversions": "keyEvents",
    "conversion_rate": "sessionConversionRate",
    "user_conversion_rate": "userConversionRate",
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

@mcp.tool()
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
    intent: str = None
):
    """
    Retrieve GA4 data with built-in intelligence for better and safer results.

    CRITICAL WORKFLOW INSTRUCTIONS FOR AI AGENTS:
    To ensure deterministic and successful data retrieval, you MUST follow this sequence:
    1. DISCOVER: NEVER guess dimension or metric names. Always call `search_schema`, `list_dimension_categories`, or `list_metric_categories` FIRST to verify the exact API names available for this property.
    2. RETRIEVE: Call this tool (`get_ga4_data`) using the verified dimensions and metrics.
    3. TROUBLESHOOT: If you receive a SchemaError, an Invalid Dimension/Metric error, or an error about `dimension_filter` structure, DO NOT RETRY BY GUESSING. You MUST immediately call `get_troubleshooting_guide(topic='schema')` to learn the correct structure and available fields.

    **Smart Features:**
    - **Data Volume Protection:** Before running a query that could produce a huge
      number of rows, the tool runs a quick estimate. If the row count exceeds a
      safe threshold (2500 rows), it will return a warning with suggestions instead
      of the data. You can override this by setting `proceed_with_large_dataset=True`.
    - **Automatic Server-Side Aggregation:** If your query does not involve a time
      dimension (like 'date'), the tool automatically asks the GA4 API to return
      aggregated totals. This is more efficient and provides cleaner results. You
      can disable this by setting `enable_aggregation=False`.
    - **Intelligent Sorting:** Results are automatically sorted by date (most recent
      first) and the primary metric (highest value first) to show the most
      relevant data at the top.

    Args:
        dimensions: List of GA4 dimensions (e.g., ["date", "city"]). MUST be verified via schema tools.
        metrics: List of GA4 metrics (e.g., ["totalUsers", "sessions"]). MUST be verified via schema tools.
        date_range_start: Start date in YYYY-MM-DD format or relative date ('7daysAgo').
        date_range_end: End date in YYYY-MM-DD format or relative date ('yesterday').
        dimension_filter: (Optional) A GA4 FilterExpression dictionary. Both camelCase and snake_case
                          keys are transparently auto-translated and supported.
                          Example simple filter structure:
                          {
                              "filter": {
                                  "fieldName": "sessionSource",
                                  "stringFilter": {"value": "google", "matchType": "CONTAINS"}
                              }
                          }
                          Example logical group (andGroup, orGroup, notExpression):
                          {
                              "andGroup": {
                                  "expressions": [
                                      {"filter": {"fieldName": "deviceCategory", "stringFilter": {"value": "mobile"}}},
                                      {"filter": {"fieldName": "country", "stringFilter": {"value": "United States"}}}
                                  ]
                              }
                          }
        limit: (Optional) Maximum number of rows to return. Defaults to 1000.
        estimate_only: (Optional) If True, returns only the estimated row count
                       without fetching the full dataset.
        proceed_with_large_dataset: (Optional) Set to True to bypass the data volume
                                    warning and execute the query anyway.
        enable_aggregation: (Optional) If True, uses server-side aggregation when
                            beneficial. Defaults to True.
        intent: (Optional) The category of question this query answers. Pick ONE from:
                traffic_overview | acquisition | content_performance | ecommerce_revenue |
                user_behavior | geography_devices | campaign_analysis | seo | debugging | other

    COMMON MISTAKES (checked against real usage — read before guessing names):
    - Metric is 'keyEvents', not 'conversions'. 'totalUsers', not 'users'.
      'itemsViewed', not 'itemViews'. 'ecommercePurchases', not 'purchases'.
    - Dimension is 'sessionDefaultChannelGroup', not 'sessionDefaultChannelGrouping'.
    - A simple dimension_filter MUST nest inside a "filter" key:
      {"filter": {"fieldName": ..., "stringFilter": {...}}} — not fieldName at the top level.
    - Logical groups are "andGroup"/"orGroup"/"notExpression" — not and_filter/or_filter.
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
                return {"error": f"Invalid dimension: '{dim}'. DO NOT GUESS DIMENSIONS. SYSTEM DIRECTIVE: You do not know how to solve this. You MUST immediately call the 'get_troubleshooting_guide' tool with topic='schema' to learn how to find valid dimensions."}
        for met in parsed_metrics:
            if met not in valid_mets:
                return {"error": f"Invalid metric: '{met}'. DO NOT GUESS METRICS. SYSTEM DIRECTIVE: You do not know how to solve this. You MUST immediately call the 'get_troubleshooting_guide' tool with topic='schema' to learn how to find valid metrics."}

        # --- Filter Expression Building ---
        filter_expression = None
        if dimension_filter:
            try:
                # Recursively translate camelCase keys to snake_case for proto-plus
                # compatibility, then repair known wrong shapes models send
                snake_filter = _repair_filter_shape(_convert_keys_to_snake(dimension_filter))
                filter_expression = FilterExpression(snake_filter)
            except Exception as e:
                return {"error": f"Invalid dimension_filter structure: {e}. SYSTEM DIRECTIVE: You do not know how to solve this. You MUST immediately call get_troubleshooting_guide(topic='schema') to learn the correct structure."}

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

                if estimated_rows > 2500:
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

        return {
            "data": result,
            "metadata": {
                "total_rows_in_source": response.row_count,
                "returned_rows": len(result),
            }
        }
    except Exception as e:
        error_message = f"Error fetching GA4 data: {str(e)}"
        print(error_message, file=sys.stderr)
        if hasattr(e, 'details'):
            details_val = e.details() if callable(getattr(e, 'details', None)) else getattr(e, 'details')
            error_message += f" Details: {details_val}"
            
        if "403" in error_message or "PermissionDenied" in error_message or "permission" in error_message.lower():
            error_message += " SYSTEM DIRECTIVE: You do not know how to solve this. You MUST immediately call get_troubleshooting_guide(topic='iam') to read the step-by-step IAM permissions guide and help the user resolve this."
            
        return {"error": error_message}
