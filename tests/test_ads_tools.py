# SPDX-License-Identifier: Apache-2.0
"""Tests for Google Ads MCP tools."""

import json
import unittest
from unittest.mock import MagicMock, patch
from ga4_mcp.tools.ads import list_ad_accounts, get_campaign_performance, get_search_terms


class TestGoogleAdsTools(unittest.TestCase):

    @patch("ga4_mcp.tools.ads._get_google_ads_auth")
    @patch("urllib.request.urlopen")
    def test_list_ad_accounts(self, mock_urlopen, mock_get_auth):
        mock_get_auth.return_value = ("fake_token", "fake_dev_token")
        
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "resourceNames": ["customers/1234567890", "customers/9876543210"]
        }).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        res = list_ad_accounts()
        self.assertEqual(res["total_accounts"], 2)
        self.assertEqual(res["accounts"][0], "123-456-7890")
        self.assertEqual(res["accounts"][1], "987-654-3210")

    @patch("ga4_mcp.tools.ads._get_google_ads_auth")
    @patch("urllib.request.urlopen")
    def test_get_campaign_performance(self, mock_urlopen, mock_get_auth):
        mock_get_auth.return_value = ("fake_token", "fake_dev_token")

        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "results": [
                {
                    "campaign": {"id": "111", "name": "Brand Search", "status": "ENABLED"},
                    "metrics": {
                        "impressions": "5000",
                        "clicks": "250",
                        "costMicros": "125000000",  # $125.00
                        "conversions": 25.0,
                        "conversionsValue": 500.0   # $500.00 -> 400% ROAS
                    }
                }
            ]
        }).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        res = get_campaign_performance(customer_id="123-456-7890")
        self.assertEqual(res["totals"]["total_spend"], 125.0)
        self.assertEqual(res["totals"]["total_clicks"], 250)
        self.assertEqual(res["totals"]["overall_roas_pct"], 400.0)
        self.assertEqual(res["campaigns"][0]["name"], "Brand Search")


if __name__ == "__main__":
    unittest.main()
