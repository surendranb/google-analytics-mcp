# Diagnose GA4 Traffic Drops: Step-by-Step Triage

> A six-step triage framework to diagnose GA4 traffic drops. Isolate channel shifts, check tracking snippet errors, and distinguish real drops from bot drops.

Canonical URL: https://ga4mcp.com/skills/traffic-diagnosis/



Systematically diagnose why Google Analytics 4 traffic changed — whether a sudden drop, an unexpected spike, or a gradual erosion in quality. Follow these steps in order to eliminate speculation and isolate the root cause.

## Step 1 — Establish the Baseline
Compare the affected timeframe to the equivalent prior period (accounting for day-of-week seasonality):

```text
dimensions: ["date"]
metrics: ["sessions", "totalUsers", "newUsers", "engagedSessions", "keyEvents"]
date_range: affected period + same-length prior period
```

Measure absolute change, percentage change, and whether all metrics moved together:
- If sessions dropped but engagement rate improved, total volume fell but visitor quality held — indicating bot filtration or paid budget cuts rather than site breakdown.
- If all metrics fell to zero overnight, the issue is an infrastructure or tag firing failure.

---

## Step 2 — Isolate Which Channel Changed
Determine which acquisition channel drove the variance:

```text
dimensions: ["sessionDefaultChannelGroup"]
metrics: ["sessions", "totalUsers", "engagedSessions", "engagementRate"]
date_range: affected period vs prior period
```

Isolate the channel accounting for the majority of the drop (Organic Search, Paid Search, Direct, Referral, or Social) before investigating deeper.

---

## Step 3 — Analyze the Time Pattern (Cliff vs. Slide)
The shape of the decline reveals the underlying mechanism:

```text
dimensions: ["date", "sessionDefaultChannelGroup"]
metrics: ["sessions"]
date_range: last 28 days
```

- **Sudden vertical cliff (overnight drop):** Points to a tracking failure (broken GTM container, Google Consent Mode v2 misconfiguration, deploy removing gtag.js, or paused ad campaign).
- **Gradual slide over weeks:** Points to SEO algorithm updates, lost search rankings, seasonal demand shifts, or content decay.
- **Permanent step change:** Indicates a filter update, internal IP exclusion rule, or channel definition change in GA4 Admin.

---

## Step 4 — Fingerprint the Root Cause

### A. Bot Traffic Removal vs. Real User Drop
See the `bot-traffic-detection` skill. If traffic dropped but `engagementRate` surged from 20% to 65%, your site didn't lose real customers — a spam bot network was filtered out.

### B. Paid Campaign Changes
```text
dimensions: ["sessionCampaignName", "sessionSource", "sessionMedium"]
metrics: ["sessions", "keyEvents", "engagementRate"]
dimension_filter: sessionDefaultChannelGroup IN ["Paid Search", "Paid Social", "Display"]
```
Check whether campaign spend paused, ad group targeting narrowed, or billing expired.

### C. Organic Search & SEO Shifts
```text
dimensions: ["sessionDefaultChannelGroup", "landingPagePlusQueryString"]
metrics: ["sessions", "engagementRate", "keyEvents"]
dimension_filter: sessionDefaultChannelGroup = "Organic Search"
date_range: 90 days
```
Cross-check with Google Search Console:
- If GSC clicks are steady but GA4 sessions dropped, you have a tracking snippet error.
- If both GSC clicks and GA4 sessions dropped, you experienced a genuine loss in search rankings.

---

## Three Prompts to Ask Your AI Agent

Copy-paste these prompts into Claude Code, Cursor, or Gemini CLI:

```text
1. "Diagnose our traffic drop over the last 14 days compared to the prior 14 days. Break down sessions, users, and engagement rate by sessionDefaultChannelGroup and identify the primary driver."

2. "Check daily organic search sessions for the last 30 days alongside landingPage. Was the drop site-wide or isolated to specific landing pages?"

3. "Audit our top 10 landing pages comparing the last 7 days to the prior 7 days. Flag pages with more than a 25% drop in sessions and check if mobile or desktop traffic fell faster."
```

## How to Check Manually in the GA4 Console
1. Open **Reports → Acquisition → Traffic acquisition**.
2. Click the date selector in the top-right corner.
3. Turn on **Compare** and select **Preceding period (match day of week)**.
4. Review the percentage change column for `sessionDefaultChannelGroup` to spot the channel with the largest negative delta.
