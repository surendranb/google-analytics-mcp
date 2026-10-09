# GA4 Plugin for Claude Code


I keep two ways into Claude Code: the plugin bundle for a managed install and the MCP entry for direct control. GA4 plugin for Claude Code covers both, with the manifest version stated so you quote it right.

## Proof strip

- Plugin manifest `.claude-plugin/plugin.json` **v2.11.1** (repo `surendranb/google-analytics-mcp`, raw fetch 2026-10-09; description names real-time reporting, schema discovery, metric aggregation, audience insights).
- Manifest `mcpServers.google-analytics-mcp` runs `uvx` args `["google-analytics-mcp"]`.
- MCP fallback verified: `claude mcp add google-analytics -- uvx google-analytics-mcp` (repo README + site install block).
- Site lists server **v2.11.4**, **MIT**, **15 skills**, **11 tools** (https://ga4mcp.com/ today).
- Read-only, local stdio. Telemetry off with `DISABLE_TELEMETRY=1` or `DO_NOT_TRACK=1`.

## Installing the Claude Code plugin

Prerequisites: Claude Code CLI on PATH, `uvx` on PATH, numeric `GA4_PROPERTY_ID`, absolute service-account JSON path.

1. Install the plugin bundle from the repo manifest (`.claude-plugin/plugin.json` v2.11.1) through your Code plugin flow.
2. Set the server env for the plugin process:
```bash
export GA4_PROPERTY_ID="123456789"
export GOOGLE_APPLICATION_CREDENTIALS="/absolute/path/to/key.json"
```
3. When you prefer the direct MCP route instead, add:
```bash
claude mcp add google-analytics -- uvx google-analytics-mcp
```
4. Verify inside Code by asking: "List my GA4 properties." You have succeeded when `list_properties` returns rows and `get_ga4_data` runs without a setup error.

## Skills worth loading first

| Skill slug | What you use it for with this plugin |
|---|---|
| `traffic-diagnosis` | You ask why sessions moved |
| `channel-acquisition` | You split by source, medium, channel group |
| `common-metric-names` | Code's model guesses a UA name |
| `date-ranges` | You compare this week to last with two queries |
| `bot-traffic-detection` | You strip scrapers before reading a drop |

Full set of 15 at https://ga4mcp.com/skills/, loaded with `search_skills("<slug>")`.

## Running your first query

Ask: "What were my top channels last week?"

The plugin should route to:
```
get_ga4_data(
  dimensions=["sessionDefaultChannelGroup"],
  metrics=["sessions"],
  date_range_start="7daysAgo",
  date_range_end="yesterday",
  intent="which channels drove sessions last week"
)
```

Read `totals` for the period figure. I rely on that block because GA4 computes it; Code's model sums drift under caps.

## Fixing the three errors you will hit

1. **Plugin shows installed but GA4 tools missing.** Symptom: no `get_ga4_data` in Code. Fix: prove `uvx google-analytics-mcp` launches in a terminal, restart Code, re-enable the plugin.
2. **Setup error on first query.** Symptom: missing property or credentials. Fix: re-export both env values with an absolute key path in Code's launching shell. `setup_ga4_access` recovers where prompts are supported.
3. **400 on names or filters.** Symptom: invalid dimension, metric, or filter. Fix: `search_schema("<keyword>")`, load `common-metric-names` and `filter-structures`, retry. Offline: `get_troubleshooting_guide(topic="schema")`.

## FAQ

**What is the GA4 plugin for Claude Code version?**
v2.11.1 at `.claude-plugin/plugin.json`, raw-fetched today. Quote path plus version together.

**Does the Claude Code plugin replace `claude mcp add`?**
No. The plugin bundles the server for Code; the add command wires the server directly. Both end at the same `uvx google-analytics-mcp` runtime.

**What command does the plugin manifest run?**
`uvx` with args `["google-analytics-mcp"]` under `mcpServers.google-analytics-mcp`, per the manifest.

**Where do I set GA4_PROPERTY_ID for this plugin?**
In the plugin host's environment, as above. The ID is numeric; the `G-` measurement ID won't work.

**Is the Claude Code plugin read-only?**
Yes. It exposes the same read-only report and metadata tools. Nothing writes GA4 configuration.

**How do I stop telemetry from this plugin?**
Set `DISABLE_TELEMETRY=1` or `DO_NOT_TRACK=1` for the Code process. Sends stop and the local ID file stops.

## Freshness and machine links

Verified 2026-10-09 against raw `.claude-plugin/plugin.json` v2.11.1, repo README Code block, https://ga4mcp.com/ (v2.11.4), https://ga4mcp.com/setup/, https://ga4mcp.com/skills/.

Version gap (2026-10-09): repo `pyproject.toml` reads 2.11.5 [source: repo pyproject.toml, verified this run] while the live site labels v2.11.4 [source: https://ga4mcp.com/ fetch 2026-10-09]; installs on this page quote the site label.

Machine: https://ga4mcp.com/llms.txt, https://ga4mcp.com/data/tools.json, https://ga4mcp.com/data/skills.json.

## Breadcrumb

Hub (/ga4-mcp-for-every-harness/) / Claude umbrella (/ga4-mcp-for-claude/) / GA4 Plugin for Claude Code (you are here) / Plugins hub (/ga4-plugins/).
