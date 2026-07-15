# SPDX-License-Identifier: Apache-2.0

"""Tools for fetching and exploring GA4 property metadata."""

from google.analytics.data_v1beta import BetaAnalyticsDataClient
from mcp.types import ToolAnnotations
from mcp.server.fastmcp import Context
from ga4_mcp.coordinator import mcp, fire_skill_tip

_SCHEMA_SKILL_HINTS = [
    (["channel", "source", "medium", "campaign", "acquisition"], "channel-acquisition"),
    (["revenue", "purchase", "ecommerce", "transaction", "cart", "checkout"], "ecommerce-analysis"),
    (["page", "content", "scroll", "landing", "article", "blog"], "content-performance"),
    (["country", "city", "device", "geo", "region", "mobile"], "geo-device-segmentation"),
    (["bot", "spam", "scraper", "crawler"], "bot-traffic-detection"),
    (["attribution", "firstuser", "first user", "last click"], "attribution-scope"),
    (["ai", "chatgpt", "claude", "perplexity", "gemini", "openai"], "ai-referral-analysis"),
    (["custom", "event parameter", "customevent"], "custom-dimensions"),
    (["conversion", "keyevent", "goal"], "ecommerce-analysis"),
]

def _hint_from_keyword(keyword: str) -> str | None:
    kw = keyword.lower()
    for terms, skill in _SCHEMA_SKILL_HINTS:
        if any(t in kw for t in terms):
            return skill
    return None

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
def search_schema(keyword: str, ctx: Context = None):
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

    # Proactive Channel 2: fire before returning results, while model is still in discovery mode
    skill = _hint_from_keyword(keyword)
    if skill:
        fire_skill_tip(ctx, f"💡 Skill match: search_skills('{skill}') has the full analytical pattern for '{keyword}' analysis — proven dimensions, metrics, filters, and how to interpret the result. Call it before get_ga4_data.", skill=skill, trigger="field_discovery", tool_name="search_schema")
    else:
        fire_skill_tip(ctx, "💡 GA4 Skills library has 15 analytical recipes. Call search_skills() to find the proven query pattern for your analysis before calling get_ga4_data.", skill=None, trigger="field_discovery", tool_name="search_schema")

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
def list_dimension_categories(ctx: Context = None):
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

    fire_skill_tip(ctx, "💡 While you explore dimensions: search_skills() has 15 analytical recipes with proven dimension+metric combinations ready to use. Call search_skills('<topic>') before get_ga4_data to skip the guesswork.", skill=None, trigger="category_browse", tool_name="list_dimension_categories")

    categories = {}
    for dim_info in PROPERTY_SCHEMA["dimensions"].values():
        category = dim_info.get("category", "Uncategorized")
        if category not in categories:
            categories[category] = 0
        categories[category] += 1

    return {"dimension_categories": categories}

@mcp.tool(annotations=_READ_ONLY)
def list_metric_categories(ctx: Context = None):
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

    fire_skill_tip(ctx, "💡 While you explore metrics: search_skills() has 15 analytical recipes with proven dimension+metric combinations ready to use. Call search_skills('<topic>') before get_ga4_data to skip the guesswork.", skill=None, trigger="category_browse", tool_name="list_metric_categories")

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