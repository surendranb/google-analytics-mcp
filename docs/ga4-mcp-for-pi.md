# GA4 MCP for Pi: Setup, Skills and First Query


I query GA4 from inside Pi with the same server I run in OpenCode. GA4 MCP for Pi gives you that: one entry in the agent-dir `mcp.json`, your property ID plus credentials in `env`, then plain questions answered from your own property schema.

## Proof strip

- Site lists **v2.11.4**, **MIT**, **15 skills**, **11 tools** (verified 2026-10-09 at https://ga4mcp.com/).
- One-line installer: `https://ga4.builditwithai.xyz/install`. Runtimes: `uvx google-analytics-mcp` and `npx -y @surendranb/google-analytics-mcp`.
- Pi path verified today: Pi reads `<agent-dir>/mcp.json` with `mcpServers` command/args; stdio, Streamable HTTP, SSE shapes; `/codemcp` manages servers (pi-codemcp docs).
- Native note verified today: Pi is a minimal terminal harness with MCP server integration; `pi-mcp` bridges configured stdio/HTTP servers into Pi tools.
- Repo `pyproject.toml` reads 2.11.5 today, ahead of site 2.11.4; I quote the site label.
- Read-only, local stdio. Telemetry off with `DISABLE_TELEMETRY=1` or `DO_NOT_TRACK=1`.

## Configuring Pi to launch the server

Prerequisites: numeric `GA4_PROPERTY_ID` (Admin, Property details, not the `G-` ID), plus a service-account JSON path or `gcloud auth application-default login`. Keep the JSON path absolute.

1. Open your agent-dir `mcp.json` and add:
```json
{
  "mcpServers": {
    "google-analytics": {
      "command": "uvx",
      "args": ["google-analytics-mcp"],
      "env": {
        "GA4_PROPERTY_ID": "123456789",
        "GOOGLE_APPLICATION_CREDENTIALS": "/absolute/path/to/key.json"
      }
    }
  }
}
```
A root-level server map without the `mcpServers` wrapper is also accepted; I show the wrapped shape because it ports cleanly from Claude configs.
2. For stdio servers, Pi passes a small safe base plus allow-listed vars (`MY_PI_CHILD_ENV_ALLOWLIST` / `MY_PI_MCP_ENV_ALLOWLIST`) plus explicit `env` above. Prefer explicit `env` for the two GA4 values.
3. Open `/codemcp` in Pi to confirm the server, or restart Pi and check the tool list.
4. Verify by asking: "List my GA4 properties." You have succeeded when `list_properties` returns rows with no setup error.

## Skills worth loading first

| Skill slug | What you use it for in Pi |
|---|---|
| `traffic-diagnosis` | You saw sessions move and want the ordered checks |
| `common-metric-names` | Your field name failed and you want the working GA4 name |
| `channel-acquisition` | You want sessions split by source, medium, channel group |
| `compatible-combinations` | Your dimensions and metrics returned a 400 incompatibility |
| `date-ranges` | You compare two periods and want the two-query pattern |

Full set of 15 at https://ga4mcp.com/skills/, loaded with `search_skills("<slug>")`.

## Running your first query

Ask: "What were my top channels last week?"

Your agent should call:
```
get_ga4_data(
  dimensions=["sessionDefaultChannelGroup"],
  metrics=["sessions"],
  date_range_start="7daysAgo",
  date_range_end="yesterday",
  intent="which channels drove sessions last week"
)
```

Read the period figure from `totals`. GA4 computes that block; hand sums drift and I stopped doing them.

## Fixing the three errors you will hit

1. **Server missing after edit.** Symptom: `/codemcp` omits google-analytics. Fix: confirm the file is the agent-dir `mcp.json` Pi reads, valid JSON, then restart Pi and trust the project where prompted.
2. **Setup error on first call.** Symptom: missing property or credentials. Fix: confirm both `env` values with an absolute key path and allow-list coverage; for ADC expiry run `gcloud auth application-default login`. `setup_ga4_access` recovers mid-session where prompts are supported.
3. **Invalid dimension, metric, or filter.** Symptom: 400 naming error. Fix: run `search_schema("<keyword>")`, load `common-metric-names` plus `filter-structures`, retry. Offline guide: `get_troubleshooting_guide(topic="schema")`.

## FAQ

**Does GA4 MCP for Pi use mcp.json?**
Yes. Agent-dir `mcp.json` with the `mcpServers` block above, verified in pi-codemcp docs today.

**Do I need a Pi extension for MCP?**
No for the server entry. `pi-mcp` and `pi-codemcp` add discovery and code-mode surfaces; the block above is the wiring either way.

**Does the installer cover Pi?**
The site auto-configure list does not name Pi. I show the hand block because it is exact and auditable.

**Why does the agent guess wrong field names?**
Training predates GA4 renames (UA sunset 2023-07-01; conversions renamed to key events 2024-05-06). The `ua-to-ga4` skill maps each old name.

**Is usage read-only and private?**
Yes. Tools read metadata and reports; they change nothing. Traffic runs from your machine to the GA4 Data API. Anonymous counts stop with `DISABLE_TELEMETRY=1`.

**Why does the repo read 2.11.5 when the site says 2.11.4?**
Main moved ahead of the site label at fetch today. I quote 2.11.4 for installs and state the gap here.

## Freshness and machine links

Verified 2026-10-09 against https://ga4mcp.com/ (v2.11.4), https://ga4mcp.com/setup/, https://ga4mcp.com/skills/, Pi package plus pi-codemcp MCP docs, and repo raw `pyproject.toml` 2.11.5.

Version gap (2026-10-09): repo `pyproject.toml` reads 2.11.5 [source: repo pyproject.toml, verified this run] while the live site labels v2.11.4 [source: https://ga4mcp.com/ fetch 2026-10-09]; installs on this page quote the site label.

Machine: https://ga4mcp.com/llms.txt, https://ga4mcp.com/data/tools.json, https://ga4mcp.com/data/skills.json.

## Breadcrumb

Hub (/ga4-mcp-for-every-harness/) / GA4 MCP for Pi (you are here).
