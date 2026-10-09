# GA4 MCP for Claude: Code, Desktop, and Cowork


I run GA4 from inside Claude every day, and the three Claude surfaces need three different entries for the same server. GA4 MCP for Claude covers all three: Code via CLI, Desktop via JSON config, and Cowork as the local agent mode inside Desktop [source: https://ga4mcp.com/ FAQ, verified 2026-10-09].

## Proof strip

- Site lists **v2.11.4**, **MIT**, **15 skills**, **11 tools** (verified 2026-10-09 at https://ga4mcp.com/).
- Site FAQ names Claude Code, Claude Desktop, and Claude Cowork as working; installer covers Desktop and Code; Cowork runs local MCP servers through the desktop app [source: https://ga4mcp.com/ FAQ, verified 2026-10-09].
- Claude Code path: `claude mcp add google-analytics -- uvx google-analytics-mcp` (repo README + site install block).
- Claude plugin bundle: `.claude-plugin/plugin.json` v2.11.1 in repo `surendranb/google-analytics-mcp` (raw fetch today).
- Read-only, local stdio, telemetry off with `DISABLE_TELEMETRY=1` or `DO_NOT_TRACK=1`.

## Configuring each Claude surface

Prerequisites: numeric `GA4_PROPERTY_ID`, plus a service-account JSON path or `gcloud auth application-default login`. Keep the JSON path absolute.

1. For Claude Code, add the server from your terminal:
```bash
claude mcp add google-analytics -- uvx google-analytics-mcp
```
Then set the environment for the server process:
```bash
export GA4_PROPERTY_ID="123456789"
export GOOGLE_APPLICATION_CREDENTIALS="/absolute/path/to/key.json"
```
2. For Claude Desktop, open `claude_desktop_config.json` and add:
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
Restart Claude Desktop after saving.
3. For Claude Cowork, use the Desktop entry above. Cowork is the local agent mode inside Claude Desktop, so it picks up the same local MCP servers. [source: https://ga4mcp.com/ FAQ, verified 2026-10-09] No second install.
4. Verify from any of the three by asking: "List my GA4 properties." You have succeeded when `list_properties` returns rows with no setup error.

Prefer hands-free? `curl -fsSL "https://ga4.builditwithai.xyz/install" | bash` writes the Claude entries for you.

## Skills worth loading first

| Skill slug | What you use it for in Claude |
|---|---|
| `traffic-diagnosis` | You ask why sessions moved and want Claude to follow the ordered checks |
| `attribution-scope` | You compare session, event, and user scope without mixing them |
| `ai-referral-analysis` | You split ChatGPT, Claude, Perplexity, Gemini, Copilot referrals from search and direct |
| `common-metric-names` | Claude guesses a UA-era name and GA4 rejects it |
| `date-ranges` | You compare periods and want the two-query pattern, not one blended pull |

Full set of 15 at https://ga4mcp.com/skills/, loaded with `search_skills("<slug>")`.

## Running your first query

Ask Claude: "Why did organic traffic drop in the last 7 days?"

Claude should first load `traffic-diagnosis`, then call:
```
get_ga4_data(
  dimensions=["date"],
  metrics=["sessions"],
  date_range_start="7daysAgo",
  date_range_end="yesterday",
  intent="diagnose organic sessions drop last 7 days"
)
```

Read the period figure from `totals`. I trust that block because GA4 computes it; summing date rows by hand is where agents drift.

## Fixing the three errors you will hit

1. **Claude Code says the server isn't found.** Symptom: MCP entry missing after add. Fix: re-run the `claude mcp add` line exactly, confirm `uvx google-analytics-mcp` runs in your terminal, restart Code.
2. **Desktop shows a setup error on launch.** Symptom: missing env. Fix: confirm both `GA4_PROPERTY_ID` and `GOOGLE_APPLICATION_CREDENTIALS` sit inside the `env` object above with an absolute path, then restart Desktop. `setup_ga4_access` recovers mid-session where prompts are supported.
3. **Query fails on names or filters.** Symptom: 400 invalid dimension, metric, or filter. Fix: run `search_schema("<keyword>")`, load `common-metric-names` plus `filter-structures`, and retry. Offline guides: `get_troubleshooting_guide(topic="schema")`.

## FAQ

**Does GA4 MCP for Claude Code use the CLI add command?**
Yes. `claude mcp add google-analytics -- uvx google-analytics-mcp` is the Code path, verified in the repo README and the site install block.

**Does GA4 MCP for Claude Desktop need hand-edited JSON?**
Only the one `claude_desktop_config.json` entry above, or the installer which writes it. Restart Desktop after either.

**How does GA4 MCP for Claude Cowork connect?**
Cowork runs through Claude Desktop's local agent mode, so the Desktop entry covers it. [source: https://ga4mcp.com/ FAQ, verified 2026-10-09] The site FAQ states this directly.

**Is there a Claude Code plugin bundle distinct from the MCP entry?**
Yes. `.claude-plugin/plugin.json` v2.11.1 ships in the repo. The MCP entry answers questions; the plugin bundles the server for Code. Sibling page /ga4-plugin-for-claude-code/ shows that manifest.

**Why does Claude guess wrong field names?**
Training predates GA4 renames (UA sunset 2023-07-01; conversions renamed to key events 2024-05-06). The `ua-to-ga4` skill maps each old name.

**Is Claude usage read-only and private?**
Yes. Tools are read-only; traffic goes from your machine to GA4. Telemetry is anonymous counts you stop with `DISABLE_TELEMETRY=1`.

## Freshness and machine links

Verified 2026-10-09 against https://ga4mcp.com/ (v2.11.4, FAQ Claude lines), https://ga4mcp.com/setup/, https://ga4mcp.com/skills/, repo README client blocks, and raw `.claude-plugin/plugin.json` v2.11.1.

Version gap (2026-10-09): repo `pyproject.toml` reads 2.11.5 [source: repo pyproject.toml, verified this run] while the live site labels v2.11.4 [source: https://ga4mcp.com/ fetch 2026-10-09]; installs on this page quote the site label.

Machine: https://ga4mcp.com/llms.txt, https://ga4mcp.com/data/tools.json, https://ga4mcp.com/data/skills.json.

## Breadcrumb

Hub (/ga4-mcp-for-every-harness/) / GA4 MCP for Claude (you are here) / Plugin for Claude Code (/ga4-plugin-for-claude-code/).
