# GA4 Channel Acquisition: Default Grouping Rules

> How GA4 Default Channel Groups work, how to audit channel performance, and how to spot traffic falling into Unassigned or Direct due to broken UTM parameters.

Canonical URL: https://ga4mcp.com/skills/channel-acquisition/



Analyze traffic sources, campaign media, and Default Channel Groups in Google Analytics 4. Determine which channels drive the highest volume, produce the longest engagement times, and deliver conversions.

## Correct Dimension Names
Always use verified GA4 Data API field names:

| Acquisition Dimension | GA4 API Name | Notes |
|---|---|---|
| **Default Channel Group** | `sessionDefaultChannelGroup` | Organic Search, Direct, Paid Search, Referral, etc. |
| **Source** | `sessionSource` | Specific entity (e.g., google, linkedin, newsletter) |
| **Medium** | `sessionMedium` | Mechanism (e.g., organic, cpc, referral, email) |
| **Source / Medium Combined** | `sessionSourceMedium` | Combined source and medium string |
| **Campaign Name** | `sessionCampaignName` | UTM campaign parameter value |
| **Campaign ID** | `sessionCampaignId` | Numeric ad campaign ID |
| **Manual Ad Content** | `sessionManualAdContent` | `utm_content` parameter value |

> ⚠️ **Common Trap:** Never use `sessionDefaultChannelGrouping` (it does not exist). Always use `sessionDefaultChannelGroup`.

---

## Step 1 — Channel Overview & Efficiency
Rank acquisition channels by total sessions and visitor quality:

```text
dimensions: ["sessionDefaultChannelGroup"]
metrics: ["sessions", "totalUsers", "newUsers", "userEngagementDuration",
          "screenPageViewsPerSession", "bounceRate"]
date_range: last 30 days
order_by: sessions DESC
```

---

## Step 2 — Source & Medium Granularity
Look beneath broad channel buckets to examine individual referring platforms:

```text
dimensions: ["sessionSource", "sessionMedium"]
metrics: ["sessions", "newUsers", "userEngagementDuration", "keyEvents"]
date_range: last 30 days
order_by: sessions DESC
limit: 25
```

---

## Step 3 — Paid Campaign ROI Audit
Evaluate performance across paid advertising channels:

```text
dimensions: ["sessionCampaignName", "sessionDefaultChannelGroup"]
metrics: ["sessions", "newUsers", "keyEvents", "userEngagementDuration"]
dimension_filter: {
  "filter": {
    "fieldName": "sessionMedium",
    "stringFilter": {"matchType": "EXACT", "value": "cpc"}
  }
}
date_range: last 30 days
order_by: sessions DESC
```

---

## Step 4 — Diagnosing 'Unassigned' Traffic Spikes
If traffic in the `Unassigned` channel group is growing, your UTM campaign tagging is malformed.

Query `sessionSource` and `sessionMedium` filtered specifically for `sessionDefaultChannelGroup = 'Unassigned'`. Common causes include:
- Typos in `utm_medium` (e.g., `utm_medium=Social` with capital S, or `utm_medium=cpc_ads`).
- Missing `utm_medium` while passing `utm_source`.
- Non-standard medium values not recognized by Google's default channel group definition rules.

---

## Three Prompts to Ask Your AI Agent

Copy-paste these prompts into Claude Code, Cursor, or Gemini CLI:

```text
1. "Break down our acquisition channels over the last 30 days. Report sessions, active users, engagement rate, and key events for each channel."

2. "List all sessions landing in the 'Unassigned' channel group over the past 60 days. Group by sessionSource and sessionMedium to identify malformed UTM tags."

3. "Compare the engagement duration and conversion rate of Paid Search versus Organic Search over the last 90 days."
```

## How to Check Manually in the GA4 Console
1. Navigate to **Reports → Acquisition → Traffic acquisition**.
2. Review the `Session default channel group` table.
3. Click the blue **+** icon beside the primary column to add **Traffic source → Session source / medium** as a secondary dimension.
