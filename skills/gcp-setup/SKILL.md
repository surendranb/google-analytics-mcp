---
name: gcp-setup
description: "Step-by-step playbook to configure GA4 MCP using a Google Cloud Service Account (offline, CI/CD, enterprise) instead of 1-Click browser OAuth."
---
# GCP Service Account Setup for GA4 MCP

Step-by-step playbook to authenticate the GA4 MCP server using a Google Cloud Platform (GCP) Service Account.

This is the standard, enterprise-grade authentication method:
- **Offline & Headless**: Requires no interactive browser popups or OAuth consent screens.
- **Persistent**: Service account JSON keys never expire (unlike user OAuth tokens).
- **Least-Privilege**: Grants read-only Viewer access exclusively to the target GA4 property.

---

## 1. Quick Setup via `gcloud` CLI (Fastest — 60 Seconds)

If you have the `gcloud` CLI installed, run these 4 commands in your terminal:

```bash
# 1. Set your target GCP Project ID
export GCP_PROJECT_ID="$(gcloud config get-value project)"

# 2. Enable the Google Analytics Data API v1beta
gcloud services enable analyticsdata.googleapis.com --project="$GCP_PROJECT_ID"

# 3. Create a dedicated Service Account for the MCP server
gcloud iam service-accounts create ga4-mcp-reader \
  --display-name="GA4 MCP Reader" \
  --description="Read-only service account for GA4 Model Context Protocol" \
  --project="$GCP_PROJECT_ID"

# 4. Generate and download the JSON key file
mkdir -p ~/.config/ga4-mcp
gcloud iam service-accounts keys create ~/.config/ga4-mcp/service-account.json \
  --iam-account="ga4-mcp-reader@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \
  --project="$GCP_PROJECT_ID"
```

Your service account email will be:
`ga4-mcp-reader@<YOUR_PROJECT_ID>.iam.gserviceaccount.com`

---

## 2. Manual Setup via Google Cloud Console (GUI Path)

If you do not have `gcloud` CLI installed:

1. **Open Google Cloud Console**:
   Go to [console.cloud.google.com](https://console.cloud.google.com) and create or select a project.
2. **Enable the API**:
   Navigate to **APIs & Services** > **Library**, search for **Google Analytics Data API**, and click **Enable**.
3. **Create Service Account**:
   Navigate to **IAM & Admin** > **Service Accounts**, click **+ Create Service Account**.
   - Name: `ga4-mcp-reader`
   - Description: `Read-only GA4 MCP reader`
   - Role: Skip GCP role assignment (GA4 permissions are managed inside Google Analytics, not GCP). Click **Done**.
4. **Download JSON Key**:
   Click on the newly created service account > go to the **Keys** tab > click **Add Key** > **Create new key** > select **JSON** > click **Create**.
   Save the downloaded file to a permanent path, e.g.:
   `~/.config/ga4-mcp/service-account.json`

---

## 3. Grant Viewer Access in Google Analytics

> ⚠️ **CRITICAL STEP**: The service account cannot read your analytics until you explicitly add its email as a Viewer in Google Analytics.

1. Open [analytics.google.com](https://analytics.google.com).
2. Click the gear icon (**Admin**) in the bottom-left corner.
3. Under the **Property** column, click **Property access management**.
4. Click the blue **+** button in the top-right corner and select **Add users**.
5. Enter the service account email (e.g. `ga4-mcp-reader@your-project.iam.gserviceaccount.com` or the `client_email` value inside your JSON key).
6. Under Standard roles, select **Viewer** (read-only).
7. Uncheck "Notify SDK users by email" and click **Add**.

---

## 4. Find Your Numeric GA4 Property ID

GA4 requires the numeric **Property ID**, NOT the data stream Measurement ID:

- ❌ **Wrong**: `G-ABC123XYZ` (Measurement ID — for website tracking tags, rejected by API)
- ✔️ **Correct**: `123456789` (Numeric Property ID — for Data API queries)

**Where to find it**:
1. In Google Analytics, click **Admin** (gear icon).
2. Under Property, click **Property details**.
3. The numeric **Property ID** is displayed in the top right (e.g., `362847407`).

---

## 5. Configure Your MCP Client Harness

Update your client configuration file with the absolute path to your JSON key and your numeric Property ID.

### Claude Desktop
File: `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows)

```json
{
  "mcpServers": {
    "google-analytics": {
      "command": "uvx",
      "args": ["google-analytics-mcp"],
      "env": {
        "GOOGLE_APPLICATION_CREDENTIALS": "/Users/YOUR_USER/.config/ga4-mcp/service-account.json",
        "GA4_PROPERTY_ID": "123456789"
      }
    }
  }
}
```

### Cursor
File: `~/.cursor/mcp.json` or `.cursor/mcp.json` in your workspace:

```json
{
  "mcpServers": {
    "google-analytics": {
      "command": "uvx",
      "args": ["google-analytics-mcp"],
      "env": {
        "GOOGLE_APPLICATION_CREDENTIALS": "/Users/YOUR_USER/.config/ga4-mcp/service-account.json",
        "GA4_PROPERTY_ID": "123456789"
      }
    }
  }
}
```

### Claude Code CLI
Run directly:
```bash
claude mcp add google-analytics -- uvx google-analytics-mcp -e GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json -e GA4_PROPERTY_ID=123456789
```

---

## 6. How to Verify It Works

Run this one-liner in your terminal to verify end-to-end connectivity without restarting your IDE:

```bash
GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json" \
GA4_PROPERTY_ID="123456789" \
uvx google-analytics-mcp
```

**Expected output**:
```
Starting GA4 MCP server...
Fetching schema for property '123456789'...
Schema loaded successfully.
```

If you see `Schema loaded successfully`, your service account is 100% operational.
