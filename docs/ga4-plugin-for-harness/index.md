# GA4 Plugin for Harness: OpenClaw and Any Generic Runner


I wanted one plugin file I could point any harness at without rewriting per client. GA4 plugin for harness is that pattern: the OpenClaw manifest at its exact version, with the stdio shape any generic runner reuses.

## Proof strip

- Manifest `plugins/openclaw/plugin.json` **v2.4.1** (repo `surendranb/google-analytics-mcp`, raw fetch 2026-10-09).
- Entry `ga4-mcp-server`, transport `stdio`, env `GOOGLE_APPLICATION_CREDENTIALS` + `GA4_PROPERTY_ID`, tools `get_ga4_data`, `search_schema`, `get_property_schema`, `list_metric_categories`, `list_dimension_categories`.
- Server base: site **v2.11.4**, **MIT**, **15 skills**, **11 tools** (https://ga4mcp.com/ today).
- Runtimes: `uvx google-analytics-mcp`, `npx -y @surendranb/google-analytics-mcp`, installer `https://ga4.builditwithai.xyz/install`.
- Read-only. Telemetry off with `DISABLE_TELEMETRY=1` or `DO_NOT_TRACK=1`.

## Installing the generic harness plugin

Prerequisites: a runner that loads a plugin manifest and launches local stdio servers, numeric `GA4_PROPERTY_ID`, absolute service-account JSON path.

1. Point your runner at the manifest:
```
plugins/openclaw/plugin.json  (v2.4.1)
```
2. Confirm the manifest's server entry resolves to a launchable command in your environment:
```bash
uvx google-analytics-mcp
```
`ga4-mcp-server` is the entry name in the manifest; the launch command above is the runtime I verified.
3. Export env for the runner process:
```bash
export GA4_PROPERTY_ID="123456789"
export GOOGLE_APPLICATION_CREDENTIALS="/absolute/path/to/key.json"
```
4. Verify by asking: "List my GA4 properties." You have succeeded when `list_properties` returns rows.

For runners without a plugin host, skip the manifest and register the same command plus env as a plain stdio MCP server.

## Skills worth loading first

| Skill slug | What you use it for on a generic runner |
|---|---|
| `traffic-diagnosis` | Ordered checks for a move in sessions |
| `compatible-combinations` | The manifest's five tools still enforce 400 pairing rules |
| `filter-structures` | Generic runners mistype `dimensionFilter` most |
| `channel-acquisition` | Source, medium, channel-group splits |
| `ai-referral-analysis` | Splitting assistant referrals from search |

Full set of 15 at https://ga4mcp.com/skills/, loaded with `search_skills("<slug>")`.

## Running your first query

Ask: "What were my top channels last week?"

The runner should call:
```
get_ga4_data(
  dimensions=["sessionDefaultChannelGroup"],
  metrics=["sessions"],
  date_range_start="7daysAgo",
  date_range_end="yesterday",
  intent="which channels drove sessions last week"
)
```

Read `totals`. I treat that block as the period figure because GA4 computes it; summing rows by hand breaks under the 2,500-row guard.

## Fixing the three errors you will hit

1. **Runner can't resolve the entry.** Symptom: `ga4-mcp-server` not found. Fix: confirm the `uvx` runtime above launches, then map entry to command in your runner's plugin config.
2. **Setup error on first tool call.** Symptom: missing property or key. Fix: re-export both env values with an absolute key path, restart the runner. Mirror: https://ga4mcp.com/setup/.
3. **400 on names, pairs, or filters.** Symptom: invalid field or incompatible combo. Fix: `search_schema("<keyword>")`, load `common-metric-names`, `compatible-combinations`, `filter-structures`. Offline: `get_troubleshooting_guide(topic="schema")`.

## FAQ

**What is the GA4 plugin for harness version?**
v2.4.1 at `plugins/openclaw/plugin.json`, raw-fetched today. It is the generic pattern page even though the path names OpenClaw.

**Does this plugin work outside OpenClaw?**
Yes. Transport is stdio with two env keys, so any runner that launches local MCP servers can reuse the shape. The manifest lists its five tools; the full server exposes 11.

**Why does the manifest list five tools when the server has eleven?**
The manifest scopes the harness to discovery plus reporting (`get_ga4_data`, `search_schema`, property schema, category browsers). I quote the manifest list for the plugin and the 11-count for the server.

**What command does the harness entry run?**
Entry `ga4-mcp-server` over stdio. I verified `uvx google-analytics-mcp` as the launch runtime; keep entry and command distinct when you wire a new runner.

**Is harness usage read-only?**
Yes. Report and metadata reads only. No GA4 configuration writes.

**How do I stop telemetry on a shared runner?**
Set `DISABLE_TELEMETRY=1` or `DO_NOT_TRACK=1` in the runner's environment. No queries or credentials leave in telemetry either way.

## Freshness and machine links

Verified 2026-10-09 against raw `plugins/openclaw/plugin.json` v2.4.1, https://ga4mcp.com/ (v2.11.4), https://ga4mcp.com/setup/, https://ga4mcp.com/skills/.

Version gap (2026-10-09): repo `pyproject.toml` reads 2.11.5 [source: repo pyproject.toml, verified this run] while the live site labels v2.11.4 [source: https://ga4mcp.com/ fetch 2026-10-09]; installs on this page quote the site label.

Machine: https://ga4mcp.com/llms.txt, https://ga4mcp.com/data/tools.json, https://ga4mcp.com/data/skills.json.

## Breadcrumb

Hub (/ga4-mcp-for-every-harness/) / Plugins hub (/ga4-plugins/) / GA4 Plugin for Harness (you are here).
