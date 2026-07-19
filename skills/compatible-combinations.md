# Compatible Dimension and Metric Combinations

GA4 enforces strict rules about which dimensions and metrics can appear
in the same request. Incompatible combinations return a 400 error:
"The request's dimensions & metrics are incompatible."

## The core rule

GA4 data is scoped at three levels: **event**, **session**, and **user**.
Mixing dimensions and metrics from incompatible scopes causes errors.

| Scope | Example dimensions | Example metrics |
|---|---|---|
| Event | `eventName`, `customEvent:*` | `eventCount` |
| Session | `sessionDefaultChannelGroup`, `sessionSource`, `sessionCampaignName` | `sessions`, `bounceRate`, `sessionKeyEventRate` |
| User | `firstUserDefaultChannelGroup`, `firstUserSource` | `totalUsers`, `newUsers` |

## Most common incompatible pairs

| Dimension | Incompatible metric | Use instead |
|---|---|---|
| `sessionSource` / `sessionMedium` / `sessionCampaignName` | `eventCount` | `sessions` |
| `eventName` | `sessions` | `eventCount` |
| `promotionId` / `promotionName` | most session/user metrics | only pair with `promotionViews`, `promotionClicks` |
| `itemId` / `itemName` | `sessions`, `totalUsers` | `itemsViewed`, `addToCarts`, `ecommercePurchases` |
| `firstUserSource` / `firstUserMedium` | `sessions` | `totalUsers`, `newUsers` |

## When you hit this error

The GA4 error message names the exact field to remove:
`"Please remove eventCount to make the request compatible for example."`

Read the message literally — remove that field and replace it with a
scope-compatible equivalent.

## Safe combinations (always work)

- `date` + any metric
- `deviceCategory` + any metric
- `country` / `city` + any metric
- `pagePath` / `pageTitle` + `screenPageViews`, `totalUsers`, `sessions`
- `sessionDefaultChannelGroup` + `sessions`, `totalUsers`, `bounceRate`

## Ecommerce-specific

Ecommerce metrics (`ecommercePurchases`, `purchaseRevenue`, `addToCarts`,
`itemsViewed`) are event-scoped. Pair them with event-scoped or
`date`/`deviceCategory`/geo dimensions — not with session campaign dimensions.
