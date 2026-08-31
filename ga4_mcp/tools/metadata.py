# SPDX-License-Identifier: Apache-2.0

"""Tools for fetching and exploring GA4 property metadata and property catalog."""

from mcp.types import ToolAnnotations
from mcp.server.mcpserver import Context
from ga4_mcp.coordinator import mcp, fire_skill_tip
from ga4_mcp.sites import registry, PropertyInfo
from ga4_mcp.schema_cache import schema_cache

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

# Read-only metadata tools
_READ_ONLY = ToolAnnotations(read_only_hint=True, idempotent_hint=True, open_world_hint=False)

# Legacy global schema holder for backward compatibility
PROPERTY_SCHEMA = None


def _resolve_schema_for_property(property_identifier: str | None = None) -> tuple[dict | None, str | None]:
    """Helper to resolve a property and return its schema dictionary."""
    global PROPERTY_SCHEMA
    prop_info, err = registry.resolve(property_identifier)
    if err or not prop_info:
        if PROPERTY_SCHEMA:
            return PROPERTY_SCHEMA, None
        return None, err or "Could not resolve GA4 property."

    try:
        schema = schema_cache.get_schema(prop_info)
        return schema, None
    except Exception as e:
        if PROPERTY_SCHEMA:
            return PROPERTY_SCHEMA, None
        return None, f"Could not load schema for property '{prop_info.display_name}' ({prop_info.property_id}): {e}"


@mcp.tool(annotations=_READ_ONLY)
def list_properties(ctx: Context = None) -> dict:
    """
    List all GA4 properties and accounts accessible with your configured credentials.

    Returns: {"properties": [{"property_id": "...", "display_name": "...", "account_name": "...", "alias": "...", "is_default": bool}, ...]}

    Use this tool to see what websites/properties you can query, or when a user mentions a site
    by name and you need to confirm its exact Property ID.
    """
    props = registry.list_all()
    if not props:
        return {
            "properties": [],
            "message": "No GA4 properties found. Please verify your credentials or run 'gcloud auth application-default login'."
        }
    return {"properties": props}


@mcp.tool(annotations=_READ_ONLY)
def search_schema(keyword: str, property: str = None, ctx: Context = None):
    """
    Search for a keyword across all dimensions and metrics for a GA4 property.
    Returns a ranked list of up to 10 matching fields scored by relevance.

    Returns: {"top_results": {"DIMENSION: api_name": score, "METRIC: api_name": score, ...}}

    Use this when you have a concept ("engagement", "revenue", "channel") and need
    exact API field names before calling get_ga4_data.

    Args:
        keyword: One or more keywords to search for (e.g., "user", "campaign revenue").
        property: Optional property name, alias, or numeric ID. Defaults to active property.
    """
    schema, err = _resolve_schema_for_property(property)
    if err or not schema:
        return {"error": err or "Schema not loaded. Please check server startup logs."}

    # Proactive Channel 2: fire before returning results, while model is still in discovery mode
    skill = _hint_from_keyword(keyword)
    if skill:
        fire_skill_tip(ctx, f"💡 Skill match: search_skills('{skill}') has the full analytical pattern for '{keyword}' analysis — proven dimensions, metrics, filters, and how to interpret the result. Call it before get_ga4_data.", skill=skill, trigger="field_discovery", tool_name="search_schema")
    else:
        fire_skill_tip(ctx, "💡 GA4 Skills library has 15 analytical recipes. Call search_skills() to find the proven query pattern for your analysis before calling get_ga4_data.", skill=None, trigger="field_discovery", tool_name="search_schema")

    scores = {}
    search_terms = keyword.lower().split()

    # Search dimensions
    for name, info in schema["dimensions"].items():
        score = 0
        for term in search_terms:
            if term in name.lower(): score += 10
            if term in info.get("ui_name", "").lower(): score += 5
            if term in info.get("description", "").lower(): score += 2
            if term in info.get("category", "").lower(): score += 1
        if score > 0:
            scores[f"DIMENSION: {name}"] = score

    # Search metrics
    for name, info in schema["metrics"].items():
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
def get_property_schema(property: str = None):
    """
    Returns the complete schema for a GA4 property, including all
    available dimensions and metrics (standard and custom). Warning: This can be
    a very large object (10k+ tokens). Use search_schema for most discovery tasks.

    Args:
        property: Optional property name, alias, or numeric ID. Defaults to active property.
    """
    schema, err = _resolve_schema_for_property(property)
    if err or not schema:
        return {"error": err or "Schema not loaded. Please check server startup logs."}
    return schema


@mcp.tool(annotations=_READ_ONLY)
def list_dimension_categories(property: str = None, ctx: Context = None):
    """
    List all dimension categories for a GA4 property, with a count of
    dimensions in each category.

    Returns: {"dimension_categories": {"Category Name": count, ...}}

    Args:
        property: Optional property name, alias, or numeric ID. Defaults to active property.
    """
    schema, err = _resolve_schema_for_property(property)
    if err or not schema:
        return {"error": err or "Schema not loaded."}

    fire_skill_tip(ctx, "💡 While you explore dimensions: search_skills() has 15 analytical recipes with proven dimension+metric combinations ready to use. Call search_skills('<topic>') before get_ga4_data to skip the guesswork.", skill=None, trigger="category_browse", tool_name="list_dimension_categories")

    categories = {}
    for dim_info in schema["dimensions"].values():
        category = dim_info.get("category", "Uncategorized")
        if category not in categories:
            categories[category] = 0
        categories[category] += 1

    return {"dimension_categories": categories}


@mcp.tool(annotations=_READ_ONLY)
def list_metric_categories(property: str = None, ctx: Context = None):
    """
    List all metric categories for a GA4 property, with a count of
    metrics in each category.

    Returns: {"metric_categories": {"Category Name": count, ...}}

    Args:
        property: Optional property name, alias, or numeric ID. Defaults to active property.
    """
    schema, err = _resolve_schema_for_property(property)
    if err or not schema:
        return {"error": err or "Schema not loaded."}

    fire_skill_tip(ctx, "💡 While you explore metrics: search_skills() has 15 analytical recipes with proven dimension+metric combinations ready to use. Call search_skills('<topic>') before get_ga4_data to skip the guesswork.", skill=None, trigger="category_browse", tool_name="list_metric_categories")

    categories = {}
    for met_info in schema["metrics"].values():
        category = met_info.get("category", "Uncategorized")
        if category not in categories:
            categories[category] = 0
        categories[category] += 1

    return {"metric_categories": categories}


@mcp.tool(annotations=_READ_ONLY)
def get_dimensions_by_category(category: str, property: str = None):
    """
    Return all dimensions in a specific category with their API names and descriptions.

    Returns: {"dimension_api_name": "description", ...}

    Args:
        category: Exact category name from list_dimension_categories (case-insensitive).
        property: Optional property name, alias, or numeric ID. Defaults to active property.
    """
    schema, err = _resolve_schema_for_property(property)
    if err or not schema:
        return {"error": err or "Schema not loaded."}

    dimensions_in_category = {}
    for name, dim_info in schema["dimensions"].items():
        if dim_info.get("category", "Uncategorized").lower() == category.lower():
            dimensions_in_category[name] = dim_info["description"]
            
    if not dimensions_in_category:
        return {"error": f"Category '{category}' not found or has no dimensions."}
        
    return dimensions_in_category


@mcp.tool(annotations=_READ_ONLY)
def get_metrics_by_category(category: str, property: str = None):
    """
    Return all metrics in a specific category with their API names and descriptions.

    Returns: {"metric_api_name": "description", ...}

    Args:
        category: Exact category name from list_metric_categories (case-insensitive).
        property: Optional property name, alias, or numeric ID. Defaults to active property.
    """
    schema, err = _resolve_schema_for_property(property)
    if err or not schema:
        return {"error": err or "Schema not loaded."}

    metrics_in_category = {}
    for name, met_info in schema["metrics"].items():
        if met_info.get("category", "Uncategorized").lower() == category.lower():
            metrics_in_category[name] = met_info["description"]

    if not metrics_in_category:
        return {"error": f"Category '{category}' not found or has no metrics."}

    return metrics_in_category
