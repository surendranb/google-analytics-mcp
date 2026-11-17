# SPDX-License-Identifier: Apache-2.0

"""Tools for fetching and exploring GA4 property metadata."""

import os
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, RunReportRequest
from mcp.types import ToolAnnotations
from mcp.server.mcpserver import Context
from ga4_mcp import coordinator
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

# Schema tools read the startup-cached property schema — no external call at
# call time, hence open_world_hint=False (SDK v2 accepts snake_case field names
# and serializes to the spec's camelCase aliases; verified empirically).
_READ_ONLY = ToolAnnotations(read_only_hint=True, idempotent_hint=True, open_world_hint=False)

# This global variable will be populated by the server on startup.
PROPERTY_SCHEMA = None

# Search Console metrics the metadata API still advertises for EVERY property,
# linked or not. On a property without an active Search Console link the report
# path 400s every request naming them ("Search Console fields require an active
# link"), so a caller that trusts search_schema burns a round-trip to learn
# nothing. GA4 exposes no flag for the link state (blocked_reasons is empty), so
# the one API call below decides it per property and the names stop being
# admitted here — the same numbers live in the Search Console API.
SEARCH_CONSOLE_REPLACEMENTS = {
    "organicGoogleSearchClicks": "clicks",
    "organicGoogleSearchImpressions": "impressions",
    "organicGoogleSearchAveragePosition": "position",
    "organicGoogleSearchClickThroughRate": "clickThroughRate",
}

# api_name -> Search Console API name, for fields this property cannot serve.
UNAVAILABLE_FIELDS = {}


def unavailable_fields():
    """Fields dropped from this property's schema at load, mapped to the Search
    Console field that carries the same number."""
    return UNAVAILABLE_FIELDS


def _drop_unservable_search_console(schema, client, property_id):
    """Decide ONCE, at schema load, whether this property can serve Search
    Console metrics. `date` is a compatible dimension for the whole family, so a
    400 naming the Search Console link is a definitive property-level answer;
    any other failure (5xx, network, wrong pairing) leaves the names admitted —
    never drop on an inconclusive answer."""
    names = [n for n in schema["metrics"] if n in SEARCH_CONSOLE_REPLACEMENTS]
    if not names:
        return
    try:
        client.run_report(request=RunReportRequest(
            property=f"properties/{property_id}",
            dimensions=[Dimension(name="date")],
            metrics=[Metric(name=names[0])],
            date_ranges=[DateRange(start_date="7daysAgo", end_date="yesterday")],
            limit=1))
        return
    except Exception as e:
        # Observed GA4 answer: "Search Console fields require an active link to be used."
        if "active link" not in str(e).lower():
            return
    for name in names:
        schema["metrics"].pop(name, None)
        UNAVAILABLE_FIELDS[name] = SEARCH_CONSOLE_REPLACEMENTS[name]


def _no_schema_error():
    """Every schema tool fails identically when boot could not load the property
    schema: hand the model the setup brief (what broke, who fixes it) instead of
    a pointer to a log it cannot read."""
    if coordinator.SERVER_INIT_ERROR:
        return {"error": str(coordinator.SERVER_INIT_ERROR)}
    return {"error": coordinator.build_guided_init_error(
        "The GA4 property schema is not loaded, so no field name can be resolved for this property.",
        ["Ask me to retry — the server reloads the schema from GA4 on the next tool call.",
         "If it stays unloaded, the property ID or credentials are wrong (call setup_ga4_access "
         "to set a missing value in-session).",
         coordinator.config_hint()],
        "setup",
        why="Field names are read from the live property schema; without it a query would be a guess.")}


def get_property_schema_uncached(property_id: str) -> dict:
    """
    Fetches the full schema (dimensions and metrics) for a GA4 property.
    This function makes a live API call and is intended to be called once on startup.
    """
    from ..coordinator import get_data_client
    client = get_data_client()
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
    UNAVAILABLE_FIELDS.clear()
    _drop_unservable_search_console(schema, client, property_id)
    return schema

@mcp.tool(annotations=_READ_ONLY)
def list_properties(account_id: str = "", ctx: Context = None) -> dict:
    """
    List all GA4 properties associated with an account.
    """
    property_id = os.getenv("GA4_PROPERTY_ID")
    if property_id:
        return {"properties": [{"property_id": property_id}]}
    return {"error": coordinator.property_id_brief()}

@mcp.tool(annotations=_READ_ONLY)
def search_schema(keyword: str, ctx: Context = None):
    """
    Search for a keyword across all dimensions and metrics for this property.
    Returns a ranked list of up to 10 matching fields scored by relevance.

    Returns: {"top_results": {"DIMENSION: api_name": score, "METRIC: api_name": score, ...}}

    Use this when you have a concept ("engagement", "revenue", "channel") and need
    exact API field names before calling get_ga4_data.
    Use list_dimension_categories or list_metric_categories instead if you want to
    browse all available fields without a specific keyword.

    Args:
        keyword: One or more keywords to search for (e.g., "user", "campaign revenue").
    """
    if not PROPERTY_SCHEMA:
        return _no_schema_error()

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
        return _no_schema_error()
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
        return _no_schema_error()

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
        return _no_schema_error()

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
        return _no_schema_error()

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
        return _no_schema_error()

    metrics_in_category = {}
    for name, met_info in PROPERTY_SCHEMA["metrics"].items():
        if met_info.get("category", "Uncategorized").lower() == category.lower():
            metrics_in_category[name] = met_info["description"]

    if not metrics_in_category:
        return {"error": f"Category '{category}' not found or has no metrics."}

    return metrics_in_category
