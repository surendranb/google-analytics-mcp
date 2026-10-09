# GA4 MCP for Codex


I treat Codex as my terminal agent for GA4: same server, same env keys, added as a local stdio MCP server. GA4 MCP for Codex shows that path without guessing at Codex config filenames I didn't verify today.

## Proof strip

- Site lists **v2.11.4**, **MIT**, **15 skills**, **11 tools** (verified 2026-10-09 at https://ga4mcp.com/).
- Site FAQ states OpenAI's Codex CLI connects and is in regular use with this server; the ChatGPT app can't launch local stdio servers so it can't connect.
- Runtimes verified: `uvx google-analytics-mcp`, `npx -y @surendranb/google-analytics-mcp`, installer `https://ga4.builditwithai.xyz/install`.
- Repo: https://github.com/surendranb/google-analytics-mcp. Skills index https://ga4mcp.com/skills/.
- Read-only, local process, telemetry off with `DISABLE_TELEMETRY=1` or `DO_NOT_TRACK=1`.

## Adding GA4 to Codex

Prerequisites: Codex CLI installed, `uvx` on PATH, numeric `GA4_PROPERTY_ID`, absolute service-account JSON path.

1. Export the two values in the shell that launches Codex:
```bash
export GA4_PROPERTY_ID="123456789"
export GOOGLE_APPLICATION_CREDENTIALS="/absolute/path/to/key.json"
```
2. In Codex, add a local MCP server with command `uvx` and args `["google-analytics-mcp"]`, carrying the two env values above. [NEEDS SOURCE: exact Codex MCP config filename and menu path, not verified in this writer run; confirm against Codex docs before publishing.]
3. Restart Codex and ask: "List my GA4 properties." You have succeeded when `list_properties` returns rows with no setup error.
4. If Codex offers an installer route, this equivalent writes known clients for you:
```bash
curl -fsSL "https://ga4.builditwithai.xyz/install" | bash
```

I kept step 2 generic on purpose. The stdio command and env keys are verified; the Codex-side filename wasn't in the repo README or site fetch, so I won't invent it.

## Skills worth loading first

| Skill slug | What you use it for in Codex |
|---|---|
| `traffic-diagnosis` | You ask why traffic moved and want ordered checks |
| `channel-acquisition` | You split sessions by source, medium, channel group |
| `ai-referral-analysis` | You isolate ChatGPT, Claude, Perplexity, Gemini, Copilot referrals |
| `common-metric-names` | The model guesses a UA-era name that GA4 rejects |
| `ga4-limitations` | You want the boundary of what the Data API can't answer |

Full set of 15 at https://ga4mcp.com/skills/, loaded with `search_skills("<slug>")`.

## Running your first query

Ask: "How much traffic came from AI assistants last week, and how did it behave?"

Codex should load `ai-referral-analysis`, then call:
```
get_ga4_data(
  dimensions=["sessionSource"],
  metrics=["sessions"],
  date_range_start="7daysAgo",
  date_range_end="yesterday",
  intent="AI assistant referral sessions last week"
)
```

Read the period figure from `totals`. I read that block because GA4 computes it; row sums mislead once filters narrow the set.

## Fixing the three errors you will hit

1. **Codex can't find the server.** Symptom: MCP entry fails to start. Fix: run `uvx google-analytics-mcp` alone in a terminal, confirm it launches, then re-add with the exact command spelling `uvx`.
2. **Setup error on first call.** Symptom: missing property or credentials. Fix: re-export both env values in the launching shell with an absolute key path, restart Codex. Steps mirror https://ga4mcp.com/setup/.
3. **400 on names or filters.** Symptom: invalid dimension, metric, or filter shape. Fix: `search_schema("<keyword>")`, load `common-metric-names` and `filter-structures`, retry. Offline path: `get_troubleshooting_guide(topic="schema")`.

## FAQ

**Does GA4 MCP for Codex really connect?**
Yes for Codex CLI as a stdio client. The site FAQ names it as connected and in regular use. The ChatGPT app can't launch local stdio servers, so it can't use this server.

**What is the exact Codex MCP config for GA4?**
Command `uvx`, args `["google-analytics-mcp"]`, env `GA4_PROPERTY_ID` plus `GOOGLE_APPLICATION_CREDENTIALS`. The Codex-side filename is [NEEDS SOURCE] and stays out until Codex docs confirm it.

**Does Codex need a different server version?**
No. Same v2.11.4 server, same 11 tools and 15 skills. Only the host entry differs.

**Can Codex use the one-line installer?**
The installer covers the clients named on the site. Run it, then confirm Codex lists `google-analytics` as connected; otherwise use the manual stdio entry above.

**Is Codex usage read-only?**
Yes. The server reads GA4 reports and metadata. It doesn't alter GA4 configuration.

**How do I stop telemetry from Codex runs?**
Export `DISABLE_TELEMETRY=1` or `DO_NOT_TRACK=1` in the launching shell. That stops sends and the local ID file.

## Freshness and machine links

Verified 2026-10-09 against https://ga4mcp.com/ (v2.11.4 + Codex FAQ lines), https://ga4mcp.com/setup/, https://ga4mcp.com/skills/, repo README runtimes. Codex config filename deliberately unverified; marked above.

Version gap (2026-10-09): repo `pyproject.toml` reads 2.11.5 [source: repo pyproject.toml, verified this run] while the live site labels v2.11.4 [source: https://ga4mcp.com/ fetch 2026-10-09]; installs on this page quote the site label.

Machine: https://ga4mcp.com/llms.txt, https://ga4mcp.com/data/tools.json, https://ga4mcp.com/data/skills.json.

## Breadcrumb

Hub (/ga4-mcp-for-every-harness/) / GA4 MCP for Codex (you are here) / Plugins (/ga4-plugins/).
