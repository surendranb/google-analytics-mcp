<!-- mcp-name: io.github.surendranb/google-analytics-mcp -->
<p align="center">
  <img src="logo.png" alt="Google Analytics MCP Logo" width="120" />
</p>

# Google Analytics 4 (GA4) MCP Server 📊

> **Model Context Protocol (MCP) server for Google Analytics 4: real-time query exploration, schema discovery, metric aggregation, and audience insights for AI agents.**

[![CI](https://github.com/surendranb/google-analytics-mcp/actions/workflows/package-checks.yml/badge.svg)](https://github.com/surendranb/google-analytics-mcp/actions)
[![PyPI version](https://img.shields.io/pypi/v/google-analytics-mcp.svg?style=flat-square&color=blue)](https://pypi.org/project/google-analytics-mcp/)
[![npm version](https://img.shields.io/npm/v/@surendranb/google-analytics-mcp.svg?style=flat-square&color=red)](https://www.npmjs.com/package/@surendranb/google-analytics-mcp)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/surendranb/google-analytics-mcp/badge)](https://scorecard.dev/viewer/?site=github.com/surendranb/google-analytics-mcp)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)](LICENSE)

🌐 **Live Documentation & Web Portal**: [https://ga4mcp.com/](https://ga4mcp.com/)

---

## ⚡ Quickstart

```bash
# 1-Line Universal Installer (Auto-configures Claude Desktop, Cursor, Claude Code, Antigravity, VS Code, Zed, Windsurf)
curl -fsSL "https://ga4mcp.com/install" | bash

# Or run directly via your preferred runtime:
uvx google-analytics-mcp
uvx --from google-analytics-mcp ga4-mcp-server
python -m ga4_mcp
npx -y @surendranb/google-analytics-mcp
```

---

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

### C. Claude Desktop (`claude_desktop_config.json`)
```json
{
  "mcpServers": {
    "google-analytics": {
      "command": "uvx",
      "args": ["google-analytics-mcp"],
      "env": {
        "GA4_PROPERTY_ID": "your_ga4_property_id",
        "GOOGLE_APPLICATION_CREDENTIALS": "/path/to/service_account.json"
      }
    }
  }
}
```

### D. VS Code (Cline / Roo Code / Continue)
```json
{
  "mcpServers": {
    "google-analytics": {
      "command": "npx",
      "args": ["-y", "@surendranb/google-analytics-mcp"]
    }
  }
}
```

---

## 🛠️ Tools & Capabilities

| Tool Name | Parameters | Description | Return Type |
|---|---|---|---|
| `get_ga4_data` | `dimensions` (list), `metrics` (list), `date_range_start` (str), `date_range_end` (str), `dimension_filter` (dict), `limit` (int), `estimate_only` (bool), `proceed_with_large_dataset` (bool), `enable_aggregation` (bool), `intent` (str) — all optional | Runs multi-dimensional GA4 reports with automated metric totals and server-side aggregation. | `JSON / Markdown` |
| `list_properties` | `account_id` (str, optional) | Lists GA4 properties. When `GA4_PROPERTY_ID` is set, returns that property. | `JSON` |
| `search_schema` | `keyword` (str, required) | Ranks dimensions and metrics by relevance for a keyword (up to 10). Use before pulling data. | `JSON` |
| `get_property_schema` | *(none)* | Returns the full dimension and metric schema for the configured property (large; prefer `search_schema`). | `JSON` |
| `list_dimension_categories` | *(none)* | Lists dimension categories with counts. First step of category browsing. | `JSON` |
| `list_metric_categories` | *(none)* | Lists metric categories with counts. First step of category browsing. | `JSON` |
| `get_dimensions_by_category` | `category` (str, required) | Returns all dimensions in a category with API names and descriptions. | `JSON` |
| `get_metrics_by_category` | `category` (str, required) | Returns all metrics in a category with API names and descriptions. | `JSON` |
| `search_skills` | `query` (str, required) | Fetches analytical recipes and how-to guides (traffic diagnosis, attribution, ecommerce, AI referrals, bot detection). | `Markdown` |
| `get_troubleshooting_guide` | `topic` (str, required: `setup` \| `iam` \| `schema`) | Returns an in-server troubleshooting guide for setup, IAM/403, or schema errors. | `Markdown` |
| `setup_ga4_access` | *(none)* | Interactively fixes a broken setup (property ID, credentials, access) and re-initializes without a restart. | `Markdown` |
| `check_for_updates` | *(none)* | Checks PyPI for a newer release and returns upgrade instructions. | `JSON` |

---

## 🧠 Dynamic Skills & Guided Playbooks

This server ships with built-in analytical recipes that load dynamically from GitHub:
- `traffic-diagnosis`: Step-by-step root cause analysis for sudden traffic drops.
- `channel-acquisition`: Best-practice channel grouping and attribution modeling.
- `ecommerce-analysis`: Revenue, item purchase rate, and conversion funnel analysis.
- `ai-referral-analysis`: Tracks and isolates referral traffic from ChatGPT, Claude, Perplexity, and Gemini.

---

## 🔒 Telemetry & Privacy

This package collects anonymous, non-PII diagnostic telemetry (command executions, latency, error codes) to improve tool reliability. No queries, user credentials, personal data, source code, or environment variables are ever collected or stored.

You can opt out anytime by setting either of the following environment variables:
```bash
export DO_NOT_TRACK=1
# or
export MCP_TELEMETRY_OPT_OUT=1
```

---

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.
