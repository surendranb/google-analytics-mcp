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

"""Tools for fetching and exploring GA4 property metadata."""

from google.analytics.data_v1beta import BetaAnalyticsDataClient
from ga4_mcp.coordinator import mcp

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

@mcp.tool()
def search_schema(keyword: str):
    """
    Searches for a keyword across all available dimensions and metrics for the property.
    Returns a short, ranked list of the most relevant fields. This is the most
    efficient way to discover dimensions and metrics for a specific query.

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


@mcp.tool()
def get_property_schema():
    """
    Returns the complete schema for the configured GA4 property, including all
    available dimensions and metrics (standard and custom). Warning: This can be
    a very large object (10k+ tokens). Use search_schema for most discovery tasks.
    """
    if not PROPERTY_SCHEMA:
        return {"error": "Schema not loaded. Please check server startup logs."}
    return PROPERTY_SCHEMA

@mcp.tool()
def list_dimension_categories():
    """
    List all available GA4 dimension categories based on the property's schema.
    This is a low-cost way to begin exploring the schema.
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

@mcp.tool()
def list_metric_categories():
    """
    List all available GA4 metric categories based on the property's schema.
    This is a low-cost way to begin exploring the schema.
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

@mcp.tool()
def get_dimensions_by_category(category: str):
    """
    Get all dimensions in a specific category with their descriptions.
    
    Args:
        category: The category name to retrieve dimensions for.
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

@mcp.tool()
def get_metrics_by_category(category: str):
    """
    Get all metrics in a specific category with their descriptions.
    
    Args:
        category: The category name to retrieve metrics for.
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