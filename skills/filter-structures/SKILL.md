---
name: filter-structures
description: "The correct shape for `dimension_filter` in `get_ga4_data`. Wrong structure returns an \"Invalid dimension_filter\" error. Use these templates."
---
# Filter Structures

The correct shape for `dimension_filter` in `get_ga4_data`.
Wrong structure returns an "Invalid dimension_filter" error. Use these templates.

## The one rule

Every leaf filter **must** be wrapped in a `"filter"` key. `fieldName` never appears at the top level.

```json
// WRONG — fieldName at top level
{"fieldName": "sessionSource", "stringFilter": {"value": "google"}}

// CORRECT — wrapped in "filter"
{"filter": {"fieldName": "sessionSource", "stringFilter": {"value": "google"}}}
```

## Template: single field filter

```json
{
  "filter": {
    "fieldName": "DIMENSION_NAME",
    "stringFilter": {
      "value": "VALUE",
      "matchType": "EXACT"
    }
  }
}
```

`matchType` options: `EXACT`, `BEGINS_WITH`, `ENDS_WITH`, `CONTAINS`, `FULL_REGEXP`, `PARTIAL_REGEXP`

## Template: AND — all conditions must match

```json
{
  "andGroup": {
    "expressions": [
      {"filter": {"fieldName": "deviceCategory", "stringFilter": {"value": "mobile", "matchType": "EXACT"}}},
      {"filter": {"fieldName": "country", "stringFilter": {"value": "United States", "matchType": "EXACT"}}}
    ]
  }
}
```

## Template: OR — any condition matches

```json
{
  "orGroup": {
    "expressions": [
      {"filter": {"fieldName": "sessionDefaultChannelGroup", "stringFilter": {"value": "Organic Search", "matchType": "EXACT"}}},
      {"filter": {"fieldName": "sessionDefaultChannelGroup", "stringFilter": {"value": "Organic Social", "matchType": "EXACT"}}}
    ]
  }
}
```

## Template: NOT — exclude matching sessions

```json
{
  "notExpression": {
    "filter": {
      "fieldName": "sessionDefaultChannelGroup",
      "stringFilter": {"value": "Direct", "matchType": "EXACT"}
    }
  }
}
```

## Template: IN LIST — match any of several values

```json
{
  "filter": {
    "fieldName": "country",
    "inListFilter": {
      "values": ["United States", "United Kingdom", "Canada"]
    }
  }
}
```

## Common wrong keys → correct keys

| Wrong key | Correct key |
|---|---|
| `and_filter` | `andGroup` |
| `or_filter` | `orGroup` |
| `not_filter` | `notExpression` |
| `filters` | `expressions` |
| `field` | `fieldName` |
| `stringFilter.exact` | `stringFilter.value` |

## Field names are always camelCase

> ⚠️ **CRITICAL FILTER TRAP**: Field names in `dimension_filter` (inside `fieldName`) MUST be exact camelCase. Passing `page_path` or `session_default_channel_group` will fail with an `Unknown field for FilterExpression` error.

| Wrong (snake_case) | Correct (camelCase) |
|---|---|
| `page_path` | `pagePath` |
| `session_default_channel_group` | `sessionDefaultChannelGroup` |
| `session_source` | `sessionSource` |
| `session_source_medium` | `sessionSourceMedium` |
| `session_campaign_name` | `sessionCampaignName` |
| `landing_page` | `landingPage` |
| `device_category` | `deviceCategory` |
| `event_name` | `eventName` |

If you use snake_case in `fieldName`, the filter will fail with an "Unknown field" error. Do NOT retry snake_case.

## Note

Only dimensions can be filtered with `dimension_filter`. To filter on metric
values (e.g. sessions > 100), you must do this in post-processing — the GA4
Data API does not support metric filters in `RunReport`.
