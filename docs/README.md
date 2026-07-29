# Google Analytics MCP Server

Welcome to the **GA4 MCP (Model Context Protocol) Server**. This server bridges the gap between Claude/Cursor/Windsurf and Google Analytics 4, allowing AI agents to query your analytics data seamlessly.

## Quick Install (Universal Setup)

The easiest way to get started is our universal installer. Run this command in your terminal:

```bash
curl -fsSL "https://ga4.builditwithai.xyz/?src=setup" | bash
```

This installer detects your environment (macOS/Linux/Windows), checks for prerequisites (like `uv` or `pip`), installs the MCP server, and gives you configuration snippets you can paste directly into your MCP client (Claude Desktop, Cursor, or Windsurf).

## Why use this MCP?

GA4 can be incredibly complex. This server provides AI agents with specialized **tools** and **skills** to:
1. **Analyze Traffic**: Query dimension/metric pairs safely.
2. **Diagnose Drops**: Break down traffic drops by channel, geo, or custom dimensions.
3. **Understand Schema**: Look up metric definitions and allowed dimensions.

## Next Steps

- Proceed to the [Detailed Setup Guide](/setup.md)
- Learn about the [MCP Schema & Capabilities](/schema.md)
- Understand the [IAM Requirements](/iam.md)
