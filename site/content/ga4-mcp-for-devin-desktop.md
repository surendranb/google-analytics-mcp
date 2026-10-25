---
slug: /ga4-mcp-for-devin-desktop/
title: "GA4 MCP for Devin Desktop"
description: "Add the GA4 MCP server to Devin Desktop, the client formerly named Windsurf. Includes the config path conflict between two live vendor pages."
group: clients
nav: "Devin Desktop"
order: 11
---

# GA4 MCP for Devin Desktop

Devin Desktop is the current name for Windsurf. The rename happened on 2 June 2026, so older guides and forum answers still call it Windsurf. The config schema did not change with the name.

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

Root key `mcpServers`, standard `env` object. Nothing unusual in the shape.

## The path problem, stated plainly

Devin's own documentation gives two different paths for the same file, and both pages are live today:

- The Cascade MCP page says `~/.config/devin/mcp_config.json` on macOS and Linux, and `%APPDATA%\devin\mcp_config.json` on Windows.
- The Devin Desktop FAQ says the MCP config is `~/.codeium/mcp_config.json`, and adds that the `~/.codeium/` directory structure is not changing in this release.

Rather than pick one and hope, check which file exists on your machine:

```bash
ls -la ~/.config/devin/mcp_config.json ~/.codeium/mcp_config.json
```

Edit whichever one is present. If neither exists, create the `.config/devin` one and restart the app — the newer path is the one on the MCP page.

> **Note:** if you are migrating from Windsurf and MCP servers still work, you are on the `.codeium` path and can leave it alone. The rename did not move it.

## Verify

```text
List my GA4 properties.
```

Then open the MCP panel in Cascade and confirm the server is running. Devin shows a failed launch there, which distinguishes a bad config from a bad credential — a distinction the other clients here generally do not make.

## If you are on Windsurf

Windsurf, before the rename, used the same `mcpServers` shape. Older Windsurf documentation and this page are compatible; only the file path differs by app version.

## Next

[Setup](/setup/) for the two values, [skills](/skills/) for what to load before asking a question that needs interpretation.
