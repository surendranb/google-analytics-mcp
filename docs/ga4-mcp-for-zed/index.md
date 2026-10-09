# GA4 MCP for Zed: Setup, Skills and First Query


I query GA4 from inside Zed with the same server I run in Cursor and VS Code. GA4 MCP for Zed gives you that: one entry under `context_servers` in Zed settings, your property ID plus credentials in `env`, then plain questions answered from your own property schema.

## Proof strip

- Site lists **v2.11.4**, **MIT**, **15 skills**, **11 tools** (verified 2026-10-09 at https://ga4mcp.com/).
- One-line installer: `https://ga4.builditwithai.xyz/install`. Runtimes: `uvx google-analytics-mcp` and `npx -y @surendranb/google-analytics-mcp`.
- Installer auto-configures Zed (site Works with list, verified today).
- Zed path verified today: Settings, AI, MCP Servers, Add Server, Add Local Server or Install from Extensions; settings file entries under `context_servers` with `command`/`args`/`env`; green indicator means connected (zed.dev MCP docs).
- Repo: https://github.com/surendranb/google-analytics-mcp. `pyproject.toml` reads 2.11.5 today, ahead of site 2.11.4; I quote the site label.
- Read-only, local stdio. Telemetry off with `DISABLE_TELEMETRY=1` or `DO_NOT_TRACK=1`.

## Configuring Zed to launch the server

Prerequisites: numeric `GA4_PROPERTY_ID` (Admin, Property details, not the `G-` ID), plus a service-account JSON path or `gcloud auth application-default login`. Keep the JSON path absolute.

1. Open Settings, AI, MCP Servers in Zed. Click Add Server, choose Add Local Server.
2. Paste this entry (Zed uses `context_servers`, not `mcpServers`):
```json
{
  "context_servers": {
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
3. Watch the indicator dot beside the server name. Green means connected; grey means the command or env needs a second look.
4. Verify by asking: "List my GA4 properties." You have succeeded when `list_properties` returns rows with no setup error. Hands-free alternative: `curl -fsSL "https://ga4.builditwithai.xyz/install" | bash` writes the Zed entry.

## Skills worth loading first

| Skill slug | What you use it for in Zed |
|---|---|
| `traffic-diagnosis` | You saw sessions move and want the ordered checks |
| `content-performance` | You want top pages and weak pages split out |
| `common-metric-names` | Your field name failed and you want the working GA4 name |
| `date-ranges` | You compare two periods and want the two-query pattern |
| `filter-structures` | Your dimension filter returned an invalid-filter error |

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

1. **Grey indicator after save.** Symptom: Zed shows the server disconnected. Fix: confirm `uvx google-analytics-mcp` runs in your terminal, the JSON key is `context_servers`, then reload Zed.
2. **Setup error on first call.** Symptom: missing property or credentials. Fix: confirm both `env` values with an absolute key path; for ADC expiry run `gcloud auth application-default login`. `setup_ga4_access` recovers mid-session where prompts are supported.
3. **Invalid dimension, metric, or filter.** Symptom: 400 naming error. Fix: run `search_schema("<keyword>")`, load `common-metric-names` plus `compatible-combinations`, retry. Offline guide: `get_troubleshooting_guide(topic="schema")`.

## FAQ

**Does GA4 MCP for Zed use context_servers?**
Yes. Zed settings use `context_servers` with `command`/`args`/`env`, verified in zed.dev MCP docs today. Other clients use `mcpServers`; Zed is the exception and I keep the key exact.

**Does the installer cover Zed?**
Yes. The site names Zed in the auto-configure list.

**Add Local Server or Install from Extensions?**
Add Local Server with the block above. Install from Extensions fits registry servers; this server wires as a custom local entry.

**Why does the agent guess wrong field names?**
Training predates GA4 renames (UA sunset 2023-07-01; conversions renamed to key events 2024-05-06). The `ua-to-ga4` skill maps each old name.

**Is usage read-only and private?**
Yes. Tools read metadata and reports; they change nothing. Traffic runs from your machine to the GA4 Data API. Anonymous counts stop with `DISABLE_TELEMETRY=1`.

**Why does the repo read 2.11.5 when the site says 2.11.4?**
Main moved ahead of the site label at fetch today. I quote 2.11.4 for installs and state the gap here.

## Freshness and machine links

Verified 2026-10-09 against https://ga4mcp.com/ (v2.11.4, Zed line), https://ga4mcp.com/setup/, https://ga4mcp.com/skills/, zed.dev MCP docs, and repo raw `pyproject.toml` 2.11.5.

Version gap (2026-10-09): repo `pyproject.toml` reads 2.11.5 [source: repo pyproject.toml, verified this run] while the live site labels v2.11.4 [source: https://ga4mcp.com/ fetch 2026-10-09]; installs on this page quote the site label.

Machine: https://ga4mcp.com/llms.txt, https://ga4mcp.com/data/tools.json, https://ga4mcp.com/data/skills.json.

## Breadcrumb

Hub (/ga4-mcp-for-every-harness/) / GA4 MCP for Zed (you are here).
