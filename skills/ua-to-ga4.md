# UA to GA4 Field Name Mapping

Universal Analytics (UA) and GA4 use different names for equivalent concepts.
UA was sunset on 2023-07-01; models trained before or around then guess UA field
names that no longer exist in the GA4 Data API. On 2024-05-06 GA4 also renamed
"conversions" to "key events" (see the conversions rows below). If a name feels
obviously right but returns "Invalid metric/dimension", assume your training
predates the change and verify with `search_schema`. This skill gives the correct
GA4 Data API name for every common UA metric and dimension.

## Metrics

| UA name (wrong) | GA4 API name (correct) |
|---|---|
| `users` | `totalUsers` |
| `uniquePageviews` | `screenPageViews` |
| `pageviews` | `screenPageViews` |
| `avgSessionDuration` | `averageSessionDuration` |
| `timeOnPage` / `avgTimeOnPage` | `userEngagementDuration` |
| `goalCompletionsAll` / `conversions` | `keyEvents` |
| `goalConversionRateAll` / `conversionRate` / `sessionConversionRate` | `sessionKeyEventRate` |
| `userConversionRate` | `userKeyEventRate` |
| `transactions` / `purchases` | `ecommercePurchases` |
| `transactionRevenue` / `revenue` | `purchaseRevenue` |
| `revenuePerTransaction` | `averagePurchaseRevenue` |
| `transactionsPerSession` | `purchaseToViewRate` |
| `itemQuantity` / `itemViews` | `itemsViewed` |
| `itemRevenue` | `itemRevenue` (same) |
| `entrances` | `sessions` (no direct equivalent — use sessions) |
| `pageValue` | no direct equivalent |

## Dimensions

| UA name (wrong) | GA4 API name (correct) |
|---|---|
| `channelGrouping` | `sessionDefaultChannelGroup` |
| `defaultChannelGrouping` | `sessionDefaultChannelGroup` |
| `source` | `sessionSource` |
| `medium` | `sessionMedium` |
| `campaign` | `sessionCampaignName` |
| `keyword` | `sessionManualTerm` |
| `sourceMedium` | `sessionSourceMedium` |
| `adContent` | `sessionManualAdContent` |
| `pagePath` | `pagePath` (same) |
| `pageTitle` | `pageTitle` (same) |
| `landingPagePath` | `landingPage` |
| `exitPagePath` | no direct equivalent |
| `deviceCategory` | `deviceCategory` (same) |
| `operatingSystem` | `operatingSystem` (same) |
| `browser` | `browser` (same) |
| `country` | `country` (same) |
| `city` | `city` (same) |
| `userType` | use `newVsReturning` |

## Key rules

All GA4 API names are camelCase — never snake_case.

| Wrong (snake_case) | Correct |
|---|---|
| `page_path` | `pagePath` |
| `session_source` | `sessionSource` |
| `device_category` | `deviceCategory` |
| `event_name` | `eventName` |
| `total_users` | `totalUsers` |

## Attribution scope

GA4 splits attribution into three scopes. Use the right prefix:

| Scope | Prefix | Use for |
|---|---|---|
| Session | `session` (e.g. `sessionSource`) | Traffic acquisition analysis |
| First user | `firstUser` (e.g. `firstUserSource`) | User acquisition analysis |
| Event | `(none)` (e.g. `pagePath`) | Event-level analysis |

Mixing scopes causes 400 errors — see `compatible-combinations` skill.
