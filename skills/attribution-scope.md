# Attribution Scope

GA4 has three distinct attribution scopes. Using the wrong scope gives
misleading results. Choose based on the question you are answering.

## The three scopes

| Scope | Dimension prefix | Question it answers | When to use |
|---|---|---|---|
| **Session** | `session` | Where did THIS session come from? | Traffic Acquisition — volume, engagement, conversions by source |
| **First-user** | `firstUser` | Which channel originally acquired this user? | User Acquisition — who brought in new users |
| **Event/attribution** | *(no prefix)* | Which channel gets credit for this conversion? | Advertising reports — AI-weighted conversion credit allocation |

## Dimensions by scope

**Session scope** — use for traffic analysis:
- `sessionDefaultChannelGroup`
- `sessionSource`
- `sessionMedium`
- `sessionCampaignName`
- `sessionSourceMedium`

**First-user scope** — use for acquisition analysis:
- `firstUserDefaultChannelGroup`
- `firstUserSource`
- `firstUserMedium`
- `firstUserCampaignName`

**Event/attribution scope** — use only in advertising/conversion contexts:
- `defaultChannelGroup` *(no prefix)*
- `source` *(no prefix)*
- `medium` *(no prefix)*

## How to choose

**"Where is my traffic coming from?"** → session scope
```
dimensions: ["sessionDefaultChannelGroup", "sessionSource", "sessionMedium"]
metrics: ["sessions", "totalUsers", "engagedSessions", "keyEvents"]
```

**"Which channels are bringing in new users?"** → first-user scope
```
dimensions: ["firstUserDefaultChannelGroup", "firstUserSource"]
metrics: ["newUsers", "totalUsers"]
```

**"How should I attribute conversion credit across channels?"** → event scope
(Use only with advertising campaign analysis; this is AI-weighted attribution.)

## Common mistake

A user acquired via Instagram who later converts via Google Organic will show:
- `sessionDefaultChannelGroup = "Organic Search"` (where this session came from)
- `firstUserDefaultChannelGroup = "Organic Social"` (where they were first acquired)

These are different questions. Mixing scopes in one query produces meaningless results.
Never combine `sessionSource` with `firstUserMedium` in the same report.

## Nested filters

When filtering, use the same scope as your dimensions:
```json
// Filtering traffic acquisition report — use session-scoped dimension
{"filter": {"fieldName": "sessionDefaultChannelGroup", "stringFilter": {"value": "Organic Search", "matchType": "EXACT"}}}

// NOT source (attribution scope) — wrong scope for this report
{"filter": {"fieldName": "source", "stringFilter": {"value": "google", "matchType": "EXACT"}}}
```
