<p align="center">
  <img src="logo.png" alt="Google Analytics MCP Logo" width="120" />


# Google Analytics MCP Server

mcp-name: io.github.surendranb/google-analytics-mcp

[![PyPI version](https://badge.fury.io/py/google-analytics-mcp.svg)](https://badge.fury.io/py/google-analytics-mcp)
[![PyPI Downloads](https://static.pepy.tech/badge/google-analytics-mcp)](https://pepy.tech/projects/google-analytics-mcp)
[![GitHub stars](https://img.shields.io/github/stars/surendranb/google-analytics-mcp?style=social)](https://github.com/surendranb/google-analytics-mcp/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/surendranb/google-analytics-mcp?style=social)](https://github.com/surendranb/google-analytics-mcp/network/members)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Made with Love](https://img.shields.io/badge/Made%20with-❤️-red.svg)](https://github.com/surendranb/google-analytics-mcp)

Connect Google Analytics 4 data to Claude, Cursor and other MCP clients. Query your website traffic, user behavior, and analytics data in natural language with access to 200+ GA4 dimensions and metrics.

**Compatible with:** Claude, Cursor and other MCP clients.

I also built a [Google Search Console MCP](https://github.com/surendranb/google-search-console-mcp) that enables you to mix & match the data from both the sources

</p>
---

## Prerequisites

**Check your Python setup:**

```bash
# Check Python version (need 3.10+)
python --version
python3 --version

# Check pip
pip --version
pip3 --version
```

**Required:**
- Python 3.10 or higher
- Google Analytics 4 property with data
- Service account with Analytics Reporting API access

---

## Step 1: Setup Google Analytics Credentials

### Create Service Account in Google Cloud Console

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. **Create or select a project**:
   - New project: Click "New Project" → Enter project name → Create
   - Existing project: Select from dropdown
3. **Enable the Analytics APIs**:
   - Go to "APIs & Services" → "Library"
   - Search for "Google Analytics Data API" → Click "Enable"
4. **Create Service Account**:
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "Service Account"
   - Enter name (e.g., "ga4-mcp-server")
   - Click "Create and Continue"
   - Skip role assignment → Click "Done"
5. **Download JSON Key**:
   - Click your service account
   - Go to "Keys" tab → "Add Key" → "Create New Key"
   - Select "JSON" → Click "Create"
   - Save the JSON file - you'll need its path

### Add Service Account to GA4

1. **Get service account email**:
   - Open the JSON file
   - Find the `client_email` field
   - Copy the email (format: `ga4-mcp-server@your-project.iam.gserviceaccount.com`)
2. **Add to GA4 property**:
   - Go to [Google Analytics](https://analytics.google.com/)
   - Select your GA4 property
   - Click "Admin" (gear icon at bottom left)
   - Under "Property" → Click "Property access management"
   - Click "+" → "Add users"
   - Paste the service account email
   - Select "Viewer" role
   - Uncheck "Notify new users by email"
   - Click "Add"

### Find Your GA4 Property ID

1. In [Google Analytics](https://analytics.google.com/), select your property
2. Click "Admin" (gear icon)
3. Under "Property" → Click "Property details"
4. Copy the **Property ID** (numeric, e.g., `123456789`)
   - **Note**: This is different from the "Measurement ID" (starts with G-)

### Test Your Setup (Optional)

Verify your credentials:

```bash
pip install google-analytics-data
```

Create a test script (`test_ga4.py`):

```python
import os
from google.analytics.data_v1beta import BetaAnalyticsDataClient

# Set credentials path
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/path/to/your/service-account-key.json"

# Test connection
client = BetaAnalyticsDataClient()
print("✅ GA4 credentials working!")
```

Run the test:

```bash
python test_ga4.py
```

If you see "✅ GA4 credentials working!" you're ready to proceed.

---

## Step 2: Install the MCP Server

Choose one method:

### Method A: pip install (Recommended)

```bash
pip install google-analytics-mcp
```

**MCP Configuration:**

First, check your Python command:

```bash
python3 --version
python --version
```

Then use the appropriate configuration:

If `python3 --version` worked:

```json
{
  "mcpServers": {
    "ga4-analytics": {
      "command": "python3",
      "args": ["-m", "ga4_mcp_server"],
      "env": {
        "GOOGLE_APPLICATION_CREDENTIALS": "/path/to/your/service-account-key.json",
        "GA4_PROPERTY_ID": "123456789"
      }
    }
  }
}
```

If `python --version` worked:

```json
{
  "mcpServers": {
    "ga4-analytics": {
      "command": "python",
      "args": ["-m", "ga4_mcp_server"],
      "env": {
        "GOOGLE_APPLICATION_CREDENTIALS": "/path/to/your/service-account-key.json",
        "GA4_PROPERTY_ID": "123456789"
      }
    }
  }
}
```

### Method B: GitHub download

```bash
git clone https://github.com/surendranb/google-analytics-mcp.git
cd google-analytics-mcp
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**MCP Configuration:**

```json
{
  "mcpServers": {
    "ga4-analytics": {
      "command": "/full/path/to/ga4-mcp-server/venv/bin/python",
      "args": ["/full/path/to/ga4-mcp-server/ga4_mcp_server.py"],
      "env": {
        "GOOGLE_APPLICATION_CREDENTIALS": "/path/to/your/service-account-key.json",
        "GA4_PROPERTY_ID": "123456789"
      }
    }
  }
}
```

---

## Step 3: Update Configuration

**Replace these placeholders in your MCP configuration:**
- `/path/to/your/service-account-key.json` with your JSON file path
- `123456789` with your GA4 Property ID
- `/full/path/to/ga4-mcp-server/` with your download path (Method B only)

---

## Usage

Once configured, ask your MCP client questions like:

### Discovery & Exploration
- What GA4 dimension categories are available?
- Show me all ecommerce metrics
- What dimensions can I use for geographic analysis?

### Traffic Analysis
- What's my website traffic for the past week?
- Show me user metrics by city for last month
- Compare bounce rates between different date ranges

### Multi-Dimensional Analysis
- Show me revenue by country and device category for last 30 days
- Analyze sessions and conversions by campaign and source/medium
- Compare user engagement across different page paths and traffic sources

### E-commerce Analysis
- What are my top-performing products by revenue?
- Show me conversion rates by traffic source and device type
- Analyze purchase behavior by user demographics

---

## Quick Start Examples

Try these example queries to see the MCP's analytical capabilities:

### 1. Geographic Distribution
```
Show me a map of visitors by city for the last 30 days, with a breakdown of new vs returning users
```
This demonstrates:
- Geographic analysis
- User segmentation
- Time-based filtering
- Data visualization

### 2. User Behavior Analysis
```
Compare average session duration and pages per session by device category and browser over the last 90 days
```
This demonstrates:
- Multi-dimensional analysis
- Time series comparison
- User engagement metrics
- Technology segmentation

### 3. Traffic Source Performance
```
Show me conversion rates and revenue by traffic source and campaign, comparing last 30 days vs previous 30 days
```
This demonstrates:
- Marketing performance analysis
- Period-over-period comparison
- Conversion tracking
- Revenue attribution

### 4. Content Performance
```
What are my top 10 pages by engagement rate, and how has their performance changed over the last 3 months?
```
This demonstrates:
- Content analysis
- Trend analysis
- Engagement metrics
- Ranking and sorting

---

## 🚀 Performance Optimizations

This MCP server includes **built-in optimizations** to prevent context window crashes and ensure smooth operation:

### Smart Data Volume Management
- **Automatic row estimation** - Checks data volume before fetching
- **Interactive warnings** - Alerts when queries would return >2,500 rows
- **Optimization suggestions** - Provides specific recommendations to reduce data volume

### Server-Side Processing
- **Intelligent aggregation** - Automatically aggregates data when beneficial (e.g., totals across time periods)
- **Smart sorting** - Returns most relevant data first (recent dates, highest values)
- **Efficient filtering** - Leverages GA4's server-side filtering capabilities

### User Control Parameters
- `limit` - Set maximum number of rows to return
- `proceed_with_large_dataset=True` - Override warnings for large datasets
- `enable_aggregation=False` - Disable automatic aggregation
- `estimate_only=True` - Get row count estimates without fetching data

### Example: Handling Large Datasets
```python
# This query would normally return 2,605 rows and crash context window
get_ga4_data(
    dimensions=["date", "pagePath", "country"],
    date_range_start="90daysAgo"
)
# Returns: {"warning": True, "estimated_rows": 2605, "suggestions": [...]}

# Use monthly aggregation instead
get_ga4_data(
    dimensions=["month", "pagePath", "country"], 
    date_range_start="90daysAgo"
)
# Returns: Clean monthly data with manageable row count
```

---

## Available Tools

The server provides 5 main tools with **built-in optimization** to prevent context window crashes:

1. **`get_ga4_data`** - Retrieve GA4 data with custom dimensions and metrics
   - **Smart data volume warnings** - Alerts when queries would return >2,500 rows
   - **Server-side aggregation** - Automatically aggregates data when beneficial
   - **Intelligent sorting** - Returns most relevant data first
   - **User control parameters** - `limit`, `proceed_with_large_dataset`, `enable_aggregation`
2. **`list_dimension_categories`** - Browse available dimension categories
3. **`list_metric_categories`** - Browse available metric categories
4. **`get_dimensions_by_category`** - Get dimensions for a specific category
5. **`get_metrics_by_category`** - Get metrics for a specific category

---

## Dimensions & Metrics

Access to **200+ GA4 dimensions and metrics** organized by category:

### Dimension Categories
- **Time**: date, hour, month, year, etc.
- **Geography**: country, city, region
- **Technology**: browser, device, operating system
- **Traffic Source**: campaign, source, medium, channel groups
- **Content**: page paths, titles, content groups
- **E-commerce**: item details, transaction info
- **User Demographics**: age, gender, language
- **Google Ads**: campaign, ad group, keyword data
- And 10+ more categories

### Metric Categories
- **User Metrics**: totalUsers, newUsers, activeUsers
- **Session Metrics**: sessions, bounceRate, engagementRate
- **E-commerce**: totalRevenue, transactions, conversions
- **Events**: eventCount, conversions, event values
- **Advertising**: adRevenue, returnOnAdSpend
- And more specialized metrics

---

## Troubleshooting

**If you get "No module named ga4_mcp_server" (Method A):**
```bash
pip3 install --user google-analytics-mcp
```

**If you get "executable file not found":**
- Try the other Python command (`python` vs `python3`)
- Use `pip3` instead of `pip` if needed

**Permission errors:**
```bash
# Try user install instead of system-wide
pip install --user google-analytics-mcp
```

**Credentials not working:**
1. **Verify the JSON file path** is correct and accessible
2. **Check service account permissions**:
   - Go to Google Cloud Console → IAM & Admin → IAM
   - Find your service account → Check permissions
3. **Verify GA4 access**:
   - GA4 → Admin → Property access management
   - Check for your service account email
4. **Verify ID type**:
   - Property ID: numeric (e.g., `123456789`) ✅
   - Measurement ID: starts with G- (e.g., `G-XXXXXXXXXX`) ❌

**API quota/rate limit errors:**
- GA4 has daily quotas and rate limits
- Try reducing the date range in your queries
- Wait a few minutes between large requests

---

## Project Structure

```
google-analytics-mcp/
├── ga4_mcp_server.py       # Main MCP server
├── ga4_dimensions.json     # All available GA4 dimensions
├── ga4_metrics.json        # All available GA4 metrics
├── requirements.txt        # Python dependencies
├── pyproject.toml          # Package configuration
├── README.md               # This file
└── claude-config-template.json  # MCP configuration template
```

---

## License

MIT License
