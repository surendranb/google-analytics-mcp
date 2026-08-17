# Google Analytics 4 (GA4) MCP Server 📊

> **Model Context Protocol (MCP) server for Google Analytics 4: real-time query exploration, schema discovery, metric aggregation, and audience insights for AI agents.**

[![CI](https://github.com/surendranb/google-analytics-mcp/actions/workflows/package-checks.yml/badge.svg)](https://github.com/surendranb/google-analytics-mcp/actions)
[![PyPI version](https://img.shields.io/pypi/v/google-analytics-mcp.svg?style=flat-square&color=blue)](https://pypi.org/project/google-analytics-mcp/)
[![npm version](https://img.shields.io/npm/v/google-analytics-mcp.svg?style=flat-square&color=red)](https://www.npmjs.com/package/google-analytics-mcp)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/surendranb/google-analytics-mcp/badge)](https://scorecard.dev/viewer/?site=github.com/surendranb/google-analytics-mcp)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)](LICENSE)

🌐 **Live Documentation & Web Portal**: [https://ga4.builditwithai.xyz](https://ga4.builditwithai.xyz)

---

## ⚡ Quickstart

```bash
# 1-Line Universal Installer (Auto-configures Claude Code, Cursor, Claude Desktop & Antigravity)
curl -fsSL "https://ga4.builditwithai.xyz/install" | bash

# Or run directly via your preferred runtime:
uvx google-analytics-mcp
npx -y google-analytics-mcp
```

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
      "args": ["-y", "google-analytics-mcp"]
    }
  }
}
```

---

## 🛠️ Tools & Capabilities

| Tool Name | Parameters | Description | Return Type |
|---|---|---|---|
| `get_ga4_data` | `dimensions` (list), `metrics` (list), `date_ranges` (list), `limit` (int) | Runs multi-dimensional GA4 reports with automated metric totals and server-side aggregation. | `JSON / Markdown` |
| `list_accounts` | *(none)* | Lists all accessible Google Analytics accounts and permission levels. | `JSON` |
| `list_properties` | `account_id` (optional) | Lists all GA4 properties associated with an account. | `JSON` |
| `get_property_metadata` | `property_id` (optional) | Fetches complete dimension and metric schemas, custom definitions, and compatibility rules. | `JSON` |
| `run_realtime_report` | `metrics` (list), `dimensions` (list) | Queries real-time active users and event counts from the last 30 minutes. | `JSON` |
| `search_skills` | `query` (string) | Searches built-in GA4 analytical playbooks (e-commerce, channel attribution, bot filtering). | `Markdown` |
| `skill_read` | `skill_name` (string) | Dynamically loads procedural skills and analytical guides from GitHub. | `Markdown` |
| `skills_list` | *(none)* | Lists all available live GA4 analytical skills. | `JSON` |

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
