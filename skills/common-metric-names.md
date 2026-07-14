# Common Metric & Dimension Names

The correct GA4 Data API names for fields models most often get wrong.
Use these before calling `get_ga4_data` — wrong names return a hard error.

## Metrics — correct API names

| What you mean | Wrong (will fail) | Correct API name |
|---|---|---|
| Goal completions / conversions | `conversions`, `goals` | `keyEvents` |
| Total users | `users`, `totalVisitors` | `totalUsers` |
| Active users (30-day) | `activeVisitors` | `active28DayUsers` |
| Page views | `pageViews`, `pageviews`, `page_views` | `screenPageViews` |
| E-commerce purchases | `purchases`, `transactions` | `ecommercePurchases` |
| Product views | `itemViews`, `productViews` | `itemsViewed` |
| Items added to cart | `addToCarts`, `cartAdds` | `itemsAddedToCart` |
| Revenue | `revenue`, `ecommerceRevenue` | `purchaseRevenue` |
| Avg session duration | `avgSessionDuration`, `avgTimeOnSite` | `averageSessionDuration` |
| Total engagement time | `engagementDuration`, `timeOnSite` | `userEngagementDuration` |
| Session conversion rate | `conversionRate`, `goalConversionRate` | `sessionConversionRate` |
| Engaged sessions | `qualifiedSessions`, `validSessions` | `engagedSessions` |
| Pages per session | `pagesPerSession`, `pageDepth` | `screenPageViewsPerSession` |

## Dimensions — correct API names

| What you mean | Wrong (will fail) | Correct API name |
|---|---|---|
| Traffic channel group | `sessionDefaultChannelGrouping`, `channelGrouping` | `sessionDefaultChannelGroup` |
| Landing page + query | `landingPage` (often wrong scope) | `landingPagePlusQueryString` |
| Page path | `pagePath`, `page` | `pagePath` |
| Page path + query | `pagePathPlusQueryString` | `unifiedPagePathScreen` |
| Session source | `source` (wrong scope — see attribution-scope skill) | `sessionSource` |
| Session medium | `medium` (wrong scope) | `sessionMedium` |
| Device type | `device`, `deviceType` | `deviceCategory` |
| Operating system | `os` | `operatingSystem` |
| Browser | `userAgent` | `browser` |
| Week of year | `week`, `weekNumber` | `week` (this one IS correct) |

## Note on bounce rate

GA4 bounce rate = sessions with NO engaged session (opposite of GA3 logic).
A bounce rate of 60% means 60% of sessions had no engagement — that is high.
In GA3, bounce rate meant single-page sessions. Do not compare GA3 and GA4 bounce rates.

## When you hit a schema error

If `get_ga4_data` returns "Invalid dimension" or "Invalid metric", do not guess
alternatives. Use `search_schema` with a keyword to find the correct name, or
check this skill's table above.
