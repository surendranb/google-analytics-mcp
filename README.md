# Google Analytics 4 (GA4) MCP Server 📊

> **Model Context Protocol (MCP) server for Google Analytics 4: real-time query exploration, schema discovery, metric aggregation, and audience insights for AI agents.**

[![CI](https://github.com/surendranb/google-analytics-mcp/actions/workflows/package-checks.yml/badge.svg)](https://github.com/surendranb/google-analytics-mcp/actions)
[![PyPI version](https://img.shields.io/pypi/v/google-analytics-mcp.svg?style=flat-square&color=blue)](https://pypi.org/project/google-analytics-mcp/)
[![npm version](https://img.shields.io/npm/v/@surendranb/google-analytics-mcp.svg?style=flat-square&color=red)](https://www.npmjs.com/package/@surendranb/google-analytics-mcp)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/surendranb/google-analytics-mcp/badge)](https://scorecard.dev/viewer/?site=github.com/surendranb/google-analytics-mcp)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)](LICENSE)

🌐 **Docs & Web Portal**: [ga4mcp.com](https://ga4mcp.com) — [Setup](https://ga4mcp.com/setup/) · [Filter schema](https://ga4mcp.com/schema/) · [IAM](https://ga4mcp.com/iam/) · [Skills library](https://ga4mcp.com/skills/) · [llms.txt](https://ga4mcp.com/llms.txt) · [llms-full.txt](https://ga4mcp.com/llms-full.txt)

---

## ⚡ Quickstart

```bash
# 1-Line Universal Installer (Auto-configures Claude Desktop, Cursor, Claude Code, Antigravity, VS Code, Zed, Windsurf)
curl -fsSL "https://ga4.builditwithai.xyz/install" | bash

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

11 tools ship in v2.11.4, all annotated read-only. Every page of [ga4mcp.com](https://ga4mcp.com) has a markdown twin (`/setup/index.md`), and the full set is machine-readable at [data/tools.json](https://ga4mcp.com/data/tools.json).

| Tool | Arguments | What it returns |
|---|---|---|
| `get_ga4_data` | `dimensions`, `metrics`, `date_range_start`, `date_range_end`, `dimension_filter`, `limit`, `estimate_only`, `proceed_with_large_dataset`, `enable_aggregation`, `intent` | Report rows plus a `totals` block computed by GA4, with pre-flight schema checks and a row-cap warning above 2,500 rows. |
| `search_schema` | `keyword` | Ranked dimension and metric API names for the property. Run this before typing a field name. |
| `get_property_schema` | *(none)* | Full dimension and metric schema, standard and custom. |
| `list_dimension_categories` | *(none)* | Dimension categories with counts. |
| `list_metric_categories` | *(none)* | Metric categories with counts. |
| `get_dimensions_by_category` | `category` | Every dimension in one category, with descriptions. |
| `get_metrics_by_category` | `category` | Every metric in one category, with descriptions. |
| `list_properties` | `account_id` (optional) | GA4 properties the configured credentials can read. |
| `search_skills` | `query` (slug or keyword; empty returns the index) | One analytical recipe as markdown. |
| `get_troubleshooting_guide` | `topic`: `setup` \| `iam` \| `schema` | The fix path for a boot error, a 403, or a filter-shape error. Works offline. |
| `setup_ga4_access` | *(none)* | Collects a missing property ID or credentials path and reconnects without a client restart. |

Also exposed: resources `docs://setup_guide`, `docs://fix/setup`, `docs://fix/iam`, `docs://fix/schema`, and `skill://<slug>` per recipe.

---

## 🧠 Dynamic Skills & Guided Playbooks

This server ships with built-in analytical recipes that load dynamically from GitHub:
- `traffic-diagnosis`: Step-by-step root cause analysis for sudden traffic drops.
- `channel-acquisition`: Best-practice channel grouping and attribution modeling.
- `ecommerce-analysis`: Revenue, item purchase rate, and conversion funnel analysis.
- `ai-referral-analysis`: Tracks and isolates referral traffic from ChatGPT, Claude, Perplexity, and Gemini.

All 15 are listed at [ga4mcp.com/skills](https://ga4mcp.com/skills/) and indexed at [data/skills.json](https://ga4mcp.com/data/skills.json).

---

## 🔒 Telemetry & Privacy

This package collects anonymous, non-PII diagnostic telemetry (command executions, latency, error codes) to improve tool reliability. No queries, user credentials, personal data, source code, or environment variables are ever collected or stored.

You can opt out anytime by setting either of the following environment variables:
```bash
export DO_NOT_TRACK=1
# or
export DISABLE_TELEMETRY=1
```
`NO_TELEMETRY=1` works too, and so does `GA_MCP_TELEMETRY=false`. When opted out, no event is sent and the local ID file is not created.

---

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.
