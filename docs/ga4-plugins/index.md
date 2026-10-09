# GA4 Plugins for Analytics Agents


I ship the MCP server for questions and plugins for harnesses that want the bundle. GA4 plugins give you that split: the server stays the engine, and each plugin manifest points one harness at it with its own version.

## Proof strip

- Site lists **v2.11.4**, **MIT**, **15 skills**, **11 tools** (verified 2026-10-09 at https://ga4mcp.com/).
- `.claude-plugin/plugin.json` **v2.11.1** (repo root path, raw fetch today).
- `gemini-extension.json` **v2.11.1** at repo root (raw fetch today); nested `gemini-extension/gemini-extension.json` reads **v2.5.0** (raw fetch today, distinct file, don't conflate).
- `plugins/openclaw/plugin.json` **v2.4.1** (raw fetch today, entry `ga4-mcp-server`, stdio, env `GOOGLE_APPLICATION_CREDENTIALS` + `GA4_PROPERTY_ID`).
- Repo: https://github.com/surendranb/google-analytics-mcp. Installer `https://ga4.builditwithai.xyz/install`.

## Choosing server or plugin

Prerequisites: decide the harness first. Server suits any stdio MCP client; plugin suits a harness with a plugin host (Claude Code, Gemini CLI, OpenClaw-style runners).

1. When you want GA4 answers inside a client you already use, install the server:
```bash
curl -fsSL "https://ga4.builditwithai.xyz/install" | bash
```
2. When you want the harness-native bundle, pick one manifest below and follow its sibling page.
3. Set env in both routes:
```bash
export GA4_PROPERTY_ID="123456789"
export GOOGLE_APPLICATION_CREDENTIALS="/absolute/path/to/key.json"
```
4. Verify with "List my GA4 properties." You have succeeded when `list_properties` returns rows.

## The three bundles

| Plugin manifest | Version today | Harness | Sibling page |
|---|---|---|---|
| `.claude-plugin/plugin.json` | v2.11.1 | Claude Code | /ga4-plugin-for-claude-code/ |
| `gemini-extension.json` (root) | v2.11.1 | Gemini CLI | /ga4-plugin-for-gemini/ |
| `plugins/openclaw/plugin.json` | v2.4.1 | OpenClaw + generic harness | /ga4-plugin-for-harness/ |

Nested `gemini-extension/gemini-extension.json` v2.5.0 is a separate file under `gemini-extension/`; quote the path with the version every time.

## Skills worth loading first

| Skill slug | Why it matters for plugin users |
|---|---|
| `attribution-scope` | Plugin preset questions mix scopes; this keeps them apart |
| `compatible-combinations` | Bundled prompts still hit 400s on bad pairs |
| `filter-structures` | Bundled prompts still mistype `dimensionFilter` |
| `ai-referral-analysis` | Most common plugin question after install |
| `traffic-diagnosis` | Most common second question after a drop |

Full set of 15 at https://ga4mcp.com/skills/.

## Running your first query

Ask: "What were my top channels last week?"

The plugin should route to:
```
get_ga4_data(
  dimensions=["sessionDefaultChannelGroup"],
  metrics=["sessions"],
  date_range_start="7daysAgo",
  date_range_end="yesterday",
  intent="which channels drove sessions last week"
)
```

Read `totals` for the period figure. I built the plugin prompts around that block because hand sums fail under row caps.

## Fixing the three errors you will hit

1. **Plugin installs but tools don't appear.** Symptom: host lists the plugin, no GA4 tools. Fix: confirm the underlying server runs (`uvx google-analytics-mcp`), restart the host, re-enable the plugin.
2. **Setup error inside the plugin.** Symptom: missing property or key. Fix: export both env values in the host's launching shell, use an absolute key path. Mid-session recovery: `setup_ga4_access` where supported.
3. **Query 400s through the plugin.** Symptom: invalid name or filter. Fix: `search_schema("<keyword>")` plus `common-metric-names` and `filter-structures`. Offline: `get_troubleshooting_guide(topic="schema")`.

## FAQ

**What is a GA4 plugin versus the GA4 MCP server?**
The server answers GA4 questions over MCP. A plugin is a manifest that registers that server plus presets inside one harness.

**Which GA4 plugin version goes with Claude Code?**
`.claude-plugin/plugin.json` v2.11.1, verified by raw fetch today. Detail lives at /ga4-plugin-for-claude-code/.

**Which GA4 plugin version goes with Gemini?**
Root `gemini-extension.json` v2.11.1. The nested `gemini-extension/gemini-extension.json` v2.5.0 is a different file. Detail lives at /ga4-plugin-for-gemini/.

**Which GA4 plugin version goes with OpenClaw or a generic harness?**
`plugins/openclaw/plugin.json` v2.4.1 with entry `ga4-mcp-server` over stdio. Detail lives at /ga4-plugin-for-harness/.

**Do plugins change telemetry or permissions?**
No. Same read-only tools, same anonymous diagnostics, same `DISABLE_TELEMETRY=1` off switch.

**Where do plugin skills load from?**
From the repo at call time via `search_skills`, so a skill addition doesn't need a plugin release. Index: https://ga4mcp.com/skills/.

## Freshness and machine links

Verified 2026-10-09 against https://ga4mcp.com/ (v2.11.4), https://ga4mcp.com/skills/, repo raw `.claude-plugin/plugin.json` v2.11.1, root `gemini-extension.json` v2.11.1, `gemini-extension/gemini-extension.json` v2.5.0, `plugins/openclaw/plugin.json` v2.4.1.

Version gap (2026-10-09): repo `pyproject.toml` reads 2.11.5 [source: repo pyproject.toml, verified this run] while the live site labels v2.11.4 [source: https://ga4mcp.com/ fetch 2026-10-09]; installs on this page quote the site label.

Machine: https://ga4mcp.com/llms.txt, https://ga4mcp.com/data/tools.json, https://ga4mcp.com/data/skills.json.

## Breadcrumb

Hub (/ga4-mcp-for-every-harness/) / GA4 Plugins (you are here) / Claude Code plugin (/ga4-plugin-for-claude-code/) / Harness plugin (/ga4-plugin-for-harness/) / Gemini plugin (/ga4-plugin-for-gemini/).
