---
slug: /troubleshooting/
title: "Fix Common GA4 Data API & IAM Errors (Quick Guide)"
description: "Troubleshooting guide for the top 5 Google Analytics 4 Data API errors: 403 Viewer permission, invalid dimension names, quota exhaustion, and token limits."
group: start
nav: "Troubleshooting"
order: 6
---

# Fix Common GA4 Data API & IAM Errors

When connecting an AI agent or querying the Google Analytics 4 Data API, five common errors cause over 90% of failures. This guide covers the root cause and immediate resolution for each error.

## 1. Error 403: The Caller Does Not Have Permission

### The Symptom
```text
google.api_core.exceptions.PermissionDenied: 403 The caller does not have permission
User does not have sufficient permissions for this property.
```

### The Root Cause
The Google Cloud Service Account authenticated successfully, but it has not been granted access inside Google Analytics. Creating a service account in Google Cloud Console does **not** grant it access to your analytics data. You must add the service account email as a **Viewer** inside the Google Analytics Admin interface.

### The Nine-Step Resolution
1. Open your service account JSON key file in any text editor.
2. Copy the `client_email` value (format: `your-agent@your-project.iam.gserviceaccount.com`).
3. Open [Google Analytics](https://analytics.google.com).
4. Select the property whose ID matches your `GA4_PROPERTY_ID`.
5. Click the gear icon (**Admin**) in the bottom-left corner.
6. In the **Property** column, click **Property access management**.
7. Click the blue **+** button in the top-right corner, then click **Add users**.
8. Paste the `client_email` into the email field and uncheck *Notify new users by email*.
9. Under **Direct roles**, select **Viewer** (read-only) and click **Add**.

Access takes effect immediately with zero propagation delay. For screenshots and detailed IAM guidance, see the [Permissions Guide](/iam/).

---

## 2. Error 400: Invalid Dimension or Metric Name

### The Symptom
```text
google.api_core.exceptions.InvalidArgument: 400 Field pageviews is not found.
Field conversions is not found in this property.
```

### The Root Cause
Your AI assistant requested a field name from Universal Analytics (sunset July 2023) or an older API schema. Common legacy terms like `pageviews`, `uniquePageviews`, `ga:sessions`, and `conversions` are rejected by the GA4 Data API.

### Common Field Translations

| Invalid Legacy Name | Valid GA4 Data API Name | Type | Notes |
| :--- | :--- | :--- | :--- |
| `pageviews` | `screenPageViews` | Metric | Total pages viewed across web and app |
| `uniquePageviews` | `screenPageViews` | Metric | GA4 does not track unique views; use sessions per page |
| `conversions` | `keyEvents` | Metric | Renamed by Google on May 6, 2024 |
| `users` | `totalUsers` or `activeUsers` | Metric | `activeUsers` is GA4's primary user metric |
| `bounceRate` | `bounceRate` | Metric | In GA4, bounceRate is the inverse of engagementRate |
| `avgSessionDuration` | `averageSessionDuration` | Metric | Average duration in seconds |
| `sourceMedium` | `sessionSourceMedium` | Dimension | Dimension combining source and medium |
| `channelGrouping` | `sessionDefaultChannelGroup` | Dimension | Default channel group (Organic, Direct, Paid) |
| `landingPage` | `landingPage` | Dimension | Landing page path without query strings |
| `pagePath` | `pagePath` | Dimension | Page URL path |

This MCP server automatically checks names against your live schema before dispatching queries. If you run into an unknown field, ask your agent to call `search_schema('<keyword>')`.

---

## 3. Property ID vs. Measurement ID Mismatch

### The Symptom
```text
google.api_core.exceptions.InvalidArgument: 400 Invalid property ID: "G-XXXXXXXXXX".
Property ID must be numeric.
```

### The Root Cause
You passed your web data stream Measurement ID (starting with `G-`) instead of your numeric **Property ID**.

- **Measurement ID** (`G-XXXXXXXXXX`): Used by front-end tracking snippets (`gtag.js`, Google Tag Manager) to send events into GA4.
- **Property ID** (`123456789`): A 9-digit number used by the Google Analytics Data API and Admin API to query reports.

### Where to Find the Numeric Property ID
1. Open [Google Analytics](https://analytics.google.com).
2. Click **Admin** (gear icon at bottom left).
3. Under the **Property** column, click **Property details**.
4. The numeric **Property ID** appears in the top-right corner (e.g. `555043732`).

Set this number as your environment variable:
```bash
export GA4_PROPERTY_ID="555043732"
```

---

## 4. Error 429: Resource Exhausted / Quota Limits

### The Symptom
```text
google.api_core.exceptions.ResourceExhausted: 429 Exhausted property quota tokens.
Resource has been exhausted (e.g. check quota).
```

### The Root Cause
Google Analytics 4 enforces hourly and daily API token quotas per property:
- **Standard Properties**: 25,000 tokens per hour, 5,000 concurrent requests, and 10 dimensions per query.
- **GA4 360 Properties**: 250,000 tokens per hour.

Tokens are consumed based on query complexity (number of dimensions, date range length, and row count).

### How to Prevent Quota Exhaustion
1. **Narrow Date Ranges**: Query `last 30 days` instead of `last 365 days` during interactive exploration.
2. **Limit Dimensions**: Keep queries to 2–4 dimensions. Each additional dimension multiplies row combinations exponentially.
3. **Use Row Limits**: Specify `limit: 50` or `limit: 100` rather than pulling thousands of rows into your client context window.
4. **Use Built-in Row Guards**: GA4 MCP includes pre-query row estimators that warn you before large multi-thousand-row requests execute.

---

## 5. Error 400: Incompatible Dimensions and Metrics

### The Symptom
```text
google.api_core.exceptions.InvalidArgument: 400 The request's dimensions and metrics are incompatible.
```

### The Root Cause
In GA4, data is organized across three primary scopes:
1. **User Scope**: Attributes of the person (e.g., `firstUserDefaultChannelGroup`, `firstUserSource`).
2. **Session Scope**: Attributes of the visit (e.g., `sessionDefaultChannelGroup`, `sessionSource`, `sessions`).
3. **Event Scope**: Attributes of a specific action (e.g., `eventName`, `pagePath`, `eventCount`).

Mixing incompatible scopes (such as pairing user-scoped acquisition dimensions with hit-level event metrics) will cause the Google Analytics Data API to reject the request.

### The Compatibility Rules
- Pair `session*` dimensions (`sessionDefaultChannelGroup`, `sessionSource`) with session metrics (`sessions`, `bounceRate`, `averageSessionDuration`).
- Pair `pagePath` or `eventName` with event metrics (`screenPageViews`, `eventCount`, `keyEvents`).
- Pair `firstUser*` dimensions with user metrics (`newUsers`, `activeUsers`).

To view valid combinations, consult our [Compatible Combinations Guide](/skills/compatible-combinations/).

---

## In-Session Setup Recovery

If your setup breaks mid-session due to a missing property ID, an expired token, or missing credentials, you do not need to restart your client or edit config files manually.

Ask your agent:
```text
Run setup_ga4_access to reconnect my analytics credentials.
```

The server will prompt you for the missing value, validate the connection against Google Cloud, and restore access immediately inside the active chat.

---

## Next Steps

- **[Installation Guide](/setup/)**: Set up your Google Cloud Service Account and local MCP server.
- **[Query Shapes](/schema/)**: Learn valid filter syntax, regex rules, and ordering parameters.
- **[Skills Index](/skills/)**: Browse 16 ready-to-use analytical playbooks with proven field combinations.
