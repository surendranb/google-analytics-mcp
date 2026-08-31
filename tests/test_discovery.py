# SPDX-License-Identifier: Apache-2.0
"""Tests for auto-discovery logic with mocked Admin API responses.
Run: python tests/test_discovery.py"""

import os
import sys
from unittest.mock import MagicMock, patch

from ga4_mcp.discovery import DiscoveredProperty, discover_properties_for_source, discover_all_properties
from ga4_mcp.sites import SiteRegistry


class _MockPropertySummary:
    def __init__(self, prop_path, display_name):
        self.property = prop_path
        self.display_name = display_name


class _MockAccountSummary:
    def __init__(self, account_path, display_name, prop_summaries):
        self.account = account_path
        self.display_name = display_name
        self.property_summaries = prop_summaries


def _run():
    failures = []

    mock_summaries = [
        _MockAccountSummary(
            "accounts/100",
            "Acme Holdings",
            [
                _MockPropertySummary("properties/111", "Acme Production Web"),
                _MockPropertySummary("properties/222", "Acme Mobile App"),
            ]
        ),
        _MockAccountSummary(
            "accounts/200",
            "Globex Corp",
            [
                _MockPropertySummary("properties/333", "Globex Store"),
            ]
        ),
    ]

    # Mock get_admin_client to return our test summaries
    mock_admin_client = MagicMock()
    mock_admin_client.list_account_summaries.return_value = mock_summaries

    with patch("ga4_mcp.discovery.client_pool.get_admin_client", return_value=mock_admin_client):
        discovered = discover_properties_for_source(credentials_path=None, source_type="adc")

        if len(discovered) != 3:
            failures.append(f"Expected 3 discovered properties, got {len(discovered)}")

        prop_ids = {p.property_id for p in discovered}
        if prop_ids != {"111", "222", "333"}:
            failures.append(f"Discovered property IDs mismatch: {prop_ids}")

        p1 = next(p for p in discovered if p.property_id == "111")
        if p1.display_name != "Acme Production Web" or p1.account_name != "Acme Holdings":
            failures.append(f"Property metadata incorrect on p1: {p1}")

        # Test integration with SiteRegistry
        with patch("ga4_mcp.sites.discover_all_properties", return_value=discovered):
            # Clean env
            os.environ.pop("GA4_SITES", None)
            os.environ.pop("GA4_PROPERTY_ID", None)

            reg = SiteRegistry()
            reg.initialize(force_refresh=True)

            all_listed = reg.list_all()
            if len(all_listed) != 3:
                failures.append(f"Expected 3 properties in SiteRegistry, got {len(all_listed)}")

            # Resolve by display name
            resolved_acme, err = reg.resolve("Acme Mobile")
            if err or not resolved_acme or resolved_acme.property_id != "222":
                failures.append(f"Failed to resolve 'Acme Mobile': {resolved_acme}, err: {err}")

            resolved_globex, err = reg.resolve("Globex Store")
            if err or not resolved_globex or resolved_globex.property_id != "333":
                failures.append(f"Failed to resolve 'Globex Store': {resolved_globex}, err: {err}")

    if failures:
        print("FAIL:")
        for f in failures:
            print("  -", f)
        sys.exit(1)

    print("PASS: Admin API auto-discovery correctly parses account summaries and indexes into SiteRegistry")


if __name__ == "__main__":
    _run()
