---
slug: /ga4-plugins/
title: "GA4 MCP plugins for Claude Code and Gemini CLI"
description: "Plugin bundles wrap the GA4 MCP server with its configuration, so a client can install the server and its settings in one step."
group: plugins
nav: "All plugins"
order: 1
---

# Plugins

A plugin is a manifest that tells a client how to launch the server and what values it needs. It is not a different server. It is the same `uvx google-analytics-mcp` with the configuration attached, so the client can install and prompt for the two values in one flow instead of asking you to edit a JSON file.

Two clients support a plugin bundle today.

<!--PLUGINS-->

## When a plugin is worth it

If you install the server once, on one machine, the plain config entry is simpler and this page adds nothing. A plugin pays off when you want the client to ask for `GA4_PROPERTY_ID` and the credentials path itself, or when you are distributing the setup to other people and do not want them editing config files.

## What is inside

Both bundles carry the same two declarations:

```json
{
  "mcp": {
    "command": "uvx",
    "args": ["google-analytics-mcp"]
  },
  "settings": [
    { "name": "GA4_PROPERTY_ID", "required": true, "type": "string" },
    { "name": "GOOGLE_APPLICATION_CREDENTIALS", "required": true, "type": "string" }
  ]
}
```

The `settings` array is what makes the client prompt. The `mcp` block is what it launches. Everything else is metadata — name, version, license, repository.

## Next

If you would rather not use a bundle, the per-client guides show the raw config: [Claude](/ga4-mcp-for-claude/), [Gemini CLI](/ga4-mcp-for-gemini/), or the [full client list](/ga4-mcp-for-every-harness/).
