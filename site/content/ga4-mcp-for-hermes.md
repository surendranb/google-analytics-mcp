---
slug: /ga4-mcp-for-hermes/
title: "Connect Hermes Agent to Google Analytics 4 (MCP Setup)"
description: "Add the GA4 MCP server to Hermes Agent. The root key is mcp_servers in YAML, not mcpServers in JSON, so a Claude snippet silently adds nothing."
group: clients
order: 16
nav: "Hermes"
---

# Connect Hermes Agent to Google Analytics 4

Hermes is Nous Research's agent harness. It configures MCP servers in YAML, and the root key is `mcp_servers` — snake case. A Claude Desktop snippet pasted here produces a file that parses fine and registers nothing.

## Copy-paste analytical prompts

Inside Hermes Agent:

- **Weekly performance overview**: "Compare activeUsers, sessions, and engagementRate for the last 7 days against the previous period."
- **AI referral audit**: "Show me sessions, bounceRate, and keyEvents referred by ChatGPT, Claude, and Perplexity over the last 30 days."
- **High-bounce page check**: "List top 10 pages by sessions where bounceRate exceeds 60% over the last 30 days."
- **Channel breakdown**: "Break down sessions and keyEvents by sessionDefaultChannelGroup this month."
- **Realtime traffic status**: "Run a realtime report showing active users and top pages over the last 30 minutes."

## The entry

In `~/.hermes/config.yaml`:

```yaml
mcp_servers:
  ga4:
    command: "uvx"
    args: ["google-analytics-mcp"]
```

That is the shape Hermes documents. Note the two differences from the common JSON form: the root key is `mcp_servers`, and the file is YAML, so indentation carries the structure.

## Credentials

Hermes' documented example shows `command` and `args` only. It does not publish an environment key for this block, and this server cannot run without two values.

The reliable route is to export them before launching Hermes, so the server process inherits them:

```bash
export GA4_PROPERTY_ID="123456789"
export GOOGLE_APPLICATION_CREDENTIALS="/absolute/path/to/key.json"
```

Launch Hermes from that shell. Application default credentials work here too — run `gcloud auth application-default login` once and you can drop the second variable.

> **Note:** if a future Hermes release documents an `env` key, prefer it over shell inheritance. This page states shell export because that is what the vendor documents today.

## Migrating from Claude

Hermes ships a migration command that rewrites a Claude configuration into its own shape:

```bash
hermes import-agent claude-code
```

It maps Claude's `mcpServers` in `~/.claude.json` onto `mcp_servers` in `config.yaml`. Worth running even if you only want the shape as a reference — the output shows exactly how Hermes expects a server to look.

There is also a picker and a catalog:

```bash
hermes mcp
```

```bash
hermes mcp install ga4
```

The catalog holds entries from Hermes' own `optional-mcps` directory. If GA4 is not in it, the manual block above is the path.

## Do not confuse the packages

`hermes-mcp` on PyPI is the opposite direction: an MCP server that exposes a Hermes agent to other clients. Installing it does not give Hermes access to Analytics.

## Verify

```text
List my GA4 properties.
```

If the agent has no GA4 tools at all, check the root key first. `mcpServers` in that file is valid YAML and completely inert.

## Next

[Install](/setup/) for the two values, [query shapes](/schema/) when a query fails on a filter.
