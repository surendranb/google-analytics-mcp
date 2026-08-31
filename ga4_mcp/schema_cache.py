# SPDX-License-Identifier: Apache-2.0

"""Multi-property schema cache.

Isolates GA4 dimension and metric schemas across distinct properties,
caching results on-demand to support custom dimensions without cross-property pollution."""

import sys
from typing import Optional

from .client_pool import client_pool
from .sites import PropertyInfo


class SchemaCache:
    """In-memory cache for GA4 property schemas."""

    def __init__(self):
        self._cache: dict[str, dict] = {}

    @staticmethod
    def _cache_key(property_info: PropertyInfo) -> str:
        cred = property_info.credentials_path or "__default__"
        return f"{property_info.property_id}::{cred}"

    def get_schema(self, property_info: PropertyInfo, force_refresh: bool = False) -> dict:
        """
        Fetches and caches the schema (dimensions and metrics) for a specific property.
        """
        key = self._cache_key(property_info)
        if key in self._cache and not force_refresh:
            return self._cache[key]

        client = client_pool.get_data_client(property_info.credentials_path)
        request = {"name": f"properties/{property_info.property_id}/metadata"}
        metadata = client.get_metadata(request=request)

        schema = {"dimensions": {}, "metrics": {}}

        for dim in metadata.dimensions:
            schema["dimensions"][dim.api_name] = {
                "ui_name": dim.ui_name,
                "description": dim.description,
                "category": dim.category,
                "custom_definition": getattr(dim, "custom_definition", False),
            }

        for met in metadata.metrics:
            type_name = met.type_.name if hasattr(met, "type_") and hasattr(met.type_, "name") else "TYPE_UNSPECIFIED"
            schema["metrics"][met.api_name] = {
                "ui_name": met.ui_name,
                "description": met.description,
                "category": met.category,
                "type": type_name,
            }

        self._cache[key] = schema
        return schema

    def set_schema(self, property_id: str, schema: dict, credentials_path: Optional[str] = None):
        """Allows manually populating a schema (useful for testing or startup caching)."""
        cred = credentials_path or "__default__"
        key = f"{property_id}::{cred}"
        self._cache[key] = schema

    def clear(self):
        """Clear all cached schemas."""
        self._cache.clear()


# Default singleton instance
schema_cache = SchemaCache()
