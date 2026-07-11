# SPDX-License-Identifier: Apache-2.0

import os
import sys
from .coordinator import mcp
from .tools import metadata, reporting
from . import resources

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
    import ga4_mcp.tools.troubleshooting  # Register the OTA tool
    import ga4_mcp.setup_flow  # Register the interactive setup-recovery tool
    config_status = "valid"

    # 1. Validate environment variables
    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    property_id = os.getenv("GA4_PROPERTY_ID")

    setup_url = "https://ga4.builditwithai.xyz/setup"

    def _config_hint():
        # Name the config surface for the detected client.
        agent = getattr(coordinator, "AGENT_NAME", "")
        if agent == "claude_code":
            return ("In Claude Code run: claude mcp add ga4-analytics -e GA4_PROPERTY_ID=<id> "
                    "-e GOOGLE_APPLICATION_CREDENTIALS=<key-path> -- uvx --from google-analytics-mcp ga4-mcp-server")
        if agent == "claude_desktop":
            return ("In Claude Desktop: Settings > Developer > Edit Config, set these env values under "
                    "mcpServers > ga4-analytics in claude_desktop_config.json")
        if agent == "cursor":
            return "In Cursor: Settings > MCP (edit .cursor/mcp.json), set these env values for ga4-analytics"
        if agent in ("vscode", "windsurf"):
            return "Edit this editor's MCP settings JSON and set these env values for ga4-analytics"
        return "Set these env values in your MCP client's server config for ga4-analytics"

    def _guided(message, steps, anchor, topic="setup"):
        step_text = " ".join(f"({i}) {s}" for i, s in enumerate(steps, 1))
        return (f"{message} FASTEST FIX — call the setup_ga4_access tool now: it walks the user through "
                f"fixing this interactively and reconnects without a restart. "
                f"Or relay these steps manually: {step_text} "
                f"Full guide: {setup_url}#{anchor}. "
                f"For deeper reference call get_troubleshooting_guide(topic='{topic}').")

    if not credentials_path:
        print("ERROR: GOOGLE_APPLICATION_CREDENTIALS environment variable not set.", file=sys.stderr)
        coordinator.SERVER_INIT_ERROR = _guided(
            "GOOGLE_APPLICATION_CREDENTIALS environment variable not set.",
            ["Create a Google Cloud service account JSON key (Cloud Console > IAM > Service Accounts > Keys), "
             "or run 'gcloud auth application-default login' and use that credentials file.",
             _config_hint()],
            "credentials")
        config_status = "error"
    elif not property_id:
        print("ERROR: GA4_PROPERTY_ID environment variable not set.", file=sys.stderr)
        coordinator.SERVER_INIT_ERROR = _guided(
            "GA4_PROPERTY_ID environment variable not set.",
            ["Open analytics.google.com > Admin > Property details and copy the numeric Property ID (e.g. 123456789).",
             _config_hint()],
            "property-id")
        config_status = "error"
    elif "ABSOLUTE/PATH/TO" in credentials_path:
        print(f"ERROR: Dummy credentials path detected: '{credentials_path}'.", file=sys.stderr)
        coordinator.SERVER_INIT_ERROR = _guided(
            "Setup failed because the dummy path is still in the config.",
            ["Replace the /ABSOLUTE/PATH/TO placeholder with the real absolute path of the downloaded "
             "service-account JSON key.",
             _config_hint()],
            "credentials")
        config_status = "error"
    elif not os.path.exists(credentials_path):
        print(f"ERROR: Credentials file not found at '{credentials_path}'.", file=sys.stderr)
        coordinator.SERVER_INIT_ERROR = _guided(
            f"Credentials file not found at '{credentials_path}'.",
            ["Verify the file exists at that exact absolute path (check the filename and folder).",
             "If it is missing, re-download the service account JSON key from Google Cloud Console > IAM > "
             "Service Accounts > Keys.",
             _config_hint()],
            "credentials")
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
                coordinator.SERVER_INIT_ERROR = _guided(
                    "IAM Error: The service account does not have Viewer access to the GA4 property.",
                    ["Open analytics.google.com > Admin > Property Access Management.",
                     "Add the service account email (the client_email field inside the JSON key) with the "
                     "Viewer role.",
                     "Wait a minute for permissions to propagate, then restart the MCP client."],
                    "iam", topic="iam")
                coordinator.SERVER_INIT_ERROR_CATEGORY = "IAMError"
            elif ("Reauthentication is needed" in err_str or "invalid_grant" in err_str
                    or "expired or revoked" in err_str):
                coordinator.SERVER_INIT_ERROR = _guided(
                    f"Google credentials have expired: {err_str}.",
                    ["Ask the user to run in a terminal: gcloud auth application-default login",
                     "Then restart the MCP client — no config changes needed."],
                    "adc")
                coordinator.SERVER_INIT_ERROR_CATEGORY = "ADCExpired"
            else:
                coordinator.SERVER_INIT_ERROR = _guided(
                    f"Could not fetch GA4 property schema: {err_str}.",
                    ["Check that GA4_PROPERTY_ID is the numeric ID of a property this service account can access.",
                     "Check the credentials file is a valid service-account JSON key.",
                     _config_hint()],
                    "setup")
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
        start_payload["error_message"] = str(coordinator.SERVER_INIT_ERROR)
        start_payload["error_category"] = coordinator.SERVER_INIT_ERROR_CATEGORY
    send_telemetry("mcp_started", start_payload)
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
