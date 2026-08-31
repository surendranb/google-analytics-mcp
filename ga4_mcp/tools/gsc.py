# SPDX-License-Identifier: Apache-2.0
"""Google Search Console (GSC) tools for AI agents.
Provides verified site discovery, multi-dimensional search analytics, sitemap inspection, and index diagnostics.
"""

import datetime
from typing import Optional, List, Dict, Any
from mcp.types import ToolAnnotations
from mcp.server.mcpserver import Context
from ga4_mcp.coordinator import mcp, fire_skill_tip
from ga4_mcp.client_pool import client_pool

_READ_ONLY = ToolAnnotations(read_only_hint=True, idempotent_hint=True, open_world_hint=False)


@mcp.tool(annotations=_READ_ONLY)
def list_search_sites(ctx: Context = None) -> dict:
    """
    List all verified sites and domain properties in Google Search Console.

    Returns: {"sites": [{"siteUrl": "sc-domain:example.com", "permissionLevel": "siteOwner"}, ...]}
    Use this to see what domain and URL-prefix properties you have access to.
    """
    try:
        service = client_pool.get_gsc_service()
        response = service.sites().list().execute()
        sites = response.get("siteEntry", [])
        
        formatted = []
        for s in sites:
            formatted.append({
                "siteUrl": s.get("siteUrl"),
                "permissionLevel": s.get("permissionLevel")
            })
            
        return {
            "sites": formatted,
            "total_sites": len(formatted),
            "how_to_query": "Pass site_url (e.g. site_url='sc-domain:example.com' or 'https://example.com/') to get_search_analytics."
        }
    except Exception as e:
        return {
            "sites": [],
            "error": f"Error fetching Search Console sites: {e}. Please ensure your account has GSC permissions."
        }


@mcp.tool(annotations=_READ_ONLY)
def get_search_analytics(
    site_url: str = None,
    dimensions: List[str] = None,
    start_date: str = None,
    end_date: str = None,
    row_limit: int = 100,
    search_type: str = "web",
    filters: List[dict] = None,
    ctx: Context = None
) -> dict:
    """
    Retrieve Google Search Console search performance data: queries, clicks, impressions, CTR, and SERP position.

    Args:
        site_url: Property URL exactly as shown in list_search_sites (e.g., 'sc-domain:example.com' or 'https://example.com/'). If omitted, queries the first verified site.
        dimensions: List of dimensions to group by: ['query', 'page', 'country', 'device', 'date', 'searchAppearance']. Default: ['query'].
        start_date: Start date (YYYY-MM-DD). Default: 28 days ago.
        end_date: End date (YYYY-MM-DD). Default: 3 days ago (Search Console data lag).
        row_limit: Max rows to return (1-25000). Default: 100.
        search_type: 'web', 'image', 'video', 'news', 'discover', 'googleNews'. Default: 'web'.
        filters: Optional filters (e.g., [{"dimension": "country", "operator": "equals", "expression": "USA"}]).

    Returns:
        JSON with 'rows' containing clicks, impressions, ctr, position, and dimension values.
    """
    try:
        service = client_pool.get_gsc_service()

        # If site_url is not passed, resolve first verified site
        if not site_url:
            sites_resp = service.sites().list().execute()
            sites = sites_resp.get("siteEntry", [])
            if not sites:
                return {"error": "No verified Search Console sites found for your account."}
            site_url = sites[0]["siteUrl"]

        if not dimensions:
            dimensions = ["query"]

        today = datetime.date.today()
        if not end_date:
            end_date = (today - datetime.timedelta(days=3)).strftime("%Y-%m-%d")
        if not start_date:
            start_date = (today - datetime.timedelta(days=31)).strftime("%Y-%m-%d")

        request_body: Dict[str, Any] = {
            "startDate": start_date,
            "endDate": end_date,
            "dimensions": dimensions,
            "rowLimit": min(row_limit, 25000),
            "type": search_type
        }

        if filters:
            request_body["dimensionFilterGroups"] = [{"filters": filters}]

        response = service.searchanalytics().query(siteUrl=site_url, body=request_body).execute()
        rows = response.get("rows", [])

        # Server-side totals
        total_clicks = sum(r.get("clicks", 0) for r in rows)
        total_impressions = sum(r.get("impressions", 0) for r in rows)
        avg_ctr = (total_clicks / total_impressions) if total_impressions > 0 else 0.0
        avg_pos = (sum(r.get("position", 0) * r.get("impressions", 0) for r in rows) / total_impressions) if total_impressions > 0 else 0.0

        return {
            "site_url": site_url,
            "start_date": start_date,
            "end_date": end_date,
            "dimensions": dimensions,
            "total_rows": len(rows),
            "totals": {
                "clicks": total_clicks,
                "impressions": total_impressions,
                "ctr": round(avg_ctr, 4),
                "position": round(avg_pos, 2)
            },
            "rows": rows
        }
    except Exception as e:
        return {"error": f"Failed to retrieve Search Console data: {e}"}


@mcp.tool(annotations=_READ_ONLY)
def get_sitemaps(site_url: str = None, ctx: Context = None) -> dict:
    """
    List submitted sitemaps for a Search Console property with crawl status and errors.

    Args:
        site_url: Property URL (e.g., 'sc-domain:example.com'). If omitted, uses first verified site.
    """
    try:
        service = client_pool.get_gsc_service()
        if not site_url:
            sites_resp = service.sites().list().execute()
            sites = sites_resp.get("siteEntry", [])
            if not sites:
                return {"error": "No verified Search Console sites found."}
            site_url = sites[0]["siteUrl"]

        response = service.sitemaps().list(siteUrl=site_url).execute()
        sitemaps = response.get("sitemap", [])
        return {
            "site_url": site_url,
            "sitemaps": sitemaps
        }
    except Exception as e:
        return {"error": f"Failed to fetch sitemaps: {e}"}


@mcp.tool(annotations=_READ_ONLY)
def inspect_url(inspection_url: str, site_url: str = None, ctx: Context = None) -> dict:
    """
    Inspect real-time Google Indexing status for a specific URL (index status, last crawl, rich results).

    Args:
        inspection_url: The exact full URL to inspect (e.g. 'https://example.com/blog/post-1').
        site_url: The Search Console property URL containing this page. If omitted, uses inspection_url domain.
    """
    try:
        service = client_pool.get_gsc_service()
        if not site_url:
            site_url = inspection_url

        response = service.urlInspection().index().inspect(body={
            "inspectionUrl": inspection_url,
            "siteUrl": site_url
        }).execute()
        
        result = response.get("inspectionResult", {})
        return {
            "inspection_url": inspection_url,
            "index_status": result.get("indexStatusResult", {}),
            "mobile_usability": result.get("mobileUsabilityResult", {}),
            "rich_results": result.get("richResultsResult", {})
        }
    except Exception as e:
        return {"error": f"Failed to inspect URL: {e}"}
