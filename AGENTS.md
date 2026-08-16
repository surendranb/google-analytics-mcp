# AGENTS.md — Agent Operational Manual

> **Canonical context and operating procedures for AI agents (Claude Code, Cursor, Codex, Gemini, Antigravity, OpenCode, Aider) operating on or integrating `google-analytics-mcp`.**

---

## 1. System Identity & Mission

- **Repository**: `surendranb/google-analytics-mcp`
- **Package Name**: `google-analytics-mcp` (PyPI) / `google-analytics-mcp` (NPM)
- **Live Portal**: [https://ga4.builditwithai.xyz](https://ga4.builditwithai.xyz)
- **Purpose**: Google Analytics 4 MCP server for real-time reporting, schema discovery, metric aggregation, and audience insights.

---

## 2. Quickstart & Invocation for Agents

Agents integrating or executing this server should use stdio transport via either runtime:

```bash
# Python runtime (FastMCP / stdio)
uvx google-analytics-mcp

# Universal 1-line auto-installer
curl -fsSL "https://ga4.builditwithai.xyz/install" | bash
```

### Required Environment Variables
- `GA4_PROPERTY_ID`: Numeric GA4 property ID (e.g. 123456789) (Required)
- `GOOGLE_APPLICATION_CREDENTIALS`: Path to service account JSON key file (Required)


---

## 3. Tool Reference & Capabilities

| Tool | Capability Summary |
|---|---|
| `get_ga4_data` | Runs multi-dimensional GA4 reports with server-side totals and aggregation. |
| `list_accounts` | Lists accessible GA4 accounts and permission levels. |
| `list_properties` | Lists GA4 properties for an account. |
| `get_property_metadata` | Fetches complete dimension and metric schemas. |
| `run_realtime_report` | Queries active users and live events from the last 30 minutes. |
| `search_skills` | Searches built-in GA4 analytical playbooks. |
| `skill_read` | Loads analytical guides dynamically from GitHub. |
| `skills_list` | Lists all available GA4 analytical skills. |

---

## 4. Agent Working Laws (Operational Rules)

When contributing code, diagnosing bugs, or modifying this repository, all visiting agents must adhere strictly to these rules:

1. **Truth Over Guessing**: Never fabricate responses, schema types, or error reasons. Run native verification scripts before asserting completion.
2. **Shortest Working Diff (Lazy Senior Dev)**: Do not introduce unrequested abstractions, extra dependencies, or architectural bloat. Standard library and native platform features first.
3. **Preserve Schema Stability**: Never remove or rename existing MCP tool parameters without strict backwards-compatibility layers.
4. **Strict Telemetry Boundaries**: Diagnostic telemetry is non-PII and strictly opt-out. Never log user queries, credentials, file contents, or environment variables. Honor `DO_NOT_TRACK=1` and `MCP_TELEMETRY_OPT_OUT=1`.
5. **No Direct Main Commits**: Always create a feature or fix branch before modifying code.

---

## 5. Verification & Test Protocol

Before marking any task as complete in this repository, run the test suite:

```bash
# Run automated verification suite
uv run pytest -v || python3 -m unittest
```

---

## 6. Plugin & Marketplace Discovery Pointers

- **Claude Code**: `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`
- **Gemini CLI / Antigravity**: `gemini-extension.json`
- **Smithery.ai**: `smithery.yaml`
- **Official MCP Registry & Glama**: `server.json`
- **OpenAI / ChatGPT Actions**: `.well-known/ai-plugin.json`
- **AI Search Crawlers (GEO)**: `llms.txt`
