# GA4 Content Performance: Views & Engagement Rates

> Evaluate landing pages and blog content in GA4: screenPageViews, average engagement time, bounce rates, and organic search conversions per URL.

Canonical URL: https://ga4mcp.com/skills/content-performance/



Audit and evaluate landing pages, documentation, and blog content in Google Analytics 4: discover top-performing URLs, identify underperforming content with high bounce rates, and track conversion efficiency per landing page.

## When to use
- You want to identify which URLs drive the highest traffic and user engagement
- You need to find pages with high views but low engagement duration (poor content fit or misleading titles)
- You want to evaluate landing page conversion rates across organic and paid channels
- You're planning content pruning, consolidation, or SEO content updates

## Dimension & Metric Reference
Always use exact GA4 Data API field names:

| Content Metric / Dimension | GA4 API Name | Type | Notes |
|---|---|---|---|
| **Page Path** | `pagePath` | Dimension | URL path without domain or query string |
| **Page Title** | `pageTitle` | Dimension | HTML title tag value |
| **Landing Page** | `landingPage` | Dimension | First page viewed in a session |
| **Pageviews** | `screenPageViews` | Metric | Do not use `pageviews` (UA metric) |
| **Unique Visitors** | `totalUsers` or `activeUsers` | Metric | Distinct users viewing content |
| **Engagement Rate** | `engagementRate` | Metric | Sessions with >10s dwell or conversion |
| **Average Engagement Time** | `userEngagementDuration` | Metric | Total active dwell time in seconds |
| **Key Events / Conversions** | `keyEvents` | Metric | Conversions triggered on or attributed to page |

---

## Step 1 — Top Pages by Total Traffic
Rank pages across your domain by total views and engagement quality:

```text
dimensions: ["pagePath", "pageTitle"]
metrics: ["screenPageViews", "totalUsers", "userEngagementDuration",
          "engagementRate", "bounceRate"]
date_range: last 30 days
order_by: screenPageViews DESC
limit: 25
```

---

## Step 2 — Landing Page Acquisition Performance
Analyze which entry pages successfully capture and retain visitors:

```text
dimensions: ["landingPage"]
metrics: ["sessions", "newUsers", "userEngagementDuration",
          "engagementRate", "keyEvents"]
date_range: last 30 days
order_by: sessions DESC
limit: 25
```

---

## Step 3 — High-Traffic, High-Bounce Page Triage
Identify pages receiving significant traffic that fail to engage users:
- Filter for pages in the top 50% of `screenPageViews`.
- Flag URLs where `engagementRate` < 35% or `userEngagementDuration` < 25 seconds.

These pages represent prime opportunities for UX improvements, clearer copy, or enhanced internal calls-to-action.

---

## Three Prompts to Ask Your AI Agent

Copy-paste these prompts into Claude Code, Cursor, or Gemini CLI:

```text
1. "List our top 20 landing pages by organic search traffic over the last 30 days. Report sessions, active users, engagement rate, and bounce rate."

2. "Find all landing pages that received at least 200 sessions over the past 30 days with an engagement rate below 40%. Sort by session volume descending."

3. "Compare the engagement duration and key event rate of our documentation pages versus our blog articles over the last 60 days."
```

## How to Check Manually in the GA4 Console
1. Open **Reports → Engagement → Pages and screens**.
2. Sort the table by **Views** descending.
3. Compare the **Average engagement time** column across URLs to spot content engagement outliers.
