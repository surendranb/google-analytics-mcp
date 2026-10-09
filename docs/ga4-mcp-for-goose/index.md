# GA4 MCP for Goose: Setup, Skills and First Query


I query GA4 from inside Goose with the same server I run in Pi and OpenCode. GA4 MCP for Goose gives you that: one entry under `extensions` in `~/.config/goose/config.yaml`, your property ID plus credentials in `env`, then plain questions answered from your own property schema.

## Proof strip

- Site lists **v2.11.4**, **MIT**, **15 skills**, **11 tools** (verified 2026-10-09 at https://ga4mcp.com/).
- One-line installer: `https://ga4.builditwithai.xyz/install`. Runtimes: `uvx google-analytics-mcp` and `npx -y @surendranb/google-analytics-mcp`.
- Goose path verified today: `~/.config/goose/config.yaml` with `extensions` entries; stdio `cmd`/`args`/`envs` plus `type: stdio`; `goose configure` wizard adds extensions (Goose configuration docs).
- Native note verified today: Block Goose is Apache 2.0 with native MCP integration in CLI plus Desktop.
- Repo `pyproject.toml` reads 2.11.5 today, ahead of site 2.11.4; I quote the site label.
- Read-only, local stdio. Telemetry off with `DISABLE_TELEMETRY=1` or `DO_NOT_TRACK=1`.

## Configuring Goose to launch the server

Prerequisites: numeric `GA4_PROPERTY_ID` (Admin, Property details, not the `G-` ID), plus a service-account JSON path or `gcloud auth application-default login`. Keep the JSON path absolute.

1. Run the wizard or edit the file directly. Wizard:
```bash
goose configure
```
Choose Add Extension, Command-line (stdio), and answer with the values in step 2.
2. Direct edit of `~/.config/goose/config.yaml`:
```yaml
extensions:
  google-analytics:
    name: google-analytics
    cmd: uvx
    args: ["google-analytics-mcp"]
    envs:
      GA4_PROPERTY_ID: "123456789"
      GOOGLE_APPLICATION_CREDENTIALS: "/absolute/path/to/key.json"
    type: stdio
    enabled: true
    timeout: 300
```
Goose uses `extensions` with `cmd`/`envs`, not `mcpServers` with `command`/`env`; I keep the keys exact so JSON snippets do not get pasted raw.
3. Restart Goose so it picks up the new extension.
4. Verify by asking: "List my GA4 properties." You have succeeded when `list_properties` returns rows with no setup error.

## Skills worth loading first

| Skill slug | What you use it for in Goose |
|---|---|
| `traffic-diagnosis` | You saw sessions move and want the ordered checks |
| `channel-acquisition` | You want sessions split by source, medium, channel group |
| `common-metric-names` | Your field name failed and you want the working GA4 name |
| `geo-device-segmentation` | You split users by country, city, device |
| `date-ranges` | You compare two periods and want the two-query pattern |

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

Read the period figure from `totals`. GA4 computes that block; hand sums drift and I stopped doing them.

## Fixing the three errors you will hit

1. **Extension missing after edit.** Symptom: Goose lists no google-analytics extension. Fix: confirm the file is `~/.config/goose/config.yaml` with top-level `extensions` (not `mcpServers`), valid YAML, then restart Goose.
2. **Setup error on first call.** Symptom: missing property or credentials. Fix: confirm both `envs` values with an absolute key path; for ADC expiry run `gcloud auth application-default login`. `setup_ga4_access` recovers mid-session where prompts are supported.
3. **Invalid dimension, metric, or filter.** Symptom: 400 naming error. Fix: run `search_schema("<keyword>")`, load `common-metric-names` plus `compatible-combinations`, retry. Offline guide: `get_troubleshooting_guide(topic="schema")`.

## FAQ

**Does GA4 MCP for Goose use config.yaml?**
Yes. `~/.config/goose/config.yaml` with the `extensions` block above, verified in Goose configuration docs today.

**Why cmd and envs instead of command and env?**
Goose YAML uses `cmd`/`envs`; JSON clients use `command`/`env`. The names differ by client and I keep each page exact.

**Does goose configure cover this server?**
Yes as a wizard. It writes the same extension entry; the YAML above is the auditable form.

**Why does the agent guess wrong field names?**
Training predates GA4 renames (UA sunset 2023-07-01; conversions renamed to key events 2024-05-06). The `ua-to-ga4` skill maps each old name.

**Is usage read-only and private?**
Yes. Tools read metadata and reports; they change nothing. Traffic runs from your machine to the GA4 Data API. Anonymous counts stop with `DISABLE_TELEMETRY=1`.

**Why does the repo read 2.11.5 when the site says 2.11.4?**
Main moved ahead of the site label at fetch today. I quote 2.11.4 for installs and state the gap here.

## Freshness and machine links

Verified 2026-10-09 against https://ga4mcp.com/ (v2.11.4), https://ga4mcp.com/setup/, https://ga4mcp.com/skills/, Goose configuration docs, and repo raw `pyproject.toml` 2.11.5.

Version gap (2026-10-09): repo `pyproject.toml` reads 2.11.5 [source: repo pyproject.toml, verified this run] while the live site labels v2.11.4 [source: https://ga4mcp.com/ fetch 2026-10-09]; installs on this page quote the site label.

Machine: https://ga4mcp.com/llms.txt, https://ga4mcp.com/data/tools.json, https://ga4mcp.com/data/skills.json.

## Breadcrumb

Hub (/ga4-mcp-for-every-harness/) / GA4 MCP for Goose (you are here).
