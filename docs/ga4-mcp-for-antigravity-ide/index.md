# GA4 MCP for Antigravity IDE: Setup, Skills and First Query


I query GA4 from inside Antigravity IDE with the same server I run in the CLI. GA4 MCP for Antigravity IDE gives you that: the MCP Store path plus the raw `mcp_config.json` block, your property ID plus credentials in `env`, then plain questions answered from your own property schema.

## Proof strip

- Site lists **v2.11.4**, **MIT**, **15 skills**, **11 tools** (verified 2026-10-09 at https://ga4mcp.com/).
- One-line installer: `https://ga4.builditwithai.xyz/install`. Runtimes: `uvx google-analytics-mcp` and `npx -y @surendranb/google-analytics-mcp`.
- Installer auto-configures Google Antigravity (site Works with list, verified today).
- IDE path verified today: MCP Store browse/install, or agent side panel `...` then MCP Servers then Manage MCP Servers then View raw config; file global `~/.gemini/config/mcp_config.json` or workspace `.agents/mcp_config.json` (antigravity.google IDE docs).
- Repo: https://github.com/surendranb/google-analytics-mcp. `pyproject.toml` reads 2.11.5 today, ahead of site 2.11.4; I quote the site label.
- Read-only, local stdio. Telemetry off with `DISABLE_TELEMETRY=1` or `DO_NOT_TRACK=1`.

## Configuring Antigravity IDE to launch the server

Prerequisites: numeric `GA4_PROPERTY_ID` (Admin, Property details, not the `G-` ID), plus a service-account JSON path or `gcloud auth application-default login`. Keep the JSON path absolute.

1. Try the MCP Store first: open the Store in Antigravity IDE, browse supported servers, install where offered.
2. For a custom entry, click `...` at the top of the agent side panel, select MCP Servers, click Manage MCP Servers, click View raw config.
3. Paste this block into the opened `mcp_config.json`:
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
4. Save, restart the IDE agent session, verify by asking: "List my GA4 properties." You have succeeded when `list_properties` returns rows with no setup error.

## Skills worth loading first

| Skill slug | What you use it for in the IDE |
|---|---|
| `content-performance` | You want top pages and weak pages split out |
| `traffic-diagnosis` | You saw sessions move and want the ordered checks |
| `common-metric-names` | Your field name failed and you want the working GA4 name |
| `geo-device-segmentation` | You split users by country, city, device |
| `date-ranges` | You compare two periods and want the two-query pattern |

Full set of 15 at https://ga4mcp.com/skills/, loaded with `search_skills("<slug>")`.

## Running your first query

Ask: "Which pages earned the most engaged sessions last week?"

Your agent should first load `content-performance`, then call:
```
get_ga4_data(
  dimensions=["pagePath"],
  metrics=["sessions"],
  date_range_start="7daysAgo",
  date_range_end="yesterday",
  intent="top pages by sessions last week"
)
```

Read the period figure from `totals`. GA4 computes it; I stopped hand-summing after watching agents drift.

## Fixing the three errors you will hit

1. **Store install stalls.** Symptom: Store entry never activates. Fix: fall back to the raw-config block above; it writes the same file the Store edits.
2. **Setup error on first call.** Symptom: missing property or credentials. Fix: confirm both `env` values with an absolute key path in the raw config, save, restart the session. `setup_ga4_access` recovers mid-session where prompts are supported.
3. **Invalid dimension, metric, or filter.** Symptom: 400 naming error. Fix: run `search_schema("<keyword>")`, load `common-metric-names` plus `filter-structures`, retry. Offline guide: `get_troubleshooting_guide(topic="schema")`.

## FAQ

**Does GA4 MCP for Antigravity IDE use the MCP Store?**
The Store is the first path; View raw config is the fallback. Both write the same `mcp_config.json`, verified in antigravity.google IDE docs today.

**Which file does the IDE edit?**
Global `~/.gemini/config/mcp_config.json` or workspace `.agents/mcp_config.json`. The CLI page /ga4-mcp-for-antigravity/ shows the same shape from the terminal side.

**Does the installer cover the IDE?**
Yes. The site names Google Antigravity in the auto-configure list.

**Why does the agent guess wrong field names?**
Training predates GA4 renames (UA sunset 2023-07-01; conversions renamed to key events 2024-05-06). The `ua-to-ga4` skill maps each old name.

**Is usage read-only and private?**
Yes. Tools read metadata and reports; they change nothing. Traffic runs from your machine to the GA4 Data API. Anonymous counts stop with `DISABLE_TELEMETRY=1`.

**Why does the repo read 2.11.5 when the site says 2.11.4?**
Main moved ahead of the site label at fetch today. I quote 2.11.4 for installs and state the gap here.

## Freshness and machine links

Verified 2026-10-09 against https://ga4mcp.com/ (v2.11.4, Antigravity line), https://ga4mcp.com/setup/, https://ga4mcp.com/skills/, antigravity.google IDE MCP docs, and repo raw `pyproject.toml` 2.11.5.

Version gap (2026-10-09): repo `pyproject.toml` reads 2.11.5 [source: repo pyproject.toml, verified this run] while the live site labels v2.11.4 [source: https://ga4mcp.com/ fetch 2026-10-09]; installs on this page quote the site label.

Machine: https://ga4mcp.com/llms.txt, https://ga4mcp.com/data/tools.json, https://ga4mcp.com/data/skills.json.

## Breadcrumb

Hub (/ga4-mcp-for-every-harness/) / Antigravity CLI (/ga4-mcp-for-antigravity/) / GA4 MCP for Antigravity IDE (you are here).
