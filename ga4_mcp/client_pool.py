# SPDX-License-Identifier: Apache-2.0

"""Multi-credential client pool for GA4 Data API and Admin API.

Caches authenticated client instances by normalized credentials source
(service account JSON file path, ADC, or environment default)."""

import os
import sys
from pathlib import Path
from google.analytics.data_v1beta import BetaAnalyticsDataClient

from google.analytics.admin_v1alpha import AnalyticsAdminServiceClient
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
import urllib.request
import json
from .auth_session import load_session, get_gateway_url


class ClientPool:
    """Thread-safe connection pool for GA4 Data and Admin API clients."""

    def __init__(self):
        self._data_clients: dict[str, BetaAnalyticsDataClient] = {}
        self._admin_clients: dict[str, AnalyticsAdminServiceClient] = {}

    @staticmethod
    def _normalize_key(credentials_path: str | None) -> str:
        if not credentials_path:
            return "__default__"
        if credentials_path.startswith("gateway://"):
            return credentials_path
        return str(Path(credentials_path).expanduser().resolve())

    @staticmethod
    def _create_credentials(credentials_path: str | None):
        if not credentials_path:
            # Check if active session exists
            session = load_session()
            if session and session.get("token"):
                return ClientPool._fetch_gateway_credentials(session["token"], session.get("gateway_url"))
            return None

        if credentials_path.startswith("gateway://"):
            session = load_session()
            token = session.get("token") if session else credentials_path.replace("gateway://", "")
            gw_url = session.get("gateway_url") if session else get_gateway_url()
            return ClientPool._fetch_gateway_credentials(token, gw_url)

        resolved = Path(credentials_path).expanduser().resolve()
        if resolved.exists():
            return service_account.Credentials.from_service_account_file(str(resolved))
        return None

    @staticmethod
    def _fetch_gateway_credentials(session_token: str, gateway_url: str | None = None) -> Credentials | None:
        """Calls Cloudflare Gateway /api/v1/token to get short-lived Google access token."""
        try:
            gw = (gateway_url or get_gateway_url()).rstrip("/")
            req = urllib.request.Request(
                f"{gw}/api/v1/token",
                headers={
                    "Authorization": f"Bearer {session_token}",
                    "User-Agent": "ga4-mcp/1.0"
                }
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                status = getattr(resp, "status", getattr(resp, "code", 200))
                if status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    access_token = data.get("access_token")
                    if access_token:
                        return Credentials(
                            token=access_token,
                            scopes=[
                                "https://www.googleapis.com/auth/analytics.readonly",
                                "https://www.googleapis.com/auth/webmasters.readonly",
                                "https://www.googleapis.com/auth/yt-analytics.readonly",
                                "https://www.googleapis.com/auth/youtube.readonly",
                                "https://www.googleapis.com/auth/adwords"
                            ]
                        )

        except Exception as e:
            print(f"DEBUG: Failed to fetch gateway credentials: {e}", file=sys.stderr)
        return None



    def get_data_client(self, credentials_path: str | None = None) -> BetaAnalyticsDataClient:
        """Get or create a BetaAnalyticsDataClient for the given credentials."""
        key = self._normalize_key(credentials_path)
        if key not in self._data_clients:
            creds = self._create_credentials(credentials_path)
            if creds:
                self._data_clients[key] = BetaAnalyticsDataClient(credentials=creds)
            else:
                self._data_clients[key] = BetaAnalyticsDataClient()
        return self._data_clients[key]

    def get_admin_client(self, credentials_path: str | None = None) -> AnalyticsAdminServiceClient:
        """Get or create an AnalyticsAdminServiceClient for the given credentials."""
        key = self._normalize_key(credentials_path)
        if key not in self._admin_clients:
            creds = self._create_credentials(credentials_path)
            if creds:
                self._admin_clients[key] = AnalyticsAdminServiceClient(credentials=creds)
            else:
                self._admin_clients[key] = AnalyticsAdminServiceClient()
        return self._admin_clients[key]

    def get_gsc_service(self, credentials_path: str | None = None):
        """Get authenticated Google Search Console service."""
        from googleapiclient.discovery import build
        creds = self._create_credentials(credentials_path)
        return build("searchconsole", "v1", credentials=creds, cache_discovery=False)

    def get_youtube_service(self, credentials_path: str | None = None):
        """Get authenticated YouTube Data API service."""
        from googleapiclient.discovery import build
        creds = self._create_credentials(credentials_path)
        return build("youtube", "v3", credentials=creds, cache_discovery=False)

    def get_youtube_analytics_service(self, credentials_path: str | None = None):
        """Get authenticated YouTube Analytics API service."""
        from googleapiclient.discovery import build
        creds = self._create_credentials(credentials_path)
        return build("youtubeAnalytics", "v2", credentials=creds, cache_discovery=False)

    def clear(self):
        """Reset cached clients."""
        self._data_clients.clear()
        self._admin_clients.clear()


# Default singleton instance
client_pool = ClientPool()
