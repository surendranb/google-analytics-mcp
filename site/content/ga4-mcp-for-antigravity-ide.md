---
slug: /ga4-mcp-for-antigravity-ide/
title: "GA4 MCP for Antigravity IDE"
description: "The Antigravity IDE uses the same mcp_config.json schema as the App and CLI. Manage it from the agent panel's MCP Servers screen, or edit the file directly."
group: clients
order: 18
nav: "Antigravity IDE"
---

# GA4 MCP for Antigravity IDE

The Antigravity IDE shares one MCP schema with the App and the CLI. Google's own documentation states it plainly: `mcp_config.json` follows a standardised schema, and the root object holds an `mcpServers` map.

What differs in the IDE is the management surface, not the file.

## The entry

```json
{
  "mcpServers": {
    "ga4": {
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

## The two files

| Scope | Path |
|---|---|
| Global, every project | `~/.gemini/config/mcp_config.json` |
| This workspace | `<workspace>/.agents/mcp_config.json` |

The global path sits under `.gemini`, not a directory named after Antigravity. That surprises people who go looking for `~/.antigravity`.

## Managing it from the IDE

The IDE has a UI for the same file:

1. Open the agent side panel.
2. Click the `…` menu.
3. Choose **MCP Servers**.
4. Choose **Manage MCP Servers**.
5. Choose **View raw config** to see or edit the file.

That screen is the fastest way to find which of the two files is actually loaded, because it shows the resolved config rather than the one you think you edited.

> **Tip:** if you edit the workspace file and nothing changes, the global file probably wins for that project. Check the raw config view before assuming the entry was ignored.

## Remote servers are Streamable HTTP only

Worth knowing if you were planning to point the IDE at a hosted endpoint: it accepts Streamable HTTP with `serverUrl` (`url` also works). Legacy HTTP with SSE and `httpUrl` are explicitly unsupported.

This server is local stdio, so none of that applies — but it explains why a hosted Analytics MCP endpoint may or may not drop into the IDE depending on how it is served.

## Verify

```text
List my GA4 properties.
```

Then check the MCP Servers list in the agent panel. A server that shows as installed with no tools means the process exited after launching; run `uvx google-analytics-mcp` in a terminal to see the error.

## Next

[Antigravity App and CLI](/ga4-mcp-for-antigravity/) for the other two surfaces, [install](/setup/) for the credentials.
