# Connect OpenCode to Google Analytics 4 (Local stdio)

> Add the GA4 MCP server to OpenCode. The config is the furthest from the common shape: root key mcp, type local, command as an array, environment not env.

Canonical URL: https://ga4mcp.com/ga4-mcp-for-opencode/



OpenCode's MCP config is the furthest from the Claude Desktop baseline in this whole set. Four things are named differently, and a standard snippet will not load.

## The entry

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "google-analytics": {
      "type": "local",
      "command": ["uvx", "google-analytics-mcp"],
      "enabled": true,
      "environment": {
        "GA4_PROPERTY_ID": "123456789",
        "GOOGLE_APPLICATION_CREDENTIALS": "/absolute/path/to/key.json"
      }
    }
  }
}
```

Read the four differences carefully, because each one fails silently:

| Elsewhere | OpenCode |
|---|---|
| `mcpServers` | `mcp` |
| `"type": "stdio"` | `"type": "local"` |
| `"command": "uvx"` plus a separate `args` array | one `command` array holding the executable and its arguments |
| `env` | `environment` |

There is no `args` key. The executable and every argument live in the same array.

## Where the file lives

- **Global:** `~/.config/opencode/opencode.json`
- **Project:** `opencode.json` in the working directory

Both accept JSON or JSONC. A project file takes precedence over the global one.

## Verify

```text
List my GA4 properties.
```

Then confirm the server appears in OpenCode's MCP list. If it does not, check the `type` value first — `"stdio"` is valid everywhere else and invalid here.

## A note on multiple properties

OpenCode's project-scoped config makes it easy to run one entry per property, which is useful if you work across several sites. Each entry gets its own key and its own `GA4_PROPERTY_ID`:

```json
{
  "mcp": {
    "ga4-studio": {
      "type": "local",
      "command": ["uvx", "google-analytics-mcp"],
      "environment": { "GA4_PROPERTY_ID": "111111111", "GOOGLE_APPLICATION_CREDENTIALS": "/keys/studio.json" }
    },
    "ga4-client": {
      "type": "local",
      "command": ["uvx", "google-analytics-mcp"],
      "environment": { "GA4_PROPERTY_ID": "222222222", "GOOGLE_APPLICATION_CREDENTIALS": "/keys/client.json" }
    }
  }
}
```

The agent then sees two servers with the same tools and different data, which is usually clearer than one server whose property changes between sessions.

## Five questions you can ask in OpenCode

Once registered, you can ask OpenCode directly during agentic sessions:

1. **Traffic overview**:
   ```text
   What were our top 10 landing pages by sessions over the last 30 days?
   ```
2. **Channel performance**:
   ```text
   Compare sessions, engagement rate, and bounce rate across our acquisition channels for the past 60 days.
   ```
3. **AI referral tracking**:
   ```text
   How many sessions arrived from AI tools like ChatGPT, Claude, and Perplexity this month?
   ```
4. **Traffic change diagnosis**:
   ```text
   Diagnose why organic search traffic dropped between last week and this week. Which landing pages were most affected?
   ```
5. **E-commerce & revenue**:
   ```text
   What was our total purchase revenue and average order value (AOV) for the last 30 days grouped by country?
   ```

## Next

[Setup](/setup/) for the two values, [permissions](/iam/) when the first query returns a 403, and [prompts](/google-analytics-ai-prompts/) for 35 tested templates.
