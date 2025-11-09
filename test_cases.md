# GA4 MCP Server - Test Cases

This document outlines a series of test cases to validate the accuracy, efficiency, and feature-set of the refactored GA4 MCP server.

## Category 1: Data Granularity & Aggregation Tests

**Objective:** To verify that the server requests and returns data at the correct level of time-based aggregation, directly addressing the concern of receiving monthly totals vs. daily breakdowns.

---

### Test Case 1.1: Monthly Granularity over a Long Period

*   **Goal:** Confirm that using `month` as a dimension for a multi-month period returns exactly one row per month per item, not daily data.
*   **Query via MCP:**
    *   **Tool:** `get_ga4_data`
    *   **dimensions:** `["month", "pagePath"]`
    *   **metrics:** `["sessions", "totalUsers"]`
    *   **date_range_start:** A date 16 months ago (e.g., `"2024-01-01"`)
    *   **date_range_end:** `"yesterday"`
    *   **dimension_filter:** A filter for 5 high-traffic pages on your site.
      ```json
      {
        "filter": {
          "fieldName": "pagePath",
          "inListFilter": {
            "values": ["/your/page/path1", "/your/page/path2", "/your/page/path3", "/your/paga/path4", "/your/page/path5"]
          }
        }
      }
      ```
*   **Expected Result:** The number of rows in the output should be `(number of months in range) * 5`. For a 16-month period, you should get **~80 rows**, not thousands of rows of daily data. Each row should represent the total metrics for a given page for an entire month.

---

### Test Case 1.2: Daily Granularity

*   **Goal:** Confirm that using `date` as a dimension returns daily data points.
*   **Query via MCP:**
    *   **Tool:** `get_ga4_data`
    *   **dimensions:** `["date", "pagePath"]`
    *   **metrics:** `["sessions"]`
    *   **date_range_start:** `"28daysAgo"`
    *   **date_range_end:** `"yesterday"`
    *   **dimension_filter:** A filter for 2 high-traffic pages.
*   **Expected Result:** The number of rows should be approximately `(number of days in range) * 2`. For a 28-day period, you should get **~56 rows**. This validates that `date` correctly provides daily granularity.

---

### Test Case 1.3: No Time Dimension (Server-Side Aggregation)

*   **Goal:** Verify that omitting a time dimension correctly triggers the automatic server-side aggregation to get a single total for the entire period.
*   **Query via MCP:**
    *   **Tool:** `get_ga4_data`
    *   **dimensions:** `["pagePath"]`
    *   **metrics:** `["sessions", "totalUsers", "averageSessionDuration"]`
    *   **date_range_start:** `"90daysAgo"`
    *   **date_range_end:** `"yesterday"`
    *   **dimension_filter:** A filter for 5 high-traffic pages.
*   **Expected Result:** The output should contain exactly **5 rows**, one for each page path. The metrics for each row should be the aggregated totals over the entire 90-day period.

---

## Category 2: "Smart Feature" Validation

**Objective:** To verify the unique helper features of this MCP server are functioning as designed.

---

### Test Case 2.1: Large Dataset Warning

*   **Goal:** Ensure the query-size estimation triggers a warning for potentially very large datasets.
*   **Query via MCP:**
    *   **Tool:** `get_ga4_data`
    *   **dimensions:** `["date", "pagePath", "country"]`
    *   **metrics:** `["sessions"]`
    *   **date_range_start:** `"90daysAgo"`
    *   **date_range_end:** `"yesterday"`
*   **Expected Result:** The server should **not** return data. Instead, it should return a `warning` message with an estimated row count (likely > 2500) and suggestions on how to refine the query.

---

### Test Case 2.2: Large Dataset Override

*   **Goal:** Ensure the override flag successfully bypasses the warning from Test Case 2.1.
*   **Query via MCP:**
    *   Use the **exact same query** as Test Case 2.1, but add the override parameter:
    *   **proceed_with_large_dataset:** `True`
*   **Expected Result:** The server **should** now execute the query and return the full (large) dataset.

---

## Category 3: Custom Schema & Filter Logic

**Objective:** To validate that the new dynamic schema works and that complex filters are handled correctly.

---

### Test Case 3.1: Query a Custom Dimension

*   **Goal:** **(Most Important)** Confirm that the server can successfully query a custom dimension specific to your property.
*   **Query via MCP:**
    *   **Tool:** `get_ga4_data`
    *   **dimensions:** `["your_custom_dimension_name"]` (Replace with a real custom dimension from your GA4 setup)
    *   **metrics:** `["sessions"]`
    *   **date_range_start:** `"28daysAgo"`
    *   **date_range_end:** `"yesterday"`
*   **Expected Result:** The query should succeed and return data broken down by your custom dimension. A failure here would indicate an issue with the dynamic schema loading.

---

### Test Case 3.2: Complex `AND`/`OR` Filter

*   **Goal:** Verify that a filter with multiple conditions is applied correctly on the server side.
*   **Query via MCP:**
    *   **Tool:** `get_ga4_data`
    *   **dimensions:** `["country", "deviceCategory"]`
    *   **metrics:** `["sessions"]`
    *   **date_range_start:** `"28daysAgo"`
    *   **date_range_end:** `"yesterday"`
    *   **dimension_filter:** A filter for sessions from either the US or Canada, but only on desktop.
      ```json
      {
        "andGroup": {
          "expressions": [
            {
              "filter": {
                "fieldName": "deviceCategory",
                "stringFilter": { "value": "desktop" }
              }
            },
            {
              "orGroup": {
                "expressions": [
                  {
                    "filter": {
                      "fieldName": "country",
                      "stringFilter": { "value": "United States" }
                    }
                  },
                  {
                    "filter": {
                      "fieldName": "country",
                      "stringFilter": { "value": "Canada" }
                    }
                  }
                ]
              }
            }
          ]
        }
      }
      ```
*   **Expected Result:** The data should only contain rows where `deviceCategory` is "desktop" and `country` is either "United States" or "Canada". This confirms the server is correctly translating the filter structure for the GA4 API.

---

## Category 4: Advanced Integrations & Event Model

**Objective:** To stress test the MCP against other common, but complex, GA4 data models like the event schema and advertising integrations.

---

### Test Case 4.1: Event-Centric Analysis

*   **Goal:** To analyze the parameters of a specific, important event, proving the tool can handle event-scoped dimensions and metrics.
*   **Query via MCP:**
    *   **Tool:** `get_ga4_data`
    *   **dimensions:** `["eventName", "country", "deviceCategory"]`
    *   **metrics:** `["eventCount", "totalUsers"]`
    *   **date_range_start:** `"28daysAgo"`
    *   **date_range_end:** `"yesterday"`
    *   **dimension_filter:** A filter for a key event on your site.
      ```json
      {
        "filter": {
          "fieldName": "eventName",
          "stringFilter": { "value": "your_key_event_name" }
        }
      }
      ```
      *(Note: Replace `your_key_event_name` with a real event, like `generate_lead`, `sign_up`, or `file_download`)*
*   **Expected Result:** The query should succeed and return data filtered to that specific event, showing where and on what devices it's being triggered.

---

### Test Case 4.2: Google Ads Performance Analysis

*   **Goal:** To verify that the tool can correctly pull data from a linked Google Ads account, a common scenario for many businesses.
*   **(Note:** This test is only applicable if you have a Google Ads account linked to your GA4 property.)*
*   **Query via MCP:**
    *   **Tool:** `get_ga4_data`
    *   **dimensions:** `["sessionGoogleAdsCampaignName", "sessionGoogleAdsAdGroupName"]`
    *   **metrics:** `["sessions", "engagementRate", "conversions"]`
    *   **date_range_start:** `"28daysAgo"`
    *   **date_range_end:** `"yesterday"`
    *   **dimension_filter:** A filter to isolate Google Ads traffic.
      ```json
      {
        "andGroup": {
          "expressions": [
            {
              "filter": {
                "fieldName": "sessionSource",
                "stringFilter": { "value": "google" }
              }
            },
            {
              "filter": {
                "fieldName": "sessionMedium",
                "stringFilter": { "value": "cpc" }
              }
            }
          ]
        }
      }
      ```
*   **Expected Result:** The query should succeed and return data showing the performance of your Google Ads campaigns and ad groups, validating that the advertising-related schema is handled correctly.
