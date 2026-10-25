---
slug: /setup/
title: "Install GA4 MCP — setup guide"
description: "Install the Google Analytics 4 MCP server, connect a service account, and verify it works. Three install routes, the two values it needs, and the four errors you can hit."
group: start
nav: "Install"
order: 2
---

# Install GA4 MCP

This guide takes you from nothing to a working GA4 query inside your agent. It assumes you have a Google Analytics 4 property and a client that speaks MCP.

## What you need first

Three things, and only the first one is easy to get wrong.

**A GA4 property ID.** It is a number like `123456789`. You find it in Analytics under **Admin → Property details**. It is not the `G-XXXXXXXXXX` measurement ID, and it is not the numeric stream ID. Pasting the measurement ID is the single most common setup failure.

**A Google Cloud project** with the Analytics Data API enabled.

**Credentials,** picked in the next section. Either a service-account JSON key or the local `gcloud` login works.

## Step 1 — Install the server

Three routes. Pick one.

The installer is the one that also writes your client entry:

```bash
curl -fsSL "https://ga4.builditwithai.xyz/install" | bash
```

It detects your client, checks for `uv`, installs the package, and writes the MCP server entry. It covers Claude Desktop, Claude Code, Cursor, VS Code with Cline or Roo Code, Continue.dev, OpenCode, Windsurf, Zed and Google Antigravity.

If you would rather not run a script, use a runtime directly:

```bash
uvx google-analytics-mcp
```

```bash
npx -y @surendranb/google-analytics-mcp
```

Both are the same server. `uvx` is faster to start after the first run; `npx` needs Node already installed.

> **Note:** the installer writes the entry, not the credentials. You still set the two values in Step 2.

## Step 2 — Connect it to your property

The server reads two environment variables. Both belong inside the client's server entry, not in your shell profile, unless you launch the client from a shell that has them.

```bash
export GA4_PROPERTY_ID="123456789"
export GOOGLE_APPLICATION_CREDENTIALS="/absolute/path/to/service-account.json"
```

The credentials path must be absolute. A relative path resolves against whatever directory the client happens to start in, which is not the one you expect.

**If you use a service account,** create it in the Google Cloud console under **IAM & Admin → Service Accounts**, then **Keys → Add key → JSON**. That key file is what the path points at. The service account also has to be added to the GA4 property itself — that is a separate step and it is where most people stop. The [permissions guide](/iam/) walks through it.

**If you use `gcloud` instead,** run this once and skip the key file entirely:

```bash
gcloud auth application-default login
```

Then omit `GOOGLE_APPLICATION_CREDENTIALS`. The server picks up application default credentials.

> **Tip:** the property ID is numeric and has no prefix. If yours starts with `G-`, you have the measurement ID, and every query will fail with a permissions error that has nothing to do with permissions.

## Step 3 — Verify it actually works

Open your client and ask this exact question:

```text
List my GA4 properties.
```

You have succeeded when the agent calls `list_properties` and returns rows. A setup error at this point is one of four things, and the next section names all of them.

Then ask one question that exercises the analysis layer:

```text
Why did organic sessions drop in the last 7 days?
```

A working install loads the `traffic-diagnosis` skill, calls `get_ga4_data`, and answers with a `totals` block rather than a summary of daily rows.

## When it fails

| What you see | What it means | Where to go |
|---|---|---|
| `InitError` on startup | One or both environment variables are missing or outside the server's `env` block | [Setup errors](/setup/#when-it-fails) |
| `IAMError` or `403` | The service account is valid but was never added to the property | [Permissions guide](/iam/) |
| `ADCExpired` or `503` | The `gcloud` login expired | Run `gcloud auth application-default login` again |
| `400` invalid dimension or metric | The field name is a UA name or a guess | [Query shapes](/schema/) and `search_schema` |

The server also carries these fix paths inside the package, so an agent can resolve most of them without a browser:

```text
get_troubleshooting_guide(topic="setup" | "iam" | "schema")
```

## Or let the agent fix it

If the client supports prompts, `setup_ga4_access` collects the missing value and reconnects without a restart. That is usually faster than editing config by hand.

## Next

Read [your client's guide](/ga4-mcp-for-every-harness/) for the exact config shape it expects, since four of the eleven clients use a different key than the rest. Then read the [skills index](/skills/) to see what the agent can do once it is connected.
