# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import sys
from .coordinator import mcp
from .tools import metadata, reporting

# --- Globals ---
# In-memory cache for the property's metadata (dimensions and metrics).
# This is populated once on server startup to avoid repeated API calls.
PROPERTY_SCHEMA = None

def main():
    """
    Main entry point for the MCP server.

    This function performs the following steps:
    1. Validates required environment variables.
    2. Fetches and caches the GA4 property schema (dimensions and metrics).
    3. Registers the tools with the MCP server.
    4. Starts the server and listens for requests.
    """
    print("Starting GA4 MCP server...", file=sys.stderr)

    # 1. Validate environment variables
    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    property_id = os.getenv("GA4_PROPERTY_ID")

    if not credentials_path:
        print("ERROR: GOOGLE_APPLICATION_CREDENTIALS environment variable not set.", file=sys.stderr)
        print("Please set it to the path of your service account JSON file.", file=sys.stderr)
        sys.exit(1)

    if not property_id:
        print("ERROR: GA4_PROPERTY_ID environment variable not set.", file=sys.stderr)
        print("Please set it to your GA4 property ID (e.g., '123456789').", file=sys.stderr)
        sys.exit(1)

    if not os.path.exists(credentials_path):
        print(f"ERROR: Credentials file not found at '{credentials_path}'.", file=sys.stderr)
        print("Please check the GOOGLE_APPLICATION_CREDENTIALS path.", file=sys.stderr)
        sys.exit(1)

    # 2. Fetch and cache the GA4 property schema
    print(f"Fetching schema for property '{property_id}'...", file=sys.stderr)
    global PROPERTY_SCHEMA
    try:
        PROPERTY_SCHEMA = metadata.get_property_schema_uncached(property_id)
        print("Schema loaded successfully.", file=sys.stderr)
    except Exception as e:
        print(f"FATAL: Could not fetch GA4 property schema: {e}", file=sys.stderr)
        print("Please ensure the service account has 'Viewer' permissions on the GA4 property and the Data API is enabled.", file=sys.stderr)
        sys.exit(1)

    # 3. Register tools
    # Tools are defined in other modules and decorated with @mcp.tool().
    # Importing them here makes them available to the server.
    # We pass the schema to the modules that need it.
    metadata.PROPERTY_SCHEMA = PROPERTY_SCHEMA
    reporting.PROPERTY_SCHEMA = PROPERTY_SCHEMA
    
    # 4. Run the server
    mcp.run(transport="stdio")

# Note: The actual tool definitions are in the .tools sub-package.
# The `if __name__ == "__main__"` block is not needed here, as the
# entry point is handled by `pyproject.toml` [project.scripts].
# For local development, you can run `python -m ga4_mcp.server`.
