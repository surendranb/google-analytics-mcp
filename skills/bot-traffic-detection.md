# Bot Traffic Detection

Identify and exclude bot, scraper, and spam sessions from GA4 data.

## When to use
- Traffic has unexplained spikes that don't correlate with any activity
- Bounce rate is 0% or near-100% across many sessions
- Sessions show 0 engagement time but high pageview counts
- Referrers look suspicious (random domains, unrecognised TLDs)
- You want to establish a clean baseline before any analysis

## How to detect

### Step 1 — Check engagement time distribution
Query sessions with very low or zero engagement:

```
dimensions: ["sessionDefaultChannelGroup", "sessionSource", "sessionMedium"]
metrics: ["sessions", "userEngagementDuration", "bounceRate", "screenPageViewsPerSession"]
date_range: last 7–14 days
```

Bot signals: `userEngagementDuration` near 0, `screenPageViewsPerSession` exactly 1,
`bounceRate` at 1.0 (100%).

### Step 2 — Inspect referrer sources
```
dimensions: ["sessionSource", "sessionMedium", "sessionDefaultChannelGroup"]
metrics: ["sessions", "userEngagementDuration", "newUsers"]
dimension_filter: sessionMedium = "referral"
```

Flag sources where `userEngagementDuration / sessions` < 2 seconds.

### Step 3 — Check hostname
```
dimensions: ["hostname"]
metrics: ["sessions", "screenPageViews"]
```

Bot traffic often hits unexpected hostnames (staging domains, raw IPs,
or hostnames you don't own). Filter to your known production hostnames.

### Step 4 — Geographic anomalies
```
dimensions: ["country", "city", "sessionSource"]
metrics: ["sessions", "userEngagementDuration"]
dimension_filter: country = [countries with no expected traffic]
```

Clusters of sessions from unexpected countries with 0 engagement = bot signal.

## Exclusion approach
GA4 does not have a native bot filter toggle beyond the automatic Google filter.
To exclude suspected bot traffic from your analysis, add a dimension filter:

```
dimension_filter: {
  "filter": {
    "fieldName": "sessionDefaultChannelGroup",
    "stringFilter": {"matchType": "EXACT", "value": "Direct"}
  }
}
```
…combined with a metric filter on `userEngagementDuration > 0`.

Note: GA4 already filters known bots automatically. What remains are
unknown/new bots and scrapers that mimic real browser behaviour.

## What to report
- Total suspicious sessions as % of all sessions
- Top suspicious sources with their engagement metrics
- Whether the pattern is new (spike) or chronic (baseline contamination)
