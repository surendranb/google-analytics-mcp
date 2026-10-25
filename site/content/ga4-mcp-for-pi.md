---
slug: /ga4-mcp-for-pi/
title: "GA4 MCP for Pi"
description: "Add the GA4 MCP server to Pi with one mcpServers entry in the agent directory, or with pi mcp add. Tools appear as mcp__ga4__get_ga4_data."
group: clients
order: 14
nav: "Pi"
---

# GA4 MCP for Pi

Pi reads MCP servers from a JSON file beside its agent configuration, and also takes them from the command line. Two files matter, and the project one only counts after you trust the project.

## The entry

In your agent directory's `mcp.json`:

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

Two locations, matching Pi's own wording of `<agent-dir>/mcp.json`:

| Scope | Path |
|---|---|
| User | `~/.pi/agent/mcp.json` |
| Project | `.pi/mcp.json` in the project root |

The project file is only read once Pi trusts that project. If the server works in one repository and not another, trust is the reason.

## From the command line

```bash
pi mcp add ga4 --command uvx --arg google-analytics-mcp --env GA4_PROPERTY_ID=123456789 --env GOOGLE_APPLICATION_CREDENTIALS=/absolute/path/to/key.json
```

`pi mcp` also lists and removes servers. Note that `--arg` repeats once per argument rather than taking a single string.

> **Note:** there is no `/codemcp` command and no `pi-mcp` package. An earlier version of this page named both; neither exists. The interactive command is `/mcp`, and `codemode` is a tool-exposure mode rather than a slash command.

## Managing at runtime

Inside a Pi session, `/mcp` is the interactive surface: inspect connected servers, reconnect one, change how its tools are exposed, or disable it for the session.

That is the fastest way to check whether the entry loaded at all. A server listed with zero tools means the process launched and exited — run `uvx google-analytics-mcp` in a terminal to see why.

## Tool names

Pi prefixes MCP tools as `mcp__<server>__<tool>`, so with the server named `ga4` above the agent calls `mcp__ga4__get_ga4_data`. Naming the server `ga4` rather than `google-analytics` keeps the tool names short enough to read in a transcript.

## Verify

```text
List my GA4 properties.
```

Then `/mcp` to confirm the server is connected rather than merely configured.

## Next

[Install](/setup/) for the two values, [skills](/skills/) for what to load before an analytical question.
