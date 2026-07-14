# SPDX-License-Identifier: Apache-2.0

"""Tools for fetching and exploring GA4 property metadata."""

from google.analytics.data_v1beta import BetaAnalyticsDataClient
from mcp.types import ToolAnnotations
from ga4_mcp.coordinator import mcp

_READ_ONLY = ToolAnnotations(readOnlyHint=True)

# This global variable will be populated by the server on startup.
PROPERTY_SCHEMA = None

def get_property_schema_uncached(property_id: str) -> dict:
    """
    Fetches the full schema (dimensions and metrics) for a GA4 property.
    This function makes a live API call and is intended to be called once on startup.
    """
    client = BetaAnalyticsDataClient()
    request = {"name": f"properties/{property_id}/metadata"}
    metadata = client.get_metadata(request=request)

    schema = {"dimensions": {}, "metrics": {}}

    for dim in metadata.dimensions:
        schema["dimensions"][dim.api_name] = {
            "ui_name": dim.ui_name,
            "description": dim.description,
            "category": dim.category,
            "custom_definition": dim.custom_definition,
        }

    for met in metadata.metrics:
        schema["metrics"][met.api_name] = {
            "ui_name": met.ui_name,
            "description": met.description,
            "category": met.category,
            "type": met.type_.name,
        }
    return schema

@mcp.tool(annotations=_READ_ONLY)
def search_schema(keyword: str):
    """
    Search for a keyword across all dimensions and metrics for this property.
    Returns a ranked list of up to 10 matching fields scored by relevance.

    Returns: {"top_results": {"DIMENSION: api_name": score, "METRIC: api_name": score, ...}}

    Use this to verify exact API names before calling get_ga4_data — fastest path
    from a concept ("engagement", "revenue", "channel") to the correct field name.
    Use list_dimension_categories or list_metric_categories instead if you want to
    browse all available fields without a specific keyword.

    Args:
        keyword: One or more keywords to search for (e.g., "user", "campaign revenue").
    """
    if not PROPERTY_SCHEMA:
        return {"error": "Schema not loaded. Please check server startup logs."}

    scores = {}
    search_terms = keyword.lower().split()

    # Search dimensions
    for name, info in PROPERTY_SCHEMA["dimensions"].items():
        score = 0
        for term in search_terms:
            if term in name.lower(): score += 10
            if term in info.get("ui_name", "").lower(): score += 5
            if term in info.get("description", "").lower(): score += 2
            if term in info.get("category", "").lower(): score += 1
        if score > 0:
            scores[f"DIMENSION: {name}"] = score

    # Search metrics
    for name, info in PROPERTY_SCHEMA["metrics"].items():
        score = 0
        for term in search_terms:
            if term in name.lower(): score += 10
            if term in info.get("ui_name", "").lower(): score += 5
            if term in info.get("description", "").lower(): score += 2
            if term in info.get("category", "").lower(): score += 1
        if score > 0:
            scores[f"METRIC: {name}"] = score

    if not scores:
        return {"message": f"No dimensions or metrics found matching '{keyword}'."}

    # Sort by score descending and return top 10
    sorted_results = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    return {"top_results": dict(sorted_results[:10])}


@mcp.tool(annotations=_READ_ONLY)
def get_property_schema():
    """
    Returns the complete schema for the configured GA4 property, including all
    available dimensions and metrics (standard and custom). Warning: This can be
    a very large object (10k+ tokens). Use search_schema for most discovery tasks.
    """
    if not PROPERTY_SCHEMA:
        return {"error": "Schema not loaded. Please check server startup logs."}
    return PROPERTY_SCHEMA

@mcp.tool(annotations=_READ_ONLY)
def list_dimension_categories():
    """
    List all dimension categories for this GA4 property, with a count of
    dimensions in each category.

    Returns: {"dimension_categories": {"Category Name": count, ...}}

    Use this as the first step in dimension exploration — browse categories,
    then call get_dimensions_by_category with the name that fits your analysis.
    Use search_schema instead if you already have a keyword to search for.
    """
    if not PROPERTY_SCHEMA:
        return {"error": "Schema not loaded."}
    
    categories = {}
    for dim_info in PROPERTY_SCHEMA["dimensions"].values():
        category = dim_info.get("category", "Uncategorized")
        if category not in categories:
            categories[category] = 0
        categories[category] += 1
        
    return {"dimension_categories": categories}

@mcp.tool(annotations=_READ_ONLY)
def list_metric_categories():
    """
    List all metric categories for this GA4 property, with a count of
    metrics in each category.

    Returns: {"metric_categories": {"Category Name": count, ...}}

    Use this as the first step in metric exploration — browse categories,
    then call get_metrics_by_category with the name that fits your analysis.
    Use search_schema instead if you already have a keyword to search for.
    """
    if not PROPERTY_SCHEMA:
        return {"error": "Schema not loaded."}

    categories = {}
    for met_info in PROPERTY_SCHEMA["metrics"].values():
        category = met_info.get("category", "Uncategorized")
        if category not in categories:
            categories[category] = 0
        categories[category] += 1

    return {"metric_categories": categories}

@mcp.tool(annotations=_READ_ONLY)
def get_dimensions_by_category(category: str):
    """
    Return all dimensions in a specific category with their API names and descriptions.

    Returns: {"dimension_api_name": "description", ...}

    The category name must exactly match a value returned by list_dimension_categories.
    Use search_schema instead if you already have a keyword — it is faster and more
    targeted than browsing by category.

    Args:
        category: Exact category name from list_dimension_categories (case-insensitive).
    """
    if not PROPERTY_SCHEMA:
        return {"error": "Schema not loaded."}

    dimensions_in_category = {}
    for name, dim_info in PROPERTY_SCHEMA["dimensions"].items():
        if dim_info.get("category", "Uncategorized").lower() == category.lower():
            dimensions_in_category[name] = dim_info["description"]
            
    if not dimensions_in_category:
        return {"error": f"Category '{category}' not found or has no dimensions."}
        
    return dimensions_in_category

@mcp.tool(annotations=_READ_ONLY)
def get_metrics_by_category(category: str):
    """
    Return all metrics in a specific category with their API names and descriptions.

    Returns: {"metric_api_name": "description", ...}

    The category name must exactly match a value returned by list_metric_categories.
    Use search_schema instead if you already have a keyword — it is faster and more
    targeted than browsing by category.

    Args:
        category: Exact category name from list_metric_categories (case-insensitive).
    """
    if not PROPERTY_SCHEMA:
        return {"error": "Schema not loaded."}

    metrics_in_category = {}
    for name, met_info in PROPERTY_SCHEMA["metrics"].items():
        if met_info.get("category", "Uncategorized").lower() == category.lower():
            metrics_in_category[name] = met_info["description"]

    if not metrics_in_category:
        return {"error": f"Category '{category}' not found or has no metrics."}

    return metrics_in_category