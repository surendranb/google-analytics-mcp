# GA4 MCP for ZCode: Setup, Skills and First Query


I query GA4 from inside ZCode with the same server I run in Zed and Cursor. GA4 MCP for ZCode gives you that: one entry in Settings, MCP, your property ID plus credentials in `env`, then plain questions answered from your own property schema.

## Proof strip

- Site lists **v2.11.4**, **MIT**, **15 skills**, **11 tools** (verified 2026-10-09 at https://ga4mcp.com/).
- One-line installer: `https://ga4.builditwithai.xyz/install`. Runtimes: `uvx google-analytics-mcp` and `npx -y @surendranb/google-analytics-mcp`.
- ZCode path verified today: Settings, MCP, Add, New MCP Server form or Full configuration mode paste; accepts both `{"server-name": {...}}` and `{"mcpServers": {...}}` shapes; remote HTTP/SSE plus OAuth button flow (zcode.z.ai MCP docs).
- Remote note verified today: workspace MCP trusted by default (v3.2.3 changelog); Sync MCP moves user-level config to SSH/WSL remotes on demand, never automatically.
- Repo `pyproject.toml` reads 2.11.5 today, ahead of site 2.11.4; I quote the site label.
- Read-only, local stdio. Telemetry off with `DISABLE_TELEMETRY=1` or `DO_NOT_TRACK=1`.

## Configuring ZCode to launch the server

Prerequisites: numeric `GA4_PROPERTY_ID` (Admin, Property details, not the `G-` ID), plus a service-account JSON path or `gcloud auth application-default login`. Keep the JSON path absolute.

1. Open ZCode Settings, MCP Servers. Click Add, New MCP Server.
2. Switch to Full configuration mode and paste:
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
The form fields map to the same keys: Name google-analytics, Scope User, Type stdio, Command uvx, Args `google-analytics-mcp`, Timeout 30000.
3. Save and return to the list. Remote workers: use Sync MCP from the workspace header or the MCP settings page to move the user-level entry to SSH/WSL; project-level and plugin-provided entries stay out of sync scope.
4. Verify by asking: "List my GA4 properties." You have succeeded when `list_properties` returns rows with no setup error.

## Skills worth loading first

| Skill slug | What you use it for in ZCode |
|---|---|
| `traffic-diagnosis` | You saw sessions move and want the ordered checks |
| `channel-acquisition` | You want sessions split by source, medium, channel group |
| `common-metric-names` | Your field name failed and you want the working GA4 name |
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

1. **Tool count shows 0.** Symptom: server connects, no tools listed. Fix: confirm command `uvx` plus args, Node/Python present on the machine running the agent, restart ZCode.
2. **Setup error on first call.** Symptom: missing property or credentials. Fix: confirm both `env` values with an absolute key path; on a synced remote, confirm the secret moved verbatim and the remote path exists. `setup_ga4_access` recovers mid-session where prompts are supported.
3. **Invalid dimension, metric, or filter.** Symptom: 400 naming error. Fix: run `search_schema("<keyword>")`, load `common-metric-names` plus `filter-structures`, retry. Offline guide: `get_troubleshooting_guide(topic="schema")`.

## FAQ

**Does GA4 MCP for ZCode use Full configuration mode?**
That is the auditable path. Paste the block above; the form writes the same keys. Verified in zcode.z.ai MCP docs today.

**Does Sync MCP copy secrets?**
Yes, verbatim, to hosts you pick. I sync only to hosts I trust, and I re-check the remote key path after sync.

**Is the workspace server trusted by default?**
Yes, since v3.2.3. That flag covers workspace entries; it never replaces the `env` values above.

**Why does the agent guess wrong field names?**
Training predates GA4 renames (UA sunset 2023-07-01; conversions renamed to key events 2024-05-06). The `ua-to-ga4` skill maps each old name.

**Is usage read-only and private?**
Yes. Tools read metadata and reports; they change nothing. Traffic runs from your machine to the GA4 Data API. Anonymous counts stop with `DISABLE_TELEMETRY=1`.

**Why does the repo read 2.11.5 when the site says 2.11.4?**
Main moved ahead of the site label at fetch today. I quote 2.11.4 for installs and state the gap here.

## Freshness and machine links

Verified 2026-10-09 against https://ga4mcp.com/ (v2.11.4), https://ga4mcp.com/setup/, https://ga4mcp.com/skills/, zcode.z.ai MCP services plus remote-development sync docs and v3.2.3 changelog, and repo raw `pyproject.toml` 2.11.5.

Version gap (2026-10-09): repo `pyproject.toml` reads 2.11.5 [source: repo pyproject.toml, verified this run] while the live site labels v2.11.4 [source: https://ga4mcp.com/ fetch 2026-10-09]; installs on this page quote the site label.

Machine: https://ga4mcp.com/llms.txt, https://ga4mcp.com/data/tools.json, https://ga4mcp.com/data/skills.json.

## Breadcrumb

Hub (/ga4-mcp-for-every-harness/) / GA4 MCP for ZCode (you are here).
