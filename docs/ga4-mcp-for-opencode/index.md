# GA4 MCP for OpenCode: Setup, Skills and First Query


I query GA4 from inside OpenCode with the same server I run in Claude and Cursor. GA4 MCP for OpenCode gives you that: one stdio entry in `opencode.jsonc`, your property ID plus credentials in `env`, then plain questions answered from your own property schema.

## Proof strip

- Site lists **v2.11.4**, **MIT**, **15 skills**, **11 tools** (verified 2026-10-09 at https://ga4mcp.com/).
- One-line installer: `https://ga4.builditwithai.xyz/install`. Runtimes: `uvx google-analytics-mcp` and `npx -y @surendranb/google-analytics-mcp`.
- Installer auto-configures OpenCode among Claude Desktop, Claude Code, Cursor, VS Code (Cline, Roo Code), Continue.dev, Windsurf, Zed, and Google Antigravity (site Works with list, verified today).
- OpenCode path verified today: `opencode.jsonc` under `mcp` with local type and `command` array; `opencode mcp list` and `opencode mcp auth list` manage entries (opencode.ai docs).
- Repo: https://github.com/surendranb/google-analytics-mcp. Main `pyproject.toml` reads 2.11.5 today, ahead of the site 2.11.4 label; I quote the site label for installs.
- Read-only, local stdio. Telemetry off with `DISABLE_TELEMETRY=1` or `DO_NOT_TRACK=1`.

## Configuring OpenCode to launch the server

Prerequisites: numeric `GA4_PROPERTY_ID` (Admin, Property details, not the `G-` ID), plus a service-account JSON path or `gcloud auth application-default login`. Keep the JSON path absolute.

1. Open your `opencode.jsonc` (global `~/.config/opencode/opencode.json` or project root) and add the server under `mcp`:
```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "google-analytics": {
      "type": "local",
      "command": ["uvx", "google-analytics-mcp"],
      "enabled": true,
      "environment": {
        "GA4_PROPERTY_ID": "123456789",
        "GOOGLE_APPLICATION_CREDENTIALS": "/absolute/path/to/key.json"
      }
    }
  }
}
```
2. Prefer the hands-free path? Run the installer, which writes the OpenCode entry for you:
```bash
curl -fsSL "https://ga4.builditwithai.xyz/install" | bash
```
3. Confirm the entry loads:
```bash
opencode mcp list
```
4. Verify by asking: "List my GA4 properties." You have succeeded when `list_properties` returns rows with no setup error.

## Skills worth loading first

| Skill slug | What you use it for in OpenCode |
|---|---|
| `traffic-diagnosis` | You saw sessions move and want the ordered checks |
| `common-metric-names` | Your field name failed and you want the working GA4 name |
| `date-ranges` | You compare two periods and want the two-query pattern |
| `compatible-combinations` | Your dimensions and metrics returned a 400 incompatibility |
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

Read the period figure from the `totals` block. GA4 computes that block; I stopped summing date rows by hand after watching agents drift on the math.

## Fixing the three errors you will hit

1. **Server missing from `opencode mcp list`.** Symptom: entry absent after edit. Fix: validate the JSONC parses, confirm the block sits under `mcp` with `type` local, restart OpenCode.
2. **Setup error on first call.** Symptom: missing property or credentials. Fix: confirm `GA4_PROPERTY_ID` is numeric and `GOOGLE_APPLICATION_CREDENTIALS` is an absolute path in `environment`, then restart. `setup_ga4_access` recovers mid-session where prompts are supported.
3. **Invalid dimension, metric, or filter.** Symptom: 400 naming error. Fix: run `search_schema("<keyword>")`, load `common-metric-names` plus `filter-structures`, retry. Offline guide: `get_troubleshooting_guide(topic="schema")`.

## FAQ

**Does GA4 MCP for OpenCode use opencode.jsonc?**
Yes. The `mcp` block above is the path, verified in opencode.ai docs today. Global file covers every project; project file covers one checkout.

**Does the installer cover OpenCode?**
Yes. The site names OpenCode in the auto-configure list. I still show the hand block because edited JSON is easier to audit.

**Plugin or MCP server: which do I need?**
The MCP server answers questions. Start with the server; add a bundle only when a harness ships one. The hub at /ga4-mcp-for-every-harness/ explains the split.

**Why does OpenCode guess wrong field names?**
Training predates GA4 renames (UA sunset 2023-07-01; conversions renamed to key events 2024-05-06). The `ua-to-ga4` skill maps each old name.

**Is usage read-only and private?**
Yes. Tools read metadata and reports; they change nothing in GA4. Traffic runs from your machine to the GA4 Data API. Anonymous counts stop with `DISABLE_TELEMETRY=1`.

**Why does the repo read 2.11.5 when the site says 2.11.4?**
Main moved ahead of the site label at fetch today. I quote 2.11.4 for installs and state the gap here so commands match the published label.

## Freshness and machine links

Verified 2026-10-09 against https://ga4mcp.com/ (v2.11.4, Works with OpenCode line), https://ga4mcp.com/setup/, https://ga4mcp.com/skills/, opencode.ai MCP servers docs, and repo raw `pyproject.toml` 2.11.5.

Version gap (2026-10-09): repo `pyproject.toml` reads 2.11.5 [source: repo pyproject.toml, verified this run] while the live site labels v2.11.4 [source: https://ga4mcp.com/ fetch 2026-10-09]; installs on this page quote the site label.

Machine: https://ga4mcp.com/llms.txt, https://ga4mcp.com/data/tools.json, https://ga4mcp.com/data/skills.json.

## Breadcrumb

Hub (/ga4-mcp-for-every-harness/) / GA4 MCP for OpenCode (you are here).
