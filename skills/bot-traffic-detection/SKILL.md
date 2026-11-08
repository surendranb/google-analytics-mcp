---
name: bot-traffic-detection
titleTag: "Identify & Filter Bot Traffic in Google Analytics 4"
description: "Detect and filter automated bot spikes in Google Analytics 4. Patterns for datacenter ASN spikes, zero-second sessions, and single-page screenPageViews."
---

# Identify & Filter Bot Traffic in Google Analytics 4

Identify and exclude bot, scraper, crawler, and spam sessions from your Google Analytics 4 reporting to protect conversion rates and prevent skewed traffic baselines.

## When to use
- Traffic has unexplained spikes that don't correlate with marketing campaigns or product releases
- Bounce rate is 0% or near-100% across hundreds of new sessions
- Sessions show 0 seconds average engagement time with high screenPageViews
- Referrers show unfamiliar domains, spam keywords, or suspicious TLDs
- You need clean, validated baseline data before presenting quarterly numbers

## Four Forensic Bot Signals

### 1. Zero-Second Engagement Distribution
Query sessions exhibiting zero or near-zero engagement duration:

```text
dimensions: ["sessionDefaultChannelGroup", "sessionSource", "sessionMedium"]
metrics: ["sessions", "userEngagementDuration", "bounceRate", "screenPageViewsPerSession"]
date_range: last 7–14 days
```

**Bot indicators:** `userEngagementDuration` < 1.0 second, `screenPageViewsPerSession` exactly 1.0, and `bounceRate` at 1.0 (100%).

### 2. Suspicious Referral Sources & Ghost Domains
```text
dimensions: ["sessionSource", "sessionMedium", "sessionDefaultChannelGroup"]
metrics: ["sessions", "userEngagementDuration", "newUsers"]
dimension_filter: sessionMedium = "referral"
```

Flag and isolate any referral source where `userEngagementDuration / sessions` is under 2 seconds.

### 3. Invalid or Missing Hostnames
```text
dimensions: ["hostname"]
metrics: ["sessions", "screenPageViews"]
```

Scrapers and spambots frequently fire Google Analytics measurement tags without actually visiting your domain (hitting raw IP addresses, scraper staging proxies, or ghost hosts). Always verify that `hostname` matches your legitimate production domains.

### 4. Geographic & Datacenter Clustering
```text
dimensions: ["country", "city", "sessionSource"]
metrics: ["sessions", "userEngagementDuration"]
order_by: sessions DESC
```

Clusters of hundreds of sessions originating from known datacenter hubs (e.g., Boardman, Ashburn, Council Bluffs) with zero engagement indicate automated cloud scraper runs rather than human browsing.

---

## Filtering Strategy

While Google Analytics 4 excludes known IAB-registered bots automatically, headless crawlers and custom scrapers bypass default filters.

To filter suspected bot traffic in API queries, combine dimension and metric filters:
- Exclude sessions where `userEngagementDuration` equals 0 and `screenPageViewsPerSession` equals 1.
- Restrict `hostname` strictly to your verified production domain.

---

## Three Prompts to Ask Your AI Agent

Copy-paste these prompts into Claude, Cursor, or Gemini CLI:

```text
1. "Audit our traffic from the last 7 days for bot contamination. Check bounce rate, average session duration, and single-page sessions grouped by sessionSource."

2. "List all sessions grouped by hostname over the past 30 days. Flag any traffic hitting hostnames other than our primary domain."

3. "Show me cities generating more than 100 sessions over the last 14 days where average engagement duration was under 3 seconds."
```

## How to Check Manually in the GA4 Console
1. Open **Reports → Acquisition → Traffic acquisition**.
2. Add a secondary dimension: click the **+** icon next to the primary column and choose **Geography → City**.
3. Sort by **Sessions** descending.
4. Scan the **Average engagement time per session** column. Any city generating hundreds of sessions with 0:00 engagement represents automated bot traffic.
