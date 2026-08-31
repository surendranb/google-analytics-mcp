# SPDX-License-Identifier: Apache-2.0
"""End-to-end native MCP protocol test for multi-site tools:
- list_properties
- search_schema across properties
- get_ga4_data with property routing
Run: python tests/test_multisite_mcp.py"""

import asyncio
import os
import sys
import json
from unittest.mock import MagicMock, patch

os.environ.setdefault("GA4_MCP_INTERNAL", "1")
os.environ.setdefault("DISABLE_TELEMETRY", "1")

# Configure 2 test sites
sites_json = json.dumps({
    "default_site": "blog",
    "sites": {
        "blog": {
            "name": "Engineering Blog",
            "property_id": "111111",
            "credentials": "/fake/path/blog.json"
        },
        "store": {
            "name": "Merch Store",
            "property_id": "222222",
            "credentials": "/fake/path/store.json"
        }
    }
})

import tempfile
os.environ["GA4_CONFIG_DIR"] = tempfile.mkdtemp()
os.environ.pop("GA4_PROPERTY_ID", None)
os.environ.pop("GOOGLE_APPLICATION_CREDENTIALS", None)
os.environ["GA4_SITES"] = sites_json





import ga4_mcp.coordinator as coord
import ga4_mcp.server
from ga4_mcp.sites import registry
from ga4_mcp.schema_cache import schema_cache
from mcp.client.client import Client
from mcp.types import Implementation


# Pre-populate schemas
schema_blog = {
    "dimensions": {
        "date": {"ui_name": "Date", "description": "Date of event", "category": "Time"},
        "customEvent:author": {"ui_name": "Author", "description": "Author name", "category": "Custom"},
    },
    "metrics": {
        "totalUsers": {"ui_name": "Total Users", "description": "Users count", "category": "User", "type": "TYPE_INTEGER"},
        "sessions": {"ui_name": "Sessions", "description": "Session count", "category": "Session", "type": "TYPE_INTEGER"},
    }
}

schema_store = {
    "dimensions": {
        "date": {"ui_name": "Date", "description": "Date of event", "category": "Time"},
        "customEvent:sku": {"ui_name": "SKU", "description": "Product SKU", "category": "Custom"},
    },
    "metrics": {
        "totalUsers": {"ui_name": "Total Users", "description": "Users count", "category": "User", "type": "TYPE_INTEGER"},
        "ecommercePurchases": {"ui_name": "Purchases", "description": "Purchase count", "category": "Ecommerce", "type": "TYPE_INTEGER"},
    }
}


class _Val:
    def __init__(self, val):
        self.value = str(val)


class _Row:
    def __init__(self, dims, mets):
        self.dimension_values = [_Val(d) for d in dims]
        self.metric_values = [_Val(m) for m in mets]


class _Header:
    def __init__(self, name):
        self.name = str(name)


class _MockReportResponse:
    def __init__(self, dims, mets, rows, totals=None):
        self.dimension_headers = [_Header(d) for d in dims]
        self.metric_headers = [_Header(m) for m in mets]
        self.rows = [_Row(d, m) for d, m in rows]
        self.totals = [_Row([], t) for t in totals] if totals else []
        self.row_count = len(self.rows)



async def main():
    failures = []
    coord.SERVER_INIT_ERROR = None
    coord.SERVER_INIT_BRIEF_VERSION = None
    registry.initialize(force_refresh=True)

    schema_cache.set_schema("111111", schema_blog, credentials_path="/fake/path/blog.json")
    schema_cache.set_schema("222222", schema_store, credentials_path="/fake/path/store.json")


    # Mock Data client run_report
    mock_report_res = _MockReportResponse(["date"], ["totalUsers"], [["2026-08-30", "500"]], totals=[["500"]])
    mock_data_client = MagicMock()
    mock_data_client.run_report.return_value = mock_report_res

    async with Client(
        coord.mcp,
        client_info=Implementation(name="test-harness", version="1.0.0"),
        mode="legacy"
    ) as client:
        # 1. Test list_properties tool
        res_list = await client.call_tool("list_properties", {})
        list_json = json.loads(res_list.content[0].text)
        props = list_json.get("properties", [])
        if len(props) != 2:
            failures.append(f"Expected 2 properties in list_properties, got {len(props)}")

        # 2. Test search_schema for blog property
        res_search_blog = await client.call_tool("search_schema", {"keyword": "author", "property": "blog"})
        search_blog_json = json.loads(res_search_blog.content[0].text)
        if "DIMENSION: customEvent:author" not in search_blog_json.get("top_results", {}):
            failures.append(f"search_schema blog author failed: {search_blog_json}")

        # 3. Test search_schema for store property
        res_search_store = await client.call_tool("search_schema", {"keyword": "sku", "property": "store"})
        search_store_json = json.loads(res_search_store.content[0].text)
        if "DIMENSION: customEvent:sku" not in search_store_json.get("top_results", {}):
            failures.append(f"search_schema store sku failed: {search_store_json}")

        # 4. Test get_ga4_data routed to blog property
        with patch("ga4_mcp.tools.reporting.client_pool.get_data_client", return_value=mock_data_client):
            res_data_blog = await client.call_tool("get_ga4_data", {
                "property": "blog",
                "dimensions": ["date"],
                "metrics": ["totalUsers"],
                "date_range_start": "yesterday",
                "date_range_end": "yesterday"
            })
            data_blog_json = json.loads(res_data_blog.content[0].text)


            if "data" not in data_blog_json or len(data_blog_json["data"]) != 1:
                failures.append(f"get_ga4_data blog failed: {data_blog_json}")

            # 5. Test get_ga4_data with property-specific custom dimension
            res_data_custom = await client.call_tool("get_ga4_data", {
                "property": "blog",
                "dimensions": ["date", "customEvent:author"],
                "metrics": ["totalUsers"]
            })
            data_custom_json = json.loads(res_data_custom.content[0].text)
            if "data" not in data_custom_json:
                failures.append(f"get_ga4_data customEvent:author failed: {data_custom_json}")

            # 6. Test schema validation error when passing blog custom dimension to store property
            res_data_mismatch = await client.call_tool("get_ga4_data", {
                "property": "store",
                "dimensions": ["date", "customEvent:author"],
                "metrics": ["totalUsers"]
            })
            data_mismatch_json = json.loads(res_data_mismatch.content[0].text)
            if "error" not in data_mismatch_json or "Invalid dimension: 'customEvent:author'" not in data_mismatch_json["error"]:
                failures.append(f"Expected schema mismatch error for store property, got: {data_mismatch_json}")

    if failures:
        print("FAIL:")
        for f in failures:
            print("  -", f)
        sys.exit(1)

    print("PASS: End-to-end MCP protocol multi-site tool execution verified successfully")


if __name__ == "__main__":
    asyncio.run(main())
