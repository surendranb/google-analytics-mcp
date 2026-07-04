---
name: ga4-analytics
description: Use when querying Google Analytics 4 data, active users, sessions, pageviews, bounce rate, channel acquisition, or custom dimensions.
---

# Google Analytics 4 Intelligence Skill

## When to Use
- User asks for GA4 traffic, active users, sessions, pageviews, or user acquisition numbers.
- User wants conversion breakdown, device breakdown, or geographical traffic reports.

## Core Rules for LLM Tool Calling
1. **Always use exact GA4 API field names**: Use `activeUsers`, `sessions`, `screenPageViews`, `date`, `country`, `sessionSource`.
2. **Search schema if unsure**: If user asks for a metric you don't know, call `search_schema(query="...")` first. Do NOT guess field names.
3. **Run query**: Call `get_ga4_data` with dimensions, metrics, and start/end dates (e.g. `2026-06-28` to `2026-07-04` or `7daysAgo`).
