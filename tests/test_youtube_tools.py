# SPDX-License-Identifier: Apache-2.0
"""Tests for YouTube Analytics & Data MCP tools."""

import unittest
from unittest.mock import MagicMock, patch
from ga4_mcp.tools.youtube import list_youtube_channels, get_channel_overview, get_video_analytics, get_youtube_traffic_sources


class TestYouTubeTools(unittest.TestCase):

    @patch("ga4_mcp.tools.youtube.client_pool.get_youtube_service")
    def test_list_youtube_channels(self, mock_get_svc):
        mock_svc = MagicMock()
        mock_svc.channels().list().execute.return_value = {
            "items": [
                {
                    "id": "UC123456789",
                    "snippet": {"title": "Build With AI", "customUrl": "@buildwithai", "publishedAt": "2024-01-01"},
                    "statistics": {"subscriberCount": "1500", "viewCount": "95000", "videoCount": "42"}
                }
            ]
        }
        mock_get_svc.return_value = mock_svc

        res = list_youtube_channels()
        self.assertEqual(res["total_channels"], 1)
        self.assertEqual(res["channels"][0]["title"], "Build With AI")
        self.assertEqual(res["channels"][0]["subscribers"], 1500)

    @patch("ga4_mcp.tools.youtube.client_pool.get_youtube_analytics_service")
    def test_get_channel_overview(self, mock_get_analytics):
        mock_analytics = MagicMock()
        mock_analytics.reports().query().execute.return_value = {
            "columnHeaders": [
                {"name": "day"}, {"name": "views"}, {"name": "estimatedMinutesWatched"},
                {"name": "averageViewDuration"}, {"name": "subscribersGained"},
                {"name": "subscribersLost"}, {"name": "likes"}, {"name": "shares"}
            ],
            "rows": [
                ["2026-08-28", 1200, 3600.0, 180, 25, 2, 85, 12],
                ["2026-08-29", 1400, 4200.0, 180, 30, 3, 110, 18]
            ]
        }
        mock_get_analytics.return_value = mock_analytics

        res = get_channel_overview(channel_id="UC123456789")
        self.assertEqual(res["totals"]["views"], 2600)
        self.assertEqual(res["totals"]["watch_time_hours"], 130.0)
        self.assertEqual(res["totals"]["net_subscribers"], 50)

    @patch("ga4_mcp.tools.youtube.client_pool.get_youtube_analytics_service")
    def test_get_youtube_traffic_sources(self, mock_get_analytics):
        mock_analytics = MagicMock()
        mock_analytics.reports().query().execute.return_value = {
            "columnHeaders": [{"name": "insightTrafficSourceType"}, {"name": "views"}, {"name": "estimatedMinutesWatched"}],
            "rows": [
                ["YT_SEARCH", 1500, 4500.0],
                ["RELATED_VIDEO", 800, 2400.0],
                ["SHORTS", 500, 500.0]
            ]
        }
        mock_get_analytics.return_value = mock_analytics

        res = get_youtube_traffic_sources(channel_id="UC123456789")
        self.assertEqual(res["total_views"], 2800)
        self.assertEqual(res["sources"][0]["source_name"], "YouTube Search")
        self.assertEqual(res["sources"][0]["share_pct"], 53.6)


if __name__ == "__main__":
    unittest.main()
