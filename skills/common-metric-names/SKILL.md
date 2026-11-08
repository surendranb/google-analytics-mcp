---
name: common-metric-names
titleTag: "GA4 Dimensions & Metrics Reference: API Field Names"
description: "Exact API field names for GA4 Data API queries. Avoid 400 errors from Universal Analytics names like ga:sessions or pageviews by using valid GA4 schema."
---

# GA4 Dimensions and Metrics Reference: API Field Names

The Google Analytics 4 (GA4) Data API enforces strict field naming conventions. Universal Analytics was sunset on July 1, 2023, and on May 6, 2024, Google renamed all conversion metrics to **key events** (`conversions` → `keyEvents`).

Querying invalid field names causes a hard 400 error. Use this reference table before constructing queries or prompts.

## Metrics Reference Table

| Metric Intent | Legacy / Invalid Names (Fails) | Valid GA4 Data API Name |
|---|---|---|
| **Conversions / Goal Completions** | `conversions`, `goals`, `conversion` | `keyEvents` |
| **Session Conversion Rate** | `conversionRate`, `sessionConversionRate` | `sessionKeyEventRate` |
| **User Conversion Rate** | `userConversionRate` | `userKeyEventRate` |
| **Total Users** | `users`, `totalVisitors` | `totalUsers` |
| **Active Users** | `uniqueUsers`, `activeVisitors` | `activeUsers` |
| **Daily Active Users (DAU)** | `DAU`, `dailyActiveUsers` | `active1DayUsers` |
| **Weekly Active Users (WAU)** | `WAU`, `weeklyActiveUsers` | `active7DayUsers` |
| **Monthly Active Users (MAU)** | `MAU`, `monthlyActiveUsers` | `active28DayUsers` |
| **Pageviews** | `pageviews`, `pageViews`, `page_views` | `screenPageViews` |
| **Pages per Session** | `pagesPerSession`, `pageDepth` | `screenPageViewsPerSession` |
| **E-commerce Purchases** | `purchases`, `transactions` | `ecommercePurchases` |
| **Product Views** | `itemViews`, `productViews` | `itemsViewed` |
| **Items Added to Cart** | `addToCarts`, `cartAdds` | `itemsAddedToCart` |
| **Purchase Revenue** | `revenue`, `ecommerceRevenue` | `purchaseRevenue` |
| **Average Order Value (AOV)** | `revenuePerTransaction` | `averagePurchaseRevenue` |
| **Average Session Duration** | `avgSessionDuration`, `avgTimeOnSite` | `averageSessionDuration` |
| **Total Engagement Time** | `engagementDuration`, `timeOnSite` | `userEngagementDuration` |
| **Engaged Sessions** | `qualifiedSessions`, `validSessions` | `engagedSessions` |
| **Bounce Rate** | `bounce_rate` | `bounceRate` |

---

## Dimensions Reference Table

| Dimension Intent | Legacy / Invalid Names (Fails) | Valid GA4 Data API Name |
|---|---|---|
| **Default Channel Group** | `channelGrouping`, `sessionDefaultChannelGrouping` | `sessionDefaultChannelGroup` |
| **Traffic Source** | `source`, `session_source` | `sessionSource` |
| **Traffic Medium** | `medium`, `session_medium` | `sessionMedium` |
| **Source / Medium Combined** | `sourceMedium` | `sessionSourceMedium` |
| **Campaign Name** | `campaign` | `sessionCampaignName` |
| **Page Path** | `page`, `page_path` | `pagePath` |
| **Page Path with Query** | `pagePathPlusQueryString` | `unifiedPagePathScreen` |
| **Landing Page** | `landingPagePath` | `landingPage` |
| **Landing Page with Query** | `landingPage` (when query needed) | `landingPagePlusQueryString` |
| **Page Title** | `title`, `page_title` | `pageTitle` |
| **Device Category** | `device`, `deviceType` | `deviceCategory` |
| **Operating System** | `os` | `operatingSystem` |
| **Browser** | `userAgent` | `browser` |
| **Country** | `countryName` | `country` |
| **City** | `cityName` | `city` |

---

## Active Users Mechanics (DAU / WAU / MAU)
GA4 does not provide literal `DAU` or `MAU` metrics. It provides rolling windows:
- `active1DayUsers`: Users active in the 1 day ending on that date (DAU).
- `active7DayUsers`: Rolling 7-day distinct active users (WAU).
- `active28DayUsers`: Rolling 28-day distinct active users (MAU).

> **Important:** Never sum daily `activeUsers` across rows to compute a monthly total. Summing rows double-counts returning users. Request `activeUsers` once over the full date range with no `date` dimension, and GA4 will return the true deduped count.

---

## How to Check Field Names in-Session
If you are unsure of a dimension or metric name for your specific property, ask your agent:

```text
search_schema("keyword")
```

The server queries your live GA4 metadata schema and returns all matching dimensions and metrics with exact API identifiers.
