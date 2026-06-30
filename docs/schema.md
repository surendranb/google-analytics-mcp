# Google Analytics 4 MCP: Schema Guide

When using the `get_ga4_data` tool, you must pass valid JSON structures for `dimension_filter` or `metric_filter`. These follow the strict Google Analytics Data API (v1beta) schema.

**DO NOT GUESS**. Use the exact JSON structures provided below.

## 1. Simple String Filter
To filter where `city` exactly matches "London":

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

## 2. In List Filter
To filter where `country` is in a list of values:

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

## 3. Numeric Filter (Metrics only)
To filter where `activeUsers` is greater than 100 (used in `metric_filter`):

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

## 4. Logical AND / OR (Nested Filters)
If you need to combine multiple filters, you MUST use `andGroup` or `orGroup`. Note the required `expressions` array!

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

**CRITICAL RULE:** A filter expression can ONLY have ONE top-level key: either `filter`, `andGroup`, `orGroup`, or `notExpression`.

## 5. Finding Valid Dimensions and Metrics
If you encounter an "Invalid dimension" or "Invalid metric" error, it means you guessed an API name that does not exist in GA4. 
You MUST use the `search_schema()` tool to find the exact API name.
For example, if the user asks for "conversions", call `search_schema(keyword="conversions")` to discover that the correct GA4 API metric is `keyEvents`.
