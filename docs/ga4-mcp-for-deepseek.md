# GA4 MCP for DeepSeek: Setup, Skills and First Query


I query GA4 from inside DeepSeek Harness with the same server I run elsewhere. GA4 MCP for DeepSeek gives you that: one `@deepseek-ai/dsh-mcp-client` entry in your patch layer, your property ID plus credentials in `env`, then plain questions answered from your own property schema.

## Proof strip

- Site lists **v2.11.4**, **MIT**, **15 skills**, **11 tools** (verified 2026-10-09 at https://ga4mcp.com/).
- One-line installer: `https://ga4.builditwithai.xyz/install`. Runtimes: `uvx google-analytics-mcp` and `npx -y @surendranb/google-analytics-mcp`.
- Harness path verified today: one plugin instance equals one MCP server, mounted in `cordis.yml`/`patch`; `@deepseek-ai/dsh-mcp-client` with `serverName`, `transport: stdio`, `command`, `args`, `env`; tools surface as `mcp__<serverName>__<tool>` (DeepSeek Harness MCP docs).
- Home verified today: `DSH_HOME` defaults to `~/.dsh`; user patch `cordis.patch.yml`; `dsh web --dump-config` inspects the composed tree.
- Repo `pyproject.toml` reads 2.11.5 today, ahead of site 2.11.4; I quote the site label.
- Read-only, local stdio. Telemetry off with `DISABLE_TELEMETRY=1` or `DO_NOT_TRACK=1`.

## Configuring DeepSeek Harness to launch the server

Prerequisites: numeric `GA4_PROPERTY_ID` (Admin, Property details, not the `G-` ID), plus a service-account JSON path or `gcloud auth application-default login`. Keep the JSON path absolute.

1. Add one entry to your patch layer (`cordis.patch.yml` or `--patch` overlay):
```yaml
- id: mcp-ga4
  name: '@deepseek-ai/dsh-mcp-client'
  config:
    serverName: ga4
    transport: stdio
    command: uvx
    args: ['google-analytics-mcp']
    env:
      GA4_PROPERTY_ID: '123456789'
      GOOGLE_APPLICATION_CREDENTIALS: '/absolute/path/to/key.json'
```
2. Keep the global-mode note straight: stock `uvx` inherits a scrubbed host env, so the explicit `env` block above is the auditable path; do not rely on shell exports alone reaching the subprocess.
3. Inspect the composed tree:
```bash
dsh web --dump-config
```
4. Verify by asking: "List my GA4 properties." You have succeeded when `list_properties` returns rows with no setup error. [NEEDS SOURCE] marks any `~/.dsh` global-mode filename beyond the patch entry, since only the plugin entry shape was fetched this run.

## Skills worth loading first

| Skill slug | What you use it for in DeepSeek |
|---|---|
| `traffic-diagnosis` | You saw sessions move and want the ordered checks |
| `channel-acquisition` | You want sessions split by source, medium, channel group |
| `common-metric-names` | Your field name failed and you want the working GA4 name |
| `date-ranges` | You compare two periods and want the two-query pattern |
| `ecommerce-analysis` | You read revenue, conversion rate, AOV from ecommerce events |

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

1. **Tools never appear as mcp__ga4__*.** Symptom: harness starts, no GA4 tools. Fix: confirm one entry per server with unique `serverName: ga4`, transport `stdio`, then restart the harness.
2. **Setup error on first call.** Symptom: missing property or credentials. Fix: confirm both `env` values in the entry with an absolute key path; for ADC expiry run `gcloud auth application-default login`. `setup_ga4_access` recovers mid-session where prompts are supported.
3. **Invalid dimension, metric, or filter.** Symptom: 400 naming error. Fix: run `search_schema("<keyword>")`, load `common-metric-names` plus `compatible-combinations`, retry. Offline guide: `get_troubleshooting_guide(topic="schema")`.

## FAQ

**Does GA4 MCP for DeepSeek use dsh-mcp-client?**
Yes. One `@deepseek-ai/dsh-mcp-client` entry per server in the patch layer, verified in DeepSeek Harness MCP docs today.

**What are the tools named?**
`mcp__ga4__<tool>` for `serverName: ga4`. The name derives from `(serverName, rawName)`; a second live instance with the same `serverName` fails by design.

**Does Grok get the same entry?**
No. Batch 2 gives zero hours to grok rows (no MCP client proof, honest hold). This page covers DeepSeek Harness alone.

**Why does the agent guess wrong field names?**
Training predates GA4 renames (UA sunset 2023-07-01; conversions renamed to key events 2024-05-06). The `ua-to-ga4` skill maps each old name.

**Is usage read-only and private?**
Yes. Tools read metadata and reports; they change nothing. Traffic runs from your machine to the GA4 Data API. Anonymous counts stop with `DISABLE_TELEMETRY=1`.

**Why does the repo read 2.11.5 when the site says 2.11.4?**
Main moved ahead of the site label at fetch today. I quote 2.11.4 for installs and state the gap here.

## Freshness and machine links

Verified 2026-10-09 against https://ga4mcp.com/ (v2.11.4), https://ga4mcp.com/setup/, https://ga4mcp.com/skills/, DeepSeek Harness MCP plus boot-config docs, and repo raw `pyproject.toml` 2.11.5.

Version gap (2026-10-09): repo `pyproject.toml` reads 2.11.5 [source: repo pyproject.toml, verified this run] while the live site labels v2.11.4 [source: https://ga4mcp.com/ fetch 2026-10-09]; installs on this page quote the site label.

Machine: https://ga4mcp.com/llms.txt, https://ga4mcp.com/data/tools.json, https://ga4mcp.com/data/skills.json.

## Breadcrumb

Hub (/ga4-mcp-for-every-harness/) / GA4 MCP for DeepSeek (you are here).
