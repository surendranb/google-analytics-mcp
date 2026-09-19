# SPDX-License-Identifier: Apache-2.0
"""Test filter repair with list shapes and exit reason telemetry tracking."""

import os
import sys

os.environ.setdefault("GA4_MCP_INTERNAL", "1")
os.environ.setdefault("DISABLE_TELEMETRY", "1")

from ga4_mcp.tools.reporting import _repair_filter_shape, _convert_keys_to_snake
from google.analytics.data_v1beta.types import FilterExpression, FilterExpressionList
import ga4_mcp.telemetry as telemetry


def test_repair_filter_shape_list():
    raw_list = [
        {"fieldName": "eventName", "stringFilter": {"value": "click", "matchType": "EXACT"}},
        {"fieldName": "pagePath", "stringFilter": {"value": "/blog", "matchType": "CONTAINS"}},
    ]
    converted = _convert_keys_to_snake(raw_list)
    repaired = _repair_filter_shape(converted)
    assert isinstance(repaired, list)
    assert len(repaired) == 2

    # Should safely construct FilterExpression
    exprs = [FilterExpression(f) if isinstance(f, dict) else f for f in repaired]
    fe = FilterExpression(and_group=FilterExpressionList(expressions=exprs))
    assert fe is not None


def test_telemetry_exit_reason():
    assert telemetry._EXIT_REASON in ("clean", "exception", "signal")
