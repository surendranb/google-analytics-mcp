# GA4 MCP for Every Harness


I built this server so I could ask plain questions of GA4 from inside my agent and get numbers I can trust. GA4 MCP for every harness gives you that: one MCP server that talks to your GA4 property from Claude, Cursor, Codex, Gemini CLI, and any client that launches a local stdio server.

## Proof strip

- Site lists **v2.11.4**, **MIT**, **15 skills**, **11 tools** (verified 2026-10-09 at https://ga4mcp.com/).
- One-line installer: `https://ga4.builditwithai.xyz/install`. Runtimes: `uvx google-analytics-mcp` and `npx -y @surendranb/google-analytics-mcp`.
- Installer auto-configures Claude Desktop, Claude Code, Cursor, VS Code (Cline, Roo Code), Continue.dev, OpenCode, Windsurf, Zed, and Google Antigravity.
- Repo: https://github.com/surendranb/google-analytics-mcp (242 stars, 48 forks at fetch today). Docs: https://ga4mcp.com/setup/, skills index https://ga4mcp.com/skills/.
- Read-only. Queries run from your machine to the GA4 Data API. Telemetry is anonymous diagnostics only; `DISABLE_TELEMETRY=1` or `DO_NOT_TRACK=1` stops it.

## Getting your client connected

Prerequisites: a numeric GA4 property ID (Admin, Property details, not the `G-` ID), plus either a service-account JSON key or `gcloud auth application-default login`.

1. Set the two values your server needs:
```bash
export GA4_PROPERTY_ID="123456789"
export GOOGLE_APPLICATION_CREDENTIALS="/absolute/path/to/key.json"
```
2. Run the installer, which writes the client entry for you:
```bash
curl -fsSL "https://ga4.builditwithai.xyz/install" | bash
```
3. Restart your client and ask for the property list to verify:
> "List my GA4 properties, then show sessions by channel for the last 7 days."

You have succeeded when the agent calls `list_properties` and `get_ga4_data` without a setup error.

Manual fallback when you prefer to wire the entry by hand:
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

## Skills worth loading first

| Skill slug | What you use it for |
|---|---|
| `traffic-diagnosis` | You saw a spike or drop and want the ordered checks |
| `channel-acquisition` | You want sessions and users split by source, medium, channel group |
| `ai-referral-analysis` | You want traffic from ChatGPT, Claude, Perplexity, Gemini, Copilot split out |
| `common-metric-names` | Your field name failed and you want the working GA4 name |
| `compatible-combinations` | Your dimensions and metrics returned a 400 incompatibility |

Full set of 15 lives at https://ga4mcp.com/skills/ and loads via `search_skills("<slug>")`.

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

Read the period figure from the `totals` block. GA4 computes that block; don't sum the rows by hand. The site states this pattern directly, and it avoids the row-sum mistakes I kept seeing.

## Fixing the three errors you will hit

1. **Missing property ID or credentials.** Symptom: setup error on boot. Fix: set `GA4_PROPERTY_ID` and `GOOGLE_APPLICATION_CREDENTIALS` as above, restart the client, or let `setup_ga4_access` collect them mid-session where your client supports prompts.
2. **403 permission error.** Symptom: credentials load but GA4 refuses. Fix: add the service-account `client_email` as Viewer on the GA4 property (Admin, Property Access Management). For expired local ADC (`503 reauthentication needed`), run `gcloud auth application-default login`. Guide: `get_troubleshooting_guide(topic="iam")`.
3. **Invalid dimension or metric.** Symptom: 400 naming error. Fix: call `search_schema("<keyword>")`, or load `common-metric-names` and `compatible-combinations` before retrying. Guide: `get_troubleshooting_guide(topic="schema")`.

## FAQ

**What does GA4 MCP for every harness actually cover?**
The stdio server plus the installer entries above. If your client launches a local MCP server, it can run this one.

**Which harness should I pick: Claude, Cursor, or Codex?**
Pick the client you already work in. The query path is the same; only the config file differs. Claude, Cursor, and Codex pages under this hub show each exact block.

**Plugin or MCP server: which do I need?**
The MCP server answers questions. A plugin bundles that server for one harness with preset skills. Start with the server; add a plugin when you want the bundle. The plugins hub at /ga4-plugins/ lists each bundle with its version.

**Does it write to my GA4 property?**
No. Every tool is read-only. It reads metadata and reports; it doesn't change configuration.

**What telemetry does it send, and how do I stop it?**
Anonymous tool, latency, and error-code counts only. No queries, credentials, or analytics data. Set `DISABLE_TELEMETRY=1` or `DO_NOT_TRACK=1`.

**Where do I go when the query fails?**
Run `get_troubleshooting_guide(topic="setup" | "iam" | "schema")`, then `search_schema` for the field name. The setup mirror lives at https://ga4mcp.com/setup/.

## Harness pages under this hub

- [GA4 MCP for Claude](/ga4-mcp-for-claude/)
- [GA4 MCP for Codex](/ga4-mcp-for-codex/)
- [GA4 MCP for Cursor](/ga4-mcp-for-cursor/)
- [GA4 Plugin for Claude Code](/ga4-plugin-for-claude-code/)
- [GA4 Plugin for Gemini](/ga4-plugin-for-gemini/)
- [GA4 Plugin for Harness](/ga4-plugin-for-harness/)
- [GA4 Plugins](/ga4-plugins/)
- [GA4 MCP for Antigravity IDE](/ga4-mcp-for-antigravity-ide/)
- [GA4 MCP for Antigravity](/ga4-mcp-for-antigravity/)
- [GA4 MCP for Copilot](/ga4-mcp-for-copilot/)
- [GA4 MCP for DeepSeek](/ga4-mcp-for-deepseek/)
- [GA4 MCP for Devin Desktop](/ga4-mcp-for-devin-desktop/)
- [GA4 MCP for Gemini](/ga4-mcp-for-gemini/)
- [GA4 MCP for Goose](/ga4-mcp-for-goose/)
- [GA4 MCP for Hermes](/ga4-mcp-for-hermes/)
- [GA4 MCP for Kiro](/ga4-mcp-for-kiro/)
- [GA4 MCP for OpenClaw](/ga4-mcp-for-openclaw/)
- [GA4 MCP for OpenCode](/ga4-mcp-for-opencode/)
- [GA4 MCP for Pi](/ga4-mcp-for-pi/)
- [GA4 MCP for VS Code](/ga4-mcp-for-vscode/)
- [GA4 MCP for ZCode](/ga4-mcp-for-zcode/)
- [GA4 MCP for Zed](/ga4-mcp-for-zed/)

## Freshness and machine links

Verified 2026-10-09 against https://ga4mcp.com/ (v2.11.4), https://ga4mcp.com/setup/, https://ga4mcp.com/skills/, and repo raw files named in sibling pages. Repo main `pyproject.toml` read 2.11.5 today, ahead of the site's 2.11.4 label; I quote the site label for installs. GSC demand figures from the brief were out of scope for this writer run and don't appear above.

Version gap (2026-10-09): repo `pyproject.toml` reads 2.11.5 [source: repo pyproject.toml, verified this run] while the live site labels v2.11.4 [source: https://ga4mcp.com/ fetch 2026-10-09]; installs on this page quote the site label.

Machine: https://ga4mcp.com/llms.txt, https://ga4mcp.com/data/tools.json, https://ga4mcp.com/data/skills.json, https://ga4mcp.com/sitemap.xml.

## Breadcrumb

Home https://ga4mcp.com/ / GA4 MCP for Every Harness (you are here) / Claude (/ga4-mcp-for-claude/) / Cursor (/ga4-mcp-for-cursor/) / Codex (/ga4-mcp-for-codex/) / Plugins (/ga4-plugins/).
