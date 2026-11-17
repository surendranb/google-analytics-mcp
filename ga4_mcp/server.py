# SPDX-License-Identifier: Apache-2.0

import os
import sys
from .coordinator import mcp
from .tools import metadata, reporting
from . import resources
from . import prompts  # noqa: F401  registers the workflow prompts (S6)

# Property schema, cached at startup.
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
    from ga4_mcp import telemetry
    import ga4_mcp.tools.troubleshooting  # Register the troubleshooting tool
    import ga4_mcp.tools.skills          # Register the skills search tool
    import ga4_mcp.setup_flow  # Register the interactive setup-recovery tool
    config_status = "valid"

    # 1. Validate environment variables or active 1-Click session
    session_creds, session_prop = coordinator.get_session_credentials()
    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    property_id = os.getenv("GA4_PROPERTY_ID") or session_prop
    if session_prop and not os.getenv("GA4_PROPERTY_ID"):
        os.environ["GA4_PROPERTY_ID"] = session_prop

    if not credentials_path and not session_creds:
        print("ERROR: Neither GOOGLE_APPLICATION_CREDENTIALS nor active session.json found.", file=sys.stderr)
        coordinator.SERVER_INIT_ERROR = coordinator.build_guided_init_error(
            "No Google credentials are configured — GOOGLE_APPLICATION_CREDENTIALS is unset and no session.json found.",
            ["Connect in 10s via 1-Click Browser Sign-In: run 'curl -fsSL https://ga4.builditwithai.xyz/install | bash'",
             "OR point GOOGLE_APPLICATION_CREDENTIALS at a Google service-account JSON key (call search_skills('gcp-setup') for step-by-step)",
             coordinator.config_hint()],
            "credentials",
            why="The server cannot authenticate to the GA4 API, so no query can run.")
        coordinator.SERVER_INIT_BRIEF_VERSION = "ga4-creds-unset-v1"
        config_status = "error"
    elif not property_id:
        print("ERROR: GA4_PROPERTY_ID environment variable not set.", file=sys.stderr)
        coordinator.SERVER_INIT_ERROR = coordinator.property_id_brief()
        coordinator.SERVER_INIT_BRIEF_VERSION = "ga4-property-id-v1"
        config_status = "error"
    elif credentials_path and "ABSOLUTE/PATH/TO" in credentials_path:
        print(f"ERROR: Dummy credentials path detected: '{credentials_path}'.", file=sys.stderr)
        coordinator.SERVER_INIT_ERROR = coordinator.build_guided_init_error(
            "The credentials path is still the copy-paste placeholder ('/ABSOLUTE/PATH/TO...'), not a real path.",
            ["Replace the /ABSOLUTE/PATH/TO placeholder in the config with the real absolute path of the "
             "downloaded service-account JSON key.",
             coordinator.config_hint()],
            "credentials",
            why="The server has no real credentials file to authenticate with, so no query can run.")
        coordinator.SERVER_INIT_BRIEF_VERSION = "ga4-creds-placeholder-v1"
        config_status = "error"
    elif credentials_path and not os.path.exists(credentials_path):
        print(f"ERROR: Credentials file not found at '{credentials_path}'.", file=sys.stderr)
        coordinator.SERVER_INIT_ERROR = coordinator.build_guided_init_error(
            f"The credentials file does not exist at the configured path '{os.path.basename(credentials_path)}'.",
            ["Verify the file exists at that exact absolute path (check the filename, folder, and any typo).",
             "If it was moved or never downloaded, re-download the service-account JSON key from "
             "Google Cloud Console > IAM > Service Accounts > Keys and point the config at it.",
             coordinator.config_hint()],
            "credentials",
            why="The server cannot read credentials, so it cannot authenticate to GA4.")
        coordinator.SERVER_INIT_BRIEF_VERSION = "ga4-creds-notfound-v1"
        config_status = "error"
    else:
        # 2. Fetch and cache the GA4 property schema
        print(f"Fetching schema for property '{property_id}'...", file=sys.stderr)
        global PROPERTY_SCHEMA
        try:
            PROPERTY_SCHEMA = metadata.get_property_schema_uncached(property_id)
            print("Schema loaded successfully.", file=sys.stderr)
            telemetry.mark_ever_worked()
        except Exception as e:
            print(f"FATAL: Could not fetch GA4 property schema: {e}", file=sys.stderr)
            (coordinator.SERVER_INIT_ERROR_CATEGORY, coordinator.SERVER_INIT_BRIEF_VERSION,
             coordinator.SERVER_INIT_ERROR) = coordinator.classify_setup_failure(
                e, property_id, credentials_path)
            config_status = "error"

    # 3. Register tools (importing the modules registers their @mcp.tool functions)
    metadata.PROPERTY_SCHEMA = PROPERTY_SCHEMA
    reporting.PROPERTY_SCHEMA = PROPERTY_SCHEMA
    
    # 4. Run the server
    from .coordinator import send_telemetry
    import time as _time
    start_payload = {
        "config_status": config_status,
        "shell": os.path.basename(os.getenv("SHELL", "") or "unknown"),
        "term_program": os.getenv("TERM_PROGRAM", "unknown"),
        "system_lang": os.getenv("LANG", "unknown"),
        "is_ci": os.getenv("CI", "false").lower() == "true" or os.getenv("GITHUB_ACTIONS", "false").lower() == "true",
        # Env var NAMES only, never values — makes harnesses we didn't
        # anticipate visible instead of falling to generic_agent.
        "env_var_names": sorted(os.environ.keys()),
    }
    if coordinator.SERVER_INIT_ERROR:
        start_payload["error_message"] = telemetry._scrub_error_message(coordinator.SERVER_INIT_ERROR)
        start_payload["error_category"] = coordinator.SERVER_INIT_ERROR_CATEGORY
    send_telemetry("mcp_started", start_payload)
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
