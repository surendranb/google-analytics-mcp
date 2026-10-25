---
slug: /ga4-mcp-for-gemini/
title: "GA4 MCP for Gemini CLI"
description: "Add the GA4 MCP server to Gemini CLI. The scope flag defaults to project, so the entry lands in .gemini/settings.json and not your home directory."
group: clients
nav: "Gemini CLI"
order: 6
---

# GA4 MCP for Gemini CLI

Gemini CLI reads MCP servers from a `settings.json` file and can also register them from the command line. The one behaviour worth knowing before you start: the default scope is **project**, not user.

## One command

```bash
gemini mcp add -e GA4_PROPERTY_ID=123456789 -e GOOGLE_APPLICATION_CREDENTIALS=/absolute/path/to/key.json google-analytics uvx google-analytics-mcp
```

The shape is `gemini mcp add [options] <name> <command> [args...]`, so the server name comes before the command and anything after it becomes an argument to the server.

Add `--scope user` if you want the entry in your home directory instead of the current project:

```bash
gemini mcp add --scope user -e GA4_PROPERTY_ID=123456789 -e GOOGLE_APPLICATION_CREDENTIALS=/absolute/path/to/key.json google-analytics uvx google-analytics-mcp
```

Without that flag the entry goes to `.gemini/settings.json` inside the directory you ran it from. That is the single most common surprise: it works in one repository and appears missing in the next.

## The file

User scope is `~/.gemini/settings.json`. Project scope is `.gemini/settings.json`.

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

The root key is `mcpServers`, which matches Claude Desktop and Cursor. Gemini additionally accepts three optional keys on a stdio server that the others do not:

- `cwd` — working directory for the spawned process
- `timeout` — milliseconds before the client gives up on a call
- `trust` — skip the confirmation prompt for tool calls

For a read-only analytics server, `"trust": true` removes a confirmation click per query and changes nothing about what the server can do.

## A project-scoped example

```json
{
  "mcpServers": {
    "google-analytics": {
      "command": "uvx",
      "args": ["google-analytics-mcp"],
      "env": {
        "GA4_PROPERTY_ID": "123456789",
        "GOOGLE_APPLICATION_CREDENTIALS": "/absolute/path/to/key.json"
      },
      "trust": true,
      "timeout": 30000
    }
  }
}
```

## Verify

```text
List my GA4 properties.
```

If Gemini reports no GA4 tools, check the scope before anything else. Run `gemini mcp list` and confirm which file the entry actually landed in.

## Next

[Setup](/setup/) for credentials, [skills](/skills/) for the recipes the agent can load once it is connected.
