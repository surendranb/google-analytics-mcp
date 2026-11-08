# Connect VS Code & Copilot to Google Analytics 4

> Add GA4 MCP to VS Code Copilot agent mode. Includes the critical root key distinction between .vscode/mcp.json and .mcp.json plus sample queries.

Canonical URL: https://ga4mcp.com/ga4-mcp-for-vscode/



VS Code's agent mode runs MCP servers, and the configuration has one trap that catches almost everyone: the root key depends on which file you are editing.

## Pick the right file first

| File | Root key | Scope |
|---|---|---|
| `.vscode/mcp.json` | `servers` | This workspace |
| `.mcp.json` at the workspace root | `mcpServers` | This workspace, portable shape |
| `~/.copilot/mcp-config.json` | `mcpServers` | Every workspace for this user |

The two workspace files are not interchangeable. A config that works in one is silently ignored in the other, because the top-level key does not match what that file expects. This is the single most common reason a working snippet "does nothing" in VS Code.

## The workspace entry

In `.vscode/mcp.json`:

```json
{
  "servers": {
    "google-analytics": {
      "type": "stdio",
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

Note `servers`, and note that `type` is required here.

## The portable entry

In `.mcp.json` at the workspace root:

```json
{
  "mcpServers": {
    "google-analytics": {
      "type": "stdio",
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

Use this one if you want the same file to work in other clients that read `.mcp.json`.

## The CLI route

One command, no file editing:

```bash
code --add-mcp '{"name":"google-analytics","type":"stdio","command":"uvx","args":["google-analytics-mcp"],"env":{"GA4_PROPERTY_ID":"123456789","GOOGLE_APPLICATION_CREDENTIALS":"/absolute/path/to/key.json"}}'
```

Note that the CLI object uses `name` rather than a keyed object — it is a different shape from the file, not a copy of it.

## Environment variable substitution

`.vscode/mcp.json` can read values from your environment instead of hardcoding a credentials path:

```json
{
  "servers": {
    "google-analytics": {
      "type": "stdio",
      "command": "uvx",
      "args": ["google-analytics-mcp"],
      "env": {
        "GA4_PROPERTY_ID": "${env:GA4_PROPERTY_ID}",
        "GOOGLE_APPLICATION_CREDENTIALS": "${env:GOOGLE_APPLICATION_CREDENTIALS}"
      }
    }
  }
}
```

The `${env:NAME}` form is specific to `.vscode/mcp.json`. The portable `.mcp.json` uses `${NAME}` instead. Another reason not to move a block between the two files.

## If you use Cline or Roo Code

Those are extensions with their own MCP settings, not consumers of `.vscode/mcp.json`. The installer writes their entries separately, so the fastest path is:

```bash
curl -fsSL "https://ga4.builditwithai.xyz/install" | bash
```

## Verify

Open the Copilot Chat agent panel and ask for something that forces a tool call:

```text
List my GA4 properties.
```

Then check the server shows as running in the MCP servers view. A server that is listed but stopped is almost always a launch failure — run `uvx google-analytics-mcp` in a terminal to see the real error.

## Five questions you can ask in VS Code

Once connected, ask Copilot or Cline directly in your editor:

1. **Traffic summary**:
   ```text
   What were our top 10 landing pages by sessions over the last 30 days?
   ```
2. **Channel performance**:
   ```text
   Compare sessions, engagement rate, and bounce rate across our top 5 acquisition channels.
   ```
3. **AI search citations**:
   ```text
   How much referral traffic did we receive from ChatGPT, Claude, and Perplexity over the last 60 days?
   ```
4. **Traffic change diagnosis**:
   ```text
   Analyze our traffic drop over the last 14 days compared to the prior period. Which channel fell first?
   ```
5. **E-commerce metrics**:
   ```text
   What was our total purchase revenue and conversion rate by country for the past 30 days?
   ```

## Next

[Setup](/setup/) for credentials, [query shapes](/schema/) when the first query fails on a filter, and [prompts](/google-analytics-ai-prompts/) for 35 tested templates.
