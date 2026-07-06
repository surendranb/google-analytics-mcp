<p align="center">
  <img src="logo.png" alt="Google Analytics MCP Logo" width="120" />

# Google Analytics 4 MCP Server

`mcp-name: io.github.surendranb/google-analytics-mcp`

[![PyPI version](https://badge.fury.io/py/google-analytics-mcp.svg)](https://badge.fury.io/py/google-analytics-mcp)
[![npm version](https://img.shields.io/npm/v/google-analytics-mcp.svg?color=cb3837)](https://www.npmjs.com/package/google-analytics-mcp)
[![PyPI Downloads](https://static.pepy.tech/badge/google-analytics-mcp)](https://pepy.tech/projects/google-analytics-mcp)
[![GitHub stars](https://img.shields.io/github/stars/surendranb/google-analytics-mcp?style=social)](https://github.com/surendranb/google-analytics-mcp/stargazers)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

Connect Google Analytics 4 data directly to AI agents, analyst copilots, and MCP runtimes across **Claude, ChatGPT, Gemini, Cursor, VS Code, and OpenClaw**. Gives models analysis-ready GA4 access with live schema discovery, metric auto-aliasing, server-side aggregation, and autonomous self-healing defenses.

🌐 **Website & Documentation:** [https://ga4mcp.com](https://ga4mcp.com)  
🔗 **Sister Project:** [Google Search Console MCP](https://github.com/surendranb/google-search-console-mcp)

</p>

---

## ⚡ Quickstart — 1-Line Installations

### 1. Universal 1-Line Installer (Recommended)

Auto-detects your system, configures **Gemini CLI, Claude Desktop, Cursor, and VS Code** automatically in 1 command:

```bash
curl -fsSL https://ga4.builditwithai.xyz | bash
```

### 2. Homebrew (macOS & Linux)

```bash
brew tap surendranb/tap
brew install google-analytics-mcp
```

### 3. NPX / Node.js (Claude Code, Cursor, VS Code, Windsurf)

Add to your MCP configuration file (`claude_desktop_config.json` or `.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "ga4-analytics": {
      "command": "npx",
      "args": ["-y", "google-analytics-mcp"],
      "env": {
        "GOOGLE_APPLICATION_CREDENTIALS": "/absolute/path/to/service-account-key.json",
        "GA4_PROPERTY_ID": "123456789"
      }
    }
  }
}
```

### 2. Gemini CLI Extension

Install directly into Google Gemini CLI with a single command:

```bash
gemini extensions install github.com/surendranb/google-analytics-mcp
```

### 3. Python `uvx` & Explicit `python -m ga4_mcp`

```json
{
  "mcpServers": {
    "ga4-analytics": {
      "command": "uvx",
      "args": ["--from", "google-analytics-mcp", "ga4-mcp-server"],
      "env": {
        "GOOGLE_APPLICATION_CREDENTIALS": "/absolute/path/to/service-account-key.json",
        "GA4_PROPERTY_ID": "123456789"
      }
    }
  }
}
```

Or run directly via `ga4-mcp-server` / `python -m ga4_mcp`:

```json
{
  "mcpServers": {
    "ga4-analytics": {
      "command": "python",
      "args": ["-m", "ga4_mcp"],
      "env": {
        "GOOGLE_APPLICATION_CREDENTIALS": "/absolute/path/to/service-account-key.json",
        "GA4_PROPERTY_ID": "123456789"
      }
    }
  }
}
```

---

## 🧠 Why AI Agents & Marketers Prefer This Server

- **Autonomous Self-Healing:** System directives automatically intercept schema hallucinations (like guessing legacy metric names or incorrect filter nesting) and guide models to self-correct via `get_troubleshooting_guide`.
- **Metric Auto-Aliasing:** Automatically maps legacy or common LLM requests like `'conversions'` → `'keyEvents'`, preventing unnecessary query failures.
- **Server-Side Aggregation:** Computes property totals dynamically for non-time-series queries, so LLMs spend time answering business questions rather than parsing raw rows.
- **Data Volume Protection:** Runs quick row-count estimates before executing large queries (>2,500 rows) to prevent crashing model context windows.
- **Multi-Platform Support:** Native packages and manifests for PyPI, npm, Gemini CLI, Smithery, OpenClaw, and OpenAPI REST actions.

---

## 🔑 Setup & Credentials Guide

### 1. Create a Google Cloud Service Account
1. Open the [Google Cloud Console](https://console.cloud.google.com/).
2. Enable the **Google Analytics Data API**.
3. Under **APIs & Services → Credentials**, create a **Service Account**.
4. Create a **JSON Key** and save it locally on your machine (e.g. `/Users/yourname/keys/ga4-key.json`).

### 2. Grant Viewer Access in GA4
1. Open [Google Analytics](https://analytics.google.com/).
2. Select your GA4 Property → Open **Admin** (gear icon) → **Property Access Management**.
3. Add the Service Account email (found inside the JSON key as `client_email`) with the **Viewer** role.

### 3. Find Your GA4 Property ID
1. In Google Analytics Admin → **Property Details**.
2. Copy the numeric **Property ID** (e.g., `123456789`).

---

## 🛠️ Available Tools

| Tool Name | Purpose |
|-----------|---------|
| `get_ga4_data` | Execute GA4 queries with dimensions, metrics, date ranges, and optional filters. |
| `search_schema` | Keyword search across 200+ GA4 dimension and metric API names. |
| `get_property_schema` | Inspect all available dimensions and metrics for your specific property. |
| `list_metric_categories` | Browse metric categories (User, Session, Revenue, Event). |
| `list_dimension_categories` | Browse dimension categories (Geography, Traffic Source, Device). |
| `get_troubleshooting_guide` | Self-healing guide for IAM permissions, setup, and filter syntax. |

---

## 🔒 Telemetry & Privacy

GA4 MCP collects anonymous usage telemetry to help maintainers track release adoption, improve error defenses, and optimize latency. A one-time notice is printed on first run, before anything is sent.

**What is collected** (events: `server_first_install`, `mcp_started`, `tool_executed`, `resource_read`):
- A random installation UUID (stored in `~/.ga4_mcp/` — delete the folder to reset it) and a per-process session UUID. Never hardware-derived.
- Package version, OS, CPU architecture, Python version, install channel (uvx/pip/brew), shell and terminal names, timezone offset.
- Which MCP client is connecting (e.g. `claude_code`, `cursor` — from the MCP handshake or env-var *presence*; env values are never read).
- Tool name, latency, success/error status, error category, row counts, and query shape (number of dimensions/metrics, whether filters were used).

**What is never collected**: file paths and contents, environment variable values, credentials, IP addresses stored, GA4 property IDs, dimension/metric *values*, report data, prompts, usernames, or emails. Every outgoing string is additionally passed through a PII scrubber that redacts paths, emails, URLs, and keys as defense in depth.

**Opt out** with any of: `DISABLE_TELEMETRY=1`, `GA_MCP_TELEMETRY=false`, `DO_NOT_TRACK=1`, or `NO_TELEMETRY=1`.

---

## 📄 License & Author

Developed by **Surendran B** under the **Apache License 2.0**.  
Website: [https://ga4mcp.com](https://ga4mcp.com)
