# GA4 MCP for OpenClaw: Setup, Skills and First Query


I query GA4 from inside OpenClaw with the same server I run in Claude Code. GA4 MCP for OpenClaw gives you that: one `openclaw mcp add` entry, your property ID plus credentials in `env`, then plain questions answered from your own property schema.

## Proof strip

- Site lists **v2.11.4**, **MIT**, **15 skills**, **11 tools** (verified 2026-10-09 at https://ga4mcp.com/).
- One-line installer: `https://ga4.builditwithai.xyz/install`. Runtimes: `uvx google-analytics-mcp` and `npx -y @surendranb/google-analytics-mcp`.
- OpenClaw path verified today: `openclaw mcp add/set/configure/tools/login/status/doctor/probe`; `add` accepts stdio flags `--command/--arg/--env/--cwd`; `doctor --probe` proves the live connection (OpenClaw MCP docs).
- Bundle kept distinct: repo `plugins/openclaw/plugin.json` v2.4.1, entry `ga4-mcp-server`, stdio transport, env `GOOGLE_APPLICATION_CREDENTIALS` plus `GA4_PROPERTY_ID` (raw fetched today).
- Repo `pyproject.toml` reads 2.11.5 today, ahead of site 2.11.4; I quote the site label.
- Read-only, local stdio. Telemetry off with `DISABLE_TELEMETRY=1` or `DO_NOT_TRACK=1`.

## Configuring OpenClaw to launch the server

Prerequisites: numeric `GA4_PROPERTY_ID` (Admin, Property details, not the `G-` ID), plus a service-account JSON path or `gcloud auth application-default login`. Keep the JSON path absolute.

1. Add the server:
```bash
openclaw mcp add google-analytics \
  --command uvx \
  --arg google-analytics-mcp \
  --env GA4_PROPERTY_ID=123456789 \
  --env GOOGLE_APPLICATION_CREDENTIALS=/absolute/path/to/key.json
```
2. Prove the live connection:
```bash
openclaw mcp doctor google-analytics --probe
openclaw mcp tools google-analytics
```
3. Bundle alternative: the repo ships an OpenClaw plugin bundle v2.4.1 with entry `ga4-mcp-server`. The `mcp add` entry answers questions; the bundle packages the server for OpenClaw. Pick the entry for daily use; reach for the bundle when you want the packaged shape.
4. Verify by asking: "List my GA4 properties." You have succeeded when `list_properties` returns rows with no setup error.

## Skills worth loading first

| Skill slug | What you use it for in OpenClaw |
|---|---|
| `traffic-diagnosis` | You saw sessions move and want the ordered checks |
| `common-metric-names` | Your field name failed and you want the working GA4 name |
| `compatible-combinations` | Your dimensions and metrics returned a 400 incompatibility |
| `filter-structures` | Your dimension filter returned an invalid-filter error |
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

1. **Probe fails after add.** Symptom: `doctor --probe` reports no tools. Fix: confirm `uvx google-analytics-mcp` runs in your terminal, re-run the add line exactly, then probe again.
2. **Setup error on first call.** Symptom: missing property or credentials. Fix: confirm both `--env` values with an absolute key path; for ADC expiry run `gcloud auth application-default login`. `setup_ga4_access` recovers mid-session where prompts are supported.
3. **Invalid dimension, metric, or filter.** Symptom: 400 naming error. Fix: run `search_schema("<keyword>")`, load `common-metric-names` plus `filter-structures`, retry. Offline guide: `get_troubleshooting_guide(topic="schema")`.

## FAQ

**Does GA4 MCP for OpenClaw use openclaw mcp add?**
Yes. The add plus doctor-probe lines above are the path, verified in OpenClaw MCP docs today.

**What is the v2.4.1 bundle?**
`plugins/openclaw/plugin.json` v2.4.1 with entry `ga4-mcp-server`. It packages the server for OpenClaw; the `mcp add` entry is the live wiring. I keep their numbers separate.

**Control UI or CLI?**
Either. Settings, MCP, Add server with stdio command plus args writes the same definition the CLI writes.

**Why does the agent guess wrong field names?**
Training predates GA4 renames (UA sunset 2023-07-01; conversions renamed to key events 2024-05-06). The `ua-to-ga4` skill maps each old name.

**Is usage read-only and private?**
Yes. Tools read metadata and reports; they change nothing. Traffic runs from your machine to the GA4 Data API. Anonymous counts stop with `DISABLE_TELEMETRY=1`.

**Why does the repo read 2.11.5 when the site says 2.11.4?**
Main moved ahead of the site label at fetch today. I quote 2.11.4 for installs and state the gap here.

## Freshness and machine links

Verified 2026-10-09 against https://ga4mcp.com/ (v2.11.4), https://ga4mcp.com/setup/, https://ga4mcp.com/skills/, OpenClaw MCP docs, and repo raw `plugins/openclaw/plugin.json` v2.4.1 plus `pyproject.toml` 2.11.5.

Version gap (2026-10-09): repo `pyproject.toml` reads 2.11.5 [source: repo pyproject.toml, verified this run] while the live site labels v2.11.4 [source: https://ga4mcp.com/ fetch 2026-10-09]; installs on this page quote the site label.

Machine: https://ga4mcp.com/llms.txt, https://ga4mcp.com/data/tools.json, https://ga4mcp.com/data/skills.json.

## Breadcrumb

Hub (/ga4-mcp-for-every-harness/) / GA4 MCP for OpenClaw (you are here).
