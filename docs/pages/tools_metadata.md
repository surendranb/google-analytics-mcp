# tools/metadata

Tools for fetching and exploring GA4 property metadata.

## Function: `get_property_schema_uncached`

Fetches the full schema (dimensions and metrics) for a GA4 property.
This function makes a live API call and is intended to be called once on startup.

## Function: `search_schema`

Searches for a keyword across all available dimensions and metrics for the property.
Returns a short, ranked list of the most relevant fields. This is the most
efficient way to discover dimensions and metrics for a specific query.

Args:
    keyword: One or more keywords to search for (e.g., "user", "campaign revenue").

## Function: `get_property_schema`

Returns the complete schema for the configured GA4 property, including all
available dimensions and metrics (standard and custom). Warning: This can be
a very large object (10k+ tokens). Use search_schema for most discovery tasks.

## Function: `list_dimension_categories`

List all available GA4 dimension categories based on the property's schema.
This is a low-cost way to begin exploring the schema.

## Function: `list_metric_categories`

List all available GA4 metric categories based on the property's schema.
This is a low-cost way to begin exploring the schema.

## Function: `get_dimensions_by_category`

Get all dimensions in a specific category with their descriptions.

Args:
    category: The category name to retrieve dimensions for.

## Function: `get_metrics_by_category`

Get all metrics in a specific category with their descriptions.

Args:
    category: The category name to retrieve metrics for.

