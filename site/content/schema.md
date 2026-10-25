---
slug: /schema/
title: "GA4 query shapes — filters, field names and totals"
description: "The exact JSON shapes for dimension_filter and metric_filter in the GA4 Data API v1beta schema, plus the field-name rule that prevents most 400 errors."
group: start
nav: "Query shapes"
order: 4
---

# Query shapes

`get_ga4_data` takes filters in the shape of the Google Analytics Data API v1beta schema. It is not SQL, and it is not a query string. This page is the six shapes that cover every filter you will write, copied exactly.

## The rule that prevents most errors

**One top-level key per expression.** A filter expression has exactly one of these keys, and nothing else beside it:

- `filter` — a single condition
- `andGroup` — all conditions must match
- `orGroup` — any condition may match
- `notExpression` — invert one condition

Two keys in the same object is the most common 400. The server translates between `camelCase` and `snake_case`, so `fieldName` and `field_name` both work, but the structure still has to be right.

## Exact match on a string

Cities that are exactly London:

```json
{
  "filter": {
    "fieldName": "city",
    "stringFilter": {
      "matchType": "EXACT",
      "value": "London"
    }
  }
}
```

`matchType` accepts `EXACT`, `BEGINS_WITH`, `ENDS_WITH`, `CONTAINS`, `FULL_REGEXP` and `PARTIAL_REGEXP`. Regex values are case-sensitive by default; add `"caseSensitive": false` to the `stringFilter` object to relax it.

## A value from a list

Any of three countries, in one condition rather than three:

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

`inListFilter` is the one to reach for when the model would otherwise write an `orGroup` of exact matches. It is shorter, and it cannot be malformed by nesting.

## A numeric threshold

Metrics only. Users above 100, in `metric_filter`:

```json
{
  "filter": {
    "fieldName": "activeUsers",
    "numericFilter": {
      "operation": "GREATER_THAN",
      "value": {
        "int64Value": "100"
      }
    }
  }
}
```

Operations are `EQUAL`, `LESS_THAN`, `LESS_THAN_OR_EQUAL`, `GREATER_THAN`, `GREATER_THAN_OR_EQUAL` and `BETWEEN`. For `BETWEEN`, the value object holds `fromValue` and `toValue` instead of a single `int64Value`.

## All conditions must hold

London, on mobile:

```json
{
  "andGroup": {
    "expressions": [
      {
        "filter": {
          "fieldName": "city",
          "stringFilter": {
            "matchType": "EXACT",
            "value": "London"
          }
        }
      },
      {
        "filter": {
          "fieldName": "deviceCategory",
          "stringFilter": {
            "matchType": "EXACT",
            "value": "Mobile"
          }
        }
      }
    ]
  }
}
```

The `expressions` array is required and the key is `andGroup`, not `and`. Writing `"and": [...]` is invalid.

## Excluding one condition

Everything except direct traffic:

```json
{
  "notExpression": {
    "filter": {
      "fieldName": "sessionDefaultChannelGroup",
      "stringFilter": {
        "matchType": "EXACT",
        "value": "Direct"
      }
    }
  }
}
```

`notExpression` wraps exactly one expression. To exclude two things, use `notExpression` around an `orGroup`.

## Field names come from your property, not from training

If you get an invalid dimension or metric error, the name you used does not exist in that property. It is usually a Universal Analytics name — `pageviews`, `users`, `conversions` — and GA4 renamed all three.

Use the search tool before typing a name:

```text
search_schema(keyword="conversions")
```

That returns `keyEvents` today, not `conversions`, because GA4 renamed the concept in 2024. The server validates field names against the live property before the query runs, so a wrong name comes back with the reason and a candidate instead of a bare 400.

For a whole category at once, `list_dimension_categories` and `list_metric_categories` return counts first; then `get_dimensions_by_category` gives you the names.

## Rows, totals and the reason both exist

Every multi-row pull returns a `totals` block that GA4 computed server-side, alongside the rows. Read the period figure from `totals`. Do not add up daily rows in the model — rates do not sum, and a seven-day total built by arithmetic is wrong while looking reasonable.

Large queries are estimated before they run and warn above 2,500 rows. If you need more than that, narrow the date range or the dimensions rather than forcing it through; a wide pull with no aggregation fills the context window and answers nothing.

## Next

If the query runs but the answer is nonsense, the problem is method rather than syntax. Read the [skills index](/skills/) and pick the recipe that matches the question.
