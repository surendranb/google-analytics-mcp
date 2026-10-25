---
slug: /ga4-mcp-for-openclaw/
title: "GA4 MCP for OpenClaw"
description: "Add the GA4 MCP server to OpenClaw with openclaw mcp add, stored under mcp.servers in ~/.openclaw/openclaw.json. No plugin needed."
group: clients
order: 15
nav: "OpenClaw"
---

# GA4 MCP for OpenClaw

OpenClaw is an MCP client directly, so the server needs no plugin. One command writes the entry.

## Add the server

```bash
openclaw mcp add ga4 --command uvx --arg google-analytics-mcp
```

`--arg` repeats once per server argument. That writes an entry under `mcp.servers` in `~/.openclaw/openclaw.json`:

```json
{
  "mcp": {
    "servers": {
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
}
```

Edit the file to add the two `env` values — the server will not start usefully without them. The root key is `mcp.servers`, two levels deep, not `mcpServers` at the top.

## Check it launched

```bash
openclaw mcp doctor ga4 --probe
```

`--probe` is the part that matters. Without it you get configuration validation; with it, OpenClaw actually starts the process and reports whether the handshake completes. A server that configures cleanly and fails the probe is almost always a missing environment variable.

## Where the file lives

`~/.openclaw/openclaw.json`. OpenClaw also discovers plugins from configured paths, workspace roots and global plugin roots, but MCP servers are separate from plugins and live in this one file.

## About the plugin route

The repository ships a file at `plugins/openclaw/plugin.json`. It is not an installable OpenClaw manifest. OpenClaw's documented manifest is `openclaw.plugin.json`, and its required fields are `id` and `configSchema` — neither of which that file has.

Use `openclaw mcp add` above. A plugin is only worth building if you want to distribute a bundle; a single local server does not need one.

## Verify

```text
List my GA4 properties.
```

If `doctor` reports the server running and the tools still do not appear in a session, the property ID is wrong rather than the config. Read [install](/setup/) for the difference between the property ID and the measurement ID.

## Next

[Install](/setup/) for credentials, [skills](/skills/) for the recipes the agent can load once connected.
