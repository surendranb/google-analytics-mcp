# Custom Dimensions and Event Parameters

How to find and query property-specific custom dimensions in GA4.

## The core rule

Custom dimensions are **property-specific**. Never guess their names.
Always call `search_schema("custom")` first — it will show every registered
custom dimension for this exact property.

## Two valid syntaxes

GA4 supports two ways to access custom data:

**Registered custom dimensions** — appear in the schema by their registered name.
Find them with `search_schema`. Use the name exactly as returned.

**Unregistered event parameters** — accessed inline with:
- `customEvent:parameter_name` for event-scoped parameters
- `customUser:property_name` for user-scoped properties

The `parameter_name` must exactly match what your tracking code sends.
If the property has not collected this parameter, the API returns an error.

## Why guessing fails

The model cannot know what custom parameters a GA4 property uses —
they are defined by the site's own tracking code and GA4 Admin settings.
`customEvent:page_category` works on one property and fails on another
depending on whether that property's tracking sends a `page_category` parameter.

## Workflow

1. Call `search_schema("custom")` — lists all registered custom dimensions.
2. If the one you need appears, use its exact API name.
3. If it does not appear, ask the user what event parameter name their
   tracking code uses, then query with `customEvent:that_name`.
4. If the query still fails, the parameter is not collected by this property.

## Scope matters

| Scope | Syntax | Use for |
|---|---|---|
| Event | `customEvent:name` | per-hit data (page category, product id, etc.) |
| User | `customUser:name` | user attributes (plan, cohort, customer type) |
| Session | registered name only | session-level custom groupings |

Mixing scopes can cause incompatibility errors — see the `compatible-combinations` skill.
