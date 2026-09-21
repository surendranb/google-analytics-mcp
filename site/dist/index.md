---
title: GA4 MCP Server — Google Analytics 4 for AI Agents
description: Google Analytics MCP server for AI agents — query GA4 from Claude, Cursor, or any MCP client. Schema discovery, totals computed by GA4, 15 skills.
url: https://ga4mcp.com/
type: website
site: https://ga4mcp.com
updated: 2026-09-21
license: MIT
---

# GA4 MCP Server

> Google Analytics 4 for AI agents.

Point Claude, Cursor, or any MCP client at your GA4 property. The server reads your property's real schema
before it writes a query, asks GA4 for period totals instead of letting the model sum rows, and keeps 15
analytical skills one call away.

v2.11.4 · MIT · PyPI + npm + one-line installer · Not affiliated with Google

- Install in one line: `#install` below
- Setup guide: https://ga4mcp.com/setup/ · [markdown](https://ga4mcp.com/setup/index.md)
- Repo: https://github.com/surendranb/google-analytics-mcp

## Install

Three ways in. The installer finds your client and writes the config entry; the runtime commands drop into
any MCP client's config.

```bash
# Universal installer (auto-configures your client)
curl -fsSL "https://ga4.builditwithai.xyz/install" | bash

# uvx
uvx google-analytics-mcp

# npx
npx -y @surendranb/google-analytics-mcp

# Claude Code users
claude mcp add google-analytics -- uvx google-analytics-mcp
```

Before the first query, set `GA4_PROPERTY_ID` and `GOOGLE_APPLICATION_CREDENTIALS`. Both are covered in
Quick start below.

## Works with your client

No hand-edited JSON needed for most setups.

- Claude Desktop
- Claude Code
- Cursor
- VS Code (Cline, Roo Code)
- Continue.dev
- Windsurf
- Zed
- Google Antigravity
- OpenCode
- Gemini CLI (extension in the repo)

The server speaks MCP over stdio. If your client can launch a local MCP server, a manual config snippet is
all it takes; the repo has snippets for each client above.

## Why this server

### Field names checked against your property

search_schema and the category browsers read a schema fetched from your own GA4 property at boot. get_ga4_data checks every dimension and metric before the API call, so an invalid name comes back with the fix instead of a raw 400.

### 15 analytical skills, loaded on request

Traffic drops, channel acquisition, ecommerce, AI referrals, bot detection, field-name maps. Skills are fetched from the repo when asked, so adding one doesn't need a package release.

### Totals computed by GA4, not your model

Multi-row pulls return a totals block from GA4's own aggregation, plus a note telling the agent to read the period figure there instead of summing rows itself.

### Defaults that stop runaway queries

Row counts are estimated before the fetch by default. A query that would return more than 2,500 rows comes back with a warning and concrete ways to narrow it, unless you pass proceed_with_large_dataset=True. Common metric aliases (conversions → keyEvents) and filter-shape repairs fix the mistakes models actually make.

### The boring failures have built-in fixes

Setup, IAM, and schema guides ship inside the package and work offline. On clients that support prompts, setup_ga4_access collects a missing property ID or credentials path mid-session and reconnects without a restart.

### Telemetry you can switch off

Anonymous diagnostics only: no queries, no credentials, no analytics data. Set DISABLE_TELEMETRY=1 or DO_NOT_TRACK=1 and the server stops sending, and stops writing its local ID file. MIT licensed, no account.

## This server vs Google's official Analytics MCP server

Both servers are real, and both are free to use. Google publishes its own Analytics MCP server (labeled
experimental, Apache-2.0). This one is community-built and MIT-licensed.

| | This server | Google's server |
|---|---|---|
| Built by | Community project by Surendran B (BuildItWithAI); not affiliated with Google | Google's Analytics organization |
| Status | v2.11.4, MIT | Labeled "Experimental", Apache-2.0 |
| API coverage | GA4 Data API: reporting + metadata | Admin API + Data API: account and property info, Google Ads links, core, funnel, and realtime reports |
| Setup | One-line installer, or uvx / npx; property ID + credentials | pipx run analytics-mcp; requires a Google Cloud project ID and enabling the Admin + Data APIs |
| Extras | 15 skills loaded at call time, pre-flight schema checks, GA4-computed totals, row-cap guard, offline troubleshooting guides, in-session setup recovery | Vendor-maintained reference toolset |

**Reach for Google's server if** you want the vendor-maintained baseline, funnel reports, or Google Ads
account links.

**Reach for this one if** you're driving an agent through day-to-day analysis and want it to stop guessing
field names, read period totals instead of summing rows, and follow a documented method per question.

GA4 MCP is an independent open-source project. It isn't affiliated with, endorsed by, or sponsored by Google.
"Google Analytics" is a trademark of Google LLC.

## Quick start

### 1. Get credentials and a property ID

Create a service account in Google Cloud Console, download its JSON key, then add the service account's
`client_email` as a **Viewer** on your GA4 property (Admin → Property Access Management). Or run
`gcloud auth application-default login` and use the generated credentials file.

```bash
export GA4_PROPERTY_ID="123456789"                      # numeric ID, Admin → Property details
export GOOGLE_APPLICATION_CREDENTIALS="/absolute/path/to/key.json"
```

Your property ID is the numeric one, not the `G-` measurement ID.

### 2. Install and wire your client

```bash
curl -fsSL "https://ga4.builditwithai.xyz/install" | bash
```

### 3. Ask your first question

"What were my top channels last week?" · "Why did organic traffic drop in the last 7 days?" · "How much
traffic came from AI assistants?"

## Tools

11 tools cover reporting, schema discovery, and the fix paths an agent hits during setup.

- `get_ga4_data(dimensions, metrics, date_range_start, date_range_end, dimension_filter, limit, estimate_only, proceed_with_large_dataset, enable_aggregation, intent)`: Runs a GA4 report and returns rows plus a server-computed totals block from GA4's own aggregation. Estimates row counts first and warns above 2,500 rows.
- `search_schema(keyword)`: Ranks dimension and metric API names for this property. Call it before typing a field name.
- `get_property_schema(-)`: The full dimension and metric schema for the property, standard and custom.
- `list_dimension_categories(-)`: Dimension categories with counts, for browsing instead of guessing.
- `list_metric_categories(-)`: Metric categories with counts.
- `get_dimensions_by_category(category)`: Every dimension in one category, with its description.
- `get_metrics_by_category(category)`: Every metric in one category, with its description.
- `list_properties(account_id (optional))`: The GA4 properties the configured credentials can read.
- `search_skills(query (slug or keyword; empty returns the index))`: Serves one analytical recipe as markdown.
- `get_troubleshooting_guide(topic: setup | iam | schema)`: The fix path for a boot error, a 403, or a filter-shape error. Bundled with the package, works offline.
- `setup_ga4_access(-)`: Collects a missing property ID or credentials path through the client and reconnects without a restart.

Machine-readable: https://ga4mcp.com/data/tools.json

## Skills

- [AI Referral Analysis](https://ga4mcp.com/skills/ai-referral-analysis/index.md): Measure traffic arriving from AI tools — ChatGPT, Claude, Perplexity, Gemini, Copilot, and others — and understand how it behaves compared to other channels.
- [Attribution Scope](https://ga4mcp.com/skills/attribution-scope/index.md): GA4 has three distinct attribution scopes. Using the wrong scope gives misleading results. Choose based on the question you are answering.
- [Bot Traffic Detection](https://ga4mcp.com/skills/bot-traffic-detection/index.md): Identify and exclude bot, scraper, and spam sessions from GA4 data.
- [Channel Acquisition Analysis](https://ga4mcp.com/skills/channel-acquisition/index.md): Break down sessions and users by traffic source, medium, and channel group to understand where your audience comes from and which channels perform best.
- [Common Metric & Dimension Names](https://ga4mcp.com/skills/common-metric-names/index.md): The correct GA4 Data API names for fields models most often get wrong. Use these before calling getga4data — wrong names return a hard error.
- [Compatible Dimension and Metric Combinations](https://ga4mcp.com/skills/compatible-combinations/index.md): GA4 enforces strict rules about which dimensions and metrics can appear in the same request. Incompatible combinations return a 400 error: \"The request's dimensions & metrics are incompatible.\
- [Content Performance Analysis](https://ga4mcp.com/skills/content-performance/index.md): Identify top-performing pages, find underperforming content, and understand engagement patterns across your site.
- [Custom Dimensions and Event Parameters](https://ga4mcp.com/skills/custom-dimensions/index.md): How to find and query property-specific custom dimensions in GA4.
- [Date Ranges](https://ga4mcp.com/skills/date-ranges/index.md): How to specify date ranges in getga4data and how to structure period-over-period comparisons.
- [Ecommerce Analysis](https://ga4mcp.com/skills/ecommerce-analysis/index.md): Revenue, conversion rate, AOV, and funnel drop-off using GA4 ecommerce events.
- [Filter Structures](https://ga4mcp.com/skills/filter-structures/index.md): The correct shape for dimensionfilter in getga4data. Wrong structure returns an \"Invalid dimensionfilter\" error. Use these templates.
- [GA4 API Limitations](https://ga4mcp.com/skills/ga4-limitations/index.md): What this MCP cannot do via the GA4 Data API, and where to go instead. Attempting these will either fail or produce meaningless aggregate data.
- [Geo and Device Segmentation](https://ga4mcp.com/skills/geo-device-segmentation/index.md): Break down user behaviour by country, city, device category, and OS to understand regional patterns and optimise for your key markets.
- [Traffic Change Diagnosis](https://ga4mcp.com/skills/traffic-diagnosis/index.md): Systematically diagnose why traffic changed — spike, drop, or shift in mix. Follow these steps in order. Each step narrows the hypothesis.
- [UA to GA4 Field Name Mapping](https://ga4mcp.com/skills/ua-to-ga4/index.md): Universal Analytics (UA) and GA4 use different names for equivalent concepts. UA was sunset on 2023-07-01; models trained before or around then guess UA field names that no longer exist in the GA4 Data API. On 2024-05-06 GA4 also renamed \"conversions\" to \"key events\" (see the conversions rows below). If a name feels obviously right but returns \"Invalid metric/dimension\", assume your training predates the change and verify with searchschema. This skill gives the correct GA4 Data API name for every common UA metric and dimension.

Machine-readable: https://ga4mcp.com/data/skills.json

## FAQ

### What is MCP?

Model Context Protocol is a standard for connecting AI apps to external tools. Your client launches this server, and the agent gets GA4 querying tools: reporting, schema search, skills, and troubleshooting.

### Does it work with Claude? What about ChatGPT?

Claude Desktop and Claude Code are both covered by the installer, along with Cursor, VS Code (Cline, Roo Code), Continue.dev, Windsurf, Zed, Google Antigravity, and OpenCode. Gemini CLI connects through the repo's extension. ChatGPT isn't in the supported list; this is a local stdio server, so it needs a client that can launch local MCP servers.

### Service account or OAuth?

Both patterns run locally. A service-account JSON key doesn't expire and suits fixed or shared setups. Google Application Default Credentials via gcloud auth application-default login use OAuth user credentials refreshed on your machine. The quick start uses a service account because it has the fewest moving parts.

### Is it free?

Yes. MIT licensed, no account, no seat pricing, no hosted service in the query path. Queries run from your machine straight to Google's GA4 Data API, and your use of Google's APIs is governed by Google's terms and quotas.

### What does it collect, and can I turn telemetry off?

Anonymous usage diagnostics: which tools ran, latency, error codes. No queries, no credentials, no analytics data, no file paths. Set DISABLE_TELEMETRY=1 or DO_NOT_TRACK=1 and nothing is sent; when opted out, the server also stops creating its local ID file. The privacy policy has the full detail.

### How many tools does it ship?

11 in v2.11.4: get_ga4_data for reports, six schema tools for field discovery (search, full schema, and category browsing), plus list_properties, search_skills, get_troubleshooting_guide, and setup_ga4_access.

### Is there an official Google Analytics MCP server?

Yes — Google ships an official Google Analytics MCP server (experimental, Apache-2.0), maintained by Google's Analytics organization, with coverage that includes funnel reports and Google Ads links. This one focuses on agent workflow: schema checks before a query runs, 15 skills on call, GA4-computed totals, and guided setup recovery. The comparison above has the full split.

### Does it support Universal Analytics?

No. UA properties stopped processing data on 2023-07-01, and this server talks to GA4 only. If you're translating old field names, the ua-to-ga4 skill maps every common one.

### Is it read-only?

Yes. Every tool is annotated read-only, and the server reads metadata and reports from the GA4 Data API. It doesn't change your GA4 configuration.

### I'm getting an error. Where do I start?

Ask your agent to run get_troubleshooting_guide(topic="setup"), ("iam"), or ("schema"). The guides are bundled with the package and work offline. setup_ga4_access walks the fix mid-session, and this site's setup, IAM, and schema pages mirror the same steps.

## Machine surfaces

- llms.txt: https://ga4mcp.com/llms.txt
- llms-full.txt: https://ga4mcp.com/llms-full.txt
- sitemap.xml: https://ga4mcp.com/sitemap.xml
- tools.json: https://ga4mcp.com/data/tools.json
- skills.json: https://ga4mcp.com/data/skills.json

---

Open source, MIT, and local. Install it, then ask your first question.

GitHub: https://github.com/surendranb/google-analytics-mcp · PyPI: https://pypi.org/project/google-analytics-mcp/ · npm: https://www.npmjs.com/package/@surendranb/google-analytics-mcp · Installer: https://ga4.builditwithai.xyz/install
