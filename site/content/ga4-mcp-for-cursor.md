---
slug: /ga4-mcp-for-cursor/
title: "GA4 MCP for Cursor"
description: "Add the GA4 MCP server to Cursor with a project or global mcp.json entry. Includes the type-field inconsistency Cursor's own docs carry."
group: clients
nav: "Cursor"
order: 3
---

# GA4 MCP for Cursor

Cursor reads MCP servers from a JSON file and supports an environment object per server. Setup is one entry and a restart.

## Where the file lives

Cursor accepts two locations:

- **Project:** `.cursor/mcp.json` in the repository root. Committed with the project, shared with anyone who clones it.
- **Global:** `~/.cursor/mcp.json`. Applies to every workspace on the machine.

Use the project file when the server is tied to one analytics property. Use the global file when you want GA4 available everywhere and you accept that the credentials path is machine-specific.

## The entry

```json
{
  "mcpServers": {
    "google-analytics": {
      "command": "uvx",
      "args": ["google-analytics-mcp"],
      "env": {
        "GA4_PROPERTY_ID": "123456789",
        "GOOGLE_APPLICATION_CREDENTIALS": "/absolute/path/to/key.json"
      }
    }
  }
}
```

Save the file. Cursor picks up changes to the MCP config without a full restart, but the first registration needs one — reload the window from the command palette.

## About the type field

Cursor's configuration reference marks `type` as a required field on stdio servers, with the value `"stdio"`. Every copy-paste example on the same page omits it.

In practice the field is optional and Cursor infers stdio when `command` is present. If the server does not appear, add it explicitly:

```json
{
  "mcpServers": {
    "google-analytics": {
      "type": "stdio",
      "command": "uvx",
      "args": ["google-analytics-mcp"],
      "env": {
        "GA4_PROPERTY_ID": "123456789",
        "GOOGLE_APPLICATION_CREDENTIALS": "/absolute/path/to/key.json"
      }
    }
  }
}
```

That is the shape the reference documents, and it is the one to prefer when something is not working.

## Keeping secrets out of the file

Cursor also supports `envFile`, which reads variables from a dotenv file instead of inlining them. That keeps the credentials path out of a committed `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "google-analytics": {
      "command": "uvx",
      "args": ["google-analytics-mcp"],
      "envFile": ".env.local"
    }
  }
}
```

With `GA4_PROPERTY_ID` and `GOOGLE_APPLICATION_CREDENTIALS` set in `.env.local`, which stays out of version control.

## Verify

In Cursor's agent panel:

```text
List my GA4 properties.
```

If the tool list is empty, the file did not parse. Cursor silently ignores a malformed `mcp.json` rather than reporting an error, so validate the JSON before assuming the server is at fault.

## Next

[Install](/setup/) covers the credentials, [permissions](/iam/) covers the 403 you will hit if the service account was never added to the property.
