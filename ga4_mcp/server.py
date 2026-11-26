# SPDX-License-Identifier: Apache-2.0

import os
import sys
from .coordinator import mcp
from .tools import metadata, reporting, gsc, youtube, ads, troubleshooting, skills
from . import resources
from . import prompts  # noqa: F401  registers the workflow prompts (S6)
from . import setup_flow  # noqa: F401
from . import auth_handshake  # noqa: F401
from .sites import registry
from .schema_cache import schema_cache


# Property schema, cached at startup for backward compatibility.
PROPERTY_SCHEMA = None

def main():
    """
    Main entry point for the MCP server.

    This function performs the following steps:
    1. Initializes site registry and discovers accessible properties.
    2. Prefetches schema for active property if available.
    3. Registers tools with the MCP server.
    4. Starts the server and listens for requests.
    """
    print("Starting GA4 MCP server...", file=sys.stderr)
    import ga4_mcp.coordinator as coordinator
    from ga4_mcp import telemetry
    import ga4_mcp.tools.troubleshooting  # Register the troubleshooting tool
    import ga4_mcp.tools.skills          # Register the skills search tool
    import ga4_mcp.tools.gsc             # Register Google Search Console tools
    import ga4_mcp.tools.youtube         # Register YouTube Analytics & Data tools
    import ga4_mcp.tools.ads             # Register Google Ads tools
    import ga4_mcp.setup_flow  # Register the interactive setup-recovery tool
    import ga4_mcp.auth_handshake  # Register browser OAuth connect tool

    config_status = "valid"

    # 1. Initialize Site Registry (config + env + Admin API discovery)
    registry.initialize()

    setup_url = "https://ga4.builditwithai.xyz/setup"

    def _config_hint():
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

    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    property_id = os.getenv("GA4_PROPERTY_ID")
    if os.getenv("GA4_FORCE_OAUTH", "").lower() in ("1", "true", "yes"):
        credentials_path = None
        property_id = None

    if credentials_path and "ABSOLUTE/PATH/TO" in credentials_path:
        print(f"ERROR: Dummy credentials path detected: '{credentials_path}'.", file=sys.stderr)
        coordinator.SERVER_INIT_ERROR = _guided(
            "The credentials path is still the copy-paste placeholder ('/ABSOLUTE/PATH/TO...'), not a real path.",
            ["Replace the /ABSOLUTE/PATH/TO placeholder in the config with the real absolute path of the "
             "downloaded service-account JSON key.",
             _config_hint()],
            "credentials",
            why="The server has no real credentials file to authenticate with, so no query can run.")
        coordinator.SERVER_INIT_BRIEF_VERSION = "ga4-creds-placeholder-v1"
        config_status = "error"
    elif credentials_path and not os.path.exists(credentials_path):
        print(f"ERROR: Credentials file not found at '{credentials_path}'.", file=sys.stderr)
        coordinator.SERVER_INIT_ERROR = _guided(
            f"The credentials file does not exist at the configured path '{credentials_path}'.",
            ["Verify the file exists at that exact absolute path (check the filename, folder, and any typo).",
             "If it was moved or never downloaded, re-download the service-account JSON key from "
             "Google Cloud Console > IAM > Service Accounts > Keys and point the config at it.",
             _config_hint()],
            "credentials",
            why="The server cannot read credentials, so it cannot authenticate to GA4.")
        coordinator.SERVER_INIT_BRIEF_VERSION = "ga4-creds-notfound-v1"
        config_status = "error"
    elif not registry.has_any():
        print("WARNING: No properties discovered or configured at startup.", file=sys.stderr)
        coordinator.SERVER_INIT_ERROR = (
            "Not connected to Google Analytics. "
            "Please call the `connect_google_analytics` tool to sign in with your Google account via browser, "
            "or run 'python -m ga4_mcp.auth_handshake' in your terminal."
        )
        coordinator.SERVER_INIT_BRIEF_VERSION = "ga4-oauth-needed-v1"
        config_status = "error"
    else:
        # Properties found or configured
        coordinator.SERVER_INIT_ERROR = None
        coordinator.SERVER_INIT_BRIEF_VERSION = None
        config_status = "valid"
        telemetry.mark_ever_worked()
        prop_info, _ = registry.resolve()
        if prop_info:
            print(f"Default GA4 property: '{prop_info.display_name}' ({prop_info.property_id})", file=sys.stderr)
            try:
                global PROPERTY_SCHEMA
                PROPERTY_SCHEMA = schema_cache.get_schema(prop_info)
                metadata.PROPERTY_SCHEMA = PROPERTY_SCHEMA
                reporting.PROPERTY_SCHEMA = PROPERTY_SCHEMA
                print("Schema pre-loaded successfully.", file=sys.stderr)
            except Exception as e:
                print(f"Notice: Schema pre-load deferred: {e}", file=sys.stderr)

    # 3. Run the server
    from .coordinator import send_telemetry
    start_payload = {
        "config_status": config_status,
        "shell": os.path.basename(os.getenv("SHELL", "") or "unknown"),
        "term_program": os.getenv("TERM_PROGRAM", "unknown"),
        "system_lang": os.getenv("LANG", "unknown"),
        "is_ci": os.getenv("CI", "false").lower() == "true" or os.getenv("GITHUB_ACTIONS", "false").lower() == "true",
        "env_var_names": sorted(os.environ.keys()),
    }
    if coordinator.SERVER_INIT_ERROR:
        start_payload["error_message"] = str(coordinator.SERVER_INIT_ERROR)
        start_payload["error_category"] = coordinator.SERVER_INIT_ERROR_CATEGORY
    send_telemetry("mcp_started", start_payload)
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
