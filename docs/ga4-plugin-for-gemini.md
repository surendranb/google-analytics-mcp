# GA4 Plugin for Gemini CLI


I tripped over the two Gemini files once, so this page keeps them apart. GA4 plugin for Gemini CLI uses the root manifest at v2.11.1; the nested file under `gemini-extension/` is a separate v2.5.0 document you quote only with its path.

## Proof strip

- Root `gemini-extension.json` **v2.11.1** (repo `surendranb/google-analytics-mcp`, raw fetch 2026-10-09; `mcp.command uvx`, `args ["google-analytics-mcp"]`, settings `GA4_PROPERTY_ID` + `GOOGLE_APPLICATION_CREDENTIALS`).
- Nested `gemini-extension/gemini-extension.json` **v2.5.0** (raw fetch 2026-10-09, distinct file; `mcpServer.command uvx`, `args ["--from", "google-analytics-mcp", "ga4-mcp-server"]`).
- Site lists server **v2.11.4**, **MIT**, **15 skills**, **11 tools** (https://ga4mcp.com/ today).
- Installer `https://ga4.builditwithai.xyz/install`; repo https://github.com/surendranb/google-analytics-mcp.
- Read-only, local stdio. Telemetry off with `DISABLE_TELEMETRY=1` or `DO_NOT_TRACK=1`.

## Installing the Gemini plugin

Prerequisites: Gemini CLI installed, `uvx` on PATH, numeric `GA4_PROPERTY_ID`, absolute service-account JSON path.

1. Install the root extension manifest (`gemini-extension.json` v2.11.1) through your Gemini CLI extension flow.
2. Provide the two settings the manifest declares:
```bash
export GA4_PROPERTY_ID="123456789"
export GOOGLE_APPLICATION_CREDENTIALS="/absolute/path/to/key.json"
```
The nested v2.5.0 file templates these as `${GOOGLE_APPLICATION_CREDENTIALS}` and `${GA4_PROPERTY_ID}`; same keys, same meaning.
3. When you wire by hand instead, use the nested file's explicit server shape:
```json
{
  "command": "uvx",
  "args": ["--from", "google-analytics-mcp", "ga4-mcp-server"],
  "env": {
    "GOOGLE_APPLICATION_CREDENTIALS": "/absolute/path/to/key.json",
    "GA4_PROPERTY_ID": "123456789"
  }
}
```
4. Verify inside Gemini CLI by asking: "List my GA4 properties." You have succeeded when `list_properties` returns rows.

## Skills worth loading first

| Skill slug | What you use it for with Gemini |
|---|---|
| `ai-referral-analysis` | You split Gemini, ChatGPT, Claude, Perplexity, Copilot referrals |
| `channel-acquisition` | You split source, medium, channel group |
| `common-metric-names` | Gemini's model guesses a UA-era name |
| `geo-device-segmentation` | You cut by country, city, device, OS |
| `date-ranges` | You compare periods with two queries |

Full set of 15 at https://ga4mcp.com/skills/, loaded with `search_skills("<slug>")`.

## Running your first query

Ask: "How much traffic came from AI assistants last week?"

Gemini should load `ai-referral-analysis`, then call:
```
get_ga4_data(
  dimensions=["sessionSource"],
  metrics=["sessions"],
  date_range_start="7daysAgo",
  date_range_end="yesterday",
  intent="AI assistant referral sessions last week"
)
```

Read `totals` for the period figure. I read that block because GA4 computes it; summed rows mislead once a filter narrows the set.

## Fixing the three errors you will hit

1. **Extension installs but GA4 tools missing.** Symptom: no `get_ga4_data`. Fix: run `uvx --from google-analytics-mcp ga4-mcp-server` in a terminal to prove the runtime, restart Gemini CLI, re-enable the extension.
2. **Setup error on first query.** Symptom: missing property or key. Fix: re-export both values with an absolute key path in the launching shell. Mirror: https://ga4mcp.com/setup/.
3. **400 on names or filters.** Symptom: invalid dimension, metric, or filter. Fix: `search_schema("<keyword>")`, load `common-metric-names` and `filter-structures`, retry. Offline: `get_troubleshooting_guide(topic="schema")`.

## FAQ

**What is the GA4 plugin for Gemini version?**
Root `gemini-extension.json` v2.11.1. Always quote the path; the nested file differs.

**What is `gemini-extension/gemini-extension.json` v2.5.0 then?**
A separate manifest under `gemini-extension/` with the explicit `uvx --from` server shape. Use it when you hand-wire; use the root file version when you cite the extension.

**What command does the Gemini manifest run?**
Root: `uvx` args `["google-analytics-mcp"]`. Nested: `uvx` args `["--from", "google-analytics-mcp", "ga4-mcp-server"]`. Both verified by raw fetch today.

**Where do GA4_PROPERTY_ID and credentials go?**
Both manifests declare the same two keys. Export them in the launching shell with an absolute key path; the ID is numeric, not `G-`.

**Is Gemini usage read-only?**
Yes. Reports and metadata reads only. Nothing writes GA4 configuration.

**How do I stop telemetry from Gemini runs?**
Set `DISABLE_TELEMETRY=1` or `DO_NOT_TRACK=1`. Anonymous counts stop, and the local ID file stops.

## Freshness and machine links

Verified 2026-10-09 against root `gemini-extension.json` v2.11.1, nested `gemini-extension/gemini-extension.json` v2.5.0, https://ga4mcp.com/ (v2.11.4), https://ga4mcp.com/setup/, https://ga4mcp.com/skills/.

Version gap (2026-10-09): repo `pyproject.toml` reads 2.11.5 [source: repo pyproject.toml, verified this run] while the live site labels v2.11.4 [source: https://ga4mcp.com/ fetch 2026-10-09]; installs on this page quote the site label.

Machine: https://ga4mcp.com/llms.txt, https://ga4mcp.com/data/tools.json, https://ga4mcp.com/data/skills.json.

## Breadcrumb

Hub (/ga4-mcp-for-every-harness/) / Plugins hub (/ga4-plugins/) / GA4 Plugin for Gemini (you are here).
