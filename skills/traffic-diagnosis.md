# Traffic Change Diagnosis

Systematically diagnose why traffic changed — spike, drop, or shift in mix.
Follow these steps in order. Each step narrows the hypothesis.

## Step 1 — Establish the baseline

Compare the period in question to the equivalent prior period:
```
dimensions: ["date"]
metrics: ["sessions", "totalUsers", "newUsers", "engagedSessions", "keyEvents"]
date_range: affected period + same-length prior period
```

Measure: absolute change, % change, and whether all metrics moved together.
If sessions dropped but engagement rate improved, volume dropped but quality held — different cause than if everything dropped proportionally.

## Step 2 — Isolate which channel changed

```
dimensions: ["sessionDefaultChannelGroup"]
metrics: ["sessions", "totalUsers", "engagedSessions", "engagementRate"]
date_range: affected period vs prior period
```

Which channel account for most of the change? Narrow to that channel before going deeper.

## Step 3 — Check time pattern (sudden vs gradual)

```
dimensions: ["date", "sessionDefaultChannelGroup"]
metrics: ["sessions"]
date_range: last 28 days
```

- **Sudden single-day spike/drop** → campaign launch/end, deploy, media mention, bot flood
- **Gradual decline over weeks** → SEO decay, seasonal drift, quality score drop
- **Step change that persists** → tracking change, filter change, channel definition update

## Step 4 — Fingerprint the cause

Run queries matching the suspected cause:

**Bot flood** — see `bot-traffic-detection` skill:
- `engagementRate` near 0, `averageSessionDuration` ≈ 0
- Unusual hostname or country concentration

**Campaign start/end**:
```
dimensions: ["sessionCampaignName", "sessionSource", "sessionMedium"]
metrics: ["sessions", "keyEvents", "engagementRate"]
dimension_filter: sessionDefaultChannelGroup IN ["Paid Search", "Paid Social", "Display"]
```

**SEO change (organic)**:
```
dimensions: ["sessionDefaultChannelGroup", "landingPagePlusQueryString"]
metrics: ["sessions", "engagementRate", "keyEvents"]
dimension_filter: sessionDefaultChannelGroup = "Organic Search"
date_range: 90 days (to see gradual trend)
```

**Technical/tracking change** — all channels drop equally at the same moment.
Check with `dimensions: ["date"]` — a vertical drop on a single date across all channels
points to a tag firing issue or consent mode change.

## Step 5 — Conclude

State:
1. What changed (metric + magnitude)
2. Which channel drove it
3. When it started (sudden or gradual)
4. Most likely cause (from fingerprinting)
5. One action: investigate further / fix tracking / pause campaign / accept as seasonal

## What not to do

Do not conclude "traffic dropped" from a single metric in isolation.
Do not compare to the prior week without accounting for day-of-week patterns
(Monday always differs from Sunday — compare Monday-to-Monday or full weeks).
