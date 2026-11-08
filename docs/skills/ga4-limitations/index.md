# GA4 API Limitations, Quotas & Cardinality Boundaries

> GA4 Data API boundaries: 10-dimension limit, 100,000 row caps, hourly token quotas, and sampling thresholds. How to query safely within API limits.

Canonical URL: https://ga4mcp.com/skills/ga4-limitations/



What the Google Analytics 4 Data API can and cannot do, where to find alternate data sources, and how to query within Google Cloud quota boundaries.

## Capabilities & Workaround Matrix

| Analytical Requirement | Available in GA4 Data API? | Recommended Alternative |
|---|---|---|
| **Multi-Step Funnel Visualizations** | Partial (Aggregate e-commerce metrics only) | **GA4 UI → Explore → Funnel Exploration** |
| **Cohort Retention Over Time** | No (API does not expose `runCohortReport`) | **GA4 UI → Explore → Cohort Exploration** |
| **Individual User Clickstreams / Journeys** | No (API returns aggregated rows only) | **BigQuery Export (Raw Event Tables)** |
| **Segment Overlap / Venn Diagrams** | No (Aggregate dimension cuts only) | **BigQuery or GA4 Explore Comparisons** |
| **Realtime User Event Streams** | Limited (Last 30-minute summary only) | **GA4 UI → Realtime Report** |
| **Google Search Console Clicks & Queries** | Separate API (Not in GA4 Data API) | **Google Search Console MCP Server** |
| **Historical Data Prior to GA4 Migration** | No (Universal Analytics data is separate) | **BigQuery UA Archive Tables** |

---

## Technical API Limits & Guardrails

When querying GA4 through an agent, keep requests within Google's structural limits:

1. **Maximum Dimensions per Request:** 10 dimensions. Attempting to pass 11 dimensions returns an API validation error.
2. **Maximum Metrics per Request:** 10 metrics.
3. **Maximum Rows Returned:** 100,000 rows per query response (subject to client memory limits).
4. **Hourly Token Quotas:** Standard properties receive 25,000 tokens per hour; GA4 360 properties receive 250,000 tokens per hour.

---

## When to Use BigQuery vs. GA4 MCP
- **Use GA4 MCP** for conversational exploration, executive reporting, attribution channel audits, e-commerce summaries, and ad-hoc troubleshooting inside Claude, Cursor, or your terminal.
- **Use BigQuery Export** when you require row-level user journey tracking, machine learning feature engineering, joining analytics with CRM database tables, or querying data older than GA4's 14-month user data retention limit.
