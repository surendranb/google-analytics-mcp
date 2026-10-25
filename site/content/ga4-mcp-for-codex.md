---
slug: /ga4-mcp-for-codex/
title: "GA4 MCP for Codex CLI"
description: "Add the GA4 MCP server to OpenAI Codex. Codex uses TOML, not JSON, and splits environment handling into env and env_vars — the two are not interchangeable."
group: clients
nav: "Codex"
order: 5
---

# GA4 MCP for Codex

Codex is the one client in this set that configures MCP servers in TOML rather than JSON, and the one that splits environment handling into two separate keys. Both trip people up.

## One command

```bash
codex mcp add google-analytics --env GA4_PROPERTY_ID=123456789 --env GOOGLE_APPLICATION_CREDENTIALS=/absolute/path/to/key.json -- uvx google-analytics-mcp
```

As with Claude Code, the `--` separates Codex's own flags from the command it will launch.

## The file

Codex reads `~/.codex/config.toml` for every session, and `.codex/config.toml` inside a project that Codex has been told to trust. Project config only applies to trusted projects, which is a deliberate security boundary rather than a bug.

```toml
[mcp_servers.google-analytics]
command = "uvx"
args = ["google-analytics-mcp"]

[mcp_servers.google-analytics.env]
GA4_PROPERTY_ID = "123456789"
GOOGLE_APPLICATION_CREDENTIALS = "/absolute/path/to/key.json"
```

That is the whole entry. TOML table headers do the work that JSON braces do elsewhere.

## env versus env_vars

This is the part that catches people, and it is specific to Codex.

- `env` **sets** a value. Use it when you want to write the value in the file.
- `env_vars` **allows an existing environment variable through** to the server. Use it when the value lives in your shell or a secret manager and you do not want it in the file.

So these two entries do different things:

```toml
[mcp_servers.google-analytics.env]
GA4_PROPERTY_ID = "123456789"
```

```toml
[mcp_servers.google-analytics]
env_vars = ["GA4_PROPERTY_ID", "GOOGLE_APPLICATION_CREDENTIALS"]
```

The first hardcodes the property ID. The second forwards whatever the shell has. Both are valid; putting a bare value inside `env_vars` is not, because that key takes names and not assignments.

A common arrangement is a hardcoded property ID plus a forwarded credentials path:

```toml
[mcp_servers.google-analytics]
command = "uvx"
args = ["google-analytics-mcp"]
env_vars = ["GOOGLE_APPLICATION_CREDENTIALS"]

[mcp_servers.google-analytics.env]
GA4_PROPERTY_ID = "123456789"
```

## Verify

Start Codex and ask:

```text
List my GA4 properties.
```

Then check that the tool appears in Codex's MCP list. If the entry loads but every call fails with a setup error, one of the two variables is missing — the TOML parsed, the `env` table did not apply.

## Next

[Install](/setup/) for the two values, [permissions](/iam/) for the 403 that means the service account is not on the property yet.
