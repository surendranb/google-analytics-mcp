---
slug: /ga4-mcp-for-kiro/
title: "GA4 MCP for Kiro"
description: "Add the GA4 MCP server to Kiro. Kiro hot-reloads mcp.json on save, so no restart is needed, and it carries per-tool approval settings the other clients do not."
group: clients
nav: "Kiro"
order: 10
---

# GA4 MCP for Kiro

Kiro reads MCP servers from `mcp.json` and reloads the file the moment you save it. That is the main practical difference from the rest of this set — you will not be restarting the editor.

## Where the file lives

- **Workspace:** `.kiro/settings/mcp.json` inside the project.
- **User:** `~/.kiro/settings/mcp.json`, applied everywhere.

Workspace scope wins when both exist.

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
      },
      "disabled": false,
      "autoApprove": ["list_properties", "search_schema", "get_ga4_data"]
    }
  }
}
```

The root key is `mcpServers`. The three optional keys are Kiro-specific:

- `disabled` — set `true` to keep the entry but stop it launching.
- `autoApprove` — tool names that run without a confirmation prompt. For a read-only analytics server there is no reason to confirm each call.
- `disabledTools` — the inverse. Useful for hiding `check_for_updates` or `setup_ga4_access` from an agent you want focused on reporting.

Kiro also expands environment placeholders, so a credentials path can come from the shell:

```json
"env": {
  "GA4_PROPERTY_ID": "123456789",
  "GOOGLE_APPLICATION_CREDENTIALS": "${GOOGLE_APPLICATION_CREDENTIALS}"
}
```

## From the CLI

```bash
kiro-cli mcp add --name google-analytics --scope global --command uvx --args google-analytics-mcp --env GA4_PROPERTY_ID=123456789
```

`--args` takes one argument per flag, so a server with several arguments needs the flag repeated rather than a single space-separated string.

## Verify

Save the file, then ask:

```text
List my GA4 properties.
```

The server should appear without a restart. If it does not, check the MCP servers panel — Kiro reports a launch failure there rather than failing silently, which it can do because it is watching the process rather than reading a file once.

## Next

[Setup](/setup/) for the two values, [permissions](/iam/) for the 403 that means the service account is not on the property.
