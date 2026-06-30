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
from . import resources

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
    import ga4_mcp.coordinator as coordinator
    config_status = "valid"

    # 1. Validate environment variables
    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    property_id = os.getenv("GA4_PROPERTY_ID")

    if not credentials_path:
        print("ERROR: GOOGLE_APPLICATION_CREDENTIALS environment variable not set.", file=sys.stderr)
        coordinator.SERVER_INIT_ERROR = "GOOGLE_APPLICATION_CREDENTIALS environment variable not set. Please set it to the path of your service account JSON file."
        config_status = "error"
    elif not property_id:
        print("ERROR: GA4_PROPERTY_ID environment variable not set.", file=sys.stderr)
        coordinator.SERVER_INIT_ERROR = "GA4_PROPERTY_ID environment variable not set. Please set it to your GA4 property ID (e.g., '123456789')."
        config_status = "error"
    elif "ABSOLUTE/PATH/TO" in credentials_path:
        print(f"ERROR: Dummy credentials path detected: '{credentials_path}'.", file=sys.stderr)
        coordinator.SERVER_INIT_ERROR = "Setup failed because the dummy path is still in the config. Please read the `docs://setup_guide` resource using your read_resource tool to help the user fix this."
        config_status = "error"
    elif not os.path.exists(credentials_path):
        print(f"ERROR: Credentials file not found at '{credentials_path}'.", file=sys.stderr)
        coordinator.SERVER_INIT_ERROR = f"Credentials file not found at '{credentials_path}'. Please check the GOOGLE_APPLICATION_CREDENTIALS path."
        config_status = "error"
    else:
        # 2. Fetch and cache the GA4 property schema
        print(f"Fetching schema for property '{property_id}'...", file=sys.stderr)
        global PROPERTY_SCHEMA
        try:
            PROPERTY_SCHEMA = metadata.get_property_schema_uncached(property_id)
            print("Schema loaded successfully.", file=sys.stderr)
        except Exception as e:
            print(f"FATAL: Could not fetch GA4 property schema: {e}", file=sys.stderr)
            err_str = str(e)
            if "403" in err_str or "PermissionDenied" in err_str or "permission" in err_str.lower():
                coordinator.SERVER_INIT_ERROR = "IAM Error: The service account does not have Viewer access to the GA4 property. Please read `docs://setup_guide` using your read_resource tool to help the user fix this."
            else:
                coordinator.SERVER_INIT_ERROR = f"Could not fetch GA4 property schema: {err_str}"
            config_status = "error"

    # 3. Register tools
    # Tools are defined in other modules and decorated with @mcp.tool().
    # Importing them here makes them available to the server.
    # We pass the schema to the modules that need it.
    metadata.PROPERTY_SCHEMA = PROPERTY_SCHEMA
    reporting.PROPERTY_SCHEMA = PROPERTY_SCHEMA
    
    # 4. Run the server
    from .coordinator import send_telemetry
    send_telemetry("mcp_started", {"config_status": config_status})
    mcp.run(transport="stdio")

# Note: The actual tool definitions are in the .tools sub-package.
# The `if __name__ == "__main__"` block is not needed here, as the
# entry point is handled by `pyproject.toml` [project.scripts].
# For local development, you can run `python -m ga4_mcp.server`.
if __name__ == "__main__":
    main()
