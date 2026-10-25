---
slug: /ga4-mcp-for-goose/
title: "GA4 MCP for Goose"
description: "Add the GA4 MCP server to Goose. Goose uses YAML, calls the command cmd, and calls the environment block envs. All three differ from the usual shape."
group: clients
nav: "Goose"
order: 9
---

# GA4 MCP for Goose

Goose is the only client here that configures MCP servers in YAML, and it renames two fields you would otherwise expect. `cmd` instead of `command`, `envs` instead of `env`.

## The file

`~/.config/goose/config.yaml`

Add an `extensions` block. If the file already has one, add the server under it rather than creating a second `extensions` key.

```yaml
extensions:
  google-analytics:
    name: Google Analytics
    cmd: uvx
    args: [google-analytics-mcp]
    enabled: true
    envs:
      GA4_PROPERTY_ID: "123456789"
      GOOGLE_APPLICATION_CREDENTIALS: "/absolute/path/to/key.json"
    type: stdio
```

Every one of the five keys matters:

- `cmd` — the executable. `command` is silently ignored.
- `args` — a YAML flow sequence, so it stays on one line in brackets.
- `envs` — plural. `env` is silently ignored, and the server starts without credentials and fails at the first query.
- `type` — `stdio` for a local process.
- `enabled` — Goose writes `false` here when you disable an extension, and the server will not launch.

## One-off without the file

For a single session, Goose takes the command inline:

```bash
goose session --with-extension "GA4_PROPERTY_ID=123456789 GOOGLE_APPLICATION_CREDENTIALS=/absolute/path/to/key.json uvx google-analytics-mcp"
```

That form passes the environment through the shell rather than YAML, which makes it the fastest way to confirm the server works before you edit a config file.

## Verify

```text
List my GA4 properties.
```

Then check the extension list. Goose reports a broken extension on startup, which makes it friendlier than most clients here — you get an error instead of silence.

## Next

[Setup](/setup/) for the two values, [permissions](/iam/) when the first query returns a 403 rather than a setup error.
