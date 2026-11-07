---
name: compatible-combinations
titleTag: "GA4 Compatible Dimensions & Metrics (Avoid 400s)"
description: "Which dimensions and metrics can be queried together in GA4 without triggering incompatible scope errors. Matrix of user, session, and event-level pairings."
---

# Compatible Dimension & Metric Combinations in GA4

Google Analytics 4 enforces strict scoping boundaries. Attempting to query dimensions and metrics with conflicting scopes causes the API to return a 400 error: `The request's dimensions & metrics are incompatible.`

This reference outlines which field pairings are valid across event, session, and user scopes.

## The Scope Hierarchy

All data in GA4 is partitioned into three hierarchical scopes:

| Scope Level | Description | Key Dimensions | Key Metrics |
|---|---|---|---|
| **Event Scope** | Actions taken at a specific moment | `eventName`, `pagePath`, `linkUrl` | `eventCount`, `screenPageViews`, `keyEvents` |
| **Session Scope** | Attributes of a single visit | `sessionDefaultChannelGroup`, `sessionSource` | `sessions`, `bounceRate`, `averageSessionDuration` |
| **User Scope** | Lifetime attributes of an individual | `firstUserDefaultChannelGroup`, `firstUserSource` | `totalUsers`, `newUsers`, `activeUsers` |

---

## Most Common Incompatible Pairings (What Fails)

| Dimension In Query | Incompatible Metric | What Fails | Valid Alternative |
|---|---|---|---|
| `sessionSource` / `sessionMedium` | `eventCount` | Mixing session dimension with hit metric | Use `sessions` or `engagedSessions` |
| `eventName` | `sessions` | Asking for session counts of an event | Use `eventCount` |
| `itemId` / `itemName` | `sessions` or `totalUsers` | Item dimensions do not carry session scope | Use `itemsViewed`, `addToCarts`, `itemsPurchased` |
| `firstUserSource` | `sessions` | Lifetime acquisition with session metric | Use `newUsers` or `totalUsers` |
| `promotionName` | `sessions` | Promotion items are hit-scoped | Use `promotionViews`, `promotionClicks` |

---

## Guaranteed Safe Combinations (Universal Dimensions)
Certain dimensions are universally compatible across almost all metrics:
- **Temporal Dimensions**: `date`, `month`, `year`, `week`
- **Geographic Dimensions**: `country`, `city`, `region`
- **Device & Platform**: `deviceCategory`, `operatingSystem`, `browser`

These can be safely combined with event metrics (`screenPageViews`, `eventCount`), session metrics (`sessions`, `bounceRate`), and e-commerce metrics (`purchaseRevenue`).

---

## How to Resolve 400 Incompatible Errors
When Google Analytics returns an incompatibility error, the API payload explicitly names the offending field:
```text
Please remove eventCount to make the request compatible for example.
```

Follow the recommendation directly: remove the conflicting metric and replace it with a metric from the same scope as your dimensions.
