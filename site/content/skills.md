---
slug: /skills/
title: "GA4 skills — sixteen analytical recipes for your agent"
description: "Sixteen playbooks that ship inside the GA4 MCP server. Each one fixes the dimensions, metrics and interpretation rules for one job, and loads only when the agent asks."
group: skills
nav: "All skills"
order: 1
---

# Skills

A skill is a short playbook that ships inside the package. The agent calls `search_skills` with a keyword, gets one back as markdown, and follows it. Nothing is fetched over the network, so it works with no API access and no credentials.

The point is to replace improvisation. Ask a general model why traffic dropped and it will invent a method. Ask it to run `traffic-diagnosis` and it runs the same six checks every time, in the same order, because the method is data instead of a guess.

## How the agent uses them

```text
search_skills("drop")
```

```text
search_skills("traffic-diagnosis")
```

An empty query returns the index. The full text of a skill arrives as markdown, and the agent uses the dimensions and metrics named inside it rather than choosing its own.

## When to load one

Before any question that involves interpretation, not just retrieval. "How many sessions yesterday" needs no skill. "Why did sessions drop", "which channel is worth more", "is this bot traffic" all do.

<!--SKILLS-->

## Next

[Query shapes](/schema/) covers the filter syntax these skills assume. If a skill names a metric your property does not have, `search_schema` will tell you what that property calls it.
