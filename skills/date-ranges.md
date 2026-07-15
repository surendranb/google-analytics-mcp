# Date Ranges

How to specify date ranges in `get_ga4_data` and how to structure
period-over-period comparisons.

## Valid formats

```
date_range_start / date_range_end accept:
  "YYYY-MM-DD"   — absolute date, e.g. "2024-01-15"
  "today"        — current day (partial — use carefully)
  "yesterday"    — last complete day
  "NdaysAgo"     — N days back from today, e.g. "7daysAgo", "30daysAgo", "90daysAgo"
```

`NdaysAgo` excludes today. `7daysAgo` to `yesterday` = last 7 complete days.

## Common windows

| Window | start | end |
|---|---|---|
| Last 7 days | `7daysAgo` | `yesterday` |
| Last 28 days | `28daysAgo` | `yesterday` |
| Last 90 days | `90daysAgo` | `yesterday` |
| This month | `YYYY-MM-01` | `today` |
| Last month | `YYYY-MM-01` (prior) | `YYYY-MM-last-day` (prior) |
| Year to date | `YYYY-01-01` | `yesterday` |

## Period-over-period comparison

The GA4 Data API does not support multi-period in a single call. Run two
separate `get_ga4_data` calls, then compare the results.

**Example: week-over-week**

Call 1 — this week:
```
date_range_start: "7daysAgo"
date_range_end:   "yesterday"
```

Call 2 — last week:
```
date_range_start: "14daysAgo"
date_range_end:   "8daysAgo"
```

**Example: year-over-year for July**

Call 1 — this year:
```
date_range_start: "2025-07-01"
date_range_end:   "2025-07-31"
```

Call 2 — last year:
```
date_range_start: "2024-07-01"
date_range_end:   "2024-07-31"
```

Then compute the delta: `(current - prior) / prior * 100` for each metric.

## Partial-day reads

`today` includes only the hours elapsed so far. Comparing `today` to `yesterday`
is misleading — yesterday is a full day, today is partial.

For intra-day analysis, use `today` for both start and end and note the
IST hours covered in your interpretation.

## Common mistakes

- `"last7days"` is NOT valid — use `"7daysAgo"`
- `"last-week"` is NOT valid — use absolute dates or `NdaysAgo`
- Do not use `date_range_end: "today"` when comparing to a prior complete period
- `"0daysAgo"` = today (same as `"today"`)
