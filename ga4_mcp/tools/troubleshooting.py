# SPDX-License-Identifier: Apache-2.0

"""In-server troubleshooting guides. Content lives with the code (bundled at
release), NOT fetched from the web — instant, offline-safe, and versioned with
the package. Written for the AI agent to act on and relay to the user."""

from ga4_mcp.coordinator import mcp

_SETUP_GUIDE = """--- SETUP GUIDE ---

The GA4 MCP server needs two things to work: a Property ID and Google credentials.

1. GA4_PROPERTY_ID — the numeric Property ID (e.g. 123456789), NOT the
   Measurement ID that starts with 'G-'. Find it at analytics.google.com >
   Admin > Property details.
2. GOOGLE_APPLICATION_CREDENTIALS — the absolute path to a Google Cloud
   service-account JSON key, OR run 'gcloud auth application-default login'
   and use that credentials file.

Set both in the env block of this server in the MCP client config, e.g.:
   "env": {
     "GOOGLE_APPLICATION_CREDENTIALS": "/absolute/path/to/key.json",
     "GA4_PROPERTY_ID": "123456789"
   }

FASTEST PATH: call setup_ga4_access — it collects the missing value
interactively and reconnects without a restart."""

_IAM_GUIDE = """--- IAM / 403 PERMISSION GUIDE ---

A 403 / PermissionDenied means the credentials are valid but the service
account has no access to the GA4 property. Grant it:

1. Open analytics.google.com > Admin > Property Access Management.
2. Click '+' > Add users.
3. Enter the service account email — it is the 'client_email' field inside
   the JSON key file.
4. Assign the 'Viewer' role and save.
5. Wait a minute for permissions to propagate, then retry.

If credentials instead need re-authentication (a 'Reauthentication is needed'
or invalid_grant / expired error), the user's Application Default Credentials
have expired — have them run: gcloud auth application-default login"""

_SCHEMA_GUIDE = """--- SCHEMA GUIDE ---

Do not guess dimension/metric names — use search_schema first. Common fixes
(verified against real usage):
- Metric is 'keyEvents', not 'conversions'. 'totalUsers', not 'users'.
  'itemsViewed', not 'itemViews'. 'ecommercePurchases', not 'purchases'.
- Dimension is 'sessionDefaultChannelGroup', not 'sessionDefaultChannelGrouping'.
- A simple dimension_filter MUST nest inside a "filter" key:
  {"filter": {"fieldName": ..., "stringFilter": {...}}} — not fieldName at top level.
- Logical groups are "andGroup"/"orGroup"/"notExpression" — not and_filter/or_filter."""

_GUIDES = {"setup": _SETUP_GUIDE, "iam": _IAM_GUIDE, "schema": _SCHEMA_GUIDE}


@mcp.tool()
def get_troubleshooting_guide(topic: str) -> str:
    """
    Returns the troubleshooting/setup guide for a topic, served from inside the
    server (no network needed). Use whenever you hit a schema error,
    dimension_filter parse error, IAM / 403 authorization error, or a
    boot-time setup error.

    Args:
        topic: One of "setup", "iam", or "schema".
    """
    guide = _GUIDES.get((topic or "").strip().lower())
    if guide is None:
        return "Invalid topic. Choose 'setup', 'iam', or 'schema'."
    return guide
