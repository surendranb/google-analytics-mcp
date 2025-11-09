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
    enable_aggregation: bool = True
):
    """
    Retrieve GA4 data with built-in intelligence for better and safer results.

    This tool is a powerful wrapper around the Google Analytics Data API. It not only
    fetches data but also includes "smart" features to protect against context window
    overloads and to provide more relevant results by default.

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
        dimensions: List of GA4 dimensions (e.g., ["date", "city"]).
        metrics: List of GA4 metrics (e.g., ["totalUsers", "sessions"]).
        date_range_start: Start date in YYYY-MM-DD format or relative date ('7daysAgo').
        date_range_end: End date in YYYY-MM-DD format or relative date ('yesterday').
        dimension_filter: (Optional) A dictionary representing a GA4 FilterExpression
                          to apply to the dimensions. See GA4 API docs for structure.
        limit: (Optional) Maximum number of rows to return. Defaults to 1000.
        estimate_only: (Optional) If True, returns only the estimated row count
                       without fetching the full dataset.
        proceed_with_large_dataset: (Optional) Set to True to bypass the data volume
                                    warning and execute the query anyway.
        enable_aggregation: (Optional) If True, uses server-side aggregation when
                            beneficial. Defaults to True.
    """
    if not PROPERTY_SCHEMA:
        return {"error": "Schema not loaded. Please check server startup logs."}

    try:
        # --- Input Parsing and Validation ---
        parsed_dimensions = dimensions if isinstance(dimensions, list) else [d.strip() for d in dimensions.split(',')]
        parsed_metrics = metrics if isinstance(metrics, list) else [m.strip() for m in metrics.split(',')]

        if not parsed_dimensions:
            return {"error": "Dimensions list cannot be empty."}
        if not parsed_metrics:
            return {"error": "Metrics list cannot be empty."}

        valid_dims = PROPERTY_SCHEMA["dimensions"].keys()
        valid_mets = PROPERTY_SCHEMA["metrics"].keys()
        for dim in parsed_dimensions:
            if dim not in valid_dims:
                return {"error": f"Invalid dimension: '{dim}'. Use list_dimension_categories() to see available dimensions."}
        for met in parsed_metrics:
            if met not in valid_mets:
                return {"error": f"Invalid metric: '{met}'. Use list_metric_categories() to see available metrics."}

        # --- Filter Expression Building ---
        filter_expression = None
        if dimension_filter:
            # The original script had a complex recursive builder. For this refactoring,
            # we'll rely on the user passing a correctly structured dict, similar to the
            # official google/analytics-mcp project. This simplifies the code greatly.
            # A more robust builder can be added back later if needed.
            try:
                filter_expression = FilterExpression(dimension_filter)
            except Exception as e:
                return {"error": f"Invalid dimension_filter structure: {e}"}

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
            error_message += f" Details: {e.details()}"
        return {"error": error_message}
