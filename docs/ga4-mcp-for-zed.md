# Connect Zed Editor to Google Analytics 4 (Setup Guide)

> Add the GA4 MCP server to Zed. Zed calls them context servers, not mcpServers, and the entry lives in Zed's own settings file.

Canonical URL: https://ga4mcp.com/ga4-mcp-for-zed/



Zed calls MCP servers **context servers**, and that is not just naming. The root key in the settings file is `context_servers`, so a snippet from any other client will not load.

## Open the settings file

From the command palette, run:

```text
zed: open settings file
```

That opens `settings.json` for Zed. Add a top-level `context_servers` key.

## The entry

```json
{
  "context_servers": {
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

If your settings file already has content, add `context_servers` alongside it rather than replacing the file. Zed's settings hold the editor configuration and the AI configuration in the same document.

## What is different here

Three things, compared with the majority shape:

- The root key is `context_servers`, not `mcpServers`.
- There is no `type` field. Zed infers stdio from the presence of `command`.
- The file is Zed's single settings document, not a dedicated MCP file. A trailing comma anywhere in it breaks every setting, not just this one.

> **Tip:** if Zed shows no GA4 tools after saving, the settings file probably failed to parse. Zed reports a JSON error at the top of the editor for a malformed settings file, and a server that simply never appears is the symptom.

## Verify

Open the assistant panel and ask:

```text
List my GA4 properties.
```

The server appears in the context server list when it launched successfully. A listed server with no tools means the process started and exited — check `uvx google-analytics-mcp` in a terminal.

## Five questions you can ask in Zed

Once connected, ask the assistant panel directly:

1. **Top landing pages**:
   ```text
   What were our top 10 landing pages by sessions over the last 30 days?
   ```
2. **Channel performance**:
   ```text
   Compare sessions, engagement rate, and bounce rate across our acquisition channels for the past 60 days.
   ```
3. **AI referral traffic**:
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

[Install](/setup/) for the two values, [skills](/skills/) for what to load before asking an analytical question, and [prompts](/google-analytics-ai-prompts/) for 35 tested templates.
