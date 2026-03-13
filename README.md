[![MseeP.ai Security Assessment Badge](https://mseep.net/pr/surendranb-google-analytics-mcp-badge.png)](https://mseep.ai/app/surendranb-google-analytics-mcp)

<p align="center">
  <img src="logo.png" alt="Google Analytics MCP Logo" width="120" />


# Google Analytics MCP Server

mcp-name: io.github.surendranb/google-analytics-mcp

[![PyPI version](https://badge.fury.io/py/google-analytics-mcp.svg)](https://badge.fury.io/py/google-analytics-mcp)
[![PyPI Downloads](https://static.pepy.tech/badge/google-analytics-mcp)](https://pepy.tech/projects/google-analytics-mcp)
[![GitHub stars](https://img.shields.io/github/stars/surendranb/google-analytics-mcp?style=social)](https://github.com/surendranb/google-analytics-mcp/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/surendranb/google-analytics-mcp?style=social)](https://github.com/surendranb/google-analytics-mcp/network/members)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Made with Love](https://img.shields.io/badge/Made%20with-❤️-red.svg)](https://github.com/surendranb/google-analytics-mcp)

Connect Google Analytics 4 data to AI agents, agentic workflows, and MCP clients. Give agents analysis-ready access to website traffic, user behavior, and performance data with schema discovery, server-side aggregation, and safe defaults that reduce data wrangling.

**Built for:** AI agents, analyst copilots, and MCP runtimes across Claude, ChatGPT, Cursor, Windsurf, and custom hosts.

I also built a [Google Search Console MCP](https://github.com/surendranb/google-search-console-mcp) that enables you to mix & match the data from both the sources

</p>
---

## Why Agents Use This Server

- **Analysis-ready outputs** with server-side aggregation, so agents spend more time answering questions and less time wrangling rows
- **Live schema discovery** for each GA4 property, including category-based exploration for dimensions and metrics
- **Context-safe defaults** that estimate large datasets before they blow up a conversation or workflow
- **Portable MCP surface** that works across agent runtimes, IDE copilots, and custom automation

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
- Service account with Google Analytics Data API access and GA4 property access

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

There are two supported ways to launch the server:

- `ga4-mcp-server` when the installed console script is available on your `PATH`
- `python -m ga4_mcp` when you want to use a specific interpreter or virtual environment

### Method A: Install from PyPI (Recommended)

```bash
python3 -m pip install google-analytics-mcp
```

If your machine uses `python` instead of `python3`, run:

```bash
python -m pip install google-analytics-mcp
```

#### Option 1: Use the console script

Use this when `ga4-mcp-server` is available on your `PATH`:

```json
{
  "mcpServers": {
    "ga4-analytics": {
      "command": "ga4-mcp-server",
      "env": {
        "GOOGLE_APPLICATION_CREDENTIALS": "/path/to/your/service-account-key.json",
        "GA4_PROPERTY_ID": "123456789"
      }
    }
  }
}
```

#### Option 2: Use an explicit Python interpreter

Use this when you want to pin the exact Python runtime or when the console script is not on your `PATH`.

If `python3 --version` worked:

```json
{
  "mcpServers": {
    "ga4-analytics": {
      "command": "python3",
      "args": ["-m", "ga4_mcp"],
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
      "args": ["-m", "ga4_mcp"],
      "env": {
        "GOOGLE_APPLICATION_CREDENTIALS": "/path/to/your/service-account-key.json",
        "GA4_PROPERTY_ID": "123456789"
      }
    }
  }
}
```

### Method B: Install from a local clone

```bash
git clone https://github.com/surendranb/google-analytics-mcp.git
cd google-analytics-mcp
python3 -m venv .venv
source .venv/bin/activate
python -m pip install .
```

If you plan to modify the package locally, use `python -m pip install -e .` instead.

**MCP Configuration:**

```json
{
  "mcpServers": {
    "ga4-analytics": {
      "command": "/full/path/to/google-analytics-mcp/.venv/bin/python",
      "args": ["-m", "ga4_mcp"],
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
- `/path/to/your/service-account-key.json` with the absolute path to your JSON key
- `123456789` with your numeric GA4 Property ID
- `/full/path/to/google-analytics-mcp/.venv/bin/python` with your virtual environment's Python path (Method B only)

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

The server provides a suite of tools for data reporting and schema discovery.

1.  **`search_schema`** - Searches for a keyword across all available dimensions and metrics. This is the most efficient way to discover fields for a query.
2.  **`get_ga4_data`** - Retrieve GA4 data with built-in intelligence for better and safer results (includes data volume protection, smart aggregation, and intelligent sorting).
3.  **`list_dimension_categories`** - Lists all available dimension categories.
4.  **`list_metric_categories`** - Lists all available metric categories.
5.  **`get_dimensions_by_category`** - Gets all dimensions for a specific category.
6.  **`get_metrics_by_category`** - Gets all metrics for a specific category.
7.  **`get_property_schema`** - Returns the complete schema for the property (Warning: this can be a very large object).

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

**If `ga4-mcp-server` is not found:**
- Use the explicit interpreter launch style instead: `python -m ga4_mcp`
- Reinstall with the same Python interpreter your MCP client will use

**If you get `No module named ga4_mcp`:**
```bash
/full/path/to/python -m pip install google-analytics-mcp
```
Install the package with the exact interpreter you reference in your MCP configuration.

**Permission errors:**
```bash
# Try user install instead of system-wide
python -m pip install --user google-analytics-mcp
```

**If the server says the credentials file is missing:**
1. **Verify the JSON file path** is absolute, correct, and accessible
2. **Check service account permissions**:
   - Go to Google Cloud Console → IAM & Admin → IAM
   - Find your service account → Check permissions
3. **Verify GA4 access**:
   - GA4 → Admin → Property access management
   - Check for your service account email

**If the server says `GA4_PROPERTY_ID` is invalid or queries return no data:**
- Use the numeric **Property ID** (for example `123456789`)
- Do **not** use the **Measurement ID** (for example `G-XXXXXXXXXX`)
- Confirm the service account has at least Viewer access on that property

**API quota/rate limit errors:**
- GA4 has daily quotas and rate limits
- Try reducing the date range in your queries
- Wait a few minutes between large requests

---

## Project Structure

```
google-analytics-mcp/
├── ga4_mcp/                # Main package directory
│   ├── server.py           # Core server logic
│   ├── coordinator.py      # MCP instance
│   └── tools/              # Tool definitions (reporting, metadata)
├── pyproject.toml          # Package configuration for PyPI
├── requirements.txt        # Dependencies for local dev
├── README.md               # This file
└── ...
```

---

## License

Apache License 2.0
