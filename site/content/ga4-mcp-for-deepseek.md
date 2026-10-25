---
slug: /ga4-mcp-for-deepseek/
title: "GA4 MCP for DeepSeek Harness"
description: "Add the GA4 MCP server to DeepSeek Harness with one entry in your patch layer. Tools then appear as mcp__ga4__get_ga4_data inside the session."
group: clients
order: 13
nav: "DeepSeek Harness"
---

# GA4 MCP for DeepSeek Harness

DeepSeek Harness mounts MCP servers as config entries in its composed tree, not through a settings screen. One entry in your patch layer adds the server, and its tools appear inside the session.

## The entry

Add this to your patch layer:

```yaml
- id: mcp-ga4
  name: '@deepseek-ai/dsh-mcp-client'
  config:
    serverName: ga4
    transport: stdio
    command: uvx
    args: ['google-analytics-mcp']
    env:
      GA4_PROPERTY_ID: '123456789'
      GOOGLE_APPLICATION_CREDENTIALS: '/absolute/path/to/key.json'
```

The package is `@deepseek-ai/dsh-mcp-client`, scoped. There is an unscoped `dsh-mcp-client` on npm published by someone else as a name reservation — it is not the DeepSeek client and installing it gives you nothing.

## Where the patch goes

`DSH_HOME` defaults to `~/.dsh`. Two patch files are read, in this order:

- `$DSH_HOME/cordis.patch.yml` applies to every profile
- `$DSH_HOME/profiles/<profile>/cordis.patch.yml` applies to one

An explicit `--patch` overlay wins over both. If you only run one profile, the first file is the simplest place.

## Reading environment from the shell

The `env` block takes literals, and DeepSeek's config supports a JavaScript tag if you would rather not write the path into the file:

```yaml
    env:
      GA4_PROPERTY_ID: '123456789'
      GOOGLE_APPLICATION_CREDENTIALS: !!js process.env.GOOGLE_APPLICATION_CREDENTIALS
```

That keeps the credentials path out of a file you might commit. The property ID stays literal; it is not a secret.

## Tool names inside the session

Tools surface as `mcp__<serverName>__<tool>`. With `serverName: ga4` above, the agent sees:

```text
mcp__ga4__get_ga4_data
mcp__ga4__search_schema
mcp__ga4__list_properties
```

If you mount two properties, give them different `serverName` values and the tool lists stay separable.

## Verify

Check the composed config first, before you start a session:

```bash
dsh web --dump-config
```

The `mcp-ga4` entry and its resolved `env` should appear in the output. Then ask:

```text
List my GA4 properties.
```

## Next

[Install](/setup/) for the two values, [query shapes](/schema/) when a call fails on a filter rather than credentials.
