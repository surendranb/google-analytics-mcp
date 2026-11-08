---
slug: /ga4-mcp-for-claude/
title: "Connect Claude to Google Analytics 4 (Code & Desktop)"
description: "Add the GA4 MCP server to Claude Code with one CLI command, or to Claude Desktop with one JSON entry. Includes five production natural language prompts."
group: clients
nav: "Claude"
order: 2
---

# Connect Claude to Google Analytics 4

Claude has two surfaces that run local MCP servers, and they take different configuration. Claude Code is a CLI and registers the server from your terminal. Claude Desktop reads a JSON file.

## Prerequisites

You need the numeric property ID and either a service-account key path or a `gcloud` login. Both are covered in [install](/setup/). Keep the key path absolute.

## Claude Code

One command:

```bash
claude mcp add google-analytics -- uvx google-analytics-mcp
```

The `--` matters. Everything after it is passed to the server untouched, so a future flag on the server is not swallowed by the CLI parser.

To pass the two environment variables at registration time instead of exporting them:

```bash
claude mcp add --env GA4_PROPERTY_ID=123456789 --env GOOGLE_APPLICATION_CREDENTIALS=/absolute/path/to/key.json --transport stdio google-analytics -- uvx google-analytics-mcp
```

If you would rather hand it a full entry as JSON:

```bash
claude mcp add-json google-analytics '{"type":"stdio","command":"uvx","args":["google-analytics-mcp"],"env":{"GA4_PROPERTY_ID":"123456789","GOOGLE_APPLICATION_CREDENTIALS":"/absolute/path/to/key.json"}}'
```

Claude Code stores project-scoped servers in `.mcp.json` at the repository root, and user-scoped ones in `~/.claude.json`. Either is fine; project scope is the better default for a server that belongs to one analytics property.

## Claude Desktop

Open the config file. On macOS it is here:

```text
~/Library/Application Support/Claude/claude_desktop_config.json
```

On Windows it is `%APPDATA%\Claude\claude_desktop_config.json`. You can also reach it from the app: **Settings → Developer → Edit Config**.

Add the entry:

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

Save, then quit Claude Desktop completely and reopen it. A window close is not a restart; the server list is read at launch.

## Verify

Ask this in either surface:

```text
List my GA4 properties.
```

Success is `list_properties` returning rows with no setup error. An empty list means the credentials work but the service account has access to no properties — see [permissions](/iam/).

## Five questions you can ask Claude once connected

Once connected, Claude has direct access to the Google Analytics Data API with server-side totals and schema verification:

1. **Executive acquisition summary**:
   ```text
   Summarize our top 5 acquisition channels by sessions over the last 30 days. Report sessions, active users, and key event conversions.
   ```
2. **AI search traffic analysis**:
   ```text
   Show all traffic arriving from AI tools like ChatGPT, Claude, and Perplexity over the last 90 days. What is the month-over-month growth rate?
   ```
3. **Traffic drop investigation**:
   ```text
   Our organic traffic dropped this week compared to last week. Follow the traffic-diagnosis methodology to isolate which channel and pages dropped first.
   ```
4. **Landing page bounce audit**:
   ```text
   Which top landing pages have a bounce rate over 60% with at least 150 sessions this month?
   ```
5. **E-commerce funnel conversion**:
   ```text
   What was our overall checkout-to-purchase conversion rate across the last 60 days? Break down purchase revenue by channel.
   ```

## The two failures specific to Claude

**The server does not appear in Claude Code.** Run `uvx google-analytics-mcp` on its own in a terminal. If that fails, the CLI is not the problem and no amount of re-registering will fix it. Usually `uv` is missing from the PATH that the client inherits.

**Claude Desktop shows a setup error on launch.** The `env` block is outside the server object, or the credentials path is relative. Both variables must sit inside the same object as `command`, and the path must start with `/` on macOS or a drive letter on Windows.

> **Note:** the installer at `/setup/` writes both entries for you, which avoids the JSON entirely.

## Next

[Skills](/skills/) explains what to load before asking an analytical question. [Query shapes](/schema/) covers filter syntax, and [prompts](/google-analytics-ai-prompts/) provides 35 tested templates.
