---
slug: /ga4-mcp-for-vscode/
title: "GA4 MCP for VS Code and Copilot"
description: "The GA4 MCP server in VS Code agent mode. Note the root key: .vscode/mcp.json uses servers, while .mcp.json uses mcpServers. Copying between them silently fails."
group: clients
nav: "VS Code"
order: 4
---

# GA4 MCP for VS Code

VS Code's agent mode runs MCP servers, and the configuration has one trap that catches almost everyone: the root key depends on which file you are editing.

## Pick the right file first

| File | Root key | Scope |
|---|---|---|
| `.vscode/mcp.json` | `servers` | This workspace |
| `.mcp.json` at the workspace root | `mcpServers` | This workspace, portable shape |
| `~/.copilot/mcp-config.json` | `mcpServers` | Every workspace for this user |

The two workspace files are not interchangeable. A config that works in one is silently ignored in the other, because the top-level key does not match what that file expects. This is the single most common reason a working snippet "does nothing" in VS Code.

## The workspace entry

In `.vscode/mcp.json`:

```json
{
  "servers": {
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

Note `servers`, and note that `type` is required here.

## The portable entry

In `.mcp.json` at the workspace root:

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

Use this one if you want the same file to work in other clients that read `.mcp.json`.

## The CLI route

One command, no file editing:

```bash
code --add-mcp '{"name":"google-analytics","type":"stdio","command":"uvx","args":["google-analytics-mcp"],"env":{"GA4_PROPERTY_ID":"123456789","GOOGLE_APPLICATION_CREDENTIALS":"/absolute/path/to/key.json"}}'
```

Note that the CLI object uses `name` rather than a keyed object — it is a different shape from the file, not a copy of it.

## Environment variable substitution

`.vscode/mcp.json` can read values from your environment instead of hardcoding a credentials path:

```json
{
  "servers": {
    "google-analytics": {
      "type": "stdio",
      "command": "uvx",
      "args": ["google-analytics-mcp"],
      "env": {
        "GA4_PROPERTY_ID": "${env:GA4_PROPERTY_ID}",
        "GOOGLE_APPLICATION_CREDENTIALS": "${env:GOOGLE_APPLICATION_CREDENTIALS}"
      }
    }
  }
}
```

The `${env:NAME}` form is specific to `.vscode/mcp.json`. The portable `.mcp.json` uses `${NAME}` instead. Another reason not to move a block between the two files.

## If you use Cline or Roo Code

Those are extensions with their own MCP settings, not consumers of `.vscode/mcp.json`. The installer writes their entries separately, so the fastest path is:

```bash
curl -fsSL "https://ga4.builditwithai.xyz/install" | bash
```

## Verify

Open the agent panel and ask for something that forces a tool call:

```text
List my GA4 properties.
```

Then check the server shows as running in the MCP servers view. A server that is listed but stopped is almost always a launch failure — run `uvx google-analytics-mcp` in a terminal to see the real error.

## Next

[Setup](/setup/) for credentials, [query shapes](/schema/) when the first query fails on a filter.
