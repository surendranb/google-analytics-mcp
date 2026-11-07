---
name: geo-device-segmentation
titleTag: "GA4 Geographic & Device Segmentation Analysis"
description: "Segment GA4 data by country, city, device category, and browser. Spot localization opportunities and mobile conversion drops with ready queries."
---
# Geo and Device Segmentation

Break down user behaviour by country, city, device category, and OS
to understand regional patterns and optimise for your key markets.

## Copy-paste prompts

### Mobile vs desktop drop-off audit
```text
Break down sessions, bounceRate, and userEngagementDuration by deviceCategory over the last 30 days. Highlight if mobile bounce rate is significantly higher than desktop.
```

### Top international markets performance
```text
Show my top 10 countries by totalUsers and sessions over the last 30 days, including engagementRate and keyEvents. Flag any countries where engagement is 20% below the average.
```

### City-level conversion breakdown
```text
Query the top 15 cities in our primary market by sessions and keyEvents over the last 30 days. Show me where conversion concentration is highest.
```

## Correct dimension names
| Concept | GA4 API name |
|---|---|
| Country | `country` |
| City | `city` |
| Region | `region` |
| Device category | `deviceCategory` |
| Operating system | `operatingSystem` |
| OS version | `operatingSystemVersion` |
| Browser | `browser` |
| Screen resolution | `screenResolution` |
| Language | `language` |

Device category values: `desktop`, `mobile`, `tablet`.

## Step 1 — Country breakdown
```
dimensions: ["country"]
metrics: ["totalUsers", "sessions", "userEngagementDuration",
          "screenPageViewsPerSession", "keyEvents"]
date_range: last 30 days
order_by: totalUsers DESC
limit: 20
```

## Step 2 — Device split
```
dimensions: ["deviceCategory"]
metrics: ["sessions", "totalUsers", "engagementRate",
          "userEngagementDuration", "bounceRate"]
date_range: last 30 days
order_by: sessions DESC
```

## Step 3 — Country + device cross-tab
Understand device preferences by market:

```
dimensions: ["country", "deviceCategory"]
metrics: ["sessions", "userEngagementDuration", "bounceRate"]
dimension_filter: country IN [your top 5 countries from Step 1]
date_range: last 30 days
order_by: sessions DESC
```

Note: combining country + deviceCategory + additional dimensions in one query
may exceed GA4's cardinality limit. Keep to 2–3 dimensions max.

## Step 4 — Single-country deep dive
For a specific country (e.g. Japan):

```
dimensions: ["city", "deviceCategory"]
metrics: ["sessions", "totalUsers", "userEngagementDuration", "keyEvents"]
dimension_filter: {
  "filter": {
    "fieldName": "country",
    "stringFilter": {"matchType": "EXACT", "value": "Japan"}
  }
}
date_range: last 30 days
order_by: sessions DESC
limit: 20
```

## Step 5 — Browser and OS (for technical optimisation)
```
dimensions: ["browser", "operatingSystem", "deviceCategory"]
metrics: ["sessions", "bounceRate", "userEngagementDuration"]
date_range: last 30 days
order_by: sessions DESC
limit: 20
```

## What to report
- Top 10 countries by users and their engagement quality
- Mobile vs desktop vs tablet split (sessions and engagement rate)
- Any country where engagement is significantly below average — flagged for investigation
- Device preferences by your top 3 markets if they differ meaningfully
