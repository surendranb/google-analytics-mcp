# SPDX-License-Identifier: Apache-2.0
"""The three shared error boundaries: field admission (unservable + duplicate
fields stop locally), transient upstream (retry-once directive), and setup-class
classification (401/403/missing-property get the guided brief, never a library
string or a raw local path). Run: uv run --with pytest python -m pytest tests"""

import os
import asyncio

os.environ.setdefault("GA4_MCP_INTERNAL", "1")
os.environ.setdefault("DISABLE_TELEMETRY", "1")

import ga4_mcp.coordinator as coord
import ga4_mcp.tools.metadata as metadata
import ga4_mcp.tools.reporting as reporting

_SCHEMA = {
    "dimensions": {"date": {}, "sessionDefaultChannelGroup": {}},
    "metrics": {"sessions": {}, "totalUsers": {}},
}


def _no_upstream():
    def _boom():
        raise AssertionError("upstream API was called — the request should have failed locally")
    return _boom


def _run(coro):
    return asyncio.run(coro)


def _reset_schema():
    reporting.PROPERTY_SCHEMA = _SCHEMA
    metadata.UNAVAILABLE_FIELDS.clear()


def test_duplicate_fields_dedupe_and_skip_upstream_on_local_error():
    """A repeated field used to reach GA4 and come back as a 400."""
    _reset_schema()
    coord.get_data_client = _no_upstream()
    result = _run(reporting.get_ga4_data(dimensions=["date", "date"], metrics=["sessions", "sessions", "nopeMetric"]))
    assert "nopeMetric" in result["error"]
    # Dedupe ran before validation: the error names the one bad field, not duplicates.
    assert "duplicate" not in result["error"].lower()


def test_unservable_search_console_field_fails_locally_naming_replacement():
    """A Search Console metric this property cannot serve is refused before any
    request; the error names both the field and where the number lives."""
    _reset_schema()
    metadata.UNAVAILABLE_FIELDS["organicGoogleSearchClicks"] = "clicks"
    coord.get_data_client = _no_upstream()
    result = _run(reporting.get_ga4_data(dimensions=["date"], metrics=["organicGoogleSearchClicks"]))
    err = result["error"]
    assert "'organicGoogleSearchClicks' cannot be read from this property" in err
    assert "'clicks'" in err
    assert "Search Console API" in err
    assert "none was sent" in err


def test_gsc_probe_drops_family_only_on_definitive_link_answer():
    """Drop on GA4's own 'requires an active link' answer; keep the names on any
    inconclusive failure (5xx, wrong pairing) so a working property loses nothing."""
    class _Linked:
        def run_report(self, request=None):
            return object()

    class _Unlinked:
        def run_report(self, request=None):
            raise Exception("400 Search Console fields require an active link to be used.")

    class _Flaky:
        def run_report(self, request=None):
            raise Exception("503 Getting metadata from plugin failed")

    names = list(metadata.SEARCH_CONSOLE_REPLACEMENTS)
    schema = {"dimensions": {}, "metrics": {n: {} for n in names}}

    metadata.UNAVAILABLE_FIELDS.clear()
    metadata._drop_unservable_search_console(dict(schema, metrics=dict(schema["metrics"])), _Linked(), "1")
    assert metadata.UNAVAILABLE_FIELDS == {}

    kept = dict(schema["metrics"])
    metadata._drop_unservable_search_console({"dimensions": {}, "metrics": kept}, _Flaky(), "1")
    assert set(kept) == set(names) and metadata.UNAVAILABLE_FIELDS == {}

    dropped = dict(schema["metrics"])
    metadata._drop_unservable_search_console({"dimensions": {}, "metrics": dropped}, _Unlinked(), "1")
    assert dropped == {}
    assert metadata.UNAVAILABLE_FIELDS["organicGoogleSearchAveragePosition"] == "position"


def test_transient_failure_returns_retry_once_directive():
    class _Blip:
        def run_report(self, request=None):
            raise Exception("503 The service is currently unavailable.")

    _reset_schema()
    coord.get_data_client = lambda: _Blip()
    result = _run(reporting.get_ga4_data(dimensions=["date"], metrics=["sessions"]))
    err = result["error"]
    assert "Transient upstream failure (429/503/504)" in err
    assert "Retry this exact call ONCE" in err
    assert "do not change fields" in err.lower() or "Do not change fields" in err


def test_transient_markers_do_not_swallow_query_errors():
    assert reporting._is_transient("503 upstream blip")
    assert reporting._is_transient("429 RESOURCE_EXHAUSTED")
    assert reporting._is_transient("Stream removed recvmsg:No route to host")
    assert not reporting._is_transient("400 Please remove organicGoogleSearchClicks")
    assert not reporting._is_transient("400 Found duplicate dimensions/metrics")


def test_setup_classifier_routes_401_403_and_generic():
    cat, version, brief = coord.classify_setup_failure(
        Exception("401 Request had invalid authentication credentials. ACCESS_TOKEN_EXPIRED"), "123", "")
    assert cat == "ADCExpired" and version == "ga4-auth-v1"
    assert "Re-authenticate" in brief

    cat, version, brief = coord.classify_setup_failure(Exception("403 PermissionDenied"), "123", "")
    assert cat == "IAMError" and version == "ga4-iam-v1"
    assert "Viewer role" in brief

    cat, _version, brief = coord.classify_setup_failure(Exception("400 malformed request"), "123", "")
    assert cat == "InitError"
    assert "[SETUP BLOCKED]" in brief


def test_setup_briefs_carry_no_raw_local_paths():
    creds = "/Users/someone/.config/gcloud/sa-keys/ga4-mcp-server.json"
    property_brief = coord.property_id_brief()
    _cat, _v, failure_brief = coord.classify_setup_failure(Exception("500 boom"), "123", creds)
    for text in (property_brief, failure_brief):
        assert "[ENVIRONMENT_FIXABLE: STOP & ASK HUMAN]" in text
        assert "/Users/someone" not in text
        assert creds not in text


def test_missing_property_tool_error_is_a_brief_not_a_bare_string():
    os.environ.pop("GA4_PROPERTY_ID", None)
    coord.SERVER_INIT_ERROR = None
    result = metadata.list_properties()
    assert "[SETUP BLOCKED]" in result["error"]
    assert "GA4_PROPERTY_ID" in result["error"]
    assert coord._classify_result(result)[1] == coord.SERVER_INIT_ERROR_CATEGORY


def _error_from(exc, dimensions=("date",), metrics=("sessions",)):
    class _Raises:
        def run_report(self, request=None):
            raise exc

    _reset_schema()
    coord.get_data_client = lambda: _Raises()
    return _run(reporting.get_ga4_data(dimensions=list(dimensions), metrics=list(metrics)))["error"]


def test_transient_status_beats_setup_classifier_on_shared_text():
    """2.12.0 sent these 503s to the IAM/ADC briefs because their text carried
    'expired'/'permission' — a recoverable blip reported as a setup blocker."""
    for text in ("503 Deadline Exceeded: upstream channel expired before response",
                 "503 failed to connect: metadata permission plugin unavailable"):
        err = _error_from(Exception(text))
        assert "Retry this exact call ONCE" in err, text
        assert "[SETUP BLOCKED]" not in err, text
        assert "Re-authenticate" not in err, text


def test_genuine_401_still_gets_adc_brief():
    err = _error_from(Exception("401 Request had invalid authentication credentials. ACCESS_TOKEN_EXPIRED"))
    assert "[SETUP BLOCKED]" in err
    assert "Re-authenticate" in err
    assert "Retry this exact call ONCE" not in err


def test_genuine_403_still_gets_iam_brief():
    err = _error_from(Exception("403 PermissionDenied: caller does not have permission"))
    assert "[SETUP BLOCKED]" in err
    assert "Viewer role" in err
    assert "Retry this exact call ONCE" not in err


def test_unrecognised_400_gets_field_shape_brief_not_raw_text():
    err = _error_from(Exception("400 Field fooBar is not a valid dimension for this property."))
    assert not err.startswith("Error fetching GA4 data:")
    assert "Error fetching GA4 data:" not in err
    assert "GA4 rejected this request" in err
    assert "search_schema('<keyword>')" in err
    assert "search_skills('compatible-combinations')" in err
    assert "fooBar" in err


def test_invalid_dimension_400_still_routes_to_invalid_dimension_brief():
    """Local admission pre-empts the catch-all: a bad name never reaches it."""
    _reset_schema()
    coord.get_data_client = _no_upstream()
    err = _run(reporting.get_ga4_data(dimensions=["nopeDim"], metrics=["sessions"]))["error"]
    assert "Invalid dimension: 'nopeDim'" in err
    assert "GA4 rejected this request" not in err
    assert "Error fetching GA4 data:" not in err
