# Google Analytics 4 (GA4) MCP Server 📊

> **Model Context Protocol (MCP) server for Google Analytics 4: real-time query exploration, schema discovery, metric aggregation, and audience insights for AI agents.**

[![CI](https://github.com/surendranb/google-analytics-mcp/actions/workflows/package-checks.yml/badge.svg)](https://github.com/surendranb/google-analytics-mcp/actions)
[![PyPI version](https://img.shields.io/pypi/v/google-analytics-mcp.svg?style=flat-square&color=blue)](https://pypi.org/project/google-analytics-mcp/)
[![npm version](https://img.shields.io/npm/v/@surendranb/google-analytics-mcp.svg?style=flat-square&color=red)](https://www.npmjs.com/package/@surendranb/google-analytics-mcp)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)](LICENSE)

---

## ⚡ Quickstart

### Option 1: 1-Click User Login (Zero GCP, All Accounts)
If your Google account (`you@agency.com` or `you@gmail.com`) is already a Viewer on your GA4 properties:
```bash
gcloud auth application-default login --scopes=https://www.googleapis.com/auth/analytics.readonly
```
Then launch the server with **zero configuration** — it auto-discovers all your accessible GA4 accounts and properties!

### Option 2: Service Account Key(s)
Set environment variables:
```bash
export GA4_PROPERTY_ID="123456789"
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service_account.json"
```
Or drop multiple service account keys into `~/.config/ga4-mcp/credentials/` for automatic multi-account indexing.

---

## 🤖 Client Setup

### A. Claude Code (CLI)
```bash
claude mcp add google-analytics -- uvx google-analytics-mcp
```

### B. Cursor & Google Antigravity (`mcp.json`)
```json
{
  "mcpServers": {
    "google-analytics": {
      "command": "uvx",
      "args": ["google-analytics-mcp"]
    }
  }
}
```

### C. Multi-Site Client Config (`claude_desktop_config.json` / `mcp.json`)
```json
{
  "mcpServers": {
    "google-analytics": {
      "command": "uvx",
      "args": ["google-analytics-mcp"],
      "env": {
        "GA4_SITES": "{\"default_site\":\"blog\",\"sites\":{\"blog\":{\"name\":\"Personal Blog\",\"property_id\":\"111111111\",\"credentials\":\"/path/to/blog-sa.json\"},\"store\":{\"name\":\"E-Commerce Shop\",\"property_id\":\"222222222\",\"credentials\":\"/path/to/store-sa.json\"}}}"
      }
    }
  }
}
```

---

## 🛠️ Tools & Capabilities

| Tool Name | Parameters | Description |
|---|---|---|
| `list_properties` | *(none)* | Discovers and lists all accessible GA4 properties and accounts across all credentials. |
| `get_ga4_data` | `dimensions`, `metrics`, `date_range_start`, `date_range_end`, `dimension_filter`, `limit`, `property` | Runs multi-dimensional reports with automated metric totals, smart sorting, and property routing. |
| `search_schema` | `keyword`, `property` | Searches valid dimension and metric names scored by relevance for a specific property. |
| `get_property_schema` | `property` | Fetches complete dimension and metric schemas for a property. |
| `list_dimension_categories` | `property` | Lists dimension categories and counts for a property. |
| `list_metric_categories` | `property` | Lists metric categories and counts for a property. |
| `search_skills` | `query` | Accesses pre-engineered analytical recipes (traffic drops, e-commerce, AI referrals, bot detection). |
| `setup_ga4_access` | *(none)* | Interactively diagnoses and repairs authentication and property configuration. |

---

## 🧪 Testing

Run the full automated test suite:
```bash
uv run python tests/test_aggregation.py
uv run python tests/test_discovery.py
uv run python tests/test_sites_registry.py
uv run python tests/test_schema_isolation.py
uv run python tests/test_multisite_mcp.py
uv run python tests/test_mcp_connection.py
uv run python tests/test_v2_inline_recovery.py
uv run python tests/test_v2_setup_recovery.py
uv run python tests/test_v2_telemetry.py
```
