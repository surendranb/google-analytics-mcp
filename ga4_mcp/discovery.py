# SPDX-License-Identifier: Apache-2.0

"""Auto-discovery engine for Google Analytics 4 accounts and properties.

Scans local credential sources (ADC, env var, and ~/.config/ga4-mcp/credentials/)
and queries the GA4 Admin API (accountSummaries.list) to discover all properties
accessible by each identity."""

import os
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

from .client_pool import client_pool


@dataclass
class DiscoveredProperty:
    property_id: str
    display_name: str
    account_id: str
    account_name: str
    credentials_source: Optional[str] = None  # None means ADC/default, otherwise path to key file
    source_type: str = "adc"  # "adc", "service_account", or "env"


def scan_credential_sources() -> list[tuple[Optional[str], str]]:
    """
    Returns a list of (credentials_path, source_type) found on this machine.
    credentials_path is None for ADC/default.
    """
    sources: list[tuple[Optional[str], str]] = []
    seen_paths: set[str] = set()

    # 1. Active Gateway OAuth Session
    from .auth_session import load_session
    session = load_session()
    if session and session.get("token"):
        sources.append(("gateway://session", "gateway"))

    # 2. Explicit env var
    env_creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if env_creds and os.path.exists(env_creds):
        resolved = str(Path(env_creds).expanduser().resolve())
        sources.append((resolved, "env"))
        seen_paths.add(resolved)

    # 3. Dedicated GA4 MCP credentials folder
    creds_dir = Path(os.getenv("GA4_CREDENTIALS_DIR", Path.home() / ".config" / "ga4-mcp" / "credentials"))
    if creds_dir.is_dir():
        for json_file in sorted(creds_dir.glob("*.json")):
            resolved = str(json_file.resolve())
            if resolved not in seen_paths:
                sources.append((resolved, "service_account"))
                seen_paths.add(resolved)

    # 4. Application Default Credentials (ADC)
    adc_standard_path = Path.home() / ".config" / "gcloud" / "application_default_credentials.json"
    if adc_standard_path.exists() or not sources:
        # If standard ADC exists, or if no other source was found, test default ADC
        sources.append((None, "adc"))


    return sources


def discover_properties_for_source(credentials_path: Optional[str], source_type: str) -> list[DiscoveredProperty]:
    """Queries GA4 Admin API accountSummaries.list for a single credential source."""
    discovered: list[DiscoveredProperty] = []
    try:
        admin_client = client_pool.get_admin_client(credentials_path)
        # Call list_account_summaries
        pager = admin_client.list_account_summaries()
        for account in pager:
            acct_id = account.account.replace("accounts/", "") if account.account else ""
            acct_name = account.display_name or "Unknown Account"
            for prop in getattr(account, "property_summaries", []):
                prop_id = prop.property.replace("properties/", "") if prop.property else ""
                prop_name = prop.display_name or f"Property {prop_id}"
                discovered.append(DiscoveredProperty(
                    property_id=prop_id,
                    display_name=prop_name,
                    account_id=acct_id,
                    account_name=acct_name,
                    credentials_source=credentials_path,
                    source_type=source_type
                ))
    except Exception as e:
        print(f"DEBUG: Auto-discovery failed for source {credentials_path or 'ADC'}: {e}", file=sys.stderr)

    return discovered


def discover_all_properties() -> list[DiscoveredProperty]:
    """Scans all credential sources and returns a combined list of discovered properties."""
    all_properties: list[DiscoveredProperty] = []
    seen_prop_ids: set[str] = set()

    for cred_path, source_type in scan_credential_sources():
        props = discover_properties_for_source(cred_path, source_type)
        for p in props:
            # Deduplicate by property_id (first matching credential takes priority)
            if p.property_id not in seen_prop_ids:
                seen_prop_ids.add(p.property_id)
                all_properties.append(p)

    return all_properties
