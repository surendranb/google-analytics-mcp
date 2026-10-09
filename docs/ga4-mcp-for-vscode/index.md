# GA4 MCP for VS Code: Setup, Skills and First Query


I query GA4 from inside VS Code with the same server I run in Cursor and Claude. GA4 MCP for VS Code gives you that: one `servers` entry in `.vscode/mcp.json`, your property ID plus credentials in `env`, then plain questions answered from your own property schema.

## Proof strip

- Site lists **v2.11.4**, **MIT**, **15 skills**, **11 tools** (verified 2026-10-09 at https://ga4mcp.com/).
- One-line installer: `https://ga4.builditwithai.xyz/install`. Runtimes: `uvx google-analytics-mcp` and `npx -y @surendranb/google-analytics-mcp`.
- Installer auto-configures VS Code paths Cline and Roo Code (site Works with list, verified today).
- VS Code path verified today: workspace `.vscode/mcp.json` (or user profile) with `servers` object, stdio `command`/`args`/`env`, IntelliSense in the file; `code --add-mcp` adds entries (VS Code MCP docs).
- Cline path verified today: Cline panel MCP Servers icon, Configure tab, Configure MCP Servers opens JSON with `mcpServers` command plus args (Cline docs).
- Repo `pyproject.toml` reads 2.11.5 today, ahead of site 2.11.4; I quote the site label.
- Read-only, local stdio. Telemetry off with `DISABLE_TELEMETRY=1` or `DO_NOT_TRACK=1`.

## Configuring VS Code to launch the server

Prerequisites: numeric `GA4_PROPERTY_ID` (Admin, Property details, not the `G-` ID), plus a service-account JSON path or `gcloud auth application-default login`. Keep the JSON path absolute.

1. Create or open `.vscode/mcp.json` in your workspace and add:
```json
{
  "servers": {
    "google-analytics": {
      "type": "stdio",
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
2. Cline/Roo variant: in the Cline panel click the MCP Servers icon, open the Configure tab, click Configure MCP Servers, add the same entry under `mcpServers` with `command` plus `args`.
3. Command-line alternative:
```bash
code --add-mcp '{"name":"google-analytics","command":"uvx","args":["google-analytics-mcp"]}'
```
Then add the two `env` values in the file by hand.
4. Restart VS Code and verify by asking: "List my GA4 properties." You have succeeded when `list_properties` returns rows with no setup error.

## Skills worth loading first

| Skill slug | What you use it for in VS Code |
|---|---|
| `traffic-diagnosis` | You saw sessions move and want the ordered checks |
| `common-metric-names` | Your field name failed and you want the working GA4 name |
| `compatible-combinations` | Your dimensions and metrics returned a 400 incompatibility |
| `channel-acquisition` | You want sessions split by source, medium, channel group |
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

1. **Server missing after edit.** Symptom: VS Code lists no google-analytics server. Fix: confirm the file is `.vscode/mcp.json` with top-level `servers` (VS Code shape, not `mcpServers`), valid JSON, then reload the window.
2. **Setup error on first call.** Symptom: missing property or credentials. Fix: confirm both `env` values with an absolute key path; for ADC expiry run `gcloud auth application-default login`. `setup_ga4_access` recovers mid-session where prompts are supported.
3. **Invalid dimension, metric, or filter.** Symptom: 400 naming error. Fix: run `search_schema("<keyword>")`, load `common-metric-names` plus `filter-structures`, retry. Offline guide: `get_troubleshooting_guide(topic="schema")`.

## FAQ

**Does GA4 MCP for VS Code use .vscode/mcp.json?**
Yes. Workspace `.vscode/mcp.json` with the `servers` block above is the path, verified in VS Code MCP docs today.

**Do Cline and Roo Code share this entry?**
They read the same stdio shape through their own Configure MCP Servers JSON (`mcpServers` with command plus args). The installer covers both; the block above ports across with the key rename noted.

**Does the installer cover VS Code?**
Yes. The site names VS Code with Cline and Roo Code in the auto-configure list.

**Why does the agent guess wrong field names?**
Training predates GA4 renames (UA sunset 2023-07-01; conversions renamed to key events 2024-05-06). The `ua-to-ga4` skill maps each old name.

**Is usage read-only and private?**
Yes. Tools read metadata and reports; they change nothing. Traffic runs from your machine to the GA4 Data API. Anonymous counts stop with `DISABLE_TELEMETRY=1`.

**Why does the repo read 2.11.5 when the site says 2.11.4?**
Main moved ahead of the site label at fetch today. I quote 2.11.4 for installs and state the gap here.

## Freshness and machine links

Verified 2026-10-09 against https://ga4mcp.com/ (v2.11.4, VS Code Cline Roo line), https://ga4mcp.com/setup/, https://ga4mcp.com/skills/, VS Code MCP docs, Cline MCP docs, and repo raw `pyproject.toml` 2.11.5.

Version gap (2026-10-09): repo `pyproject.toml` reads 2.11.5 [source: repo pyproject.toml, verified this run] while the live site labels v2.11.4 [source: https://ga4mcp.com/ fetch 2026-10-09]; installs on this page quote the site label.

Machine: https://ga4mcp.com/llms.txt, https://ga4mcp.com/data/tools.json, https://ga4mcp.com/data/skills.json.

## Breadcrumb

Hub (/ga4-mcp-for-every-harness/) / GA4 MCP for VS Code (you are here).
