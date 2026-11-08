# GA4 MCP Server

> Query Google Analytics 4 from your AI agent. Twelve tools, sixteen analytical skills, schema validation before every query. MIT, local, read-only.

Canonical URL: https://ga4mcp.com/
Version: v2.11.7
Repository: https://github.com/surendranb/google-analytics-mcp

Ask GA4 a question. Get the answer an analyst would give. One Model Context Protocol (MCP) server for Claude, Cursor, Codex, Gemini CLI and 14 more clients. Twelve tools, sixteen analytical skills, and a schema check that validates every field name against your property before the query runs.

## 1-Line Universal Install

```bash
curl -fsSL "https://ga4.builditwithai.xyz/install" | bash
```

Or launch via package runners:
```bash
uvx google-analytics-mcp
npx -y @surendranb/google-analytics-mcp
```

## Required Credentials

- `GA4_PROPERTY_ID`: 9-digit numeric Property ID (from Admin -> Property Settings -> Property Details).
- `GOOGLE_APPLICATION_CREDENTIALS`: Absolute path to a Google Cloud Service Account JSON key with Viewer access on the GA4 property.

## Key Capabilities

- **Schema Check Before Query**: Validates every dimension and metric against your live property schema. Replaces 400 errors with correct field suggestions.
- **Server-Side Computed Totals**: Returns pre-calculated metric totals so LLMs don't improperly sum non-additive rates or active users.
- **16 Embedded Analytical Skills**: Playbooks for traffic drops, e-commerce funnels, bot detection, and AI referral attribution.
- **Zero Third-Party Relays**: Local stdio process running on your machine. All queries go directly from your machine to Google Analytics APIs.

## Supported Clients (17)

- [Antigravity IDE](https://ga4mcp.com/ga4-mcp-for-antigravity-ide/) ([markdown](https://ga4mcp.com/ga4-mcp-for-antigravity-ide/index.md)): The Antigravity IDE uses the same mcp_config.json schema as the App and CLI. Manage it from the agent panel's MCP Servers screen, or edit the file directly.
- [Antigravity](https://ga4mcp.com/ga4-mcp-for-antigravity/) ([markdown](https://ga4mcp.com/ga4-mcp-for-antigravity/index.md)): Add the GA4 MCP server to Antigravity, App, IDE or CLI. All three read the same mcp_config.json schema, and the App registers servers through the settings UI.
- [Claude](https://ga4mcp.com/ga4-mcp-for-claude/) ([markdown](https://ga4mcp.com/ga4-mcp-for-claude/index.md)): Add the GA4 MCP server to Claude Code with one CLI command, or to Claude Desktop with one JSON entry. Includes five production natural language prompts.
- [Codex](https://ga4mcp.com/ga4-mcp-for-codex/) ([markdown](https://ga4mcp.com/ga4-mcp-for-codex/index.md)): Add the GA4 MCP server to OpenAI Codex. Codex uses TOML, not JSON, and splits environment handling into env and env_vars — the two are not interchangeable.
- [Cursor](https://ga4mcp.com/ga4-mcp-for-cursor/) ([markdown](https://ga4mcp.com/ga4-mcp-for-cursor/index.md)): Add the GA4 MCP server to Cursor with a project or global mcp.json entry. Includes the type-field inconsistency Cursor's own docs carry.
- [DeepSeek Harness](https://ga4mcp.com/ga4-mcp-for-deepseek/) ([markdown](https://ga4mcp.com/ga4-mcp-for-deepseek/index.md)): Add the GA4 MCP server to DeepSeek Harness with one entry in your patch layer. Tools then appear as mcp__ga4__get_ga4_data inside the session.
- [Devin Desktop](https://ga4mcp.com/ga4-mcp-for-devin-desktop/) ([markdown](https://ga4mcp.com/ga4-mcp-for-devin-desktop/index.md)): Add the GA4 MCP server to Devin Desktop, the client formerly named Windsurf. Includes the config path conflict between two live vendor pages.
- [Gemini CLI](https://ga4mcp.com/ga4-mcp-for-gemini/) ([markdown](https://ga4mcp.com/ga4-mcp-for-gemini/index.md)): Add the GA4 MCP server to Gemini CLI. The scope flag defaults to project, so the entry lands in .gemini/settings.json and not your home directory.
- [Goose](https://ga4mcp.com/ga4-mcp-for-goose/) ([markdown](https://ga4mcp.com/ga4-mcp-for-goose/index.md)): Add the GA4 MCP server to Goose. Goose uses YAML, calls the command cmd, and calls the environment block envs. All three differ from the usual shape.
- [Hermes](https://ga4mcp.com/ga4-mcp-for-hermes/) ([markdown](https://ga4mcp.com/ga4-mcp-for-hermes/index.md)): Add the GA4 MCP server to Hermes Agent. The root key is mcp_servers in YAML, not mcpServers in JSON, so a Claude snippet silently adds nothing.
- [Kiro](https://ga4mcp.com/ga4-mcp-for-kiro/) ([markdown](https://ga4mcp.com/ga4-mcp-for-kiro/index.md)): Add the GA4 MCP server to Kiro. Kiro hot-reloads mcp.json on save, so no restart is needed, and it carries per-tool approval settings the other clients do not.
- [OpenClaw](https://ga4mcp.com/ga4-mcp-for-openclaw/) ([markdown](https://ga4mcp.com/ga4-mcp-for-openclaw/index.md)): Add the GA4 MCP server to OpenClaw with openclaw mcp add, stored under mcp.servers in ~/.openclaw/openclaw.json. No plugin needed.
- [OpenCode](https://ga4mcp.com/ga4-mcp-for-opencode/) ([markdown](https://ga4mcp.com/ga4-mcp-for-opencode/index.md)): Add the GA4 MCP server to OpenCode. The config is the furthest from the common shape: root key mcp, type local, command as an array, environment not env.
- [Pi](https://ga4mcp.com/ga4-mcp-for-pi/) ([markdown](https://ga4mcp.com/ga4-mcp-for-pi/index.md)): Add the GA4 MCP server to Pi with one mcpServers entry in the agent directory, or with pi mcp add. Tools appear as mcp__ga4__get_ga4_data.
- [VS Code](https://ga4mcp.com/ga4-mcp-for-vscode/) ([markdown](https://ga4mcp.com/ga4-mcp-for-vscode/index.md)): Add GA4 MCP to VS Code Copilot agent mode. Includes the critical root key distinction between .vscode/mcp.json and .mcp.json plus sample queries.
- [ZCode](https://ga4mcp.com/ga4-mcp-for-zcode/) ([markdown](https://ga4mcp.com/ga4-mcp-for-zcode/index.md)): Add the GA4 MCP server to ZCode. Servers live under mcp.servers in ~/.zcode/cli/config.json, and a competing .agents/mcp.json is skipped entirely, not merged.
- [Zed](https://ga4mcp.com/ga4-mcp-for-zed/) ([markdown](https://ga4mcp.com/ga4-mcp-for-zed/index.md)): Add the GA4 MCP server to Zed. Zed calls them context servers, not mcpServers, and the entry lives in Zed's own settings file.

## Analytical Skills (17)

- [Track AI Referral Traffic in Google Analytics 4](https://ga4mcp.com/skills/ai-referral-analysis/) ([markdown](https://ga4mcp.com/skills/ai-referral-analysis/index.md)): How to track and measure traffic from ChatGPT, Claude, Perplexity, and Gemini in GA4. Exact dimension filters, regex patterns, and channel comparison rules.
- [GA4 Attribution Scope: User vs. Session vs. Event](https://ga4mcp.com/skills/attribution-scope/) ([markdown](https://ga4mcp.com/skills/attribution-scope/index.md)): Why session, user, and event metrics never match in GA4. Rules for pairing dimensions and metrics across user-scoped, session-scoped, and event-scoped models.
- [Identify & Filter Bot Traffic in Google Analytics 4](https://ga4mcp.com/skills/bot-traffic-detection/) ([markdown](https://ga4mcp.com/skills/bot-traffic-detection/index.md)): Detect and filter automated bot spikes in Google Analytics 4. Patterns for datacenter ASN spikes, zero-second sessions, and single-page screenPageViews.
- [GA4 Channel Acquisition: Default Grouping Rules](https://ga4mcp.com/skills/channel-acquisition/) ([markdown](https://ga4mcp.com/skills/channel-acquisition/index.md)): How GA4 Default Channel Groups work, how to audit channel performance, and how to spot traffic falling into Unassigned or Direct due to broken UTM parameters.
- [GA4 Dimensions and Metrics Reference: API Field Names](https://ga4mcp.com/skills/common-metric-names/) ([markdown](https://ga4mcp.com/skills/common-metric-names/index.md)): Exact API field names for GA4 Data API queries. Avoid 400 errors from Universal Analytics names like ga:sessions or pageviews by using valid GA4 schema.
- [Compatible Dimension & Metric Combinations in GA4](https://ga4mcp.com/skills/compatible-combinations/) ([markdown](https://ga4mcp.com/skills/compatible-combinations/index.md)): Which dimensions and metrics can be queried together in GA4 without triggering incompatible scope errors. Matrix of user, session, and event-level pairings.
- [GA4 Content Performance: Views & Engagement Rates](https://ga4mcp.com/skills/content-performance/) ([markdown](https://ga4mcp.com/skills/content-performance/index.md)): Evaluate landing pages and blog content in GA4: screenPageViews, average engagement time, bounce rates, and organic search conversions per URL.
- [GA4 Custom Dimensions & Event Parameters Guide](https://ga4mcp.com/skills/custom-dimensions/) ([markdown](https://ga4mcp.com/skills/custom-dimensions/index.md)): Query custom dimensions and event parameters in the GA4 Data API. How to find parameter names, register them in GA4 Admin, and query custom event schemas.
- [GA4 API Date Ranges: Syntax, Offsets & Comparisons](https://ga4mcp.com/skills/date-ranges/) ([markdown](https://ga4mcp.com/skills/date-ranges/index.md)): Allowed date string formats for the GA4 Data API: YYYY-MM-DD, today, yesterday, 7daysAgo, 30daysAgo, and multi-range period comparisons without API errors.
- [GA4 Ecommerce Analysis: Revenue, AOV & Funnel Drop-off](https://ga4mcp.com/skills/ecommerce-analysis/) ([markdown](https://ga4mcp.com/skills/ecommerce-analysis/index.md)): Analyze GA4 ecommerce performance: purchase revenue, average order value, checkout funnel drop-off, and item revenue by acquisition channel.
- [GA4 API Filter Expressions & Dimension Regex Syntax](https://ga4mcp.com/skills/filter-structures/) ([markdown](https://ga4mcp.com/skills/filter-structures/index.md)): Copy-paste filter templates for the GA4 Data API: exact match, beginsWith, contains, regex, AND/OR group expressions, and inListFilter structures.
- [GA4 API Limitations, Quotas & Cardinality Boundaries](https://ga4mcp.com/skills/ga4-limitations/) ([markdown](https://ga4mcp.com/skills/ga4-limitations/index.md)): GA4 Data API boundaries: 10-dimension limit, 100,000 row caps, hourly token quotas, and sampling thresholds. How to query safely within API limits.
- [GCP Service Account Setup for GA4 Data API](https://ga4mcp.com/skills/gcp-setup/) ([markdown](https://ga4mcp.com/skills/gcp-setup/index.md)): Step-by-step GCP service account provisioning for the GA4 Data API. Create JSON keys, assign the Viewer role in GA4 Admin, and avoid common 403 errors.
- [Geo and Device Segmentation](https://ga4mcp.com/skills/geo-device-segmentation/) ([markdown](https://ga4mcp.com/skills/geo-device-segmentation/index.md)): Segment GA4 data by country, city, device category, and browser. Spot localization opportunities and mobile conversion drops with ready queries.
- [GA4 Service Account Setup Guide](https://ga4mcp.com/skills/service-account-setup/) ([markdown](https://ga4mcp.com/skills/service-account-setup/index.md)): Step-by-step GA4 service account setup. Generate Google Cloud JSON keys, enable the Data API, and grant Viewer permissions in Google Analytics Admin.
- [Diagnose GA4 Traffic Drops: Step-by-Step Triage](https://ga4mcp.com/skills/traffic-diagnosis/) ([markdown](https://ga4mcp.com/skills/traffic-diagnosis/index.md)): A six-step triage framework to diagnose GA4 traffic drops. Isolate channel shifts, check tracking snippet errors, and distinguish real drops from bot drops.
- [Universal Analytics to GA4 Field Name Mapping](https://ga4mcp.com/skills/ua-to-ga4/) ([markdown](https://ga4mcp.com/skills/ua-to-ga4/index.md)): Mapping table from Universal Analytics (UA) field names to Google Analytics 4 (GA4) Data API names. Replace ga:pageviews, ga:bounces, and ga:users correctly.

## Tools (12)

- `check_for_updates`: Check PyPI for newer versions of this MCP server and get upgrade instructions.
- `list_properties`: List all GA4 properties associated with an account.
- `search_schema`: Search for a keyword across all dimensions and metrics for this property.
- `get_property_schema`: Returns the complete schema for the configured GA4 property, including all available dimensions and metrics (standard and custom).
- `list_dimension_categories`: List all dimension categories for this GA4 property, with a count of dimensions in each category.
- `list_metric_categories`: List all metric categories for this GA4 property, with a count of metrics in each category.
- `get_dimensions_by_category`: Return all dimensions in a specific category with their API names and descriptions.
- `get_metrics_by_category`: Return all metrics in a specific category with their API names and descriptions.
- `get_ga4_data`: Retrieve GA4 data with built-in intelligence for better and safer results.
- `get_troubleshooting_guide`: Returns the troubleshooting/setup guide for a topic, served from inside the server (no network needed).
- `search_skills`: Fetch analytical recipes and how-to guides from the GA4 skills library.
- `setup_ga4_access`: Interactively fix a broken GA4 MCP setup (missing property ID, missing or expired credentials, or missing GA4 access) by asking the user for the needed input through...

## Documentation & Guides

- [GA4 MCP client setup — the config each one expects](https://ga4mcp.com/ga4-mcp-for-every-harness/) ([markdown](https://ga4mcp.com/ga4-mcp-for-every-harness/index.md)): Eleven client guides, each with the config shape that client documents. MCP is not portable: four of these use a different root key, so a snippet from one will silently fail in another.
- [Connect Antigravity IDE to GA4 (Setup & Queries)](https://ga4mcp.com/ga4-mcp-for-antigravity-ide/) ([markdown](https://ga4mcp.com/ga4-mcp-for-antigravity-ide/index.md)): The Antigravity IDE uses the same mcp_config.json schema as the App and CLI. Manage it from the agent panel's MCP Servers screen, or edit the file directly.
- [Connect Google Antigravity to GA4 (App, IDE & CLI)](https://ga4mcp.com/ga4-mcp-for-antigravity/) ([markdown](https://ga4mcp.com/ga4-mcp-for-antigravity/index.md)): Add the GA4 MCP server to Antigravity, App, IDE or CLI. All three read the same mcp_config.json schema, and the App registers servers through the settings UI.
- [Connect Claude to Google Analytics 4 (Code & Desktop)](https://ga4mcp.com/ga4-mcp-for-claude/) ([markdown](https://ga4mcp.com/ga4-mcp-for-claude/index.md)): Add the GA4 MCP server to Claude Code with one CLI command, or to Claude Desktop with one JSON entry. Includes five production natural language prompts.
- [Connect OpenAI Codex to Google Analytics 4 (Data API)](https://ga4mcp.com/ga4-mcp-for-codex/) ([markdown](https://ga4mcp.com/ga4-mcp-for-codex/index.md)): Add the GA4 MCP server to OpenAI Codex. Codex uses TOML, not JSON, and splits environment handling into env and env_vars — the two are not interchangeable.
- [Connect Cursor to Google Analytics 4 (Setup & Queries)](https://ga4mcp.com/ga4-mcp-for-cursor/) ([markdown](https://ga4mcp.com/ga4-mcp-for-cursor/index.md)): Add the GA4 MCP server to Cursor with a project or global mcp.json entry. Includes the type-field inconsistency Cursor's own docs carry.
- [Connect DeepSeek Harness to GA4 (Data API Setup)](https://ga4mcp.com/ga4-mcp-for-deepseek/) ([markdown](https://ga4mcp.com/ga4-mcp-for-deepseek/index.md)): Add the GA4 MCP server to DeepSeek Harness with one entry in your patch layer. Tools then appear as mcp__ga4__get_ga4_data inside the session.
- [Connect Devin Desktop (Windsurf) to GA4 MCP](https://ga4mcp.com/ga4-mcp-for-devin-desktop/) ([markdown](https://ga4mcp.com/ga4-mcp-for-devin-desktop/index.md)): Add the GA4 MCP server to Devin Desktop, the client formerly named Windsurf. Includes the config path conflict between two live vendor pages.
- [Connect Gemini CLI to Google Analytics 4 (Data API)](https://ga4mcp.com/ga4-mcp-for-gemini/) ([markdown](https://ga4mcp.com/ga4-mcp-for-gemini/index.md)): Add the GA4 MCP server to Gemini CLI. The scope flag defaults to project, so the entry lands in .gemini/settings.json and not your home directory.
- [Connect Goose CLI to Google Analytics 4 (MCP Setup)](https://ga4mcp.com/ga4-mcp-for-goose/) ([markdown](https://ga4mcp.com/ga4-mcp-for-goose/index.md)): Add the GA4 MCP server to Goose. Goose uses YAML, calls the command cmd, and calls the environment block envs. All three differ from the usual shape.
- [Connect Hermes Agent to Google Analytics 4 (MCP Setup)](https://ga4mcp.com/ga4-mcp-for-hermes/) ([markdown](https://ga4mcp.com/ga4-mcp-for-hermes/index.md)): Add the GA4 MCP server to Hermes Agent. The root key is mcp_servers in YAML, not mcpServers in JSON, so a Claude snippet silently adds nothing.
- [Connect Kiro IDE to Google Analytics 4 (MCP Setup)](https://ga4mcp.com/ga4-mcp-for-kiro/) ([markdown](https://ga4mcp.com/ga4-mcp-for-kiro/index.md)): Add the GA4 MCP server to Kiro. Kiro hot-reloads mcp.json on save, so no restart is needed, and it carries per-tool approval settings the other clients do not.
- [Connect OpenClaw to Google Analytics 4 (MCP Setup)](https://ga4mcp.com/ga4-mcp-for-openclaw/) ([markdown](https://ga4mcp.com/ga4-mcp-for-openclaw/index.md)): Add the GA4 MCP server to OpenClaw with openclaw mcp add, stored under mcp.servers in ~/.openclaw/openclaw.json. No plugin needed.
- [Connect OpenCode to Google Analytics 4 (Local stdio)](https://ga4mcp.com/ga4-mcp-for-opencode/) ([markdown](https://ga4mcp.com/ga4-mcp-for-opencode/index.md)): Add the GA4 MCP server to OpenCode. The config is the furthest from the common shape: root key mcp, type local, command as an array, environment not env.
- [Connect Pi Agent to Google Analytics 4 (MCP Setup)](https://ga4mcp.com/ga4-mcp-for-pi/) ([markdown](https://ga4mcp.com/ga4-mcp-for-pi/index.md)): Add the GA4 MCP server to Pi with one mcpServers entry in the agent directory, or with pi mcp add. Tools appear as mcp__ga4__get_ga4_data.
- [Connect VS Code & Copilot to Google Analytics 4](https://ga4mcp.com/ga4-mcp-for-vscode/) ([markdown](https://ga4mcp.com/ga4-mcp-for-vscode/index.md)): Add GA4 MCP to VS Code Copilot agent mode. Includes the critical root key distinction between .vscode/mcp.json and .mcp.json plus sample queries.
- [Connect ZCode Harness to Google Analytics 4 (MCP)](https://ga4mcp.com/ga4-mcp-for-zcode/) ([markdown](https://ga4mcp.com/ga4-mcp-for-zcode/index.md)): Add the GA4 MCP server to ZCode. Servers live under mcp.servers in ~/.zcode/cli/config.json, and a competing .agents/mcp.json is skipped entirely, not merged.
- [Connect Zed Editor to Google Analytics 4 (Setup Guide)](https://ga4mcp.com/ga4-mcp-for-zed/) ([markdown](https://ga4mcp.com/ga4-mcp-for-zed/index.md)): Add the GA4 MCP server to Zed. Zed calls them context servers, not mcpServers, and the entry lives in Zed's own settings file.
- [GA4 plugin for Claude Code](https://ga4mcp.com/ga4-plugin-for-claude-code/) ([markdown](https://ga4mcp.com/ga4-plugin-for-claude-code/index.md)): The Claude Code plugin bundle declares the GA4 MCP server and its two required settings, so Claude Code can install the server and prompt for the values.
- [GA4 extension for Gemini CLI](https://ga4mcp.com/ga4-plugin-for-gemini/) ([markdown](https://ga4mcp.com/ga4-plugin-for-gemini/index.md)): The Gemini extension declares the GA4 MCP server and the two settings Gemini CLI prompts for, so the server installs without hand-edited JSON.
- [35 Production GA4 Prompts for Claude, Cursor & AI](https://ga4mcp.com/google-analytics-ai-prompts/) ([markdown](https://ga4mcp.com/google-analytics-ai-prompts/index.md)): Copy-paste prompt cookbook for querying Google Analytics 4 with AI agents. Tested recipes for traffic drops, channel ROI, e-commerce, and AI referrals.
- [Fix GA4 Missing Permissions: Service Account 403 Guide](https://ga4mcp.com/iam/) ([markdown](https://ga4mcp.com/iam/index.md)): How to fix Google Analytics missing permissions and 403 Permission Denied errors. Step-by-step resolution for adding service account Viewer access in GA4 Admin.
- [Natural Language Google Analytics: Query GA4 with AI](https://ga4mcp.com/natural-language-google-analytics/) ([markdown](https://ga4mcp.com/natural-language-google-analytics/index.md)): How to query Google Analytics 4 in natural language using Claude, Cursor, and AI agents. Local stdio execution, pre-flight schema checks, zero data leakage.
- [GA4 MCP plugins for Claude Code and Gemini CLI](https://ga4mcp.com/ga4-plugins/) ([markdown](https://ga4mcp.com/ga4-plugins/index.md)): Plugin bundles wrap the GA4 MCP server with its configuration, so a client can install the server and its settings in one step.
- [Privacy — what the GA4 MCP server sends](https://ga4mcp.com/privacy/) ([markdown](https://ga4mcp.com/privacy/index.md)): The server runs locally, reads your Analytics data with your credentials, and sends anonymous usage counts you can switch off with one environment variable.
- [GA4 query shapes — filters, field names and totals](https://ga4mcp.com/schema/) ([markdown](https://ga4mcp.com/schema/index.md)): The exact JSON shapes for dimension_filter and metric_filter in the GA4 Data API v1beta schema, plus the field-name rule that prevents most 400 errors.
- [Install GA4 MCP: Connect Google Analytics to AI Clients](https://ga4mcp.com/setup/) ([markdown](https://ga4mcp.com/setup/index.md)): Step-by-step setup guide for the Google Analytics 4 MCP server. 1-line installer, service account authentication, and verification for Claude, Cursor & AI agents.
- [GA4 skills — sixteen analytical recipes for your agent](https://ga4mcp.com/skills/) ([markdown](https://ga4mcp.com/skills/index.md)): Sixteen playbooks that ship inside the GA4 MCP server. Each one fixes the dimensions, metrics and interpretation rules for one job, and loads only when the agent asks.
- [Terms of use](https://ga4mcp.com/terms/) ([markdown](https://ga4mcp.com/terms/index.md)): MIT licensed, provided as-is, not affiliated with Google. Use it with a Google Analytics property you are entitled to read.
- [Fix Common GA4 Data API & IAM Errors (Quick Guide)](https://ga4mcp.com/troubleshooting/) ([markdown](https://ga4mcp.com/troubleshooting/index.md)): Troubleshooting guide for the top 5 Google Analytics 4 Data API errors: 403 Viewer permission, invalid dimension names, quota exhaustion, and token limits.
