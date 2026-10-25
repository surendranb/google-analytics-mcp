---
slug: /privacy/
title: "Privacy — what the GA4 MCP server sends"
description: "The server runs locally, reads your Analytics data with your credentials, and sends anonymous usage counts you can switch off with one environment variable."
group: legal
nav: "Privacy"
order: 1
---

# Privacy

Short version: the server runs on your machine, talks to Google with your credentials, never writes to your property, and sends anonymous usage counts that you can turn off with one variable.

## What stays local

Your credentials, your service-account key, your property ID, and every report the server returns. Queries go from your machine to `analyticsdata.googleapis.com` and the rows come back to your machine. Nothing passes through studio infrastructure.

## What is sent

The server posts anonymous usage events to `ga4.builditwithai.xyz`, a Cloudflare Worker that forwards them to the studio's analytics. One event per lifecycle step, not per query.

Each event carries:

- a random installation identifier, generated on first run. It is not derived from your machine, your Google account, or your credentials
- the event name — for example `mcp_started`, `tool_executed`, `server_first_install`
- the tool name that ran, and whether it succeeded
- an error category on failure, such as `InitError` or `IAMError`
- duration in milliseconds
- the client name and version the server was launched by
- the server version

## What is not sent

- your credentials, tokens, or key file path
- your GA4 property ID — numeric IDs are redacted to `<id>` before sending
- report rows, metrics, dimensions, or anything the GA4 API returned
- file paths, email addresses, or hostnames

One caveat worth stating: `get_ga4_data` accepts an optional `intent` string that describes the question in plain English. That string is recorded with the tool event so the studio can tell which questions the server answers badly. If your intent text contains something you would not send, omit it. The field is optional and the tool works without it.

## Turning it off

Any one of these does it:

```bash
export DISABLE_TELEMETRY=1
```

```bash
export DO_NOT_TRACK=1
```

```bash
export NO_TELEMETRY=1
```

The check happens before any network call, so with one of them set the server makes no request to studio infrastructure at all. It still works exactly the same.

## Third parties

The site at ga4mcp.com uses Google Analytics and Microsoft Clarity to count page views. The MCP server itself does not load either, and neither is involved in a query.

## Contact

Open an issue at [github.com/surendranb/google-analytics-mcp](https://github.com/surendranb/google-analytics-mcp) for any question about this page.
