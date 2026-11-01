# SPDX-License-Identifier: Apache-2.0
"""get_ga4_data's optional dimension_filter must accept an explicit null.

Its schema advertises "default": null, so a client may send that default back
as null. Schema and argument validation only: no GA4 call is made.
Run: python tests/test_optional_args_accept_null.py"""

import asyncio
import os

os.environ.setdefault("GA4_MCP_INTERNAL", "1")
os.environ.setdefault("DISABLE_TELEMETRY", "1")

import ga4_mcp.coordinator as coord  # noqa: E402
import ga4_mcp.server  # noqa: E402  registers metadata/reporting tools

from mcp.client.client import Client  # noqa: E402


async def _dimension_filter_schema():
    async with Client(coord.mcp, mode="legacy") as client:
        tools = (await client.list_tools()).tools
    tool = next(t for t in tools if t.name == "get_ga4_data")
    return tool.input_schema["properties"]["dimension_filter"]


def _validate(arguments):
    fn_metadata = coord.mcp._tool_manager.get_tool("get_ga4_data").fn_metadata
    return fn_metadata.arg_model.model_validate(fn_metadata.pre_parse_json(arguments))


def test_dimension_filter_accepts_null():
    schema = asyncio.run(_dimension_filter_schema())
    assert schema.get("default") is None
    types = {s.get("type") for s in schema.get("anyOf", [schema])}
    assert "null" in types, f"default is null but schema rejects null: {schema}"

    assert _validate({"dimension_filter": None}).dimension_filter is None
    # A filter sent as JSON text is still parsed into a dict.
    parsed = _validate({"dimension_filter": '{"filter": {"fieldName": "country"}}'})
    assert parsed.dimension_filter == {"filter": {"fieldName": "country"}}


if __name__ == "__main__":
    test_dimension_filter_accepts_null()
    print("PASS: get_ga4_data accepts dimension_filter=null")
