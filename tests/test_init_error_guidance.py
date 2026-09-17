# SPDX-License-Identifier: Apache-2.0
"""Test InitError guidance, classification, and reinitialization brief formatting.
Run: python tests/test_init_error_guidance.py"""

import os
import sys

os.environ.setdefault("GA4_MCP_INTERNAL", "1")
os.environ.setdefault("DISABLE_TELEMETRY", "1")

import ga4_mcp.coordinator as coord


def test_guided_init_error_format():
    brief = coord.build_guided_init_error(
        "No Google credentials are configured — GOOGLE_APPLICATION_CREDENTIALS is unset.",
        ["Step 1: Point to credentials file.", "Step 2: Re-run."],
        anchor="credentials",
        topic="credentials",
        why="The server cannot authenticate.",
    )
    assert "[ENVIRONMENT_FIXABLE: STOP & ASK HUMAN]" in brief
    assert "[SETUP BLOCKED]" in brief
    assert "RETRYING WON'T HELP" in brief
    assert "(1) Step 1: Point to credentials file." in brief
    assert "(2) Step 2: Re-run." in brief
    assert "WHO CAN DO IT:" in brief


def test_classify_result_init_error():
    # Schema not loaded should classify as InitError, not APIError
    status, category = coord._classify_result({"error": "Schema not loaded. Please check server startup logs."})
    assert status == "error"
    assert category == "InitError"

    # Setup paused should classify as InitError
    status, category = coord._classify_result({"error": "Setup paused — no Property ID provided."})
    assert status == "error"
    assert category == "InitError"


def test_reinitialize_builds_guided_brief():
    # Test reinitialize with missing credentials
    os.environ.pop("GOOGLE_APPLICATION_CREDENTIALS", None)
    os.environ["GA4_PROPERTY_ID"] = "123456789"
    ok, cat, detail = coord.reinitialize()
    assert not ok
    assert cat == "credentials"
    assert coord.SERVER_INIT_ERROR_CATEGORY == "InitError"
    assert "[ENVIRONMENT_FIXABLE: STOP & ASK HUMAN]" in coord.SERVER_INIT_ERROR
    assert "GOOGLE_APPLICATION_CREDENTIALS is unset" in coord.SERVER_INIT_ERROR

    # Test reinitialize with missing property ID
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/tmp/dummy_creds.json"
    os.environ.pop("GA4_PROPERTY_ID", None)
    ok, cat, detail = coord.reinitialize()
    assert not ok
    assert cat == "property-id"
    assert coord.SERVER_INIT_ERROR_CATEGORY == "InitError"
    assert "[ENVIRONMENT_FIXABLE: STOP & ASK HUMAN]" in coord.SERVER_INIT_ERROR
    assert "GA4_PROPERTY_ID is unset" in coord.SERVER_INIT_ERROR


def main():
    test_guided_init_error_format()
    test_classify_result_init_error()
    test_reinitialize_builds_guided_brief()
    print("PASS: InitError decision brief formatting and classification verified.")


if __name__ == "__main__":
    main()
