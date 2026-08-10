# SPDX-License-Identifier: Apache-2.0

from .coordinator import mcp, send_telemetry

SETUP_GUIDE_MD = """# Google Analytics 4 MCP Setup Guide

It looks like your setup is incomplete or broken. As an AI agent, you can help the user fix this by guiding them through the following troubleshooting steps.

## 1. Missing Environment Variables
If the server reports `GOOGLE_APPLICATION_CREDENTIALS` or `GA4_PROPERTY_ID` is not set:
1. Ask the user which MCP client they are using (Claude Desktop, Cursor, Windsurf, etc.).
2. Ask the user for their GA4 Property ID (a numeric string, NOT the Measurement ID starting with G-) and the absolute path to their Google Cloud JSON service account key.
3. Update their configuration file (e.g. `claude_desktop_config.json` or `mcp.json`) to include the `env` block:
   ```json
   "env": {
     "GOOGLE_APPLICATION_CREDENTIALS": "/absolute/path/to/key.json",
     "GA4_PROPERTY_ID": "123456789"
   }
   ```

## 2. The Credentials Path (Copy-Paste Trap)
If the configuration contains `/ABSOLUTE/PATH/TO/`, the user copied the example verbatim. 
Ask the user: "Where did you save your Google Cloud JSON service account key?"
Once they provide the path, please update their configuration file to use that real absolute path instead of the dummy path.

## 3. Invalid Credentials Path
If the server reports `Credentials file not found at '...'`:
The path provided in `GOOGLE_APPLICATION_CREDENTIALS` does not point to a valid file. 
1. Ask the user to verify the exact location of their JSON key file.
2. If they are on Windows, ensure the path uses properly escaped backslashes (e.g., `C:\\\\Users\\\\Name\\\\key.json`) or forward slashes.
3. Update their MCP client config with the correct path.

## 4. The IAM Wall (403 Permission Denied)
If the path is correct but the server gets a 403 Permission Denied, the service account does not have access to the GA4 Property.
Instruct the user to do the following:
1. Go to https://analytics.google.com
2. Navigate to Admin -> Property Access Management
3. Click the '+' button to Add Users.
4. Enter the service account email (found inside the JSON key file) and assign it the **Viewer** role.
5. Wait a few minutes for permissions to propagate.

## 5. Reauthentication Needed (ADC Error)
If the server reports a metadata error or asks to run `gcloud auth application-default login`, the user's Application Default Credentials have expired or are invalid.
Instruct the user to open their terminal and run:
`gcloud auth application-default login`

Once the user confirms they have applied the fix, please retry your tool execution or prompt them to restart their MCP client.
"""

@mcp.resource("docs://setup_guide")
def get_setup_guide() -> str:
    """Provides instructions to the agent on how to heal the human's MCP setup."""
    send_telemetry("resource_read", {"resource_uri": "docs://setup_guide"})
    return SETUP_GUIDE_MD


# Category-addressed fix guides, same content the get_troubleshooting_guide tool
# serves — exposed as resources for clients that surface resources to the model.
# One source of truth (tools.troubleshooting._GUIDES); progressive enhancement
# on top of the always-reaches error playbook.
from .tools.troubleshooting import _GUIDES as _FIX_GUIDES


def _make_fix_resource(topic):
    def _read() -> str:
        send_telemetry("resource_read", {"resource_uri": f"docs://fix/{topic}"})
        return _FIX_GUIDES[topic]
    _read.__name__ = f"get_fix_{topic}"
    return mcp.resource(f"docs://fix/{topic}")(_read)


for _t in _FIX_GUIDES:
    _make_fix_resource(_t)


# Skills mirrored as resources (channel standard S5): the same analytical
# recipes search_skills serves, addressable as skill://<name> for clients that
# surface resources to the model — discovery without a tool call. Content is
# identical to the tool path: the repo's skills/ dir when present locally
# (source/editable installs), else the pinned GitHub raw fetch (the fleet path;
# skills/ is not packaged). search_skills itself is unchanged.
from pathlib import Path as _Path

from .tools.skills import _SKILLS_BASE, _fetch as _fetch_skill

_SKILL_SLUGS = (
    "index",
    "ai-referral-analysis",
    "attribution-scope",
    "bot-traffic-detection",
    "channel-acquisition",
    "common-metric-names",
    "compatible-combinations",
    "content-performance",
    "custom-dimensions",
    "date-ranges",
    "ecommerce-analysis",
    "filter-structures",
    "ga4-limitations",
    "geo-device-segmentation",
    "traffic-diagnosis",
    "ua-to-ga4",
)

_LOCAL_SKILLS_DIR = _Path(__file__).resolve().parent.parent / "skills"


def _read_skill(slug: str) -> str:
    try:
        local = _LOCAL_SKILLS_DIR / f"{slug}.md"
        if local.is_file():
            return local.read_text(encoding="utf-8")
    except Exception:
        pass
    try:
        return _fetch_skill(f"{_SKILLS_BASE}/{slug}.md")
    except Exception as e:
        return f"Skill '{slug}' unavailable: {e}. Call the search_skills tool instead."


def _make_skill_resource(slug):
    def _read() -> str:
        send_telemetry("resource_read", {"resource_uri": f"skill://{slug}"})
        return _read_skill(slug)
    _read.__name__ = f"get_skill_{slug.replace('-', '_')}"
    _read.__doc__ = (f"GA4 analytical skill '{slug}' — the same recipe served by "
                     f"search_skills('{slug}'): proven dimensions, metrics, filters, "
                     "and how to interpret the result.")
    return mcp.resource(f"skill://{slug}", name=f"skill-{slug}",
                        mime_type="text/markdown")(_read)


for _s in _SKILL_SLUGS:
    _make_skill_resource(_s)
