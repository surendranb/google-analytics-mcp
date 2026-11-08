# Universal Analytics to GA4 Field Name Mapping

> Mapping table from Universal Analytics (UA) field names to Google Analytics 4 (GA4) Data API names. Replace ga:pageviews, ga:bounces, and ga:users correctly.

Canonical URL: https://ga4mcp.com/skills/ua-to-ga4/



Universal Analytics (UA) was sunset on July 1, 2023. Language models trained on legacy documentation frequently guess deprecated UA field names (e.g., `ga:sessions`, `pageviews`, `uniquePageviews`, `conversions`) that cause hard 400 validation errors in the Google Analytics 4 Data API.

Additionally, on May 6, 2024, Google officially renamed **conversions** to **key events** across GA4. Use this mapping table to translate legacy dimensions and metrics into their valid GA4 Data API equivalents.

## Metrics Mapping

| Legacy UA Name (Invalid) | GA4 Data API Name (Valid) | Type | Notes |
|---|---|---|---|
| `users` | `totalUsers` or `activeUsers` | Metric | `activeUsers` is GA4's primary user metric |
| `pageviews` | `screenPageViews` | Metric | Total pages viewed across web and app |
| `uniquePageviews` | `screenPageViews` | Metric | GA4 does not track unique views; use sessions per page |
| `avgSessionDuration` | `averageSessionDuration` | Metric | Average duration in seconds |
| `timeOnPage` / `avgTimeOnPage` | `userEngagementDuration` | Metric | Total engagement time in seconds |
| `conversions` / `goalCompletionsAll` | `keyEvents` | Metric | Renamed from conversions on May 6, 2024 |
| `conversionRate` / `sessionConversionRate` | `sessionKeyEventRate` | Metric | Percentage of sessions with a key event |
| `userConversionRate` | `userKeyEventRate` | Metric | Percentage of users who triggered a key event |
| `transactions` / `purchases` | `ecommercePurchases` | Metric | Number of completed e-commerce purchases |
| `transactionRevenue` / `revenue` | `purchaseRevenue` | Metric | Total purchase revenue |
| `revenuePerTransaction` | `averagePurchaseRevenue` | Metric | Average purchase revenue per transaction |
| `itemQuantity` | `itemsViewed` or `itemsPurchased` | Metric | Specify viewed or purchased |
| `entrances` | `sessions` | Metric | Use session count with landingPage |
| `bounces` | `bounceRate` | Metric | GA4 calculates bounce rate as (1 - engagementRate) |

## Dimensions Mapping

| Legacy UA Name (Invalid) | GA4 Data API Name (Valid) | Scope | Notes |
|---|---|---|---|
| `channelGrouping` | `sessionDefaultChannelGroup` | Session | Organic Search, Direct, Paid, Referral |
| `source` | `sessionSource` | Session | Domain or entity driving the session |
| `medium` | `sessionMedium` | Session | organic, cpc, referral, email |
| `sourceMedium` | `sessionSourceMedium` | Session | Combined source / medium |
| `campaign` | `sessionCampaignName` | Session | UTM campaign name |
| `keyword` | `sessionManualTerm` | Session | UTM term |
| `landingPagePath` | `landingPage` | Event | Landing page path without query parameters |
| `pagePath` | `pagePath` | Event | Page path including directories |
| `pageTitle` | `pageTitle` | Event | Page HTML title tag |
| `deviceCategory` | `deviceCategory` | Event | desktop, mobile, tablet |
| `operatingSystem` | `operatingSystem` | Event | iOS, Android, Windows, Macintosh |
| `browser` | `browser` | Event | Chrome, Safari, Firefox, Edge |
| `country` | `country` | Event | Full country name |
| `city` | `city` | Event | Full city name |
| `userType` | `newVsReturning` | User | 'new' or 'returning' |

## The camelCase Syntax Rule

All GA4 Data API field names are strictly **camelCase**. Using snake_case will cause an invalid field error.

| Wrong (snake_case) | Correct (camelCase) |
|---|---|
| `page_path` | `pagePath` |
| `session_source` | `sessionSource` |
| `device_category` | `deviceCategory` |
| `event_name` | `eventName` |
| `total_users` | `totalUsers` |
| `screen_page_views` | `screenPageViews` |

## Attribution Scopes

GA4 splits attribution into three distinct scopes:
1. **Session Scope (`session*`)**: Attributes the visit (e.g., `sessionSource`, `sessionMedium`). Use for traffic acquisition.
2. **First User Scope (`firstUser*`)**: Attributes the person across their lifetime (e.g., `firstUserSource`). Use for user acquisition.
3. **Event Scope (no prefix)**: Attributes the specific action (e.g., `pagePath`, `eventName`). Use for page and event analytics.

Never mix user-scoped dimensions with session-scoped metrics in the same query. Consult the [Compatible Combinations Guide](/skills/compatible-combinations/) for valid groupings.
