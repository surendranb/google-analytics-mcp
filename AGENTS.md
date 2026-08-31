# AGENTS.md — Agent Operating Manual

> **For AI Agents (Claude Code, Cursor, Codex, Gemini, Antigravity, OpenCode, Aider) connecting to or executing `google-analytics-mcp`.**

---

## ⚡ 1. Fast Install & Multi-Site Configuration

### A. Zero-Config User Login (1-Command Consultant Login)
If the user was invited to their GA4 properties via Google email, they only need:
```bash
gcloud auth application-default login --scopes=https://www.googleapis.com/auth/analytics.readonly
```
Then launch with **zero environment variables**! The server auto-discovers all accessible accounts and properties.

### B. Client Config Snippet: Single Site or Legacy
```json
{
  "mcpServers": {
    "google-analytics": {
      "command": "uvx",
      "args": ["google-analytics-mcp"],
      "env": {
        "GA4_PROPERTY_ID": "123456789",
        "GOOGLE_APPLICATION_CREDENTIALS": "/path/to/service_account.json"
      }
    }
  }
}
```

### C. Client Config Snippet: Multi-Site Registry
Define multiple sites and credentials via `GA4_SITES` env var or `~/.config/ga4-mcp/sites.json`:
```json
{
  "mcpServers": {
    "google-analytics": {
      "command": "uvx",
      "args": ["google-analytics-mcp"],
      "env": {
        "GA4_SITES": "{\"default_site\":\"blog\",\"sites\":{\"blog\":{\"name\":\"Personal Blog\",\"property_id\":\"111111111\",\"credentials\":\"/path/to/blog-sa.json\"},\"store\":{\"name\":\"E-Commerce Shop\",\"property_id\":\"222222222\",\"credentials\":\"/path/to/store-sa.json\"}}}"
      }
    }
  }
}
```
Or simply drop multiple service account keys into `~/.config/ga4-mcp/credentials/` — the server auto-scans and indexes all properties.

---

## 📖 2. Primary Tools & Multi-Site Workflow

1. **`list_properties`**: Call this FIRST to discover all accounts and properties accessible with your credentials.
2. **`search_schema(keyword="...", property="<site_or_id>")`**: Search valid dimension/metric names for a specific property.
3. **`get_ga4_data(dimensions=[...], metrics=[...], property="<site_or_id>")`**: Run reports with server-side totals and automated routing.
4. **`search_skills(query="...")`**: Access analytical playbooks (traffic drops, e-commerce, AI referrals, bot detection).

---

## 👤 3. How to Handle the Human (Auth & Setup)

If no credentials exist, guide the user with these exact steps:

1. **If using personal/agency Google account (Zero GCP required)**:
   - *"Run `gcloud auth application-default login --scopes=https://www.googleapis.com/auth/analytics.readonly` in your terminal to connect all your GA4 properties in 1 minute."*
2. **If using Service Accounts**:
   - The user needs a Service Account with the **Viewer** role on their GA4 Property in *Google Analytics Admin → Property Access Management*.
   - Point `GOOGLE_APPLICATION_CREDENTIALS` to the `.json` file, or drop it into `~/.config/ga4-mcp/credentials/`.
3. **If Auth Fails**: Call `get_troubleshooting_guide(topic="setup")` or `get_troubleshooting_guide(topic="iam")`.

---

## ⚠️ 4. Zero-Hallucination Query Rules

1. **Field Naming**:
   - `sessionDefaultChannelGroup`, `pagePath`, `country` are **dimensions**.
   - `sessions`, `activeUsers`, `screenPageViews`, `eventCount` are **metrics**.
   - 'screenPageViews' not 'pageViews'; 'totalUsers' not 'users'; 'keyEvents' not 'conversions'.
2. **Multi-Property Queries**:
   - When the user asks about a specific site, pass `property="<alias_or_name>"` to `get_ga4_data` and `search_schema`.
   - The server validates against that specific property's live custom dimensions.
3. **Server-Side Aggregation**:
   - `get_ga4_data` returns pre-calculated metric totals in `"totals"`. Read the period figure directly from `"totals"`; do not sum rows manually.
