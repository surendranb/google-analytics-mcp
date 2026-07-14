# GA4 API Limitations

What this MCP **cannot** do via the GA4 Data API, and where to go instead.
Attempting these will either fail or produce meaningless aggregate data.

## Not available via this MCP

| Analysis type | Why not available | Where to do it instead |
|---|---|---|
| Funnel analysis (drop-off by step) | `runFunnelReport` exists in the API but is not exposed by this MCP | GA4 UI → Explore → Funnel Exploration |
| Cohort retention (week N return rate) | `runCohortReport` not exposed | GA4 UI → Explore → Cohort Exploration |
| User path / flow analysis | Not available in aggregate API | GA4 UI → Explore → Path Exploration |
| Per-user event sequences | API returns aggregate rows only — no individual user journeys | BigQuery export (raw events) |
| Real-time custom breakdowns | Realtime API is limited to last 30 minutes, basic dimensions | GA4 UI → Realtime report |
| Raw event-level data | Data API aggregates; no row-level access | BigQuery export |
| Segment overlap / Venn analysis | Not a native API feature | BigQuery or GA4 Explore comparisons |
| Custom channel group definitions | Read-only via API; custom groups must be created in UI | GA4 UI → Admin → Custom Channel Groups |

## What IS available (and often underused)

- **Period-over-period in one call**: pass two `date_ranges` — GA4 returns both periods in a single response (use `date_range_start`/`date_range_end` for each; call twice if two-range isn't supported)
- **Ecommerce metrics**: full purchase funnel metrics (`itemsViewed`, `itemsAddedToCart`, `itemsPurchased`, `purchaseRevenue`, `cartToViewRate`) — aggregate only, not per-session funnel
- **Search Console integration**: available as a linked report in GA4 UI but the Search Console data is on a separate API — not queryable via this MCP (use Google Search Console API directly)
- **Custom dimensions and metrics**: available if defined in the property — they appear in the schema alongside standard fields
- **Attribution modeling comparisons**: not directly queryable — data-driven vs last-click is set at the property level, not a query-time parameter

## When a user asks for funnel or cohort analysis

Tell them: the GA4 Data API returns aggregate metrics, not event sequences.
For funnel drop-off between specific steps, use GA4 Explore → Funnel Exploration.
For cohort retention (week 1 / week 2 return), use GA4 Explore → Cohort Exploration.
These analyses require the GA4 UI or a BigQuery export, not the Data API.
