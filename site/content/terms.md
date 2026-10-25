---
slug: /terms/
title: "Terms of use"
description: "MIT licensed, provided as-is, not affiliated with Google. Use it with a Google Analytics property you are entitled to read."
group: legal
nav: "Terms"
order: 2
---

# Terms of use

The GA4 MCP server is open source under the MIT licence. This page summarises what that means in practice; the licence text in the repository is the binding version.

## Licence

MIT. You can use, copy, modify, merge, publish, distribute, sublicense and sell copies. The copyright notice and permission notice must travel with the software.

## No warranty

The software is provided "as is", without warranty of any kind. The author is not liable for any claim, damage, or other liability arising from its use. Analytics numbers drive decisions, and a wrong number is expensive — verify anything that matters against the Analytics interface before you act on it.

## Not affiliated with Google

This is an independent community project by Surendran B, published under BuildItWithAI. It is not made, endorsed, or supported by Google. "Google Analytics" and "GA4" are trademarks of Google LLC and are used here only to describe what the software connects to.

## Your responsibilities

- Use credentials for a property you are entitled to read.
- Keep your own use within [Google's Analytics terms](https://marketingplatform.google.com/about/analytics/terms/us/) and the Data API terms.
- Do not use the server to work around an access control Google has put in place.

## Read-only by design

The server calls the Analytics Data API only. It cannot create, modify, or delete anything in your property, and it has no tools that attempt to. If a future release adds a write capability, it will be documented as one and off by default.

## Changes

The project is developed in the open. Breaking changes are noted in the repository changelog and in the release notes on GitHub.

## Contact

Issues and questions: [github.com/surendranb/google-analytics-mcp](https://github.com/surendranb/google-analytics-mcp).
