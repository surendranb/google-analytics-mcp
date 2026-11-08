# Track AI Referral Traffic in Google Analytics 4

> How to track and measure traffic from ChatGPT, Claude, Perplexity, and Gemini in GA4. Exact dimension filters, regex patterns, and channel comparison rules.

Canonical URL: https://ga4mcp.com/skills/ai-referral-analysis/



Measure traffic arriving from generative AI assistants — ChatGPT, Claude, Perplexity, Gemini, Microsoft Copilot, and others — and understand how AI-driven discovery behaves compared to organic search and direct traffic.

## When to use
- You want to quantify how much of your total traffic originates from AI assistants
- You're tracking whether AI-driven discovery (Generative Engine Optimization / GEO) is growing over time
- You want to compare AI referral engagement quality (session duration, bounce rate, key events) against traditional organic search
- You need to identify which specific URLs AI models cite and recommend to users

## Known AI referral sources
These domains appear in GA4 under the `sessionSource` dimension when users click links cited inside AI chat windows:

| AI Platform | Source Domains (`sessionSource`) | Default Channel Group |
|---|---|---|
| **ChatGPT** | `chatgpt.com`, `chat.openai.com` | `AI Assistant` or `Referral` |
| **Claude** | `claude.ai` | `AI Assistant` or `Referral` |
| **Perplexity** | `perplexity.ai` | `AI Assistant` or `Referral` |
| **Google Gemini** | `gemini.google.com` | `AI Assistant` or `Referral` |
| **Microsoft Copilot** | `copilot.microsoft.com`, `bing.com` | `AI Assistant` or `Organic Search` |
| **You.com** | `you.com` | `Referral` |
| **Grok** | `grok.x.ai`, `x.com` | `Referral` or `Organic Social` |

> **Note on Native GA4 Tracking:** Google Analytics 4 includes an **AI Assistant** channel within the Default Channel Group for major platforms. However, traffic from new AI browsers or unclassified models frequently lands under generic `Referral` or `Direct`. Filtering by `sessionSource` guarantees complete coverage.

---

## Step 1 — Volume and 90-Day Trend
Track total volume and trajectory over time:

```text
dimensions: ["date", "sessionSource"]
metrics: ["sessions", "newUsers", "userEngagementDuration", "screenPageViews"]
dimension_filter: sessionSource contains "chatgpt.com" OR "perplexity.ai" OR
                  "claude.ai" OR "gemini.google.com" OR "copilot.microsoft.com"
date_range: last 30–90 days
```

Plotting `date` against `sessions` reveals whether AI traffic is expanding month-over-month.

---

## Step 2 — Engagement Quality vs. Organic Search
Compare visitor engagement quality between AI referrals and your standard channels:

```text
dimensions: ["sessionDefaultChannelGroup", "sessionSource"]
metrics: ["sessions", "userEngagementDuration", "screenPageViewsPerSession",
          "keyEvents", "bounceRate"]
date_range: last 30 days
```

Filter results to AI sources and evaluate:
- Do AI visitors spend more or less time on site than organic search visitors?
- What is the key event conversion rate from ChatGPT vs. Google Search?

---

## Step 3 — Which Pages AI Engines Cite
Discover which URLs AI models cite most frequently:

```text
dimensions: ["sessionSource", "landingPage"]
metrics: ["sessions", "userEngagementDuration", "keyEvents"]
dimension_filter: sessionSource contains "chatgpt.com" OR "perplexity.ai" OR "claude.ai"
date_range: last 30 days
order_by: sessions DESC
```

This pinpoints the exact documentation, articles, or product pages driving AI search citations.

---

## Three Prompts to Ask Your AI Agent

Once connected to GA4 MCP, you can copy-paste these prompts directly into Claude, Cursor, or Gemini CLI:

```text
1. "Show all referral traffic from AI platforms (ChatGPT, Claude, Perplexity, Gemini) over the last 90 days. Report monthly sessions, active users, and average engagement duration per source."

2. "Compare the engagement quality of AI assistant traffic against traditional Organic Search for the past 30 days. Show bounce rate, session duration, and key events per session."

3. "Which specific landing pages are AI assistants citing? List the top 10 landing pages for chatgpt.com and perplexity.ai over the last 60 days sorted by sessions descending."
```

## How to Check Manually in the GA4 Console
1. Open [Google Analytics](https://analytics.google.com).
2. Go to **Reports → Acquisition → Traffic acquisition**.
3. Switch the primary dimension dropdown from *Session default channel group* to **Session source / medium**.
4. In the table search bar, type `chatgpt.com` or `perplexity.ai` to view immediate session totals.
