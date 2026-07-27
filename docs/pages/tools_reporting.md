# tools/reporting

The core reporting tool for fetching GA4 data.

## Function: `_get_smart_sorting`

Determine optimal sorting strategy for relevance.

## Function: `_should_aggregate`

Detect when server-side aggregation would be beneficial.

## Function: `get_ga4_data`

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

