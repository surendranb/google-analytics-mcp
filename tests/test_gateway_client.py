# SPDX-License-Identifier: Apache-2.0
"""Tests for Gateway client integration: token dispenser and property discovery.
Run: python tests/test_gateway_client.py"""

import os
import sys
import tempfile
from unittest.mock import MagicMock, patch

temp_dir = tempfile.mkdtemp()
os.environ["GA4_CONFIG_DIR"] = temp_dir

from ga4_mcp.auth_session import save_session, clear_session
from ga4_mcp.client_pool import client_pool
from ga4_mcp.sites import SiteRegistry
from ga4_mcp.discovery import DiscoveredProperty


def _run():
    failures = []

    # 1. Test Gateway Credential Fetch
    save_session(token="ga4_live_mocktoken123", email="suren@atlan.com", gateway_url="https://mock-gw.builditwithai.xyz")

    mock_resp_data = {"access_token": "ya29.mock_google_access_token_xyz", "expires_in": 3600}

    with patch("ga4_mcp.client_pool.ClientPool._fetch_gateway_credentials") as mock_fetch:
        mock_creds = MagicMock()
        mock_creds.token = "ya29.mock_google_access_token_xyz"
        mock_fetch.return_value = mock_creds

        # Retrieve client with gateway credentials
        client = client_pool.get_data_client("gateway://session")
        if not client:
            failures.append("Failed to create BetaAnalyticsDataClient with gateway credentials")

    # 2. Test Discovery with Gateway Session
    mock_discovered = [
        DiscoveredProperty(
            property_id="987654321",
            display_name="Atlan Production Analytics",
            account_id="55555",
            account_name="Atlan Inc",
            credentials_source="gateway://session",
            source_type="gateway"
        )
    ]

    with patch("ga4_mcp.sites.discover_all_properties", return_value=mock_discovered):
        os.environ.pop("GA4_SITES", None)
        os.environ.pop("GA4_PROPERTY_ID", None)

        registry = SiteRegistry()
        registry.initialize(force_refresh=True)

        props = registry.list_all()
        if len(props) != 1:
            failures.append(f"Expected 1 property in registry, got {len(props)}")

        prop, err = registry.resolve("Atlan Production")
        if err or not prop or prop.property_id != "987654321":
            failures.append(f"Failed to resolve property from gateway discovery: {prop}, err: {err}")

        if prop.credentials_path != "gateway://session":
            failures.append(f"Expected credentials_path 'gateway://session', got {prop.credentials_path}")


    if failures:
        print("FAIL:")
        for f in failures:
            print("  -", f)
        sys.exit(1)

    print("PASS: Gateway client token resolution and property indexing verified successfully")


if __name__ == "__main__":
    _run()
