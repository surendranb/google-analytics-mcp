# Google Analytics 4 (GA4) MCP Server 📊

> **Production Model Context Protocol (MCP) server for Google Analytics 4: real-time query exploration, schema discovery, metric aggregation, and audience insights for AI agents.**

[![CI](https://github.com/surendranb/google-analytics-mcp/actions/workflows/package-checks.yml/badge.svg)](https://github.com/surendranb/google-analytics-mcp/actions)
[![PyPI version](https://img.shields.io/pypi/v/google-analytics-mcp.svg?style=flat-square&color=blue)](https://pypi.org/project/google-analytics-mcp/)
[![npm version](https://img.shields.io/npm/v/@surendranb/google-analytics-mcp.svg?style=flat-square&color=red)](https://www.npmjs.com/package/@surendranb/google-analytics-mcp)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)](LICENSE)

---

## ⚡ How It Works (Zero-Friction Architecture)

This MCP server supports **two operating modes**:

### Mode 1: 1-Click Zero-Config Login (Recommended for 95% of Users)
**No GCP setup, no JSON files, no environment variables.**

```bash
# Run directly in any MCP client:
uvx google-analytics-mcp
```

1. **First Tool Call**: When your AI agent calls any GA4 tool, your default browser opens to `https://ga4.builditwithai.xyz`.
2. **Google Approval**: You sign in with your Google account and grant read-only GA4 access.
3. **Automated Handshake**: A local ephemeral loopback listener captures the session token, writes `~/.config/ga4-mcp/session.json`, and shuts down.
4. **Instant Execution**: The server auto-discovers all GA4 properties you have access to, and the AI agent immediately answers your question in the same turn.

---

### Mode 2: Service Account Keys (For CI/CD, Enterprise & Offline Teams)
For headless environments or enterprise deployments:

1. Create a Google Cloud Service Account with **Viewer** role in *Google Analytics Admin → Property Access Management*.
2. Download the `.json` key and point `GOOGLE_APPLICATION_CREDENTIALS` to it:
   ```bash
   export GA4_PROPERTY_ID="123456789"
   export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service_account.json"
   ```
3. Or drop multiple keys into `~/.config/ga4-mcp/credentials/` for automatic multi-account indexing.

---

## 🔒 Privacy & Security Guarantees

- **Zero Analytics Data Retention**: All GA4 report queries execute directly between your machine and Google Analytics. BuildItWithAI servers never see, store, or log your report rows.
- **Read-Only Scope**: The server requests `https://www.googleapis.com/auth/analytics.readonly`. It is mathematically impossible for the server or AI agent to modify or delete GA4 configurations or data.
- **Encrypted Session Storage**: Cloudflare Edge Gateway encrypts OAuth refresh tokens in Cloudflare D1 with AES-GCM-256.

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

### C. Multi-Site Client Config (Optional Static Aliases)
```json
{
  "mcpServers": {
    "google-analytics": {
      "command": "uvx",
      "args": ["google-analytics-mcp"],
      "env": {
        "GA4_SITES": "{\"default_site\":\"blog\",\"sites\":{\"blog\":{\"name\":\"Personal Blog\",\"property_id\":\"111111111\"},\"store\":{\"name\":\"E-Commerce Shop\",\"property_id\":\"222222222\"}}}"
      }
    }
  }
}
```

---

## 🛠️ Tools & Capabilities

| Tool Name | Parameters | Description |
|---|---|---|
| `list_properties` | *(none)* | Discovers and catalogs all accessible GA4 properties and accounts across all credentials. |
| `get_ga4_data` | `dimensions`, `metrics`, `date_range_start`, `date_range_end`, `dimension_filter`, `limit`, `property` | Runs multi-dimensional GA4 reports with server-side totals, smart sorting, and property routing. |
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
uv run python tests/test_auth_handshake.py
uv run python tests/test_gateway_client.py
uv run python tests/test_discovery.py
uv run python tests/test_sites_registry.py
uv run python tests/test_schema_isolation.py
uv run python tests/test_multisite_mcp.py
uv run python tests/test_aggregation.py
uv run python tests/test_mcp_connection.py
uv run python tests/test_v2_inline_recovery.py
uv run python tests/test_v2_setup_recovery.py
uv run python tests/test_v2_telemetry.py
```
