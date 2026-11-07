---
name: custom-dimensions
titleTag: "GA4 Custom Dimensions & Event Parameters Guide"
description: "Query custom dimensions and event parameters in the GA4 Data API. How to find parameter names, register them in GA4 Admin, and query custom event schemas."
---

# GA4 Custom Dimensions & Event Parameters Guide

How to identify, register, and query custom dimensions and event parameters using the Google Analytics 4 Data API.

## The Core Rule: Property-Specific Schemas
Custom dimensions and user properties are unique to your individual website or application. Never guess their names. Always instruct your AI agent to call `search_schema("custom")` first to retrieve the active custom definitions for your specific property.

---

## Two Methods to Access Custom Data

### 1. Registered Custom Dimensions (Standard Syntax)
When an event parameter is registered inside Google Analytics (**Admin → Data display → Custom definitions**), it becomes an official dimension in your schema.
- Format: Uses the exact API name assigned during registration (e.g. `author_name`, `membership_tier`).
- How to discover: Run `search_schema("keyword")` to inspect live registered names.

### 2. Inline Event Parameters (Direct API Syntax)
If a parameter is actively collected by your tracking code (`gtag.js`, GTM) but has not yet been registered in the GA4 Admin UI, you can query it directly using prefix syntax:
- **Event-scoped parameters:** `customEvent:<parameter_name>` (e.g., `customEvent:blog_category`, `customEvent:error_code`).
- **User-scoped properties:** `customUser:<property_name>` (e.g., `customUser:plan_type`, `customUser:company_size`).

> ⚠️ **Note:** The parameter name following the colon must match the exact case-sensitive string sent by your front-end tracking code.

---

## Scope Boundaries

| Parameter Scope | Syntax | Common Use Cases |
|---|---|---|
| **Event Scope** | `customEvent:<param>` | Page category, button ID, search filter, video title |
| **User Scope** | `customUser:<property>` | Account tier, signup cohort, customer lifetime segment |
| **Session Scope** | Registered name only | Session-level calculated groups (requires Admin registration) |

---

## Verification Workflow

1. Prompt your agent: `search_schema("custom")`.
2. If your target dimension appears, use its declared API identifier.
3. If it does not appear, verify the parameter name in your Google Tag Manager container or tracking script and query using `customEvent:<param_name>`.
4. If the query returns a 400 error, verify that the parameter has collected at least one event in the queried date range.
