---
slug: /google-analytics-ai-prompts/
title: "35 Production GA4 Prompts for Claude, Cursor & AI"
description: "Copy-paste prompt cookbook for querying Google Analytics 4 with AI agents. Tested recipes for traffic drops, channel ROI, e-commerce, and AI referrals."
group: start
nav: "AI Prompts"
order: 4
---

# 35 Production GA4 Prompts for Claude, Cursor & AI Agents

Querying Google Analytics 4 through an AI agent requires prompts that instruct the model on methodology, comparison periods, and scope. Vague questions like *"How is my site doing?"* produce vague summaries. Precise prompts produce actionable analytical breakdowns.

This cookbook provides 35 tested prompts designed for Claude Code, Cursor, Codex, Gemini CLI, and any MCP-compatible client connected to GA4 MCP.

## 1. Traffic Change & Drop Diagnosis

Use these prompts when metrics shift unexpectedly and you need to isolate the root cause before reacting.

### Prompt 1.1: Sudden Traffic Drop Triage
```text
Diagnose our traffic over the last 14 days compared to the prior 14-day period. 
Break down sessions, active users, and engagement rate by sessionDefaultChannelGroup. 
Identify which specific channel drove the decline and check if the drop was site-wide or isolated to specific landing pages.
```
*API calls: `get_ga4_data` with `sessionDefaultChannelGroup`, `date`, `sessions`, `activeUsers`, `engagementRate`.*

### Prompt 1.2: Organic Search Drop vs. Tracking Snippet Error
```text
Our organic traffic dropped this week. Compare the last 7 days to the previous 7 days. 
Check daily session totals alongside landingPage paths. 
Tell me if the drop occurred as a sudden cliff (suggesting a broken tag or consent banner) or a gradual slide (suggesting a ranking or algorithm change).
```

### Prompt 1.3: Direct Traffic Spike Audit
```text
We had an unexpected spike in direct traffic over the last 48 hours. 
Pull sessions, screenPageViews, and userEngagementDuration broken down by city and deviceCategory. 
Check whether this traffic exhibits bot patterns (near-zero engagement duration, 100% single-page views, single datacenter origin).
```

### Prompt 1.4: Channel Mix Shift
```text
Analyze our traffic mix over the last 30 days compared to the 30 days before that. 
Calculate the percentage share of total sessions for each sessionDefaultChannelGroup. 
Which channels gained share and which channels lost share?
```

### Prompt 1.5: Weekend vs. Weekday Traffic Baseline
```text
Pull our daily sessions and active users for the past 6 weeks. 
Calculate our average weekday volume versus our average weekend volume. 
Flag any weekday that fell more than 20% below our trailing weekday average.
```

### Prompt 1.6: Campaign UTM Performance Audit
```text
List all sessions from the past 30 days where sessionMedium is 'cpc' or 'paid'. 
Group by sessionCampaign and sessionSource. 
Report sessions, keyEvents, and engagementRate to identify our best-performing and lowest-performing paid campaigns.
```

---

## 2. AI Search & Answer Engine Tracking

Measure visitors arriving from generative AI assistants (ChatGPT, Claude, Perplexity, Gemini).

### Prompt 2.1: Monthly AI Referral Overview
```text
Identify all referral traffic from AI platforms over the last 90 days. 
Filter sessionSource for chatgpt.com, chat.openai.com, claude.ai, perplexity.ai, and gemini.google.com. 
Report monthly sessions, activeUsers, and average engagement duration per source.
```

### Prompt 2.2: AI Traffic Quality vs. Organic Search
```text
Compare the engagement quality of AI assistant referrals (ChatGPT, Perplexity, Claude) against traditional Organic Search for the last 30 days. 
Show sessions, bounceRate, userEngagementDuration, and keyEvents per session.
```

### Prompt 2.3: Top Landing Pages for AI Visitors
```text
Which specific landing pages are AI assistants citing? 
Filter sessionSource for chatgpt.com and perplexity.ai over the last 60 days. 
List landingPage sorted by sessions descending with total pageviews and key events.
```

### Prompt 2.4: Perplexity vs. ChatGPT Share
```text
Calculate the traffic split between ChatGPT (chatgpt.com, chat.openai.com) and Perplexity (perplexity.ai) over the last 30 days. 
Show daily session trends for both sources to determine which assistant is growing faster on our domain.
```

### Prompt 2.5: Conversion Rate of AI Referrals
```text
What is the key event conversion rate for visitors arriving from AI assistants compared to our site-wide average? 
Pull sessions and keyEvents for AI sources over the last 90 days and calculate keyEvents per session.
```

### Prompt 2.6: New User Acquisition via AI Engines
```text
How many first-time visitors arrived via AI engines this quarter? 
Query newUsers and sessions where sessionSource matches AI platforms, and calculate new users as a percentage of total AI sessions.
```

---

## 3. Acquisition & Channel Performance

Evaluate how marketing channels deliver qualified visitors.

### Prompt 3.1: Top Acquisition Channels Overview
```text
Summarize our top 10 acquisition channels for the past 30 days. 
Include sessions, activeUsers, screenPageViewsPerSession, averageSessionDuration, and keyEvents. 
Sort by sessions descending.
```

### Prompt 3.2: First User vs. Session Channel Comparison
```text
Compare firstUserDefaultChannelGroup (how users first discovered us) with sessionDefaultChannelGroup (how users returned) for the last 60 days. 
Highlight channels that drive discovery versus channels that drive return visits.
```

### Prompt 3.3: Referral Domain Quality Breakdown
```text
List the top 15 referring websites (sessionSource where sessionMedium is 'referral') over the last 30 days. 
Report sessions, engagementRate, and keyEvents. Exclude internal subdomains.
```

### Prompt 3.4: Social Media Channel Comparison
```text
Break down traffic from social media platforms over the last 30 days. 
Filter for sessionDefaultChannelGroup equals 'Organic Social' and 'Paid Social'. 
Compare LinkedIn, Twitter/X, YouTube, and Reddit by engagement rate and key events.
```

### Prompt 3.5: Email Campaign ROI
```text
Pull all traffic where sessionMedium equals 'email' for the past 60 days. 
Group by sessionCampaign and show sessions, userEngagementDuration, and keyEvents to identify our most effective newsletter sends.
```

### Prompt 3.6: Unassigned Traffic Diagnosis
```text
Check how much traffic fell into the 'Unassigned' channel group over the last 30 days. 
Pull sessionSource and sessionMedium for all Unassigned sessions so we can identify broken UTM parameters.
```

---

## 4. Content & Landing Page Audits

Discover which URLs attract visitors and which lose them immediately.

### Prompt 4.1: Top 20 Landing Pages by Engagement
```text
List our top 20 landing pages by organic search traffic over the last 30 days. 
Report sessions, activeUsers, userEngagementDuration, and bounceRate. 
Sort by userEngagementDuration descending.
```

### Prompt 4.2: High-Traffic, High-Bounce Page Alert
```text
Find all landing pages that received at least 250 sessions over the past 30 days but have a bounce rate above 65%. 
Sort by session volume descending so we know which pages require immediate UX or content revision.
```

### Prompt 4.3: New Content Velocity Check
```text
Audit traffic to all URLs under our blog or docs path published in the last 60 days. 
Show weekly screenPageViews and active users for each URL since publication.
```

### Prompt 4.4: Low-Performing Content Audit
```text
Identify pages on our site that received fewer than 20 total screenPageViews over the past 90 days. 
Group by pagePath and sort ascending to help us plan content pruning or consolidation.
```

### Prompt 4.5: Internal Search Terms Analysis
```text
What terms are visitors searching for inside our site? 
Query the searchTerm dimension for the last 30 days with eventCount and activeUsers. 
Sort by frequency descending.
```

### Prompt 4.6: Desktop vs. Mobile Landing Page Drop-off
```text
Compare bounceRate and userEngagementDuration across mobile and desktop for our top 10 landing pages over the last 30 days. 
Flag pages where mobile bounce rate exceeds desktop bounce rate by more than 15 percentage points.
```

---

## 5. E-Commerce & Funnel Conversion

Analyze purchases, average order value, and checkout drop-offs.

### Prompt 5.1: Overall E-Commerce Performance Summary
```text
Summarize our e-commerce performance for the last 30 days compared to the prior 30 days. 
Report purchaseRevenue, transactions, averagePurchaseRevenue, and ecommercePurchases. 
Calculate our average order value (AOV).
```

### Prompt 5.2: Revenue by Acquisition Channel
```text
Which marketing channels generate the most revenue? 
Break down purchaseRevenue, transactions, and averagePurchaseRevenue by sessionDefaultChannelGroup for the last 60 days. 
Sort by purchaseRevenue descending.
```

### Prompt 5.3: Checkout Funnel Drop-off Analysis
```text
Examine our checkout funnel events over the last 30 days: view_item, add_to_cart, begin_checkout, and purchase. 
Report the total eventCount for each stage and calculate the drop-off percentage between each consecutive step.
```

### Prompt 5.4: Top 15 Products by Revenue
```text
List our top 15 products by gross revenue over the past 90 days. 
Query itemName, itemRevenue, itemsPurchased, and itemsViewed. 
Calculate the view-to-purchase conversion rate for each product.
```

### Prompt 5.5: High Cart-Abandonment Products
```text
Identify products with high cart additions but low final purchases over the last 60 days. 
Compare itemsAddedToCart against itemsPurchased per itemName for all items added to cart at least 50 times.
```

### Prompt 5.6: Repeat Buyer vs. First-Time Buyer Revenue
```text
Compare revenue generated by new users versus returning users over the last 60 days. 
Query newUsers and activeUsers alongside purchaseRevenue grouped by newVsReturning dimension.
```

---

## 6. Geographic, Device & Audience Segmentation

Identify international opportunities and hardware friction.

### Prompt 6.1: Top Countries by Active Users & Value
```text
List our top 15 countries by activeUsers over the last 30 days. 
Show sessions, userEngagementDuration, and keyEvents per country. 
Sort by activeUsers descending.
```

### Prompt 6.2: City-Level Growth in Primary Market
```text
Filter traffic to our primary country over the last 60 days. 
Break down sessions, activeUsers, and keyEvents by city. 
Identify the top 10 fastest-growing metropolitan areas.
```

### Prompt 6.3: Browser & Operating System Health Check
```text
Audit traffic by browser and operatingSystem for the past 30 days. 
Check bounceRate and engagementRate across Chrome, Safari, Firefox, Edge, and mobile in-app browsers. 
Flag any browser with an unusually high bounce rate that might indicate a rendering bug.
```

### Prompt 6.4: Screen Resolution Friction Analysis
```text
Pull screenResolution with sessions and bounceRate for mobile devices over the last 30 days. 
Check whether specific small-screen resolutions suffer from higher drop-off rates.
```

### Prompt 6.5: New vs. Returning User Engagement
```text
Compare new users and returning users over the last 90 days. 
Report sessions, userEngagementDuration, screenPageViewsPerSession, and keyEvents to see how customer retention influences overall engagement.
```

---

## Next Steps

- **[Natural Language Guide](/natural-language-google-analytics/)**: How the schema validation engine prevents API errors.
- **[Analytical Skills Index](/skills/)**: Explore the 16 bundled playbooks that power these queries.
- **[Installation Guide](/setup/)**: Set up GA4 MCP in your editor or terminal in 60 seconds.
