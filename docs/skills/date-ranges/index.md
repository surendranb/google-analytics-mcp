# GA4 API Date Ranges: Syntax, Offsets & Comparisons

> Allowed date string formats for the GA4 Data API: YYYY-MM-DD, today, yesterday, 7daysAgo, 30daysAgo, and multi-range period comparisons without API errors.

Canonical URL: https://ga4mcp.com/skills/date-ranges/



How to specify date ranges in the Google Analytics 4 Data API and structure period-over-period comparisons without triggering syntax or parsing errors.

## Supported Date String Formats

The GA4 Data API accepts four formats for start and end dates:

| Format String | Description | Example |
|---|---|---|
| `YYYY-MM-DD` | Exact calendar date | `"2026-10-15"` |
| `today` | Current calendar day (partial data) | `"today"` |
| `yesterday` | Most recent complete calendar day | `"yesterday"` |
| `NdaysAgo` | Relative offset from current day | `"7daysAgo"`, `"30daysAgo"`, `"90daysAgo"` |

> ⚠️ **Common Syntax Errors:** Strings like `"last7days"`, `"last-week"`, or `"lastMonth"` are **invalid** and will cause an API parse error. Always use `NdaysAgo` or exact ISO dates (`YYYY-MM-DD`).

---

## Standard Comparison Windows

| Analysis Window | Recommended Start Date | Recommended End Date |
|---|---|---|
| **Last 7 Complete Days** | `"7daysAgo"` | `"yesterday"` |
| **Last 28 Complete Days** | `"28daysAgo"` | `"yesterday"` |
| **Last 90 Complete Days** | `"90daysAgo"` | `"yesterday"` |
| **Current Month to Date** | `"YYYY-MM-01"` | `"today"` |
| **Full Prior Month** | Prior month 1st | Prior month last day |
| **Year to Date (YTD)** | `"YYYY-01-01"` | `"yesterday"` |

---

## Structuring Period-Over-Period Comparisons

To compare two non-overlapping timeframes (e.g., week-over-week or month-over-month), execute two separate `get_ga4_data` calls:

### Week-Over-Week Example
- **Current Week (Call 1):** `start_date="7daysAgo"`, `end_date="yesterday"`
- **Prior Week (Call 2):** `start_date="14daysAgo"`, `end_date="8daysAgo"`

**Delta Calculation:** `((current_value - prior_value) / prior_value) * 100`

### Beware of Day-of-Week Seasonality
Never compare an incomplete current week against a full prior week, and avoid comparing weekends to weekdays directly. Traffic on Mondays often differs substantially from Saturdays. Always compare identical day-of-week groupings.

---

## The Intra-Day "Today" Rule
`today` contains partial-day data up to the current hour. Comparing `today` to `yesterday` directly will always show an artificial traffic drop because `yesterday` represents 24 hours of data while `today` covers only elapsed hours. For daily trend tracking, use `"yesterday"` as your end boundary.
