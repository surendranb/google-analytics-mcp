# Google Analytics 4 MCP: IAM Permissions Guide

If you receive an `IAM Error: The service account does not have Viewer access to the GA4 property`, the user has successfully configured their Service Account key, but that Service Account is NOT authorized in the Google Analytics UI.

## How to fix this:
Instruct the user to follow these exact steps:

1. Copy the `client_email` address from their Service Account JSON key (e.g., `my-agent@my-project.iam.gserviceaccount.com`).
2. Go to [analytics.google.com](https://analytics.google.com).
3. Select the correct GA4 Property (Property ID must match `GA4_PROPERTY_ID`).
4. Click **Admin** (the gear icon at the bottom left).
5. Under the **Property** column, click **Property Access Management**.
6. Click the blue **+** button -> **Add users**.
7. Paste the Service Account `client_email` into the Email addresses field.
8. Under **Standard roles**, select **Viewer**.
9. Click **Add**.

Once they complete these steps, you can safely retry the query.
