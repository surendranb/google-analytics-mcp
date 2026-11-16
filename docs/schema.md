# GA4 Invalid Dimension or Metric: Fix the 400 Error

> Fix 400 invalid dimension or metric, incompatible dimensions and metrics, and filter parse errors on GA4. Verify every field name with search_schema first.

Canonical URL: https://ga4mcp.com/schema/



`get_ga4_data` takes filters in the shape of the Google Analytics Data API v1beta schema. It is not SQL, and it is not a query string. This page is the six shapes that cover every filter you will write, plus the three 400 errors they prevent.

| The 400 says | What is actually wrong | Jump to |
|---|---|---|
| `Field pageviews is not found` | The field name is a Universal Analytics name or a guess | [Field names](#field-names-come-from-your-property-not-from-training) |
| `dimensions and metrics are incompatible` | A user-, session- or event-scoped dimension is paired with the wrong metric family | [Scope rules](#scope-rules-are-what-cause-incompatible-errors) |
| `Invalid JSON payload` on a filter | Two expression keys in one object, or `and` instead of `andGroup` | [The rule](#the-rule-that-prevents-most-errors) |

## The rule that prevents most errors

**One top-level key per expression.** A filter expression has exactly one of these keys, and nothing else beside it:

- `filter` — a single condition
- `andGroup` — all conditions must match
- `orGroup` — any condition may match
- `notExpression` — invert one condition

Two keys in the same object is the most common 400. So is `fieldName` sitting at the top level of the expression instead of nested inside `filter`. The server translates between `camelCase` and `snake_case`, so `fieldName` and `field_name` both work, but the structure still has to be right.

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

The `expressions` array is required and the key is `andGroup`, not `and`. Writing `"and": [...]` is invalid. The other wrong keys the server sees are `or_filter` for `orGroup`, `not_filter` for `notExpression`, and `filters` for `expressions`.

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

If you get an invalid dimension or metric error, the name you used does not exist in that property. It is usually a Universal Analytics name — `pageviews`, `users`, `conversions` — and GA4 renamed all three. These are the substitutions the server's own guide carries:

| Wrong name | Correct GA4 name |
|---|---|
| `pageviews`, `uniquePageviews` | `screenPageViews` |
| `users` | `totalUsers` or `activeUsers` |
| `conversions` | `keyEvents` (renamed May 2024) |
| `conversionRate`, `sessionConversionRate` | `sessionKeyEventRate` |
| `avgSessionDuration` | `averageSessionDuration` |
| `timeOnPage`, `avgTimeOnPage` | `userEngagementDuration` |
| `sessionDefaultChannelGrouping` | `sessionDefaultChannelGroup` |
| `source`, `medium` | `sessionSource`, `sessionMedium` |

All API names are camelCase. `page_path` and `event_name` are rejected; `pagePath` and `eventName` are not.

Use the search tool before typing a name:

```text
search_schema(keyword="conversions")
```

That returns `keyEvents` today, because GA4 renamed the concept in 2024. The server validates field names against the live property before the query runs, so a wrong name comes back with the reason and a candidate instead of a bare 400.

For a whole category at once, `list_dimension_categories` and `list_metric_categories` return counts first; then `get_dimensions_by_category` gives you the names.

## Scope rules are what cause incompatible errors

GA4 groups every field by the thing it describes. Pair across two groups and the API returns `The request's dimensions and metrics are incompatible`, which is a 400 about the combination rather than any single name.

- **Session scope** — `sessionSource`, `sessionMedium`, `sessionCampaignName`. Pair with `sessions`, `bounceRate`, `sessionKeyEventRate`. Not with `eventCount`.
- **Event scope** — `eventName`, `pagePath`. Pair with `eventCount`, `screenPageViews`, `keyEvents`. Not with `sessions`.
- **User scope** — `firstUserSource`, `firstUserMedium`. Pair with `totalUsers`, `newUsers`. Not with `sessions`.
- **Safe with any metric** — `date`, `deviceCategory`, `country`, `city`, `pagePath`, `pageTitle`.

When a combination is rejected, do not retry with a guessed pair. `search_skills('compatible-combinations')` returns the tested pairs, and the [skills index](/skills/) lists every recipe with the fields it uses.

## Rows, totals and the reason both exist

Every multi-row pull returns a `totals` block that GA4 computed server-side, alongside the rows. Read the period figure from `totals`. Do not add up daily rows in the model — rates do not sum, and a seven-day total built by arithmetic is wrong while looking reasonable.

Large queries are estimated before they run and warn above 2,500 rows. If you need more than that, narrow the date range or the dimensions rather than forcing it through; a wide pull with no aggregation fills the context window and answers nothing.

## Five prompts that resolve a schema error

Paste one into [Claude](/ga4-mcp-for-claude/), [Cursor](/ga4-mcp-for-cursor/), [Gemini CLI](/ga4-mcp-for-gemini/), or any of the [17 clients](/ga4-mcp-for-every-harness/). Each forces a lookup instead of a second guess.

1. **Find the name that replaced a UA field**
   ```text
   My query failed with "Field pageviews is not found". Call search_schema("pageviews"), tell me the GA4 name it resolves to, and rewrite my query with every legacy name replaced.
   ```
2. **Resolve an incompatible pair**
   ```text
   GA4 returned "dimensions and metrics are incompatible". Load search_skills("compatible-combinations"), name the scope each of my dimensions and metrics belongs to, and give me the smallest valid rewrite that still answers my question.
   ```
3. **Fix a filter that will not parse**
   ```text
   My dimension_filter is rejected. Check it for two keys in one expression, for fieldName outside a filter object, and for and/or/not instead of andGroup/orGroup/notExpression. Show the corrected JSON.
   ```
4. **Discover the valid fields before writing the query**
   ```text
   Before running anything, call list_metric_categories, then get_dimensions_by_category for the category that fits my question, and list the exact names you will use. Then run the query with those names only.
   ```
5. **Reject a plausible-looking name**
   ```text
   Do not trust your training for GA4 field names. Verify each dimension and metric in my query with search_schema first, list any that do not exist in this property, and substitute the returned candidates.
   ```

## Next

If the query runs but the answer is nonsense, the problem is method rather than syntax. Read the [skills index](/skills/) and pick the recipe that matches the question.
