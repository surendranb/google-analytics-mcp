---
slug: /ga4-mcp-for-every-harness/
title: "GA4 MCP client setup — the config each one expects"
description: "Eleven client guides, each with the config shape that client documents. MCP is not portable: four of these use a different root key, so a snippet from one will silently fail in another."
group: clients
nav: "All clients"
order: 1
---

# Every client, and the config it actually wants

Most MCP installation guides give you one JSON block and tell you it works everywhere. It does not. Across the seventeen clients below there are six different root keys, four different names for the environment object, and four file formats.

Copying a Claude Desktop snippet into Hermes produces a file that parses and registers no servers. Copying one into OpenCode produces a server that never appears. Neither reports an error.

| What varies | Values across these clients |
|---|---|
| Root key | `mcpServers` (most clients), `servers` (VS Code), `context_servers` (Zed), `mcp` (OpenCode), `mcp_servers` (Hermes), `mcp.servers` (OpenClaw, ZCode) |
| Environment key | `env` (most), `envs` (Goose), `environment` (OpenCode), `env` plus `env_vars` (Codex) |
| Command shape | String everywhere except OpenCode, which takes an array |
| File format | JSON (most), TOML (Codex), YAML (Goose, Hermes, DeepSeek) |

Every block on the pages below is quoted from that vendor's own documentation, with the source page named. Where a vendor has not published a path, this site says so instead of inventing one.

<!--CLIENTS-->

## If your client is not here

It probably still works. The server speaks MCP over stdio, which is the transport every client here uses. Start from the shape used by the client closest to yours, run `uvx google-analytics-mcp` in a terminal to confirm the server itself is fine, and then find where your client keeps its server list.

The server itself is client-agnostic. It speaks MCP over stdio. The only thing that changes per client is where the entry lives and what the surrounding keys are called.

## Next

Whichever client you pick, the credentials and verification steps are the same. Read [install](/setup/) for those, then [permissions](/iam/) when the first query returns a 403.
