---
slug: /ga4-plugin-for-gemini/
title: "GA4 extension for Gemini CLI"
description: "The Gemini extension declares the GA4 MCP server and the two settings Gemini CLI prompts for, so the server installs without hand-edited JSON."
group: plugins
nav: "Gemini extension"
order: 3
---

# GA4 extension for Gemini CLI

Gemini CLI calls these bundles extensions. The manifest lives at the repository root as `gemini-extension.json`.

## What the manifest declares

```json
{
  "name": "google-analytics-mcp",
  "version": "2.11.1",
  "description": "Google Analytics 4 MCP server for real-time reporting, schema discovery, metric aggregation, and audience insights.",
  "author": "Surendran B",
  "homepage": "https://ga4.builditwithai.xyz",
  "repository": "https://github.com/surendranb/google-analytics-mcp",
  "license": "MIT",
  "mcp": {
    "command": "uvx",
    "args": ["google-analytics-mcp"]
  },
  "settings": [
    {
      "name": "GA4_PROPERTY_ID",
      "description": "Numeric GA4 property ID (e.g. 123456789)",
      "required": true,
      "type": "string"
    },
    {
      "name": "GOOGLE_APPLICATION_CREDENTIALS",
      "description": "Path to service account JSON key file",
      "required": true,
      "type": "string"
    }
  ]
}
```

The `settings` array is the part that matters. It tells Gemini CLI to ask for both values during install, so you never open `settings.json` by hand. Both are marked `required: true`, and the extension will not finish installing without them.

## Extension or settings file

Use the extension when you want Gemini CLI to prompt for the values. Use the [settings file](/ga4-mcp-for-gemini/) when you would rather write them yourself, or when you need to set `trust` and `timeout` — the extension manifest has no equivalent for those.

## Next

[Gemini CLI guide](/ga4-mcp-for-gemini/) for the full settings shape, or [plugins overview](/ga4-plugins/).
