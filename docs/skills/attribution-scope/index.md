# GA4 Attribution Scope: User vs. Session vs. Event

> Why session, user, and event metrics never match in GA4. Rules for pairing dimensions and metrics across user-scoped, session-scoped, and event-scoped models.

Canonical URL: https://ga4mcp.com/skills/attribution-scope/



Google Analytics 4 features three distinct attribution scopes. Selecting the wrong scope produces distorted reports and misleading ROI conclusions. Choose your dimensions based on the specific business question you are answering.

## The Three Scopes Explained

| Scope | Dimension Prefix | Core Question | Standard GA4 Report |
|---|---|---|---|
| **Session Scope** | `session*` | Where did *this specific visit* originate? | **Traffic Acquisition** (Reports > Acquisition) |
| **First-User Scope** | `firstUser*` | Which channel originally introduced this person? | **User Acquisition** (Reports > Acquisition) |
| **Event / Cross-Channel** | *(no prefix)* | Which touchpoint receives credit for this conversion? | **Advertising / Attribution** (Explore > Attribution) |

---

## Dimensions by Attribution Scope

### Session Scope (Use for Traffic Analysis)
- `sessionDefaultChannelGroup`
- `sessionSource`
- `sessionMedium`
- `sessionSourceMedium`
- `sessionCampaignName`

*Pair with session metrics: `sessions`, `engagedSessions`, `bounceRate`, `averageSessionDuration`.*

### First-User Scope (Use for Top-of-Funnel Acquisition)
- `firstUserDefaultChannelGroup`
- `firstUserSource`
- `firstUserMedium`
- `firstUserCampaignName`

*Pair with user metrics: `newUsers`, `totalUsers`, `userKeyEventRate`.*

### Event / Cross-Channel Scope (Use for Fractional Attribution)
- `defaultChannelGroup` (no prefix)
- `source` (no prefix)
- `medium` (no prefix)
- `campaignName` (no prefix)

*Pair with event and conversion metrics: `keyEvents`, `purchaseRevenue`.*

---

## How to Choose the Right Scope

### Scenario 1: "Where is our daily web traffic coming from?"
Use **Session Scope**. This tells you which channels are actively generating sessions today.
```text
dimensions: ["sessionDefaultChannelGroup", "sessionSource"]
metrics: ["sessions", "activeUsers", "engagementRate"]
date_range: last 30 days
```

### Scenario 2: "Which marketing channels attract new customers?"
Use **First-User Scope**. This isolates the initial touchpoint that converted an anonymous person into a known visitor.
```text
dimensions: ["firstUserDefaultChannelGroup", "firstUserSource"]
metrics: ["newUsers", "activeUsers"]
date_range: last 90 days
```

---

## The Attribution Multi-Touch Trap
Consider a visitor who discovers your website via a LinkedIn post, returns two days later via an organic Google search, and buys a subscription.

In GA4:
- In a **User Acquisition** report, the conversion attributes to `Organic Social` (`firstUserDefaultChannelGroup`).
- In a **Traffic Acquisition** report, the session attributes to `Organic Search` (`sessionDefaultChannelGroup`).
- In an **Advertising Attribution** model, credit is split according to data-driven weighting.

Neither report is broken; they simply measure different stages of the customer journey. Always specify which scope you want your AI agent to examine.
