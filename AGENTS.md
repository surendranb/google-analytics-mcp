# AGENTS.md — Codebase Operational Guide for AI Agents

> **Context, architecture, file map, and execution commands for AI coding agents (Claude Code, Cursor, Codex, Gemini, Antigravity, OpenCode, Aider) working on `google-analytics-mcp`.**

---

## 1. Codebase Overview

- **Language & Runtime**: Python 3.10+ (using `mcp` SDK / FastMCP, `google-analytics-data`, `google-analytics-admin`, `httpx`).
- **Package Name**: `google-analytics-mcp` (PyPI) / `google-analytics-mcp` (NPM thin wrapper).
- **Core Function**: Connects LLMs to Google Analytics 4 (Data API v1beta & Admin API v1alpha) with schema discovery, multi-dimensional queries, realtime metrics, and domain-specific analytical playbooks.

---

## 2. Directory & File Map

```
google-analytics-mcp/
├── ga4_mcp/
│   ├── server.py              # FastMCP server definition, tool registrations, signal handling
│   ├── coordinator.py         # Multi-client orchestration, session context, skill tips
│   ├── prompts.py             # Pre-engineered prompts (traffic-diagnosis, explain-drop)
│   ├── resources.py           # Static setup resources and error-recovery guides
│   ├── setup_flow.py          # Interactive credential validation and in-session recovery
│   ├── telemetry.py           # Non-PII diagnostic telemetry gateway (Edge Schema v2)
│   └── tools/
│       ├── reporting.py       # Core get_ga4_data / run_report execution & metric aggregation
│       ├── metadata.py        # Schema discovery, custom dimensions/metrics lookup
│       ├── skills.py          # Dynamic GitHub analytical recipes loader (search_skills)
│       └── troubleshooting.py # Error diagnosis (IAM 403, invalid filters, missing fields)
├── npm/                       # Thin Node.js CLI launcher for npm / npx distribution
│   ├── bin/index.js           # Subprocess wrapper spawning uvx google-analytics-mcp
│   └── package.json           # NPM package metadata
├── tests/                     # Automated test suite
│   ├── test_reporting.py      # Multi-dimensional reporting tests
│   ├── test_telemetry.py      # Telemetry payload & DNT validation tests
│   ├── test_setup_flow.py     # Auth recovery tests
│   └── test_skills.py         # Skills loader tests
├── pyproject.toml             # Python packaging, dependencies, and CLI entrypoint (ga4-mcp-server)
├── smithery.yaml              # Smithery.ai marketplace configuration
├── server.json                # Official MCP registry specification
├── gemini-extension.json      # Google Gemini / Antigravity extension manifest
├── .claude-plugin/            # Claude Code plugin manifests (plugin.json, marketplace.json)
└── .well-known/ai-plugin.json # OpenAI / ChatGPT Actions manifest
```

---

## 3. Environment Variables & Auth

| Variable | Description | Required |
|---|---|---|
| `GA4_PROPERTY_ID` | Numeric GA4 property ID (e.g. `123456789`). | Yes (or passed per tool call) |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to Google Cloud Service Account JSON key file. | Yes (or via ADC / gcloud auth) |
| `DO_NOT_TRACK` / `MCP_TELEMETRY_OPT_OUT` | Set to `1` to disable anonymous telemetry. | Optional |

---

## 4. Development & Testing Commands

```bash
# Install dependencies in editable mode
uv sync || pip install -e ".[dev]"

# Run the MCP server in stdio mode locally
uv run python -m ga4_mcp.server

# Run the test suite
uv run pytest tests/ -v

# Run linting & formatting checks
uv run ruff check .
```

---

## 5. Tool Implementation Invariants & Gotchas

1. **Server-Side Aggregation (`reporting.py`)**:
   - `get_ga4_data` must always compute server-side totals and format date ranges consistently.
   - Do not request incompatible metric/dimension combinations; let `metadata.py` validate schema fields before executing queries.
2. **Setup Recovery & Elicitation (`setup_flow.py`)**:
   - If `GA4_PROPERTY_ID` or `GOOGLE_APPLICATION_CREDENTIALS` is missing, the server prompts the client interactively via MCP elicitation if the client advertises capability, rather than crashing on boot.
3. **Telemetry Boundary (`telemetry.py`)**:
   - Telemetry must remain strictly non-PII (command names, latency, HTTP error codes). Never log property IDs, account numbers, queries, or metric values.
