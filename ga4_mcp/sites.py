# SPDX-License-Identifier: Apache-2.0

"""Site registry and property catalog management.

Merges static configuration (sites.json / GA4_SITES env var / legacy env vars)
with dynamic GA4 Admin API discovery to provide unified property resolution."""

import os
import sys
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

from .discovery import discover_all_properties, DiscoveredProperty


@dataclass
class PropertyInfo:
    property_id: str
    display_name: str
    account_name: str = "Default Account"
    account_id: str = ""
    credentials_path: Optional[str] = None
    alias: Optional[str] = None
    is_default: bool = False
    source: str = "discovered"  # "config", "env", "discovered", "dynamic"


class SiteRegistry:
    """Unified catalog of all accessible GA4 properties."""

    def __init__(self):
        self._properties: dict[str, PropertyInfo] = {}  # keyed by property_id
        self._default_property_id: Optional[str] = None
        self._initialized: bool = False

    def initialize(self, force_refresh: bool = False):
        """Loads properties from config, env, and Admin API auto-discovery."""
        if self._initialized and not force_refresh:
            return

        self._properties.clear()
        self._default_property_id = None

        # 1. Load from sites.json or GA4_SITES config
        self._load_config_sources()

        # 2. Load from legacy single-site environment variables
        self._load_legacy_env()

        # 3. Discover properties from Admin API across available credentials
        self._discover_and_merge()

        self._initialized = True

    def _load_config_sources(self):
        """Loads static config from GA4_CONFIG_PATH, ~/.config/ga4-mcp/sites.json, or GA4_SITES env."""
        config_path = os.getenv("GA4_CONFIG_PATH")
        if not config_path:
            standard_path = Path.home() / ".config" / "ga4-mcp" / "sites.json"
            if standard_path.exists():
                config_path = str(standard_path)

        data = None
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, encoding="utf-8") as f:
                    data = json.load(f)
            except Exception as e:
                print(f"WARNING: Could not parse sites config at {config_path}: {e}", file=sys.stderr)

        if not data:
            env_sites = os.getenv("GA4_SITES")
            if env_sites:
                try:
                    data = json.loads(env_sites)
                except Exception as e:
                    print(f"WARNING: Could not parse GA4_SITES env var: {e}", file=sys.stderr)

        if data:
            self._apply_config_dict(data)

    def _apply_config_dict(self, data: dict):
        default_site = data.get("default_site")
        sites = data.get("sites", {})
        if isinstance(sites, list):
            # Convert list format [{"alias": "blog", "property_id": "123"}, ...]
            sites = {item.get("alias", item.get("property_id")): item for item in sites}

        for alias, site_data in sites.items():
            prop_id = str(site_data.get("property_id", "")).strip()
            if not prop_id:
                continue
            is_def = (alias == default_site) or (prop_id == default_site) or bool(site_data.get("is_default"))
            prop_info = PropertyInfo(
                property_id=prop_id,
                display_name=site_data.get("name", site_data.get("display_name", f"Site {alias}")),
                account_name=site_data.get("account_name", "Configured Account"),
                credentials_path=site_data.get("credentials_path") or site_data.get("credentials"),
                alias=alias,
                is_default=is_def,
                source="config"
            )
            self._properties[prop_id] = prop_info
            if is_def:
                self._default_property_id = prop_id

    def _load_legacy_env(self):
        """Loads legacy GA4_PROPERTY_ID and GOOGLE_APPLICATION_CREDENTIALS."""
        prop_id = os.getenv("GA4_PROPERTY_ID")
        creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if prop_id:
            prop_id = prop_id.strip()
            if prop_id not in self._properties:
                self._properties[prop_id] = PropertyInfo(
                    property_id=prop_id,
                    display_name=f"Property {prop_id}",
                    credentials_path=creds_path,
                    alias="default",
                    is_default=True,
                    source="env"
                )
                if not self._default_property_id:
                    self._default_property_id = prop_id

    def _discover_and_merge(self):
        """Performs Admin API auto-discovery and merges properties into catalog."""
        try:
            discovered = discover_all_properties()
            for d in discovered:
                if d.property_id not in self._properties:
                    self._properties[d.property_id] = PropertyInfo(
                        property_id=d.property_id,
                        display_name=d.display_name,
                        account_name=d.account_name,
                        account_id=d.account_id,
                        credentials_path=d.credentials_source,
                        source="discovered"
                    )
            # If only 1 property exists and no default is set, make it the default
            if len(self._properties) == 1 and not self._default_property_id:
                single_id = next(iter(self._properties.keys()))
                self._properties[single_id].is_default = True
                self._default_property_id = single_id
        except Exception as e:
            print(f"DEBUG: Discovery merge error: {e}", file=sys.stderr)

    def resolve(self, identifier: Optional[str] = None) -> tuple[Optional[PropertyInfo], Optional[str]]:
        """
        Resolves a property identifier (alias, numeric ID, or display name) to PropertyInfo.
        Returns (PropertyInfo, None) on success, or (None, error_message) on failure.
        """
        if not self._initialized:
            self.initialize()

        if not self._properties:
            return None, "No GA4 properties are configured or discovered. Please check your credentials."

        # If no identifier specified
        if not identifier or not identifier.strip():
            if self._default_property_id and self._default_property_id in self._properties:
                return self._properties[self._default_property_id], None
            if len(self._properties) == 1:
                return next(iter(self._properties.values())), None
            
            # Multiple properties available without default
            prop_list = ", ".join(f"'{p.display_name}' ({p.property_id})" for p in self._properties.values())
            return None, f"Multiple properties available [{prop_list}]. Please specify one using property='<name_or_id>'."

        target = identifier.strip().lower()

        # 1. Exact numeric property ID match
        if target in self._properties:
            return self._properties[target], None

        # 2. Match by alias (case-insensitive)
        for p in self._properties.values():
            if p.alias and p.alias.lower() == target:
                return p, None

        # 3. Match by display name (case-insensitive exact or substring)
        exact_matches = [p for p in self._properties.values() if p.display_name.lower() == target]
        if len(exact_matches) == 1:
            return exact_matches[0], None

        substr_matches = [p for p in self._properties.values() if target in p.display_name.lower()]
        if len(substr_matches) == 1:
            return substr_matches[0], None

        # 4. If target is purely digits, treat as dynamic ad-hoc property ID
        if target.isdigit() and len(target) >= 6:
            # Inherit default credentials or env creds
            default_creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
            return PropertyInfo(
                property_id=target,
                display_name=f"Property {target}",
                credentials_path=default_creds,
                source="dynamic"
            ), None

        available = ", ".join(f"'{p.display_name}' (id: {p.property_id})" for p in self._properties.values())
        return None, f"Property '{identifier}' not found. Available properties: {available}. Call list_properties to view all."

    def list_all(self) -> list[dict]:
        """Returns a serializable list of all properties in the catalog."""
        if not self._initialized:
            self.initialize()

        results = []
        for p in self._properties.values():
            cred_display = "ADC / User Login" if not p.credentials_path else os.path.basename(p.credentials_path)
            results.append({
                "property_id": p.property_id,
                "display_name": p.display_name,
                "account_name": p.account_name,
                "alias": p.alias or "",
                "credentials": cred_display,
                "is_default": p.is_default or (p.property_id == self._default_property_id),
                "source": p.source
            })
        return results

    def has_any(self) -> bool:
        """Returns True if at least one property is cataloged."""
        if not self._initialized:
            self.initialize()
        return len(self._properties) > 0


# Default singleton instance
registry = SiteRegistry()
