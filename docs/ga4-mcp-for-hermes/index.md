# GA4 MCP for Hermes: Setup, Skills and First Query


I query GA4 from inside Hermes with the same server I run in Claude Code. GA4 MCP for Hermes gives you that: one entry under `mcp_servers` in `~/.hermes/config.yaml`, your property ID plus credentials in `env`, then plain questions answered from your own property schema.

## Proof strip

- Site lists **v2.11.4**, **MIT**, **15 skills**, **11 tools** (verified 2026-10-09 at https://ga4mcp.com/).
- One-line installer: `https://ga4.builditwithai.xyz/install`. Runtimes: `uvx google-analytics-mcp` and `npx -y @surendranb/google-analytics-mcp`.
- Hermes path verified today: `~/.hermes/config.yaml` under `mcp_servers` with `command`/`args`/`env` for stdio and `url` for HTTP; `hermes mcp add/test`, `hermes chat`; standard install ships MCP, no extra step (Hermes MCP docs).
- Mapping verified today: `~/.claude.json` `mcpServers` maps to Hermes `mcp_servers`; `hermes import-agent claude-code` migrates it.
- Repo `pyproject.toml` reads 2.11.5 today, ahead of site 2.11.4; I quote the site label.
- Read-only, local stdio. Telemetry off with `DISABLE_TELEMETRY=1` or `DO_NOT_TRACK=1`.

## Configuring Hermes to launch the server

Prerequisites: numeric `GA4_PROPERTY_ID` (Admin, Property details, not the `G-` ID), plus a service-account JSON path or `gcloud auth application-default login`. Keep the JSON path absolute. Secrets belong in `~/.hermes/.env`; non-secret settings belong in `config.yaml`.

1. Open `~/.hermes/config.yaml` and add:
```yaml
mcp_servers:
  google-analytics:
    command: "uvx"
    args: ["google-analytics-mcp"]
    env:
      GA4_PROPERTY_ID: "123456789"
      GOOGLE_APPLICATION_CREDENTIALS: "/absolute/path/to/key.json"
```
2. Command alternative:
```bash
hermes mcp add google-analytics --command uvx --args google-analytics-mcp
```
Then add the two `env` values in `config.yaml` by hand.
3. Test the connection:
```bash
hermes mcp test google-analytics
hermes chat
```
Exit 0 means the server connected and listed tools.
4. Verify by asking: "List my GA4 properties." You have succeeded when `list_properties` returns rows with no setup error.

## Skills worth loading first

| Skill slug | What you use it for in Hermes |
|---|---|
| `traffic-diagnosis` | You saw sessions move and want the ordered checks |
| `common-metric-names` | Your field name failed and you want the working GA4 name |
| `bot-traffic-detection` | You strip bot, scraper, spam sessions before reading a trend |
| `date-ranges` | You compare two periods and want the two-query pattern |
| `filter-structures` | Your dimension filter returned an invalid-filter error |

Full set of 15 at https://ga4mcp.com/skills/, loaded with `search_skills("<slug>")`.

## Running your first query

Ask: "Did bots inflate last week's sessions?"

Your agent should first load `bot-traffic-detection`, then call:
```
get_ga4_data(
  dimensions=["date"],
  metrics=["sessions"],
  date_range_start="7daysAgo",
  date_range_end="yesterday",
  intent="check sessions trend last 7 days before bot split"
)
```

Read the period figure from `totals`. GA4 computes it; I stopped hand-summing after watching agents drift.

## Fixing the three errors you will hit

1. **No MCP servers configured.** Symptom: Hermes reports no servers. Fix: confirm the key is `mcp_servers` with underscore in `~/.hermes/config.yaml` (not `mcpServers`), YAML indent exact, then restart.
2. **Setup error on first call.** Symptom: missing property or credentials. Fix: confirm both `env` values resolve (`${VAR}` and `${env:VAR}` both read process env plus `.env`); for ADC expiry run `gcloud auth application-default login`. `setup_ga4_access` recovers mid-session where prompts are supported.
3. **Invalid dimension, metric, or filter.** Symptom: 400 naming error. Fix: run `search_schema("<keyword>")`, load `common-metric-names` plus `compatible-combinations`, retry. Offline guide: `get_troubleshooting_guide(topic="schema")`.

## FAQ

**Does GA4 MCP for Hermes use config.yaml?**
Yes. `~/.hermes/config.yaml` under `mcp_servers`, verified in Hermes MCP docs today. YAML, not JSON; the underscore key matters.

**Does hermes import-agent claude-code move my GA4 entry?**
Yes. It migrates `mcpServers` plus skills and instructions from Claude Code into `mcp_servers` automatically.

**Does the standard install include MCP?**
Yes. No extra package step. The `uv pip install -e .[mcp]` line in older guides covers source checkouts without extras.

**Why does the agent guess wrong field names?**
Training predates GA4 renames (UA sunset 2023-07-01; conversions renamed to key events 2024-05-06). The `ua-to-ga4` skill maps each old name.

**Is usage read-only and private?**
Yes. Tools read metadata and reports; they change nothing. Traffic runs from your machine to the GA4 Data API. Anonymous counts stop with `DISABLE_TELEMETRY=1`.

**Why does the repo read 2.11.5 when the site says 2.11.4?**
Main moved ahead of the site label at fetch today. I quote 2.11.4 for installs and state the gap here.

## Freshness and machine links

Verified 2026-10-09 against https://ga4mcp.com/ (v2.11.4), https://ga4mcp.com/setup/, https://ga4mcp.com/skills/, Hermes MCP plus config-reference docs, and repo raw `pyproject.toml` 2.11.5.

Version gap (2026-10-09): repo `pyproject.toml` reads 2.11.5 [source: repo pyproject.toml, verified this run] while the live site labels v2.11.4 [source: https://ga4mcp.com/ fetch 2026-10-09]; installs on this page quote the site label.

Machine: https://ga4mcp.com/llms.txt, https://ga4mcp.com/data/tools.json, https://ga4mcp.com/data/skills.json.

## Breadcrumb

Hub (/ga4-mcp-for-every-harness/) / GA4 MCP for Hermes (you are here).
