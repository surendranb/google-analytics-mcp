# AI Referral Analysis

Measure traffic arriving from AI tools — ChatGPT, Claude, Perplexity, Gemini,
Copilot, and others — and understand how it behaves compared to other channels.

## When to use
- You want to quantify how much of your traffic comes from AI assistants
- You're tracking whether AI-driven discovery is growing over time
- You want to compare AI referral quality (engagement, conversion) to SEO or direct

## Known AI referral sources
These domains appear as `sessionSource` in GA4 when users click links from AI tools:

| Tool | Source domains |
|---|---|
| ChatGPT | `chatgpt.com`, `chat.openai.com` |
| Claude | `claude.ai` |
| Perplexity | `perplexity.ai` |
| Gemini | `gemini.google.com` |
| Copilot | `copilot.microsoft.com`, `bing.com` (when AI-driven) |
| You.com | `you.com` |
| Grok | `grok.x.ai`, `x.com` |

## Step 1 — Volume and trend
```
dimensions: ["date", "sessionSource"]
metrics: ["sessions", "newUsers", "userEngagementDuration", "screenPageViews"]
dimension_filter: sessionSource contains "chatgpt.com" OR "perplexity.ai" OR
                  "claude.ai" OR "gemini.google.com" OR "copilot.microsoft.com"
date_range: last 30–90 days
```

Use `date` as a dimension to see the growth trend.

## Step 2 — Quality comparison
Compare AI referral quality against your other top channels:

```
dimensions: ["sessionDefaultChannelGroup", "sessionSource"]
metrics: ["sessions", "userEngagementDuration", "screenPageViewsPerSession",
          "keyEvents", "bounceRate"]
date_range: last 30 days
```

Then filter the results to AI sources and compare engagement metrics
against `Organic Search` and `Direct`.

## Step 3 — Which pages AI drives traffic to
```
dimensions: ["sessionSource", "landingPage"]
metrics: ["sessions", "userEngagementDuration", "keyEvents"]
dimension_filter: sessionSource contains "chatgpt.com" OR "perplexity.ai" OR "claude.ai"
date_range: last 30 days
order_by: sessions DESC
```

This shows which content AI tools are citing and sending users to.

## What to report
- AI referral as % of total sessions (and % of total new users)
- Month-over-month growth rate for AI referral traffic
- Engagement quality: AI vs Organic Search (userEngagementDuration, keyEvents)
- Top landing pages receiving AI referral traffic
- Which AI tool sends the most traffic
