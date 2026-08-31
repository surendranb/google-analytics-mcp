# SPDX-License-Identifier: Apache-2.0
"""Tests for multi-property schema isolation: ensures custom dimensions and metrics
do not leak across different GA4 properties.
Run: python tests/test_schema_isolation.py"""

import os
import sys
import json

from ga4_mcp.sites import registry, PropertyInfo
from ga4_mcp.schema_cache import schema_cache
from ga4_mcp.tools.metadata import search_schema, get_property_schema


def _run():
    failures = []

    # Configure 2 distinct properties
    sites_json = json.dumps({
        "default_site": "blog",
        "sites": {
            "blog": {
                "name": "Tech Blog",
                "property_id": "1001",
            },
            "store": {
                "name": "E-Commerce Shop",
                "property_id": "2002",
            }
        }
    })

    os.environ["GA4_SITES"] = sites_json
    registry.initialize(force_refresh=True)
    schema_cache.clear()

    # Pre-populate distinct schemas for Property 1001 and Property 2002
    schema_blog = {
        "dimensions": {
            "date": {"ui_name": "Date", "description": "Date of event", "category": "Time"},
            "pagePath": {"ui_name": "Page Path", "description": "Path of page", "category": "Page"},
            "customEvent:blog_author": {"ui_name": "Author", "description": "Author of article", "category": "Custom"},
        },
        "metrics": {
            "totalUsers": {"ui_name": "Total Users", "description": "Number of users", "category": "User", "type": "TYPE_INTEGER"},
            "customMetric:read_time": {"ui_name": "Read Time", "description": "Time spent reading", "category": "Custom", "type": "TYPE_SECONDS"},
        }
    }

    schema_store = {
        "dimensions": {
            "date": {"ui_name": "Date", "description": "Date of event", "category": "Time"},
            "customEvent:product_sku": {"ui_name": "Product SKU", "description": "SKU of item", "category": "Custom"},
        },
        "metrics": {
            "totalUsers": {"ui_name": "Total Users", "description": "Number of users", "category": "User", "type": "TYPE_INTEGER"},
            "customMetric:cart_value": {"ui_name": "Cart Value", "description": "Value of cart", "category": "Custom", "type": "TYPE_CURRENCY"},
        }
    }

    schema_cache.set_schema("1001", schema_blog)
    schema_cache.set_schema("2002", schema_store)

    # 1. Search schema for "author" on blog property -> MUST find
    res_blog_author = search_schema(keyword="author", property="blog")
    top_blog = res_blog_author.get("top_results", {})
    if "DIMENSION: customEvent:blog_author" not in top_blog:
        failures.append(f"Expected customEvent:blog_author in blog schema search, got {res_blog_author}")

    # 2. Search schema for "author" on store property -> MUST NOT find
    res_store_author = search_schema(keyword="author", property="store")
    top_store = res_store_author.get("top_results", {})
    if "DIMENSION: customEvent:blog_author" in top_store:
        failures.append("customEvent:blog_author leaked into store property schema search!")

    # 3. Search schema for "sku" on store property -> MUST find
    res_store_sku = search_schema(keyword="sku", property="store")
    top_sku = res_store_sku.get("top_results", {})
    if "DIMENSION: customEvent:product_sku" not in top_sku:
        failures.append(f"Expected customEvent:product_sku in store schema search, got {res_store_sku}")

    # 4. Search schema for "sku" on blog property -> MUST NOT find
    res_blog_sku = search_schema(keyword="sku", property="blog")
    top_blog_sku = res_blog_sku.get("top_results", {})
    if "DIMENSION: customEvent:product_sku" in top_blog_sku:
        failures.append("customEvent:product_sku leaked into blog property schema search!")

    # 5. Full schema retrieval isolation
    full_blog = get_property_schema(property="blog")
    full_store = get_property_schema(property="store")

    if "customMetric:read_time" not in full_blog.get("metrics", {}):
        failures.append("customMetric:read_time missing from full blog schema")
    if "customMetric:cart_value" in full_blog.get("metrics", {}):
        failures.append("customMetric:cart_value leaked into blog schema")

    if "customMetric:cart_value" not in full_store.get("metrics", {}):
        failures.append("customMetric:cart_value missing from full store schema")
    if "customMetric:read_time" in full_store.get("metrics", {}):
        failures.append("customMetric:read_time leaked into store schema")

    if failures:
        print("FAIL:")
        for f in failures:
            print("  -", f)
        sys.exit(1)

    print("PASS: SchemaCache properly isolates custom dimensions and metrics across distinct properties")


if __name__ == "__main__":
    _run()
