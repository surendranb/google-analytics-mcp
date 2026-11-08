---
slug: /natural-language-google-analytics/
title: "Natural Language Google Analytics: Query GA4 with AI"
description: "How to query Google Analytics 4 in natural language using Claude, Cursor, and AI agents. Local stdio execution, pre-flight schema checks, zero data leakage."
group: start
nav: "Natural Language"
order: 3
---

# Natural Language Google Analytics

Querying Google Analytics 4 through a conversation changes how teams extract marketing insights. Instead of building custom explorations in the GA4 web UI, writing BigQuery SQL, or navigating the Analytics Data API documentation, you ask questions in plain English and receive structured, verified answers.

General-purpose language models fail when pointed directly at the Google Analytics Data API without a specialized protocol layer. This guide explains why naive LLM queries fail, how the Model Context Protocol (MCP) fixes them, and how to query your analytics with natural language.

## Why General LLMs Fail on Google Analytics 4

Every developer who asks an untuned AI to query GA4 encounters three structural failures:

### 1. Universal Analytics Vocabulary Hallucination
Language models were trained on millions of pages of Universal Analytics (UA) documentation and StackOverflow answers written prior to July 2023. When asked for traffic data, models reflexively generate queries containing `ga:sessions`, `pageviews`, `uniquePageviews`, and `bounces`.

In the GA4 Data API:
- `pageviews` does not exist; the dimension is `pagePath` and the metric is `screenPageViews`.
- `conversions` was renamed to `keyEvents` on May 6, 2024.
- `ga:` prefixes cause hard 400 validation errors.

An unassisted model enters a retry loop, guessing variations until hitting API rate limits.

### 2. Incompatible Dimensional Scopes
GA4 enforces strict separation between user-scoped, session-scoped, and event-scoped data:
- `firstUserDefaultChannelGroup` (user-scoped) cannot be paired with event-scoped metrics like `eventCount` without distorting attribution.
- Session dimensions require session metrics.

When an AI guesses dimension pairings, the GA4 API rejects the request with: `The request's dimensions and metrics are incompatible.`

### 3. Mental Arithmetic Drift on Ratios and Averages
If an agent pulls seven daily rows and calculates the weekly bounce rate, average session duration, or conversion rate, it sums or averages the ratio column. Ratios and averages do not sum arithmetically. The resulting figures look plausible but are mathematically incorrect.

## How GA4 MCP Solves Natural Language Queries

The GA4 MCP server acts as an intelligent intermediary between your AI harness (Claude, Cursor, Codex, Gemini CLI) and the Google Analytics Data API.

```
┌─────────────────┐       Natural Language Question       ┌────────────────────────┐
│  Claude / Cursor│ ────────────────────────────────────► │  GA4 MCP Coordinator   │
└─────────────────┘                                       └───────────┬────────────┘
         ▲                                                            │
         │ Verified Response + Totals                                 ▼
┌────────┴────────┐       Validated API Request           ┌────────────────────────┐
│  GA4 Data API   │ ◄──────────────────────────────────── │ Pre-Flight Validation  │
│  (Google Cloud) │                                       │ • Property Schema Match│
└─────────────────┘                                       │ • Scope Compatibility  │
                                                          │ • Server-Side Totals   │
                                                          └────────────────────────┘
```

Three mechanisms guarantee accuracy:

1. **Pre-Flight Schema Validation**: Before executing any request, `get_ga4_data` inspects the live metadata of your property. If an agent requests an invalid field, the server intercepts the call and returns the valid GA4 equivalent.
2. **Deterministic Skills on Demand**: When an agent faces an analytical task, it loads a local skill (`traffic-diagnosis`, `ecommerce-analysis`, `attribution-scope`). The skill dictates the proven dimensions, metrics, and interpretation rules.
3. **GA4 Server-Side Totals**: The server requests `metricAggregations: ["TOTAL"]` directly from Google. The agent reports the Google-computed total rather than performing client-side math.

## Ten Natural Language Questions You Can Ask Today

Once configured in your AI client, you can ask questions directly in your editor or chat terminal:

### Traffic & Acquisition
- *"What were our top 5 acquisition channels by sessions over the last 30 days, and which had the highest engagement rate?"*
- *"Compare this week's active users with last week's. Did organic search or direct traffic drive the variance?"*
- *"Show me all referral traffic from AI platforms (ChatGPT, Claude, Perplexity) for the past 90 days."*

### Content & Engagement
- *"Which blog posts had the highest average engagement time among users from organic search this month?"*
- *"List the top 10 landing pages with the highest bounce rate that received at least 200 sessions."*
- *"What are our top pages viewed by mobile users compared to desktop users?"*

### E-Commerce & Conversions
- *"What is our overall checkout-to-purchase conversion rate across the last 60 days?"*
- *"Which traffic channel produced the highest average order value (AOV) last month?"*
- *"Show me purchase revenue broken down by country and city for the last quarter."*

### Technical & Anomaly Detection
- *"Did our site experience an abnormal spike in direct traffic yesterday? Check city and device category to verify if it was bot traffic."*

## Local Stdio Architecture & Data Privacy

Security is a primary concern when connecting analytics to AI assistants. Cloud-hosted analytics SaaS wrappers require passing your Google Cloud credentials to third-party servers.

GA4 MCP operates entirely over local **stdio transport**:
- **Direct Connection**: All communication travels over stdin/stdout between your local AI harness and the local Python subprocess.
- **No Third-Party Relay**: API calls travel directly from your machine to `https://analyticsdata.googleapis.com` via your own Google Cloud Service Account.
- **Zero Query Retention**: Your analytics numbers never touch external proxy databases or third-party loggers.

## Next Steps

- **[Installation Guide](/setup/)**: Step-by-step setup using the 1-line auto-installer or native package managers.
- **[Prompt Cookbook](/google-analytics-ai-prompts/)**: 35 production-tested prompts across e-commerce, SEO, and acquisition.
- **[Client Configuration](/ga4-mcp-for-every-harness/)**: How to add GA4 MCP to Cursor, Claude, VS Code, and 14 other environments.
