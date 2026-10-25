---
slug: /ga4-plugin-for-claude-code/
title: "GA4 plugin for Claude Code"
description: "The Claude Code plugin bundle declares the GA4 MCP server and its two required settings, so Claude Code can install the server and prompt for the values."
group: plugins
nav: "Claude Code bundle"
order: 2
---

# GA4 plugin for Claude Code

Claude Code can install an MCP server from a plugin manifest instead of from a CLI command. The bundle ships in the repository at `.claude-plugin/plugin.json`.

## What the manifest declares

```json
{
  "name": "google-analytics-mcp",
  "version": "2.11.1",
  "description": "Google Analytics 4 MCP server for real-time reporting, schema discovery, metric aggregation, and audience insights.",
  "author": { "name": "Surendran B", "url": "https://github.com/surendranb" },
  "homepage": "https://ga4.builditwithai.xyz",
  "repository": "https://github.com/surendranb/google-analytics-mcp",
  "license": "MIT",
  "mcpServers": {
    "google-analytics-mcp": {
      "command": "uvx",
      "args": ["google-analytics-mcp"]
    }
  }
}
```

That is the whole file. The `mcpServers` block is what Claude Code launches; everything above it is metadata.

## Plugin or plain entry

Both end up in the same place: a server named `google-analytics-mcp` launched with `uvx`. The difference is who writes it.

- A **plugin** is for distribution. Someone else adds the bundle and Claude Code reads the command from the manifest.
- A **plain entry** is for your own machine, and it can inline the two environment values so nothing prompts.

If you are setting this up once, the plain entry is fewer steps:

```bash
claude mcp add --env GA4_PROPERTY_ID=123456789 --env GOOGLE_APPLICATION_CREDENTIALS=/absolute/path/to/key.json --transport stdio google-analytics -- uvx google-analytics-mcp
```

The [Claude guide](/ga4-mcp-for-claude/) covers both Claude surfaces in full.

## Version note

The plugin manifest tracks its own version number, which is not the server version. Today the manifest reads `2.11.1` while the server is on 2.11.6. The manifest version controls the bundle, not the package that `uvx` resolves — that always pulls the latest release. Read the version from the server, not from the bundle, when you need to know what is running.

## Next

[Plugins overview](/ga4-plugins/) or the [Gemini bundle](/ga4-plugin-for-gemini/).
