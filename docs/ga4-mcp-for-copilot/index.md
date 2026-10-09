# GA4 MCP for Copilot: Setup, Skills and First Query


I query GA4 from inside Copilot CLI with the same server I run in VS Code. GA4 MCP for Copilot gives you that: one entry in `~/.copilot/mcp-config.json` via `copilot mcp add`, your property ID plus credentials in `env`, then plain questions answered from your own property schema.

## Proof strip

- Site lists **v2.11.4**, **MIT**, **15 skills**, **11 tools** (verified 2026-10-09 at https://ga4mcp.com/).
- One-line installer: `https://ga4.builditwithai.xyz/install`. Runtimes: `uvx google-analytics-mcp` and `npx -y @surendranb/google-analytics-mcp`.
- Copilot path verified today: user config `~/.copilot/mcp-config.json` with `mcpServers` local type; `copilot mcp add SERVER-NAME -- COMMAND` and in-session `/mcp add`; project `.mcp.json` and `.github/mcp.json` scopes (GitHub Copilot CLI docs).
- Repo: https://github.com/surendranb/google-analytics-mcp. `pyproject.toml` reads 2.11.5 today, ahead of site 2.11.4; I quote the site label.
- Read-only, local stdio. Telemetry off with `DISABLE_TELEMETRY=1` or `DO_NOT_TRACK=1`.

## Configuring Copilot CLI to launch the server

Prerequisites: numeric `GA4_PROPERTY_ID` (Admin, Property details, not the `G-` ID), plus a service-account JSON path or `gcloud auth application-default login`. Keep the JSON path absolute.

1. Add the server from your terminal:
```bash
copilot mcp add google-analytics -- uvx google-analytics-mcp
```
This writes to `~/.copilot/mcp-config.json`.
2. Open that file and confirm the entry carries your values:
```json
{
  "mcpServers": {
    "google-analytics": {
      "type": "local",
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
3. In-session alternative: run `/mcp add` inside Copilot CLI and answer the prompts with the same command plus env values.
4. Verify by asking: "List my GA4 properties." You have succeeded when `list_properties` returns rows with no setup error.

## Skills worth loading first

| Skill slug | What you use it for in Copilot |
|---|---|
| `traffic-diagnosis` | You saw sessions move and want the ordered checks |
| `ai-referral-analysis` | You split ChatGPT, Claude, Perplexity, Gemini, Copilot referrals from search |
| `common-metric-names` | Copilot guessed a UA-era name and GA4 rejected it |
| `date-ranges` | You compare two periods and want the two-query pattern |
| `compatible-combinations` | Your dimensions and metrics returned a 400 incompatibility |

Full set of 15 at https://ga4mcp.com/skills/, loaded with `search_skills("<slug>")`.

## Running your first query

Ask: "How much traffic came from AI assistants last month?"

Your agent should first load `ai-referral-analysis`, then call:
```
get_ga4_data(
  dimensions=["sessionSource"],
  metrics=["sessions"],
  date_range_start="30daysAgo",
  date_range_end="yesterday",
  intent="split AI assistant referrals from search and direct last 30 days"
)
```

Read the period figure from `totals`. GA4 computes it; I stopped hand-summing after watching agents drift.

## Fixing the three errors you will hit

1. **Server missing after add.** Symptom: `/mcp` lists no google-analytics server. Fix: confirm `~/.copilot/mcp-config.json` holds the block above, then restart the CLI session.
2. **Setup error on first call.** Symptom: missing property or credentials. Fix: confirm both `env` values with an absolute key path; for ADC expiry run `gcloud auth application-default login`. `setup_ga4_access` recovers mid-session where prompts are supported.
3. **Invalid dimension, metric, or filter.** Symptom: 400 naming error. Fix: run `search_schema("<keyword>")`, load `common-metric-names` plus `filter-structures`, retry. Offline guide: `get_troubleshooting_guide(topic="schema")`.

## FAQ

**Does GA4 MCP for Copilot use copilot mcp add?**
Yes. `copilot mcp add google-analytics -- uvx google-analytics-mcp` is the path, verified in GitHub Copilot CLI docs today. Config lives at `~/.copilot/mcp-config.json`.

**Is this page about the VS Code Copilot extension?**
No. This page covers Copilot CLI. The VS Code block lives at /ga4-mcp-for-vscode/; the shapes differ (`servers` there, `mcpServers` here).

**Does the installer cover Copilot?**
The site auto-configure list names VS Code paths; for Copilot CLI I show the hand block above because the CLI command is exact and auditable.

**Why does Copilot guess wrong field names?**
Training predates GA4 renames (UA sunset 2023-07-01; conversions renamed to key events 2024-05-06). The `ua-to-ga4` skill maps each old name.

**Is usage read-only and private?**
Yes. Tools read metadata and reports; they change nothing. Traffic runs from your machine to the GA4 Data API. Anonymous counts stop with `DISABLE_TELEMETRY=1`.

**Why does the repo read 2.11.5 when the site says 2.11.4?**
Main moved ahead of the site label at fetch today. I quote 2.11.4 for installs and state the gap here.

## Freshness and machine links

Verified 2026-10-09 against https://ga4mcp.com/ (v2.11.4), https://ga4mcp.com/setup/, https://ga4mcp.com/skills/, GitHub Copilot CLI MCP docs, and repo raw `pyproject.toml` 2.11.5.

Version gap (2026-10-09): repo `pyproject.toml` reads 2.11.5 [source: repo pyproject.toml, verified this run] while the live site labels v2.11.4 [source: https://ga4mcp.com/ fetch 2026-10-09]; installs on this page quote the site label.

Machine: https://ga4mcp.com/llms.txt, https://ga4mcp.com/data/tools.json, https://ga4mcp.com/data/skills.json.

## Breadcrumb

Hub (/ga4-mcp-for-every-harness/) / VS Code (/ga4-mcp-for-vscode/) / GA4 MCP for Copilot (you are here).
