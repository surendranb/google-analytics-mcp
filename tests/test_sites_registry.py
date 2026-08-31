# SPDX-License-Identifier: Apache-2.0
"""Tests for SiteRegistry: static config, env vars, alias resolution, and default selection.
Run: python tests/test_sites_registry.py"""

import os
import sys
import json
import tempfile
from pathlib import Path

from ga4_mcp.sites import SiteRegistry, PropertyInfo


def _run():
    failures = []

    # 1. Test loading from inline GA4_SITES JSON
    sites_json = json.dumps({
        "default_site": "blog",
        "sites": {
            "blog": {
                "name": "Personal Blog",
                "property_id": "111111111",
                "credentials": "/path/to/blog-sa.json"
            },
            "store": {
                "name": "E-Commerce Store",
                "property_id": "222222222",
                "credentials": "/path/to/store-sa.json"
            },
            "docs": {
                "name": "Documentation Portal",
                "property_id": "333333333"
            }
        }
    })

    os.environ["GA4_SITES"] = sites_json
    os.environ["GA4_CONFIG_DIR"] = tempfile.mkdtemp()
    os.environ.pop("GA4_PROPERTY_ID", None)
    os.environ.pop("GOOGLE_APPLICATION_CREDENTIALS", None)


    reg = SiteRegistry()
    reg.initialize(force_refresh=True)

    if not reg.has_any():
        failures.append("SiteRegistry failed to load properties from GA4_SITES")

    # Resolve default
    default_prop, err = reg.resolve()
    if err or not default_prop or default_prop.property_id != "111111111":
        failures.append(f"Default resolution failed: expected 111111111, got {default_prop}, err: {err}")

    # Resolve by alias
    store_prop, err = reg.resolve("store")
    if err or not store_prop or store_prop.property_id != "222222222":
        failures.append(f"Alias resolution 'store' failed: {store_prop}, err: {err}")

    # Resolve by display name substring
    docs_prop, err = reg.resolve("Documentation")
    if err or not docs_prop or docs_prop.property_id != "333333333":
        failures.append(f"Substring resolution 'Documentation' failed: {docs_prop}, err: {err}")

    # Resolve by exact numeric ID
    exact_prop, err = reg.resolve("222222222")
    if err or not exact_prop or exact_prop.alias != "store":
        failures.append(f"Numeric ID resolution failed: {exact_prop}, err: {err}")

    # Resolve unknown non-digit
    unk_prop, err = reg.resolve("non_existent_site")
    if unk_prop is not None or not err:
        failures.append(f"Expected error for non-existent site, got: {unk_prop}")

    # 2. Test dynamic ad-hoc numeric ID resolution
    dynamic_prop, err = reg.resolve("999888777")
    if err or not dynamic_prop or dynamic_prop.property_id != "999888777" or dynamic_prop.source != "dynamic":
        failures.append(f"Dynamic ad-hoc ID resolution failed: {dynamic_prop}, err: {err}")

    # 3. Test list_all format
    all_props = reg.list_all()
    if len(all_props) != 3:
        failures.append(f"Expected 3 properties in list_all, got {len(all_props)}")

    # 4. Test legacy env fallback
    os.environ.pop("GA4_SITES", None)
    os.environ["GA4_PROPERTY_ID"] = "123456789"
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/path/to/legacy-sa.json"

    reg2 = SiteRegistry()
    reg2.initialize(force_refresh=True)

    legacy_prop, err = reg2.resolve()
    if err or not legacy_prop or legacy_prop.property_id != "123456789":
        failures.append(f"Legacy env resolution failed: {legacy_prop}, err: {err}")

    if failures:
        print("FAIL:")
        for f in failures:
            print("  -", f)
        sys.exit(1)

    print("PASS: SiteRegistry correctly handles static configs, aliases, dynamic IDs, and legacy env vars")


if __name__ == "__main__":
    _run()
