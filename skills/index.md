# GA4 MCP Skills Library

Analytical recipes for common GA4 analysis patterns. Each skill gives you
the exact dimensions, metrics, filters, and interpretation logic to answer
a specific question using the tools already available in this MCP.

To use a skill: call `search_skills("skill-name")` to fetch the full instructions.

| Skill | What it answers | Use when |
|---|---|---|
| `common-metric-names` | Correct GA4 API names for metrics and dimensions — the exact fields to use | You're unsure of a field name, or hit an "Invalid metric/dimension" error |
| `filter-structures` | Correct JSON shape for `dimension_filter` — templates for AND, OR, NOT, IN LIST | You hit an "Invalid dimension_filter" error or need to filter by a field value |
| `attribution-scope` | When to use session-scoped vs first-user vs event-scoped dimensions | You're doing traffic acquisition vs user acquisition analysis, or mixing source/medium dimensions |
| `bot-traffic-detection` | Which sessions are bots, scrapers, or spam — and how to exclude them | You see inflated traffic, suspicious spikes, or want to audit data quality |
| `traffic-diagnosis` | Step-by-step methodology to diagnose traffic spikes, drops, or channel shifts | Traffic changed unexpectedly and you need to find the cause |
| `ga4-limitations` | What this MCP cannot do via the API — and where to go instead | User asks for funnel, cohort, path, or per-user analysis |
| `ai-referral-analysis` | How much traffic arrives from AI tools (ChatGPT, Claude, Perplexity, Gemini, etc.) | You want to understand AI-driven discovery and measure it over time |
| `ecommerce-analysis` | Revenue, conversion rate, AOV, funnel drop-off using GA4 ecommerce events | You have purchase/add-to-cart events and want to understand buying behaviour |
| `channel-acquisition` | Session and user breakdown by traffic source, medium, and channel group | You want to know where users come from and which channels perform best |
| `content-performance` | Which pages drive engagement, scroll depth, and return visits | You want to identify top content and find underperforming pages |
| `geo-device-segmentation` | User behaviour split by country, city, device type, and OS | You want to understand regional or device-specific patterns |
