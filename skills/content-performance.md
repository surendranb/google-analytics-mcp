# Content Performance Analysis

Identify top-performing pages, find underperforming content, and understand
engagement patterns across your site.

## When to use
- You want to know which pages drive the most traffic and engagement
- You want to find pages with high views but low engagement (poor content fit)
- You want to identify content that drives conversions or return visits

## Correct dimension and metric names
| Concept | GA4 API name |
|---|---|
| Page path | `pagePath` |
| Page title | `pageTitle` |
| Landing page | `landingPage` |
| Page views | `screenPageViews` |
| Unique page views (users) | `totalUsers` |
| Engagement rate | `engagementRate` |
| Avg engagement time | `userEngagementDuration` |
| Scroll depth | `scrolledUsers` (if scroll event is tracked) |
| Entries (landing views) | `sessions` with `landingPage` dimension |

Do not use `pageviews` — the correct metric is `screenPageViews`.

## Step 1 — Top pages by traffic
```
dimensions: ["pagePath", "pageTitle"]
metrics: ["screenPageViews", "totalUsers", "userEngagementDuration",
          "engagementRate", "bounceRate"]
date_range: last 30 days
order_by: screenPageViews DESC
limit: 25
```

## Step 2 — Landing page performance
Which pages do users enter your site through, and how well do they engage:

```
dimensions: ["landingPage"]
metrics: ["sessions", "newUsers", "userEngagementDuration",
          "engagementRate", "keyEvents"]
date_range: last 30 days
order_by: sessions DESC
limit: 25
```

## Step 3 — Underperforming content (high views, low engagement)
Run Step 1, then flag pages where:
- `screenPageViews` is in the top 50% AND
- `engagementRate` is below 0.3 (30%) OR `userEngagementDuration` < 30 seconds

These pages attract traffic but fail to hold attention — candidates for
content improvement or better internal linking.

## Step 4 — Content trend over time
```
dimensions: ["date", "pagePath"]
metrics: ["screenPageViews", "totalUsers"]
dimension_filter: pagePath contains "/blog" (or your content path)
date_range: last 90 days
order_by: date ASC
```

## What to report
- Top 10 pages by views and by engagement time
- Top 5 landing pages and their conversion rate
- 3–5 underperforming pages (high traffic, low engagement) as actionable findings
- Any page with a notable trend (growing or declining) over the period
