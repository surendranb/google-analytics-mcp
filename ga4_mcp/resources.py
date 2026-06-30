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
