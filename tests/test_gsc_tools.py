# SPDX-License-Identifier: Apache-2.0
"""Tests for Google Search Console MCP tools."""

import unittest
from unittest.mock import MagicMock, patch
from ga4_mcp.tools.gsc import list_search_sites, get_search_analytics, get_sitemaps, inspect_url


class TestGSCTools(unittest.TestCase):

    @patch("ga4_mcp.tools.gsc.client_pool.get_gsc_service")
    def test_list_search_sites(self, mock_get_svc):
        mock_svc = MagicMock()
        mock_svc.sites().list().execute.return_value = {
            "siteEntry": [
                {"siteUrl": "sc-domain:builditwithai.xyz", "permissionLevel": "siteOwner"},
                {"siteUrl": "https://surendranb.com/", "permissionLevel": "siteFullUser"}
            ]
        }
        mock_get_svc.return_value = mock_svc

        res = list_search_sites()
        self.assertEqual(res["total_sites"], 2)
        self.assertEqual(res["sites"][0]["siteUrl"], "sc-domain:builditwithai.xyz")

    @patch("ga4_mcp.tools.gsc.client_pool.get_gsc_service")
    def test_get_search_analytics(self, mock_get_svc):
        mock_svc = MagicMock()
        mock_svc.searchanalytics().query().execute.return_value = {
            "rows": [
                {"keys": ["mcp server"], "clicks": 150, "impressions": 3000, "ctr": 0.05, "position": 2.4},
                {"keys": ["ga4 analytics mcp"], "clicks": 80, "impressions": 1000, "ctr": 0.08, "position": 1.2}
            ]
        }
        mock_get_svc.return_value = mock_svc

        res = get_search_analytics(site_url="sc-domain:builditwithai.xyz", dimensions=["query"])
        self.assertEqual(res["total_rows"], 2)
        self.assertEqual(res["totals"]["clicks"], 230)
        self.assertEqual(res["totals"]["impressions"], 4000)

    @patch("ga4_mcp.tools.gsc.client_pool.get_gsc_service")
    def test_get_sitemaps(self, mock_get_svc):
        mock_svc = MagicMock()
        mock_svc.sitemaps().list().execute.return_value = {
            "sitemap": [
                {"path": "https://surendranb.com/sitemap.xml", "lastDownloaded": "2026-08-30", "errors": 0}
            ]
        }
        mock_get_svc.return_value = mock_svc

        res = get_sitemaps(site_url="https://surendranb.com/")
        self.assertEqual(len(res["sitemaps"]), 1)
        self.assertEqual(res["sitemaps"][0]["path"], "https://surendranb.com/sitemap.xml")


if __name__ == "__main__":
    unittest.main()
