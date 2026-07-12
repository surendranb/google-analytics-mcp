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
    from ga4_mcp import telemetry
    import ga4_mcp.tools.troubleshooting  # Register the troubleshooting tool
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

    def _guided(what, steps, anchor, topic="setup", why=None, who=None, handoff=None):
        """Self-contained decision brief written FOR THE MODEL: what broke, why it
        blocks everything, that retrying is futile, exactly what the user must do
        (with their values), and who can do it. setup_ga4_access and docs are
        OPTIONAL depth, not the path to understanding — reduce hops."""
        step_text = " ".join(f"({i}) {s}" for i, s in enumerate(steps, 1))
        why = why or "No GA4 data can be returned until this is resolved."
        who = who or "the user (whoever set up this server's Google access)"
        parts = [
            f"[SETUP BLOCKED] {what}",
            f"WHY: {why}",
            "RETRYING WON'T HELP — every call fails identically until the user changes setup outside this tool; do not re-call data tools.",
            f"WHAT MUST HAPPEN (only the user can do this): {step_text}",
            f"WHO CAN DO IT: {who}.",
        ]
        if handoff:
            parts.append(f'FORWARDABLE — the user can send this verbatim to whoever admins their GA4/Google Cloud: "{handoff}"')
        parts.append(
            f"OPTIONAL (not needed to understand or relay this): call setup_ga4_access to collect a missing value "
            f"in-session; get_troubleshooting_guide(topic='{topic}') or resource docs://fix/{topic} for detail; "
            f"full guide {setup_url}#{anchor}.")
        return "  ".join(parts)

    if not credentials_path:
        print("ERROR: GOOGLE_APPLICATION_CREDENTIALS environment variable not set.", file=sys.stderr)
        coordinator.SERVER_INIT_ERROR = _guided(
            "No Google credentials are configured — GOOGLE_APPLICATION_CREDENTIALS is unset.",
            ["Point GOOGLE_APPLICATION_CREDENTIALS at a Google service-account JSON key "
             "(Cloud Console > IAM > Service Accounts > Keys) — best for a persistent/shared setup; "
             "OR if you have the gcloud CLI, run 'gcloud auth application-default login' and use that credentials file.",
             _config_hint()],
            "credentials",
            why="The server cannot authenticate to the GA4 API, so no query can run.")
        config_status = "error"
    elif not property_id:
        print("ERROR: GA4_PROPERTY_ID environment variable not set.", file=sys.stderr)
        coordinator.SERVER_INIT_ERROR = _guided(
            "No GA4 Property ID is set — GA4_PROPERTY_ID is unset.",
            ["Set GA4_PROPERTY_ID to the numeric Property ID (NOT the 'G-' Measurement ID) — "
             "find it at analytics.google.com > Admin > Property details (e.g. 123456789).",
             _config_hint()],
            "property-id",
            why="Every query must target a specific property; without the ID nothing can be read.")
        config_status = "error"
    elif "ABSOLUTE/PATH/TO" in credentials_path:
        print(f"ERROR: Dummy credentials path detected: '{credentials_path}'.", file=sys.stderr)
        coordinator.SERVER_INIT_ERROR = _guided(
            "The credentials path is still the copy-paste placeholder ('/ABSOLUTE/PATH/TO...'), not a real path.",
            ["Replace the /ABSOLUTE/PATH/TO placeholder in the config with the real absolute path of the "
             "downloaded service-account JSON key.",
             _config_hint()],
            "credentials",
            why="The server has no real credentials file to authenticate with, so no query can run.")
        config_status = "error"
    elif not os.path.exists(credentials_path):
        print(f"ERROR: Credentials file not found at '{credentials_path}'.", file=sys.stderr)
        coordinator.SERVER_INIT_ERROR = _guided(
            f"The credentials file does not exist at the configured path '{credentials_path}'.",
            ["Verify the file exists at that exact absolute path (check the filename, folder, and any typo).",
             "If it was moved or never downloaded, re-download the service-account JSON key from "
             "Google Cloud Console > IAM > Service Accounts > Keys and point the config at it.",
             _config_hint()],
            "credentials",
            why="The server cannot read credentials, so it cannot authenticate to GA4.")
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
            err_str = str(e)
            if "403" in err_str or "PermissionDenied" in err_str or "permission" in err_str.lower():
                model, email, _ = coordinator.inspect_credentials(credentials_path)
                if model == "service_account" and email:
                    grantee = f"the service account {email}"
                    handoff = (f"Please add {email} as a Viewer on GA4 property {property_id} "
                               f"(analytics.google.com > Admin > Property Access Management).")
                elif model == "adc":
                    grantee = "the Google account you authenticated with via gcloud"
                    handoff = (f"Please grant my Google account Viewer access on GA4 property {property_id} "
                               f"(Admin > Property Access Management).")
                else:
                    grantee = "the service account (the client_email inside the JSON key)"
                    handoff = f"Please add my service account as a Viewer on GA4 property {property_id}."
                coordinator.SERVER_INIT_ERROR = _guided(
                    f"Credentials are valid, but {grantee} has no access to GA4 property {property_id}.",
                    [f"At analytics.google.com > Admin > Property Access Management, add {grantee} with the Viewer role.",
                     "Wait ~1 minute for the grant to propagate, then ask me to retry (no restart needed)."],
                    "iam", topic="iam",
                    why="Authentication succeeded but this account is not authorized to read this property (Google returns 403).",
                    who="the user, or whoever administers this GA4 property if that is someone else",
                    handoff=handoff)
                coordinator.SERVER_INIT_ERROR_CATEGORY = "IAMError"
            elif ("Reauthentication is needed" in err_str or "invalid_grant" in err_str
                    or "expired or revoked" in err_str):
                worked_before = telemetry.HAS_EVER_WORKED
                lead = ("This server was working before — the Google credentials have now expired."
                        if worked_before else "The Google credentials are expired or revoked.")
                coordinator.SERVER_INIT_ERROR = _guided(
                    lead,
                    ["Re-authenticate: run 'gcloud auth application-default login' in a terminal (for ADC), "
                     "or replace the service-account key file if that is what this server uses.",
                     "Then ask me to retry — no config changes needed.",
                     "Tip: service-account keys do not expire; prefer one if this recurs."],
                    "adc",
                    why="The stored credentials are no longer valid, so authentication to GA4 fails.",
                    who="the user (re-auth is a local action only they can take)")
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
