# AGENTS.md — Agent Operating Manual

> **For AI Agents (Claude Code, Cursor, Codex, Gemini, Antigravity, OpenCode, Aider) connecting to or executing `google-analytics-mcp`.**

---

## ⚡ 1. Fast Install & Client Wiring (Start Here)

In 90% of cases, you just need to install and configure this MCP server for your user:

```bash
# 1-Line Universal Auto-Installer (Configures Claude Code, Cursor, Claude Desktop & Antigravity)
curl -fsSL "https://ga4.builditwithai.xyz/install" | bash

# Or launch directly via stdio:
uvx google-analytics-mcp
npx -y google-analytics-mcp
```

### Client Config Snippet (`mcp.json` / `claude_desktop_config.json`)
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

---

## 📖 2. What This Repo Is

A production MCP server for **Google Analytics 4 (GA4)**. It gives you direct access to the Google Analytics Data API v1beta and Admin API v1alpha.

### Primary Tools Available:
- `get_ga4_data`: Run multi-dimensional reports with date ranges, metric totals, and server-side aggregation.
- `list_accounts` & `list_properties`: Discover all GA4 properties the credentials can access.
- `get_property_metadata`: Fetch exact dimension/metric schemas and custom event definitions for a property.
- `run_realtime_report`: Fetch live active users and 30-minute event streams.
- `search_skills`: Access pre-engineered analytical recipes (traffic drops, e-commerce, bot filtering).

---

## 👤 3. How to Handle the Human (Auth & Setup)

If credentials are not yet configured, do **not** fail or dump a raw Python traceback on the human. Guide them with these exact steps:

1. **Ask for their 9-digit GA4 Property ID**:
   - *"You can find your numeric Property ID in Google Analytics under Admin → Property Settings → Property Details."*
2. **Ask for a Google Cloud Service Account JSON Key**:
   - The human needs a Service Account with the **Viewer** role on their GA4 Property in *Google Analytics Admin → Property Access Management*.
   - Once they have the `.json` file, set:
     ```bash
     export GA4_PROPERTY_ID="123456789"
     export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service_account.json"
     ```
3. **If Auth Fails**: Call `get_troubleshooting_guide(topic="setup")` or `get_troubleshooting_guide(topic="iam")` to guide the human through permission repair.

---

## ⚠️ 4. Quirks & API Landmines (Zero-Hallucination Rules)

1. **Field Naming**:
   - **Never use Universal Analytics names** (e.g. `ga:sessions` or `ga:pageviews` will hard-fail).
   - `sessionDefaultChannelGroup`, `pagePath`, `country` are **dimensions**.
   - `sessions`, `activeUsers`, `screenPageViews`, `eventCount` are **metrics**.
2. **Scope Compatibility**:
   - Do NOT mix incompatible scopes (e.g., User-scoped dimensions with Hit/Item-scoped metrics). When in doubt, call `get_property_metadata` first.
3. **Date String Formats**:
   - Allowed values: `'YYYY-MM-DD'`, `'today'`, `'yesterday'`, `'7daysAgo'`, `'30daysAgo'`, `'90daysAgo'`.
4. **Server-Side Aggregation**:
   - `get_ga4_data` returns pre-calculated metric totals. You do not need to do token-heavy arithmetic in your prompt.

---

## 🎯 5. Playbooks & Skills (How to Answer User Questions)

When your human user asks high-level business questions, call `search_skills("<topic>")` **before** constructing queries:

- **"Why did my traffic drop?"** → Call `search_skills("traffic-diagnosis")`
- **"Where is our revenue / e-commerce sales coming from?"** → Call `search_skills("ecommerce-analysis")`
- **"Are bots skewing our analytics?"** → Call `search_skills("bot-traffic-detection")`
- **"How much traffic comes from AI (ChatGPT, Claude, Perplexity)?"** → Call `search_skills("ai-referral-analysis")`
- **"Which acquisition channels perform best?"** → Call `search_skills("channel-acquisition")`
