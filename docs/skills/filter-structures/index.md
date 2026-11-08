# GA4 API Filter Expressions & Dimension Regex Syntax

> Copy-paste filter templates for the GA4 Data API: exact match, beginsWith, contains, regex, AND/OR group expressions, and inListFilter structures.

Canonical URL: https://ga4mcp.com/skills/filter-structures/



The Google Analytics 4 Data API requires structured `FilterExpression` objects for `dimension_filter`. It does not accept raw SQL, plain strings, or unnested JSON.

Use these copy-paste templates to construct valid filters for exact matches, string containment, regular expressions, and boolean logic.

## The Cardinal Wrapping Rule
Every leaf filter **must** be nested inside a `"filter"` key. `fieldName` cannot appear at the top level of the JSON object.

```json
// ❌ WRONG — fieldName at top level causes validation error:
{"fieldName": "sessionSource", "stringFilter": {"value": "google"}}

// ✔️ CORRECT — leaf filter wrapped inside "filter":
{"filter": {"fieldName": "sessionSource", "stringFilter": {"value": "google", "matchType": "EXACT"}}}
```

---

## 1. Single Field Filter Templates

### Exact Match
```json
{
  "filter": {
    "fieldName": "sessionDefaultChannelGroup",
    "stringFilter": {
      "matchType": "EXACT",
      "value": "Organic Search"
    }
  }
}
```

### String Contains / Partial Match
```json
{
  "filter": {
    "fieldName": "pagePath",
    "stringFilter": {
      "matchType": "CONTAINS",
      "value": "/blog/"
    }
  }
}
```

### Regular Expression (Regex Match)
```json
{
  "filter": {
    "fieldName": "sessionSource",
    "stringFilter": {
      "matchType": "PARTIAL_REGEXP",
      "value": "chatgpt\\.com|perplexity\\.ai|claude\\.ai"
    }
  }
}
```

Allowed `matchType` values: `EXACT`, `BEGINS_WITH`, `ENDS_WITH`, `CONTAINS`, `FULL_REGEXP`, `PARTIAL_REGEXP`.

---

## 2. Boolean Group Expressions

### AND Group (All Conditions Must Match)
```json
{
  "andGroup": {
    "expressions": [
      {
        "filter": {
          "fieldName": "deviceCategory",
          "stringFilter": {"matchType": "EXACT", "value": "mobile"}
        }
      },
      {
        "filter": {
          "fieldName": "country",
          "stringFilter": {"matchType": "EXACT", "value": "United States"}
        }
      }
    ]
  }
}
```

### OR Group (Any Condition Matches)
```json
{
  "orGroup": {
    "expressions": [
      {
        "filter": {
          "fieldName": "sessionDefaultChannelGroup",
          "stringFilter": {"matchType": "EXACT", "value": "Organic Search"}
        }
      },
      {
        "filter": {
          "fieldName": "sessionDefaultChannelGroup",
          "stringFilter": {"matchType": "EXACT", "value": "Organic Social"}
        }
      }
    ]
  }
}
```

### NOT Expression (Exclude Matching Values)
```json
{
  "notExpression": {
    "filter": {
      "fieldName": "sessionDefaultChannelGroup",
      "stringFilter": {"matchType": "EXACT", "value": "Direct"}
    }
  }
}
```

---

## 3. In-List Filter (Match Multiple Strings Efficiently)
Instead of nesting multiple OR expressions, use `inListFilter` to match against a collection of strings:

```json
{
  "filter": {
    "fieldName": "country",
    "inListFilter": {
      "values": ["United States", "United Kingdom", "Canada", "Germany"]
    }
  }
}
```

---

## Key Structure Translations

| Invalid Key (Common Guess) | Valid GA4 Data API Key |
|---|---|
| `and_filter` | `andGroup` |
| `or_filter` | `orGroup` |
| `not_filter` | `notExpression` |
| `filters` | `expressions` |
| `field` | `fieldName` |
| `stringFilter.exact` | `stringFilter.value` with `matchType: "EXACT"` |

> ⚠️ **Field Casing:** Values inside `fieldName` must be strictly **camelCase** (e.g. `sessionDefaultChannelGroup`, `pagePath`, `landingPage`). Snake_case values will be rejected with an `Unknown field for FilterExpression` error.
