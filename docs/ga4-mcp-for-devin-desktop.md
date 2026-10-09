# GA4 MCP for Devin Desktop: Setup, Skills and First Query


I query GA4 from inside Devin with the same server I run locally elsewhere. GA4 MCP for Devin Desktop gives you that: one `mcpServers` entry in the Devin MCP config, your property ID plus credentials in `env`, then plain questions answered from your own property schema.

## Proof strip

- Site lists **v2.11.4**, **MIT**, **15 skills**, **11 tools** (verified 2026-10-09 at https://ga4mcp.com/).
- One-line installer: `https://ga4.builditwithai.xyz/install`. Runtimes: `uvx google-analytics-mcp` and `npx -y @surendranb/google-analytics-mcp`.
- Devin path verified today: `devin mcp add/list/get/login` CLI; configs `~/.config/devin/mcp_config.json` (user), `.devin/mcp_config.json` (project), `.devin/mcp_config.local.json` (local, gitignored); legacy Cascade agent uses `mcp_config.json` (Devin docs).
- Hosted alternate verified today: Composio Devin MCP is a hosted bridge (`windsurf://windsurf-mcp-registry` one-click or `~/.codeium/windsurf/mcp_config.json` with `serverUrl`); it is not the native entry below.
- Repo `pyproject.toml` reads 2.11.5 today, ahead of site 2.11.4; I quote the site label.
- Read-only, local stdio. Telemetry off with `DISABLE_TELEMETRY=1` or `DO_NOT_TRACK=1`.

## Configuring Devin to launch the server

Prerequisites: numeric `GA4_PROPERTY_ID` (Admin, Property details, not the `G-` ID), plus a service-account JSON path or `gcloud auth application-default login`. Keep the JSON path absolute.

1. Add the server from your terminal:
```bash
devin mcp add google-analytics --command uvx --arg google-analytics-mcp
```
Default scope writes `.devin/mcp_config.local.json`. Use `-s user` for `~/.config/devin/mcp_config.json` or `-s project` for shared `.devin/mcp_config.json`.
2. Confirm the entry carries your values:
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
3. Check the connection:
```bash
devin mcp list
devin mcp get google-analytics
```
4. Verify by asking: "List my GA4 properties." You have succeeded when `list_properties` returns rows with no setup error. Do not mix the Composio hosted `serverUrl` entry into this file; pick native stdio or hosted, not both under one name.

## Skills worth loading first

| Skill slug | What you use it for in Devin |
|---|---|
| `traffic-diagnosis` | You saw sessions move and want the ordered checks |
| `channel-acquisition` | You want sessions split by source, medium, channel group |
| `common-metric-names` | Your field name failed and you want the working GA4 name |
| `date-ranges` | You compare two periods and want the two-query pattern |
| `filter-structures` | Your dimension filter returned an invalid-filter error |

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

1. **Server missing after add.** Symptom: `devin mcp list` omits google-analytics. Fix: confirm which scope file you wrote (local vs user vs project), then re-run the add with the intended `-s` flag.
2. **Setup error on first call.** Symptom: missing property or credentials. Fix: confirm both `env` values with an absolute key path in the same scope file; for ADC expiry run `gcloud auth application-default login`. `setup_ga4_access` recovers mid-session where prompts are supported.
3. **Invalid dimension, metric, or filter.** Symptom: 400 naming error. Fix: run `search_schema("<keyword>")`, load `common-metric-names` plus `compatible-combinations`, retry. Offline guide: `get_troubleshooting_guide(topic="schema")`.

## FAQ

**Does GA4 MCP for Devin Desktop use devin mcp add?**
Yes. The add plus scope files above are the path, verified in Devin docs today.

**Native stdio or Composio hosted: which does this page use?**
Native stdio. Composio hosts a Devin bridge over `serverUrl`; I name it here so you can tell them apart, and I wire only the native entry above.

**Does the Windsurf rename affect this page?**
Windsurf retired as a name and Devin Desktop is the successor surface. I do not ship a /windsurf/ page; this page is the live path.

**Why does the agent guess wrong field names?**
Training predates GA4 renames (UA sunset 2023-07-01; conversions renamed to key events 2024-05-06). The `ua-to-ga4` skill maps each old name.

**Is usage read-only and private?**
Yes. Tools read metadata and reports; they change nothing. Traffic runs from your machine to the GA4 Data API. Anonymous counts stop with `DISABLE_TELEMETRY=1`.

**Why does the repo read 2.11.5 when the site says 2.11.4?**
Main moved ahead of the site label at fetch today. I quote 2.11.4 for installs and state the gap here.

## Freshness and machine links

Verified 2026-10-09 against https://ga4mcp.com/ (v2.11.4), https://ga4mcp.com/setup/, https://ga4mcp.com/skills/, Devin MCP configuration docs plus Desktop cascade page, Composio Connect page, and repo raw `pyproject.toml` 2.11.5.

Version gap (2026-10-09): repo `pyproject.toml` reads 2.11.5 [source: repo pyproject.toml, verified this run] while the live site labels v2.11.4 [source: https://ga4mcp.com/ fetch 2026-10-09]; installs on this page quote the site label.

Machine: https://ga4mcp.com/llms.txt, https://ga4mcp.com/data/tools.json, https://ga4mcp.com/data/skills.json.

## Breadcrumb

Hub (/ga4-mcp-for-every-harness/) / GA4 MCP for Devin Desktop (you are here).
