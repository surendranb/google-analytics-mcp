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

from .coordinator import mcp, send_telemetry

SETUP_GUIDE_MD = """# Google Analytics 4 MCP Setup Guide

It looks like your setup is incomplete. As an AI agent, you can help the user fix this by guiding them through the following steps:

## 1. The Credentials Path (Copy-Paste Trap)
If the configuration contains `/ABSOLUTE/PATH/TO/`, the user copied the example verbatim. 
Ask the user: "Where did you save your Google Cloud JSON service account key?"
Once they provide the path, please update their configuration file (e.g. `claude.json` or `mcp.json`) to use that real absolute path instead of the dummy path.

## 2. The IAM Wall (403 Permission Denied)
If the path is correct but the server gets a 403 Permission Denied, the service account does not have access to the GA4 Property.
Instruct the user to do the following:
1. Go to https://analytics.google.com
2. Navigate to Admin -> Property Access Management
3. Click the '+' button to Add Users.
4. Enter the service account email (found inside the JSON key file) and assign it the **Viewer** role.

Once the user confirms they have done this, please retry your tool execution.
"""

@mcp.resource("docs://setup_guide")
def get_setup_guide() -> str:
    """Provides instructions to the agent on how to heal the human's MCP setup."""
    send_telemetry("resource_read", {"resource_uri": "docs://setup_guide"})
    return SETUP_GUIDE_MD
