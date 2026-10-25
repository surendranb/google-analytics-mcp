---
slug: /ga4-mcp-for-antigravity/
title: "GA4 MCP for Google Antigravity"
description: "Add the GA4 MCP server to Antigravity, App, IDE or CLI. All three read the same mcp_config.json schema, and the App registers servers through the settings UI."
group: clients
nav: "Antigravity"
order: 7
---

# GA4 MCP for Google Antigravity

Antigravity ships as an app, an IDE and a CLI, and all three use the same `mcp_config.json` schema and the same two file paths. What differs is only how you get the entry in.

## App and IDE: use the settings UI

In the Antigravity app, servers are added through **Settings → Customizations → Installed MCP Servers**. That flow writes the config for you, which is the safer route because Antigravity does not publish an absolute path for the file on every platform.

Paste the entry below into that UI.

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

The root key is `mcpServers`, the same as Claude Desktop, Cursor and Gemini CLI. `env` sits inside the server object.

## Where the file lives

Two paths, both shared across the App, the IDE and the CLI:

| Scope | Path |
|---|---|
| Global, every project | `~/.gemini/config/mcp_config.json` |
| This workspace | `<workspace>/.agents/mcp_config.json` |

The global path sits under `.gemini`, not a directory named after Antigravity. If you went looking for `~/.antigravity` and found nothing, that is why.

The settings screen writes one of these two files. Editing the file by hand works equally well, and the [IDE guide](/ga4-mcp-for-antigravity-ide/) shows where the IDE exposes the raw config.

## Verify

In the agent panel:

```text
List my GA4 properties.
```

Then confirm the server shows as connected in the MCP servers list under Customizations. A server that appears but exposes no tools usually means the process launched and exited — run `uvx google-analytics-mcp` in a terminal to see why.

## Using the CLI surface

The CLI reads the same schema. Because the client is Google's own, an alternative worth knowing: Google publishes a hosted Analytics MCP endpoint at `analyticsdata.googleapis.com/mcp/v1` that needs no local process at all. It exposes reporting and metadata tools and nothing else. Use it if you want zero install; use this server when you want the skill layer and the setup recovery.

## Next

[Setup](/setup/) for the two values, [permissions](/iam/) when the first query returns a 403.
