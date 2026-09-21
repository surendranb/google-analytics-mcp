---
title: Agent Skills — GA4 MCP Server
description: 15 GA4 analytical recipes an agent can load on request: traffic diagnosis, channel acquisition, ecommerce, AI referrals, bot detection, field-name maps.
url: https://ga4mcp.com/skills/
type: collection
site: https://ga4mcp.com
updated: 2026-09-21
license: MIT
---

# GA4 MCP Skills Library

15 analytical recipes. Each one is an MCP resource at `skill://<slug>`, loadable with `search_skills("<slug>")`.

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

Machine-readable index: https://ga4mcp.com/data/skills.json
