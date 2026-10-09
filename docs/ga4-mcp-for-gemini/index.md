# GA4 MCP for Gemini: Setup, Skills and First Query


I query GA4 from inside Gemini CLI with the same server I run in Claude and OpenCode. GA4 MCP for Gemini gives you that: one `mcpServers` entry in `~/.gemini/settings.json`, your property ID plus credentials in `env`, then plain questions answered from your own property schema.

## Proof strip

- Site lists **v2.11.4**, **MIT**, **15 skills**, **11 tools** (verified 2026-10-09 at https://ga4mcp.com/).
- One-line installer: `https://ga4.builditwithai.xyz/install`. Runtimes: `uvx google-analytics-mcp` and `npx -y @surendranb/google-analytics-mcp`.
- Site names Gemini CLI with the extension in the repo (verified today in Works with list).
- Gemini path verified today: `~/.gemini/settings.json` (project `.gemini/settings.json` overrides) with `mcpServers` command/args/env; `gemini mcp add` writes entries (geminicli.com docs).
- Extension versions kept distinct: repo root `gemini-extension.json` v2.11.1; nested `gemini-extension/gemini-extension.json` v2.5.0 with `mcpServer` command `uvx --from google-analytics-mcp ga4-mcp-server` (both raw fetched today).
- Repo `pyproject.toml` reads 2.11.5 today, ahead of site 2.11.4; I quote the site label for installs.
- Read-only, local stdio. Telemetry off with `DISABLE_TELEMETRY=1` or `DO_NOT_TRACK=1`.

## Configuring Gemini CLI to launch the server

Prerequisites: numeric `GA4_PROPERTY_ID` (Admin, Property details, not the `G-` ID), plus a service-account JSON path or `gcloud auth application-default login`. Keep the JSON path absolute.

1. Open `~/.gemini/settings.json` and add the server:
```json
{
  "mcpServers": {
    "google-analytics": {
      "command": "uvx",
      "args": ["google-analytics-mcp"],
      "env": {
        "GA4_PROPERTY_ID": "123456789",
        "GOOGLE_APPLICATION_CREDENTIALS": "/absolute/path/to/key.json"
      },
      "timeout": 30000
    }
  }
}
```
2. Alternative: let the CLI write it:
```bash
gemini mcp add google-analytics uvx google-analytics-mcp
```
Then add the two `env` values above by hand.
3. Extension alternative: the repo ships `gemini-extension.json` v2.11.1 at root and v2.5.0 nested. The nested bundle runs `uvx --from google-analytics-mcp ga4-mcp-server` with the same two env keys. Pick the settings block or the extension, not both at once.
4. Verify by asking: "List my GA4 properties." You have succeeded when `list_properties` returns rows with no setup error.

## Skills worth loading first

| Skill slug | What you use it for in Gemini |
|---|---|
| `traffic-diagnosis` | You saw sessions move and want the ordered checks |
| `channel-acquisition` | You want sessions split by source, medium, channel group |
| `common-metric-names` | Gemini guessed a UA-era name and GA4 rejected it |
| `date-ranges` | You compare two periods and want the two-query pattern |
| `ai-referral-analysis` | You split Gemini, ChatGPT, Claude, Perplexity, Copilot referrals from search |

Full set of 15 at https://ga4mcp.com/skills/, loaded with `search_skills("<slug>")`.

## Running your first query

Ask: "Why did organic traffic drop in the last 7 days?"

Your agent should first load `traffic-diagnosis`, then call:
```
get_ga4_data(
  dimensions=["date"],
  metrics=["sessions"],
  date_range_start="7daysAgo",
  date_range_end="yesterday",
  intent="diagnose organic sessions drop last 7 days"
)
```

Read the period figure from `totals`. GA4 computes it; summing rows by hand is where I watched agents drift.

## Fixing the three errors you will hit

1. **Server absent after edit.** Symptom: Gemini lists no google-analytics server. Fix: confirm the file is `~/.gemini/settings.json` with top-level `mcpServers`, valid JSON, then restart the CLI.
2. **Setup error on first call.** Symptom: missing property or credentials. Fix: confirm both `env` values present with an absolute key path, or run `gcloud auth application-default login` for ADC expiry (`503 reauthentication needed`). `setup_ga4_access` recovers mid-session where prompts are supported.
3. **Invalid dimension, metric, or filter.** Symptom: 400 naming error. Fix: run `search_schema("<keyword>")`, load `common-metric-names` plus `compatible-combinations`, retry. Offline guide: `get_troubleshooting_guide(topic="schema")`.

## FAQ

**Does GA4 MCP for Gemini use settings.json?**
Yes. `~/.gemini/settings.json` with the `mcpServers` block above is the path, verified in geminicli.com docs today.

**Which Gemini extension version do I quote?**
Both, distinctly. Root `gemini-extension.json` is v2.11.1; nested `gemini-extension/gemini-extension.json` is v2.5.0. They are separate manifests; I never merge their numbers.

**Does the ChatGPT app path apply here?**
No. ChatGPT app limits are stated per page only when touched; this page covers Gemini CLI alone. Batch 2 gives zero hours to chatgpt rows (no local stdio path, honest hold).

**Why does Gemini guess wrong field names?**
Training predates GA4 renames (UA sunset 2023-07-01; conversions renamed to key events 2024-05-06). The `ua-to-ga4` skill maps each old name.

**Is usage read-only and private?**
Yes. Tools read metadata and reports; they change nothing. Traffic runs from your machine to the GA4 Data API. Anonymous counts stop with `DISABLE_TELEMETRY=1`.

**Why does the repo read 2.11.5 when the site says 2.11.4?**
Main moved ahead of the site label at fetch today. I quote 2.11.4 for installs and state the gap here.

## Freshness and machine links

Verified 2026-10-09 against https://ga4mcp.com/ (v2.11.4, Gemini CLI line), https://ga4mcp.com/setup/, https://ga4mcp.com/skills/, geminicli.com MCP docs, and repo raw `gemini-extension.json` v2.11.1 plus nested v2.5.0 and `pyproject.toml` 2.11.5.

Version gap (2026-10-09): repo `pyproject.toml` reads 2.11.5 [source: repo pyproject.toml, verified this run] while the live site labels v2.11.4 [source: https://ga4mcp.com/ fetch 2026-10-09]; installs on this page quote the site label.

Machine: https://ga4mcp.com/llms.txt, https://ga4mcp.com/data/tools.json, https://ga4mcp.com/data/skills.json.

## Breadcrumb

Hub (/ga4-mcp-for-every-harness/) / GA4 MCP for Gemini (you are here).
