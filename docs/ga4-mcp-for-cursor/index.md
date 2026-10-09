# GA4 MCP for Cursor


I use Cursor when the question sits next to code, and I want GA4 numbers in the same window. GA4 MCP for Cursor gives you that: the stdio server wired through Cursor's `mcp.json` with your property ID and key path.

## Proof strip

- Site lists **v2.11.4**, **MIT**, **15 skills**, **11 tools** (verified 2026-10-09 at https://ga4mcp.com/).
- Installer auto-configures Cursor (site install section, verified today). Manual path below matches repo README section B for Cursor and Antigravity.
- Runtime: `uvx google-analytics-mcp`. Alt runtime: `npx -y @surendranb/google-analytics-mcp`.
- Repo: https://github.com/surendranb/google-analytics-mcp. Skills index https://ga4mcp.com/skills/.
- Read-only. Telemetry off with `DISABLE_TELEMETRY=1` or `DO_NOT_TRACK=1`.

## Connecting Cursor with mcp.json

Prerequisites: Cursor installed, `uvx` on PATH (verify with `uvx --version`), numeric `GA4_PROPERTY_ID`, absolute service-account JSON path.

1. Open Cursor Settings, MCP, and locate `mcp.json` (project or global, per your setup).
2. Add the GA4 entry:
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
3. Save, restart Cursor's MCP host or reload the window, and confirm `google-analytics` shows as connected with its tools listed.
4. Verify by asking: "List my GA4 properties." You have succeeded when `list_properties` returns rows and `search_schema("sessions")` ranks field names.

Hands-free alternative:
```bash
curl -fsSL "https://ga4.builditwithai.xyz/install" | bash
```

## Skills worth loading first

| Skill slug | What you use it for in Cursor |
|---|---|
| `content-performance` | You want top and weak pages with engagement behind them |
| `channel-acquisition` | You split sessions by source, medium, channel group |
| `common-metric-names` | Cursor's model guesses a UA name and GA4 rejects it |
| `filter-structures` | Your `dimensionFilter` shape returns invalid-filter |
| `bot-traffic-detection` | You want bots and scrapers out before you read a drop |

Full set of 15 at https://ga4mcp.com/skills/, loaded with `search_skills("<slug>")`.

## Running your first query

Ask: "Which pages earned the most engaged sessions last week, excluding bots?"

Cursor's agent should load `content-performance` and `bot-traffic-detection`, then call:
```
get_ga4_data(
  dimensions=["pagePath"],
  metrics=["sessions"],
  date_range_start="7daysAgo",
  date_range_end="yesterday",
  intent="top pages by sessions last week"
)
```

Read the period figure from `totals`. I keep that habit because GA4's aggregation is the period truth; hand sums drift when row caps apply.

## Fixing the three errors you will hit

1. **Cursor shows the server as unreachable.** Symptom: red entry in MCP settings. Fix: run `uvx google-analytics-mcp` in a terminal to prove the runtime works, check the `command` spelling is `uvx`, then reload Cursor.
2. **Setup error about missing env.** Symptom: server starts but tools refuse. Fix: confirm `GA4_PROPERTY_ID` is numeric and `GOOGLE_APPLICATION_CREDENTIALS` is an absolute existing path inside `mcp.json`, then reload. Mirror steps at https://ga4mcp.com/setup/.
3. **400 on dimensions, metrics, or filters.** Symptom: invalid name or incompatible combo. Fix: `search_schema("<keyword>")`, then load `common-metric-names` and `compatible-combinations`. Guides work offline via `get_troubleshooting_guide(topic="schema")`.

## FAQ

**Where does GA4 MCP for Cursor config live?**
In Cursor's `mcp.json`, under `mcpServers.google-analytics` as shown above. The installer writes it when you'd rather not hand-edit.

**Does the Cursor entry differ from Claude Desktop?**
Only the file name and host. Command, args, and env keys match. I keep them identical so I can copy between clients.

**Can Cursor use npx instead of uvx?**
Yes. Swap command to `npx` with args `["-y", "@surendranb/google-analytics-mcp"]`. I use uvx because it matches the repo default.

**How do I confirm Cursor loaded the 11 tools?**
Open MCP settings and expand `google-analytics`. You should see `get_ga4_data`, `search_schema`, `search_skills`, and the rest. If the count looks short, reload the window.

**Is Cursor usage read-only?**
Yes. The server reads reports and metadata. It never writes GA4 configuration.

**How do I stop telemetry from Cursor runs?**
Add `"DISABLE_TELEMETRY": "1"` to the entry's `env`, or export `DO_NOT_TRACK=1` for the host process.

## Freshness and machine links

Verified 2026-10-09 against https://ga4mcp.com/ (v2.11.4, installer client list names Cursor), repo README Cursor block, https://ga4mcp.com/setup/, https://ga4mcp.com/skills/.

Version gap (2026-10-09): repo `pyproject.toml` reads 2.11.5 [source: repo pyproject.toml, verified this run] while the live site labels v2.11.4 [source: https://ga4mcp.com/ fetch 2026-10-09]; installs on this page quote the site label.

Machine: https://ga4mcp.com/llms.txt, https://ga4mcp.com/data/tools.json, https://ga4mcp.com/data/skills.json.

## Breadcrumb

Hub (/ga4-mcp-for-every-harness/) / GA4 MCP for Cursor (you are here) / Plugins (/ga4-plugins/).
