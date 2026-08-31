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


class ClientPool:
    """Thread-safe connection pool for GA4 Data and Admin API clients."""

    def __init__(self):
        self._data_clients: dict[str, BetaAnalyticsDataClient] = {}
        self._admin_clients: dict[str, AnalyticsAdminServiceClient] = {}

    @staticmethod
    def _normalize_key(credentials_path: str | None) -> str:
        if not credentials_path:
            return "__default__"
        return str(Path(credentials_path).expanduser().resolve())

    @staticmethod
    def _create_credentials(credentials_path: str | None):
        if credentials_path:
            resolved = Path(credentials_path).expanduser().resolve()
            if resolved.exists():
                return service_account.Credentials.from_service_account_file(str(resolved))
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

    def clear(self):
        """Reset cached clients."""
        self._data_clients.clear()
        self._admin_clients.clear()


# Default singleton instance
client_pool = ClientPool()
