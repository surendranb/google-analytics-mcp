# AGENTS.md — Agent Operating Manual

> **For AI Agents (Claude Code, Cursor, Codex, Gemini, Antigravity, OpenCode, Aider) connecting to or executing `google-analytics-mcp`.**

---

## ⚡ 1. How This MCP Works

This server provides instant, direct access to Google Analytics 4 Data and Admin APIs through two authentication paths:

1. **Zero-Config Web Login**: When first launched, opening the browser allows the human user to sign in with Google once. The local server automatically captures the session token into `~/.config/ga4-mcp/session.json`.
2. **Offline Service Account**: If the human sets `GOOGLE_APPLICATION_CREDENTIALS`, the server uses the local JSON key directly.

---

## 📖 2. Recommended Agent Query Workflow

1. **Discover Properties**:
   - Call `list_properties` to see all accessible GA4 accounts and properties.
   - Note the `active_default` and any property names/IDs.
2. **Find Exact Dimension/Metric Names**:
   - Before executing complex queries, call `search_schema(keyword="...", property="<name_or_id>")` to get verified API names.
3. **Execute Reports**:
   - Call `get_ga4_data(dimensions=[...], metrics=[...], property="<name_or_id>")`.
   - Read pre-calculated totals directly from `"totals"` in the response payload.
4. **Use Analytical Recipes**:
   - For high-level diagnostic questions (e.g. traffic drops, e-commerce, AI referrals, bot filtering), call `search_skills("<topic>")`.

---

## 👤 3. How to Handle the Human (Auth & Permissions)

- **If no session or credentials exist**: Inform the human that a browser window has opened for Google sign-in. Once they click Allow, continue the query.
- **If permissions are missing**: Call `get_troubleshooting_guide(topic="setup")` or `get_troubleshooting_guide(topic="iam")`.

---

## ⚠️ 4. Zero-Hallucination Query Rules

1. **Field Naming**:
   - `sessionDefaultChannelGroup`, `pagePath`, `country` are **dimensions**.
   - `sessions`, `activeUsers`, `screenPageViews`, `eventCount` are **metrics**.
   - 'screenPageViews' not 'pageViews'; 'totalUsers' not 'users'; 'keyEvents' not 'conversions'.
2. **Multi-Property Queries**:
   - Pass `property="<alias_or_name>"` (e.g. `property="RunInsight"`) to query specific properties.
3. **Server-Side Aggregation**:
   - `get_ga4_data` returns exact period totals in `"totals"`. Never sum individual rows manually.
