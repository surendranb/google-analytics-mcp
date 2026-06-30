# Google Analytics 4 MCP: Setup Guide

If you are seeing a setup error, it means the IDE (Claude Desktop, Cursor, etc.) started the MCP server, but the required environment variables are missing or incorrect. 

## 1. Missing `GA4_PROPERTY_ID`
The user must provide the exact numeric Property ID of their Google Analytics 4 property.
**Action required by user:**
Tell the user to set the `GA4_PROPERTY_ID` environment variable in their MCP configuration (e.g., `claude_desktop_config.json` or Cursor settings).
Example:
```json
"env": {
  "GA4_PROPERTY_ID": "123456789",
  "GOOGLE_APPLICATION_CREDENTIALS": "..."
}
```

## 2. Missing `GOOGLE_APPLICATION_CREDENTIALS`
The server requires Google Cloud credentials to query the GA4 API. 
**Action required by user:**
They must set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable to the absolute path of their Service Account JSON key.
Example:
```json
"env": {
  "GA4_PROPERTY_ID": "123456789",
  "GOOGLE_APPLICATION_CREDENTIALS": "/Users/name/keys/ga4-key.json"
}
```

## 3. Expired Application Default Credentials (ADC)
If the user is relying on `gcloud` local authentication (instead of a JSON file) and receives a `503 Reauthentication is needed` error, their local token has expired.
**Action required by user:**
Tell the user to open their terminal and run:
```bash
gcloud auth application-default login
```
