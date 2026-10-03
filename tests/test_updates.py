# SPDX-License-Identifier: Apache-2.0

"""Unit tests for check_for_updates tool, get_upgrade_nudge, and cache throttling."""

import json
import time
from unittest.mock import MagicMock, patch
from io import BytesIO

from ga4_mcp import coordinator
from ga4_mcp.updates import (
    _parse_version,
    check_server_update,
    get_upgrade_nudge,
    _FLEET_CACHE_FILE,
)


def test_parse_version():
    assert _parse_version("2.11.5") == (2, 11, 5)
    assert _parse_version("v2.11.5") == (2, 11, 5)
    assert _parse_version("2.12.0") > _parse_version("2.11.5")
    assert _parse_version("2.11.5") > _parse_version("2.11.4")
    assert _parse_version("2.11.10") > _parse_version("2.11.5")
    assert _parse_version("unknown") == (0,)
    assert _parse_version("") == (0,)


def test_check_server_update_update_available(tmp_path):
    mock_pypi_data = json.dumps({"info": {"version": "2.12.0"}}).encode("utf-8")
    mock_resp = MagicMock()
    mock_resp.read.return_value = mock_pypi_data
    mock_resp.__enter__.return_value = mock_resp

    test_cache = tmp_path / "fleet_updates.json"
    with patch("ga4_mcp.updates._FLEET_CACHE_FILE", test_cache), \
         patch("urllib.request.urlopen", return_value=mock_resp):
        res = check_server_update("google-analytics-mcp", "2.11.5", force_check=True)

        assert res["server"] == "google-analytics-mcp"
        assert res["current_version"] == "2.11.5"
        assert res["latest_version"] == "2.12.0"
        assert res["update_available"] is True
        assert res["upgrade_command"] == "uvx --refresh google-analytics-mcp"
        assert "Inform the user to run 'uvx --refresh google-analytics-mcp' to update." in res["message"]
        assert "Do NOT attempt to run this command yourself in this session." in res["message"]


def test_check_server_update_up_to_date(tmp_path):
    mock_pypi_data = json.dumps({"info": {"version": "2.11.5"}}).encode("utf-8")
    mock_resp = MagicMock()
    mock_resp.read.return_value = mock_pypi_data
    mock_resp.__enter__.return_value = mock_resp

    test_cache = tmp_path / "fleet_updates.json"
    with patch("ga4_mcp.updates._FLEET_CACHE_FILE", test_cache), \
         patch("urllib.request.urlopen", return_value=mock_resp):
        res = check_server_update("google-analytics-mcp", "2.11.5", force_check=True)

        assert res["update_available"] is False
        assert res["upgrade_command"] is None
        assert res["message"] == "google-analytics-mcp is up to date (v2.11.5)."


def test_get_upgrade_nudge_throttle(tmp_path):
    test_cache = tmp_path / "fleet_updates.json"
    test_cache.write_text(json.dumps({
        "google-analytics-mcp": {
            "latest_version": "2.12.0",
            "last_checked": time.time(),
            "last_nudged": 0,
        }
    }))

    with patch("ga4_mcp.updates._FLEET_CACHE_FILE", test_cache):
        # First call: should produce nudge
        nudge1 = get_upgrade_nudge("google-analytics-mcp", "2.11.5")
        assert "[NOTICE: An updated version of google-analytics-mcp is available (v2.12.0, current: v2.11.5)." in nudge1
        assert "Inform the user to run 'uvx --refresh google-analytics-mcp' to update. Do NOT attempt to run this command yourself in this session." in nudge1

        # Second call immediately after: should be throttled
        nudge2 = get_upgrade_nudge("google-analytics-mcp", "2.11.5")
        assert nudge2 == ""

        # Bump latest_version to 2.13.0: should re-nudge despite throttle
        cache = json.loads(test_cache.read_text())
        cache["google-analytics-mcp"]["latest_version"] = "2.13.0"
        test_cache.write_text(json.dumps(cache))

        nudge3 = get_upgrade_nudge("google-analytics-mcp", "2.11.5")
        assert "v2.13.0" in nudge3


def test_coordinator_check_for_updates_tool():
    res = coordinator.check_for_updates()
    assert isinstance(res, dict)
    assert res["server"] == "google-analytics-mcp"
    assert "current_version" in res
    assert "latest_version" in res
    assert "update_available" in res
    assert "message" in res


def test_telemetry_tool_upgrade_notice_attachment():
    @coordinator.mcp.tool(name="_test_dummy_dict_tool")
    def _dummy_dict_tool():
        return {"data": "test_data"}

    @coordinator.mcp.tool(name="_test_dummy_str_tool")
    def _dummy_str_tool():
        return "test_string"

    fake_nudge = "\n\n[NOTICE: An updated version is available]"
    with patch.object(coordinator, "SERVER_INIT_ERROR", None), \
         patch("ga4_mcp.coordinator.get_upgrade_nudge", return_value=fake_nudge):
        res_dict = _dummy_dict_tool()
        assert isinstance(res_dict, dict)
        assert res_dict.get("_upgrade_notice") == fake_nudge.strip()

        res_str = _dummy_str_tool()
        assert fake_nudge in res_str

