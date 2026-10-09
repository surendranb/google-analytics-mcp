# GA4 MCP for Antigravity: Setup, Skills and First Query


I query GA4 from inside Antigravity CLI with the same server I run elsewhere. GA4 MCP for Antigravity gives you that: one `mcpServers` entry in the shared config tree, your property ID plus credentials in `env`, then plain questions answered from your own property schema.

## Proof strip

- Site lists **v2.11.4**, **MIT**, **15 skills**, **11 tools** (verified 2026-10-09 at https://ga4mcp.com/).
- One-line installer: `https://ga4.builditwithai.xyz/install`. Runtimes: `uvx google-analytics-mcp` and `npx -y @surendranb/google-analytics-mcp`.
- Installer auto-configures Google Antigravity (site Works with list, verified today).
- Antigravity CLI path verified today: global `~/.gemini/config/mcp_config.json`, workspace `.agents/mcp_config.json`, single `mcpServers` object with `command`/`args`/`env` for stdio and `serverUrl` for remote (antigravity.google docs).
- Repo: https://github.com/surendranb/google-analytics-mcp. `pyproject.toml` reads 2.11.5 today, ahead of site 2.11.4; I quote the site label.
- Read-only, local stdio. Telemetry off with `DISABLE_TELEMETRY=1` or `DO_NOT_TRACK=1`.

## Configuring Antigravity CLI to launch the server

Prerequisites: numeric `GA4_PROPERTY_ID` (Admin, Property details, not the `G-` ID), plus a service-account JSON path or `gcloud auth application-default login`. Keep the JSON path absolute.

1. Open the global file `~/.gemini/config/mcp_config.json` (or workspace `.agents/mcp_config.json` for one project) and add:
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
2. Prefer the hands-free path? Run:
```bash
curl -fsSL "https://ga4.builditwithai.xyz/install" | bash
```
3. Restart the CLI and verify by asking: "List my GA4 properties." You have succeeded when `list_properties` returns rows with no setup error. Note: remote entries use `serverUrl`, not `url`; this server uses stdio `command`, so the distinction never bites here.

## Skills worth loading first

| Skill slug | What you use it for in Antigravity |
|---|---|
| `traffic-diagnosis` | You saw sessions move and want the ordered checks |
| `channel-acquisition` | You want sessions split by source, medium, channel group |
| `common-metric-names` | Your field name failed and you want the working GA4 name |
| `filter-structures` | Your dimension filter returned an invalid-filter error |
| `date-ranges` | You compare two periods and want the two-query pattern |

Full set of 15 at https://ga4mcp.com/skills/, loaded with `search_skills("<slug>")`.

## Running your first query

Ask: "How much traffic came from AI assistants last month?"

Your agent should first load `ai-referral-analysis`, then call:
```
get_ga4_data(
  dimensions=["sessionSource"],
  metrics=["sessions"],
  date_range_start="30daysAgo",
  date_range_end="yesterday",
  intent="split AI assistant referrals from search and direct last 30 days"
)
```

Read the period figure from `totals`. I trust that block because GA4 computes it; hand sums drift.

## Fixing the three errors you will hit

1. **Server missing after edit.** Symptom: Antigravity lists no google-analytics server. Fix: confirm the file path (`~/.gemini/config/mcp_config.json` global or `.agents/mcp_config.json` workspace), valid JSON, top-level `mcpServers`, then restart.
2. **Setup error on first call.** Symptom: missing property or credentials. Fix: confirm both `env` values with an absolute key path; for ADC expiry run `gcloud auth application-default login`. `setup_ga4_access` recovers mid-session where prompts are supported.
3. **Invalid dimension, metric, or filter.** Symptom: 400 naming error. Fix: run `search_schema("<keyword>")`, load `common-metric-names` plus `compatible-combinations`, retry. Offline guide: `get_troubleshooting_guide(topic="schema")`.

## FAQ

**Does GA4 MCP for Antigravity use mcp_config.json?**
Yes. Global `~/.gemini/config/mcp_config.json` or workspace `.agents/mcp_config.json`, verified in antigravity.google docs today.

**How is this page different from the Antigravity IDE page?**
This page covers the CLI config tree. The IDE page covers the MCP Store plus View raw config flow. Same file shape, different entry surface; sibling page /ga4-mcp-for-antigravity-ide/ shows the IDE clicks.

**Does the installer cover Antigravity?**
Yes. The site names Google Antigravity in the auto-configure list.

**Why does the agent guess wrong field names?**
Training predates GA4 renames (UA sunset 2023-07-01; conversions renamed to key events 2024-05-06). The `ua-to-ga4` skill maps each old name.

**Is usage read-only and private?**
Yes. Tools read metadata and reports; they change nothing. Traffic runs from your machine to the GA4 Data API. Anonymous counts stop with `DISABLE_TELEMETRY=1`.

**Why does the repo read 2.11.5 when the site says 2.11.4?**
Main moved ahead of the site label at fetch today. I quote 2.11.4 for installs and state the gap here.

## Freshness and machine links

Verified 2026-10-09 against https://ga4mcp.com/ (v2.11.4, Antigravity line), https://ga4mcp.com/setup/, https://ga4mcp.com/skills/, antigravity.google MCP docs, and repo raw `pyproject.toml` 2.11.5.

Version gap (2026-10-09): repo `pyproject.toml` reads 2.11.5 [source: repo pyproject.toml, verified this run] while the live site labels v2.11.4 [source: https://ga4mcp.com/ fetch 2026-10-09]; installs on this page quote the site label.

Machine: https://ga4mcp.com/llms.txt, https://ga4mcp.com/data/tools.json, https://ga4mcp.com/data/skills.json.

## Breadcrumb

Hub (/ga4-mcp-for-every-harness/) / GA4 MCP for Antigravity (you are here) / IDE (/ga4-mcp-for-antigravity-ide/).
