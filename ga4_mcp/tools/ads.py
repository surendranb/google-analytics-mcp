# SPDX-License-Identifier: Apache-2.0
"""Google Ads API tools for AI agents.
Provides ad account discovery, campaign performance monitoring, search term analysis, and ROAS tracking.
"""

import os
import json
import datetime
import urllib.request
from typing import Optional, List, Dict, Any
from mcp.types import ToolAnnotations
from mcp.server.mcpserver import Context
from ga4_mcp.coordinator import mcp
from ga4_mcp.client_pool import client_pool

_READ_ONLY = ToolAnnotations(read_only_hint=True, idempotent_hint=True, open_world_hint=False)


def _get_google_ads_auth(developer_token: str = None) -> tuple[str | None, str | None]:
    """Resolves access token and developer token for Google Ads API."""
    dev_token = developer_token or os.environ.get("GOOGLE_ADS_DEVELOPER_TOKEN", "mock_or_gateway")
    
    # Get access token from client_pool credentials
    creds = client_pool._create_credentials(None)
    if not creds or not creds.token:
        return None, dev_token
    return creds.token, dev_token


@mcp.tool(annotations=_READ_ONLY)
def list_ad_accounts(developer_token: str = None, ctx: Context = None) -> dict:
    """
    List all accessible Google Ads customer accounts for the authenticated user.

    Returns: {"accounts": ["123-456-7890", "987-654-3210"]}
    """
    access_token, dev_token = _get_google_ads_auth(developer_token)
    if not access_token:
        return {"error": "No active Google authentication found. Please log in first."}

    try:
        url = "https://googleads.googleapis.com/v18/customers:listAccessibleCustomers"
        req = urllib.request.Request(
            url,
            headers={
                "Authorization": f"Bearer {access_token}",
                "developer-token": dev_token,
                "User-Agent": "ga4-mcp/1.0"
            }
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            raw_ids = data.get("resourceNames", [])
            formatted = []
            for r in raw_ids:
                cid = r.replace("customers/", "")
                if len(cid) == 10:
                    formatted.append(f"{cid[:3]}-{cid[3:6]}-{cid[6:]}")
                else:
                    formatted.append(cid)
            return {
                "accounts": formatted,
                "total_accounts": len(formatted),
                "how_to_query": "Pass customer_id (e.g. '123-456-7890') to get_campaign_performance or get_search_terms."
            }
    except Exception as e:
        return {
            "accounts": [],
            "note": "Google Ads API requires a developer token. Set GOOGLE_ADS_DEVELOPER_TOKEN in your environment if using custom tokens.",
            "error": str(e)
        }


@mcp.tool(annotations=_READ_ONLY)
def get_campaign_performance(
    customer_id: str,
    start_date: str = None,
    end_date: str = None,
    developer_token: str = None,
    ctx: Context = None
) -> dict:
    """
    Retrieve campaign performance: spend, impressions, clicks, CPC, conversions, and ROAS.

    Args:
        customer_id: Google Ads Customer ID (e.g. '123-456-7890' or '1234567890').
        start_date: Start date (YYYY-MM-DD). Default: 28 days ago.
        end_date: End date (YYYY-MM-DD). Default: yesterday.
    """
    access_token, dev_token = _get_google_ads_auth(developer_token)
    if not access_token:
        return {"error": "No active Google authentication found. Please log in first."}

    clean_cid = customer_id.replace("-", "").strip()
    today = datetime.date.today()
    if not end_date:
        end_date = (today - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    if not start_date:
        start_date = (today - datetime.timedelta(days=29)).strftime("%Y-%m-%d")

    query = f"""
        SELECT 
            campaign.id, 
            campaign.name, 
            campaign.status, 
            metrics.impressions, 
            metrics.clicks, 
            metrics.cost_micros, 
            metrics.conversions, 
            metrics.conversions_value 
        FROM campaign 
        WHERE segments.date BETWEEN '{start_date}' AND '{end_date}'
        ORDER BY metrics.cost_micros DESC
    """

    try:
        url = f"https://googleads.googleapis.com/v18/customers/{clean_cid}/googleAds:search"
        payload = json.dumps({"query": query}).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "Authorization": f"Bearer {access_token}",
                "developer-token": dev_token,
                "Content-Type": "application/json",
                "User-Agent": "ga4-mcp/1.0"
            }
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            results = data.get("results", [])

            campaigns = []
            total_spend = 0.0
            total_clicks = 0
            total_impressions = 0
            total_conversions = 0.0
            total_conversion_value = 0.0

            for row in results:
                c = row.get("campaign", {})
                m = row.get("metrics", {})
                spend = round(float(m.get("costMicros", 0)) / 1_000_000.0, 2)
                clicks = int(m.get("clicks", 0))
                impressions = int(m.get("impressions", 0))
                conversions = float(m.get("conversions", 0))
                conv_value = float(m.get("conversionsValue", 0))

                cpc = round(spend / clicks, 2) if clicks > 0 else 0.0
                roas = round((conv_value / spend) * 100, 1) if spend > 0 else 0.0

                total_spend += spend
                total_clicks += clicks
                total_impressions += impressions
                total_conversions += conversions
                total_conversion_value += conv_value

                campaigns.append({
                    "campaign_id": c.get("id"),
                    "name": c.get("name"),
                    "status": c.get("status"),
                    "spend": spend,
                    "clicks": clicks,
                    "impressions": impressions,
                    "cpc": cpc,
                    "conversions": conversions,
                    "conversion_value": conv_value,
                    "roas_pct": roas
                })

            avg_cpc = round(total_spend / total_clicks, 2) if total_clicks > 0 else 0.0
            overall_roas = round((total_conversion_value / total_spend) * 100, 1) if total_spend > 0 else 0.0

            return {
                "customer_id": customer_id,
                "start_date": start_date,
                "end_date": end_date,
                "totals": {
                    "total_spend": round(total_spend, 2),
                    "total_clicks": total_clicks,
                    "total_impressions": total_impressions,
                    "total_conversions": round(total_conversions, 1),
                    "average_cpc": avg_cpc,
                    "overall_roas_pct": overall_roas
                },
                "campaigns": campaigns
            }
    except Exception as e:
        return {"error": f"Failed to query Google Ads performance: {e}"}


@mcp.tool(annotations=_READ_ONLY)
def get_search_terms(
    customer_id: str,
    start_date: str = None,
    end_date: str = None,
    top_n: int = 25,
    developer_token: str = None,
    ctx: Context = None
) -> dict:
    """
    Retrieve search query report: actual queries typed by searchers that triggered your ads, with spend and conversion metrics.

    Args:
        customer_id: Google Ads Customer ID (e.g. '123-456-7890').
        start_date: Start date (YYYY-MM-DD). Default: 28 days ago.
        end_date: End date (YYYY-MM-DD). Default: yesterday.
        top_n: Number of top queries to return (1-100). Default: 25.
    """
    access_token, dev_token = _get_google_ads_auth(developer_token)
    if not access_token:
        return {"error": "No active Google authentication found. Please log in first."}

    clean_cid = customer_id.replace("-", "").strip()
    today = datetime.date.today()
    if not end_date:
        end_date = (today - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    if not start_date:
        start_date = (today - datetime.timedelta(days=29)).strftime("%Y-%m-%d")

    query = f"""
        SELECT 
            search_term_view.search_term, 
            metrics.impressions, 
            metrics.clicks, 
            metrics.cost_micros, 
            metrics.conversions 
        FROM search_term_view 
        WHERE segments.date BETWEEN '{start_date}' AND '{end_date}'
        ORDER BY metrics.cost_micros DESC 
        LIMIT {min(top_n, 100)}
    """

    try:
        url = f"https://googleads.googleapis.com/v18/customers/{clean_cid}/googleAds:search"
        payload = json.dumps({"query": query}).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "Authorization": f"Bearer {access_token}",
                "developer-token": dev_token,
                "Content-Type": "application/json",
                "User-Agent": "ga4-mcp/1.0"
            }
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            results = data.get("results", [])

            terms = []
            for row in results:
                st = row.get("searchTermView", {})
                m = row.get("metrics", {})
                spend = round(float(m.get("costMicros", 0)) / 1_000_000.0, 2)
                clicks = int(m.get("clicks", 0))
                conversions = float(m.get("conversions", 0))

                terms.append({
                    "search_term": st.get("searchTerm"),
                    "spend": spend,
                    "clicks": clicks,
                    "impressions": int(m.get("impressions", 0)),
                    "conversions": conversions,
                    "cost_per_conversion": round(spend / conversions, 2) if conversions > 0 else 0.0
                })

            return {
                "customer_id": customer_id,
                "start_date": start_date,
                "end_date": end_date,
                "total_search_terms": len(terms),
                "search_terms": terms
            }
    except Exception as e:
        return {"error": f"Failed to query search terms: {e}"}
