# Channel Acquisition Analysis

Break down sessions and users by traffic source, medium, and channel group
to understand where your audience comes from and which channels perform best.

## Correct dimension names
| Concept | GA4 API name |
|---|---|
| Channel group | `sessionDefaultChannelGroup` |
| Source | `sessionSource` |
| Medium | `sessionMedium` |
| Source / Medium | `sessionSourceMedium` |
| Campaign name | `sessionCampaignName` |
| Campaign ID | `sessionCampaignId` |
| Ad content | `sessionManualAdContent` |

Do not use `sessionDefaultChannelGrouping` — it does not exist.
Do not combine `sessionCampaignName` with user-scoped metrics like `totalUsers`.

## Step 1 — Channel overview
```
dimensions: ["sessionDefaultChannelGroup"]
metrics: ["sessions", "totalUsers", "newUsers", "userEngagementDuration",
          "screenPageViewsPerSession", "bounceRate"]
date_range: last 30 days
order_by: sessions DESC
```

## Step 2 — Source / medium detail
```
dimensions: ["sessionSource", "sessionMedium"]
metrics: ["sessions", "newUsers", "userEngagementDuration", "keyEvents"]
date_range: last 30 days
order_by: sessions DESC
limit: 25
```

## Step 3 — Campaign performance (paid)
```
dimensions: ["sessionCampaignName", "sessionDefaultChannelGroup"]
metrics: ["sessions", "newUsers", "keyEvents", "userEngagementDuration"]
dimension_filter: {
  "filter": {
    "fieldName": "sessionMedium",
    "stringFilter": {"matchType": "EXACT", "value": "cpc"}
  }
}
date_range: last 30 days
order_by: sessions DESC
```

## Step 4 — Trend by channel over time
```
dimensions: ["date", "sessionDefaultChannelGroup"]
metrics: ["sessions", "newUsers"]
date_range: last 90 days
order_by: date ASC
```

## What to report
- Top 5 channels by sessions and by new users
- Engagement quality per channel (userEngagementDuration per session)
- Which channel drives the most key events (conversions)
- Week-over-week or month-over-month trend for top channels
