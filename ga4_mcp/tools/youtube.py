# SPDX-License-Identifier: Apache-2.0
"""YouTube Analytics and Data API tools for AI agents.
Provides channel discovery, audience overview, video performance tracking, and traffic source insights.
"""

import datetime
from typing import Optional, List, Dict, Any
from mcp.types import ToolAnnotations
from mcp.server.mcpserver import Context
from ga4_mcp.coordinator import mcp
from ga4_mcp.client_pool import client_pool

_READ_ONLY = ToolAnnotations(read_only_hint=True, idempotent_hint=True, open_world_hint=False)


@mcp.tool(annotations=_READ_ONLY)
def list_youtube_channels(ctx: Context = None) -> dict:
    """
    List all YouTube channels owned or managed by the authenticated Google account.

    Returns: {"channels": [{"channel_id": "...", "title": "...", "subscribers": 1200, "videos": 45, "views": 85000}, ...]}
    """
    try:
        service = client_pool.get_youtube_service()
        response = service.channels().list(
            mine=True,
            part="snippet,statistics,contentDetails"
        ).execute()

        items = response.get("items", [])
        channels = []
        for ch in items:
            snip = ch.get("snippet", {})
            stats = ch.get("statistics", {})
            channels.append({
                "channel_id": ch.get("id"),
                "title": snip.get("title"),
                "custom_url": snip.get("customUrl"),
                "subscribers": int(stats.get("subscriberCount", 0)),
                "total_views": int(stats.get("viewCount", 0)),
                "video_count": int(stats.get("videoCount", 0)),
                "published_at": snip.get("publishedAt")
            })

        return {
            "channels": channels,
            "total_channels": len(channels),
            "how_to_query": "Pass channel_id to get_channel_overview, get_video_analytics, or get_youtube_traffic_sources."
        }
    except Exception as e:
        return {"error": f"Failed to list YouTube channels: {e}"}


@mcp.tool(annotations=_READ_ONLY)
def get_channel_overview(
    channel_id: str = None,
    start_date: str = None,
    end_date: str = None,
    ctx: Context = None
) -> dict:
    """
    Retrieve YouTube channel performance overview: total views, watch time hours, subscriber gains, and average duration.

    Args:
        channel_id: YouTube Channel ID (e.g. 'UC...'). If omitted, queries the primary authenticated channel ('MINE').
        start_date: Start date (YYYY-MM-DD). Default: 28 days ago.
        end_date: End date (YYYY-MM-DD). Default: 3 days ago.
    """
    try:
        yt_analytics = client_pool.get_youtube_analytics_service()

        today = datetime.date.today()
        if not end_date:
            end_date = (today - datetime.timedelta(days=3)).strftime("%Y-%m-%d")
        if not start_date:
            start_date = (today - datetime.timedelta(days=31)).strftime("%Y-%m-%d")

        channel_filter = f"channel=={channel_id}" if channel_id else "channel==MINE"

        response = yt_analytics.reports().query(
            ids=channel_filter,
            startDate=start_date,
            endDate=end_date,
            metrics="views,estimatedMinutesWatched,averageViewDuration,subscribersGained,subscribersLost,likes,shares",
            dimensions="day",
            sort="day"
        ).execute()

        headers = [h["name"] for h in response.get("columnHeaders", [])]
        rows = response.get("rows", [])

        # Calculate period totals
        total_views = 0
        total_mins = 0.0
        total_gained = 0
        total_lost = 0
        total_likes = 0
        total_shares = 0

        views_idx = headers.index("views") if "views" in headers else -1
        mins_idx = headers.index("estimatedMinutesWatched") if "estimatedMinutesWatched" in headers else -1
        gained_idx = headers.index("subscribersGained") if "subscribersGained" in headers else -1
        lost_idx = headers.index("subscribersLost") if "subscribersLost" in headers else -1
        likes_idx = headers.index("likes") if "likes" in headers else -1
        shares_idx = headers.index("shares") if "shares" in headers else -1

        for r in rows:
            if views_idx >= 0:
                total_views += r[views_idx]
            if mins_idx >= 0:
                total_mins += r[mins_idx]
            if gained_idx >= 0:
                total_gained += r[gained_idx]
            if lost_idx >= 0:
                total_lost += r[lost_idx]
            if likes_idx >= 0:
                total_likes += r[likes_idx]
            if shares_idx >= 0:
                total_shares += r[shares_idx]

        watch_time_hours = round(total_mins / 60.0, 1)
        net_subscribers = total_gained - total_lost
        avg_view_duration_seconds = round(total_mins * 60.0 / total_views, 1) if total_views > 0 else 0.0

        return {
            "channel": channel_id or "MINE",
            "start_date": start_date,
            "end_date": end_date,
            "totals": {
                "views": total_views,
                "watch_time_hours": watch_time_hours,
                "net_subscribers": net_subscribers,
                "subscribers_gained": total_gained,
                "subscribers_lost": total_lost,
                "likes": total_likes,
                "shares": total_shares,
                "average_view_duration_seconds": avg_view_duration_seconds
            },
            "daily_trend": [dict(zip(headers, r)) for r in rows]
        }
    except Exception as e:
        return {"error": f"Failed to fetch YouTube channel overview: {e}"}


@mcp.tool(annotations=_READ_ONLY)
def get_video_analytics(
    channel_id: str = None,
    top_n: int = 10,
    start_date: str = None,
    end_date: str = None,
    ctx: Context = None
) -> dict:
    """
    Retrieve top performing videos ranked by views with watch time, retention, and engagement metrics.

    Args:
        channel_id: YouTube Channel ID. If omitted, uses primary channel ('MINE').
        top_n: Number of top videos to return (1-50). Default: 10.
        start_date: Start date (YYYY-MM-DD). Default: 28 days ago.
        end_date: End date (YYYY-MM-DD). Default: 3 days ago.
    """
    try:
        yt_analytics = client_pool.get_youtube_analytics_service()
        yt_data = client_pool.get_youtube_service()

        today = datetime.date.today()
        if not end_date:
            end_date = (today - datetime.timedelta(days=3)).strftime("%Y-%m-%d")
        if not start_date:
            start_date = (today - datetime.timedelta(days=31)).strftime("%Y-%m-%d")

        channel_filter = f"channel=={channel_id}" if channel_id else "channel==MINE"

        response = yt_analytics.reports().query(
            ids=channel_filter,
            startDate=start_date,
            endDate=end_date,
            metrics="views,estimatedMinutesWatched,averageViewDuration,subscribersGained,likes,shares",
            dimensions="video",
            maxResults=min(top_n, 50),
            sort="-views"
        ).execute()

        headers = [h["name"] for h in response.get("columnHeaders", [])]
        rows = response.get("rows", [])

        # Fetch video titles using Data API
        video_ids = [r[0] for r in rows if len(r) > 0]
        titles = {}
        if video_ids:
            v_resp = yt_data.videos().list(id=",".join(video_ids), part="snippet").execute()
            for v in v_resp.get("items", []):
                titles[v["id"]] = v.get("snippet", {}).get("title", v["id"])

        video_list = []
        for r in rows:
            item = dict(zip(headers, r))
            vid = item.get("video")
            item["title"] = titles.get(vid, vid)
            mins = item.get("estimatedMinutesWatched", 0)
            item["watch_time_hours"] = round(mins / 60.0, 1)
            video_list.append(item)

        return {
            "channel": channel_id or "MINE",
            "start_date": start_date,
            "end_date": end_date,
            "total_videos": len(video_list),
            "videos": video_list
        }
    except Exception as e:
        return {"error": f"Failed to fetch video performance: {e}"}


@mcp.tool(annotations=_READ_ONLY)
def get_youtube_traffic_sources(
    channel_id: str = None,
    start_date: str = None,
    end_date: str = None,
    ctx: Context = None
) -> dict:
    """
    Break down YouTube views and watch time by traffic source (YouTube Search, Suggested Videos, Shorts Feed, External).

    Args:
        channel_id: YouTube Channel ID. If omitted, uses primary channel ('MINE').
        start_date: Start date (YYYY-MM-DD). Default: 28 days ago.
        end_date: End date (YYYY-MM-DD). Default: 3 days ago.
    """
    try:
        yt_analytics = client_pool.get_youtube_analytics_service()

        today = datetime.date.today()
        if not end_date:
            end_date = (today - datetime.timedelta(days=3)).strftime("%Y-%m-%d")
        if not start_date:
            start_date = (today - datetime.timedelta(days=31)).strftime("%Y-%m-%d")

        channel_filter = f"channel=={channel_id}" if channel_id else "channel==MINE"

        response = yt_analytics.reports().query(
            ids=channel_filter,
            startDate=start_date,
            endDate=end_date,
            metrics="views,estimatedMinutesWatched",
            dimensions="insightTrafficSourceType",
            sort="-views"
        ).execute()

        headers = [h["name"] for h in response.get("columnHeaders", [])]
        rows = response.get("rows", [])

        source_labels = {
            "YT_SEARCH": "YouTube Search",
            "RELATED_VIDEO": "Suggested Videos",
            "SHORTS": "Shorts Feed",
            "EXT_URL": "External Websites / Links",
            "SUBSCRIBER": "Subscribers / Channel Page",
            "PLAYLIST": "Playlists",
            "NOTIFICATION": "YouTube Notifications",
            "NO_LINK_OTHER": "Direct / Other"
        }

        formatted = []
        total_views = sum(r[1] for r in rows if len(r) > 1)

        for r in rows:
            raw_type = r[0]
            views = r[1]
            mins = r[2] if len(r) > 2 else 0
            share = round((views / total_views) * 100, 1) if total_views > 0 else 0.0

            formatted.append({
                "source_type": raw_type,
                "source_name": source_labels.get(raw_type, raw_type),
                "views": views,
                "watch_time_hours": round(mins / 60.0, 1),
                "share_pct": share
            })

        return {
            "channel": channel_id or "MINE",
            "start_date": start_date,
            "end_date": end_date,
            "total_views": total_views,
            "sources": formatted
        }
    except Exception as e:
        return {"error": f"Failed to fetch YouTube traffic sources: {e}"}
