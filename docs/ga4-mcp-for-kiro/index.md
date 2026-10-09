# GA4 MCP for Kiro: Setup, Skills and First Query


I query GA4 from inside Kiro with the same server I run in Cursor and VS Code. GA4 MCP for Kiro gives you that: one `mcpServers` entry in `.kiro/settings/mcp.json`, your property ID plus credentials in `env`, then plain questions answered from your own property schema.

## Proof strip

- Site lists **v2.11.4**, **MIT**, **15 skills**, **11 tools** (verified 2026-10-09 at https://ga4mcp.com/).
- One-line installer: `https://ga4.builditwithai.xyz/install`. Runtimes: `uvx google-analytics-mcp` and `npx -y @surendranb/google-analytics-mcp`.
- Kiro path verified today: workspace `.kiro/settings/mcp.json` plus user `~/.kiro/settings/mcp.json`, merged with workspace winning; local `command`/`args`/`env` plus remote `url`/`headers`; command palette Kiro: Open workspace/user MCP config (Kiro MCP docs).
- Steering note verified today: `.kiro/steering/` plus root `AGENTS.md` carry project rules; MCP servers stay in `mcp.json`, never in steering files.
- Repo `pyproject.toml` reads 2.11.5 today, ahead of site 2.11.4; I quote the site label.
- Read-only, local stdio. Telemetry off with `DISABLE_TELEMETRY=1` or `DO_NOT_TRACK=1`.

## Configuring Kiro to launch the server

Prerequisites: numeric `GA4_PROPERTY_ID` (Admin, Property details, not the `G-` ID), plus a service-account JSON path or `gcloud auth application-default login`. Keep the JSON path absolute.

1. Open the command palette (`Cmd+Shift+P` / `Ctrl+Shift+P`), search MCP, pick Kiro: Open workspace MCP config for one project or Kiro: Open user MCP config for every workspace.
2. Add the server:
```json
{
  "mcpServers": {
    "google-analytics": {
      "command": "uvx",
      "args": ["google-analytics-mcp"],
      "env": {
        "GA4_PROPERTY_ID": "123456789",
        "GOOGLE_APPLICATION_CREDENTIALS": "/absolute/path/to/key.json"
      },
      "disabled": false
    }
  }
}
```
Workspace `.kiro/settings/mcp.json` wins over user `~/.kiro/settings/mcp.json` on name collisions.
3. Save the file (`Cmd+S`); Kiro reconnects automatically. No restart dance.
4. Verify by asking: "List my GA4 properties." You have succeeded when `list_properties` returns rows with no setup error.

## Skills worth loading first

| Skill slug | What you use it for in Kiro |
|---|---|
| `traffic-diagnosis` | You saw sessions move and want the ordered checks |
| `content-performance` | You want top pages and weak pages split out |
| `common-metric-names` | Your field name failed and you want the working GA4 name |
| `compatible-combinations` | Your dimensions and metrics returned a 400 incompatibility |
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

1. **Server disabled after save.** Symptom: Kiro lists google-analytics as disabled. Fix: confirm `"disabled": false` in the same scope file you edited (workspace vs user), save again.
2. **Setup error on first call.** Symptom: missing property or credentials. Fix: confirm both `env` values with an absolute key path in the winning scope file; for ADC expiry run `gcloud auth application-default login`. `setup_ga4_access` recovers mid-session where prompts are supported.
3. **Invalid dimension, metric, or filter.** Symptom: 400 naming error. Fix: run `search_schema("<keyword>")`, load `common-metric-names` plus `filter-structures`, retry. Offline guide: `get_troubleshooting_guide(topic="schema")`.

## FAQ

**Does GA4 MCP for Kiro use .kiro/settings/mcp.json?**
Yes. Workspace `.kiro/settings/mcp.json` or user `~/.kiro/settings/mcp.json`, verified in Kiro MCP docs today.

**Do steering files configure MCP?**
No. Steering plus `AGENTS.md` carry rules; `mcp.json` carries servers. I keep them in separate files.

**Does the installer cover Kiro?**
The site auto-configure list does not name Kiro. I show the hand block because it is exact and auditable.

**Why does the agent guess wrong field names?**
Training predates GA4 renames (UA sunset 2023-07-01; conversions renamed to key events 2024-05-06). The `ua-to-ga4` skill maps each old name.

**Is usage read-only and private?**
Yes. Tools read metadata and reports; they change nothing. Traffic runs from your machine to the GA4 Data API. Anonymous counts stop with `DISABLE_TELEMETRY=1`.

**Why does the repo read 2.11.5 when the site says 2.11.4?**
Main moved ahead of the site label at fetch today. I quote 2.11.4 for installs and state the gap here.

## Freshness and machine links

Verified 2026-10-09 against https://ga4mcp.com/ (v2.11.4), https://ga4mcp.com/setup/, https://ga4mcp.com/skills/, Kiro MCP configuration docs, and repo raw `pyproject.toml` 2.11.5.

Version gap (2026-10-09): repo `pyproject.toml` reads 2.11.5 [source: repo pyproject.toml, verified this run] while the live site labels v2.11.4 [source: https://ga4mcp.com/ fetch 2026-10-09]; installs on this page quote the site label.

Machine: https://ga4mcp.com/llms.txt, https://ga4mcp.com/data/tools.json, https://ga4mcp.com/data/skills.json.

## Breadcrumb

Hub (/ga4-mcp-for-every-harness/) / GA4 MCP for Kiro (you are here).
