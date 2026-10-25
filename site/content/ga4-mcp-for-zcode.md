---
slug: /ga4-mcp-for-zcode/
title: "GA4 MCP for ZCode"
description: "Add the GA4 MCP server to ZCode. Servers live under mcp.servers in ~/.zcode/cli/config.json, and a competing .agents/mcp.json is skipped entirely, not merged."
group: clients
order: 17
nav: "ZCode"
---

# GA4 MCP for ZCode

ZCode is Z.ai's coding harness. It reads MCP servers from two possible file locations per scope, and the precedence rule between them is the thing that catches people: it is not a merge.

## The entry

In `~/.zcode/cli/config.json`:

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

Note `mcp.servers`, two levels deep. Not `mcpServers`.

## The four locations

| Scope | File | Root key |
|---|---|---|
| User | `~/.zcode/cli/config.json` | `mcp.servers` |
| Workspace | `<project>/.zcode/config.json` | `mcp.servers` |
| User, compatibility | `~/.agents/mcp.json` | `mcpServers` |
| Workspace, compatibility | `<project>/.agents/mcp.json` | `mcpServers` |

ZCode also reads the `.agents` files, which use the plain `mcpServers` shape shared with several other clients. Useful if you already maintain one, and a trap if you maintain both.

## The precedence rule

Within a single scope, `.zcode/config.json` wins **wholesale**. If it contains any server at all, the matching `.agents/mcp.json` at that scope is skipped entirely — not merged, not combined.

So a user who adds GA4 to `~/.agents/mcp.json` while `~/.zcode/cli/config.json` already holds one server sees no GA4 tools, with no error. Either consolidate into the `.zcode` file, or keep the `.agents` file as the only source at that scope.

## Legacy keys

ZCode accepts a set of older key names and translates them: `environment` is read as `env`, `http_headers` as `headers`, `enable` as `enabled`, and `type: "remote"` as `type: "http"`. The current schema takes `env`, and `type` accepts `http`, `sse` or `stdio`.

Writing `env` is the right choice for a new entry. The legacy names work, but they are compatibility rather than the current shape.

## Verify

```text
List my GA4 properties.
```

If the tool list is empty, check which file ZCode actually loaded. A populated `.zcode/config.json` hides `.agents/mcp.json` at the same scope, and that is by design rather than a bug.

## Next

[Install](/setup/) for the two values, [skills](/skills/) for what to load before an analytical question.
