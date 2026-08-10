# SPDX-License-Identifier: Apache-2.0

"""Workflow prompts (channel standard S6): named, user-invokable analysis
workflows registered via the MCP prompt API. Each renders an authored,
quirk-aware instruction message that teaches the model this server's proven
sequence — discover names via search_schema, load the skill first, always pass
`intent`, read `totals` instead of summing rows. Pull-only: costs nothing until
a client fetches it. Telemetry: `prompt_used` (prompt_name, has_args) per fetch;
prompt argument VALUES are never sent."""

from .coordinator import mcp, send_telemetry


def _used(prompt_name: str, has_args: bool) -> None:
    try:
        send_telemetry("prompt_used", {"prompt_name": prompt_name, "has_args": bool(has_args)})
    except Exception:
        pass


@mcp.prompt(
    name="traffic-deep-dive",
    title="Traffic deep-dive",
    description="Full GA4 traffic review for a period: volume, channels, content, "
                "geo/devices — using the server's proven query patterns.",
)
def traffic_deep_dive(date_range: str | None = None) -> str:
    """Run a structured deep-dive on this GA4 property's traffic."""
    _used("traffic-deep-dive", has_args=bool(date_range))
    period = date_range or "the last 28 days (date_range_start='28daysAgo', date_range_end='yesterday')"
    return f"""Run a traffic deep-dive on my GA4 property for {period}.

Work this exact sequence — it avoids this server's known failure modes:

1. Load the methodology first: call search_skills('traffic-diagnosis') and
   search_skills('channel-acquisition'). Skills carry the proven dimension/metric
   combinations AND how to interpret the result — interpretation is the hard part.
2. Never hand-type dimension or metric names. Your training data likely predates
   this property's GA4 schema. Verify every name with search_schema('<keyword>')
   before querying.
3. Query with get_ga4_data, and ALWAYS pass the `intent` argument (a short plain-
   English description of what I'm trying to learn) on every call.
4. Read period figures from the `totals` block in the response — do NOT sum rows
   yourself. Rate metrics (bounceRate, engagement rates) are period-computed by GA4.
5. Respect scope rules: session dimensions pair with session metrics, event
   dimensions with event metrics, user dimensions with user metrics. On an
   'incompatible' error call search_skills('compatible-combinations').

Cover, in order: (a) overall volume and trend (totalUsers, newUsers, sessions by
date); (b) where traffic comes from (sessionDefaultChannelGroup, then top
sessionSource/sessionMedium); (c) what people consume (top pagePath by
screenPageViews and engagement); (d) who and where (country, deviceCategory).

Finish with what the numbers mean and what I should do about them — not just
tables. If any figure looks anomalous, say so plainly with the number, and name
the follow-up query that would confirm the cause."""


@mcp.prompt(
    name="find-whats-broken",
    title="Find what's broken",
    description="Triage a GA4 MCP setup or configuration problem: pinpoint the exact "
                "blocker (credentials, property ID, IAM, expired auth) and fix it.",
)
def find_whats_broken() -> str:
    """Diagnose and fix a broken GA4 MCP setup/configuration."""
    _used("find-whats-broken", has_args=False)
    return """My GA4 MCP setup may be broken — find what's wrong and help me fix it.

Follow this triage sequence:

1. Probe: call get_ga4_data with the smallest possible query
   (dimensions=['date'], metrics=['totalUsers'], date_range_start='yesterday',
   date_range_end='yesterday', intent='setup health check').
2. If it succeeds: setup is fine. Report the working state and stop.
3. If it returns a [SETUP BLOCKED] brief: read it fully. It states exactly what
   broke, why retrying won't help, and the numbered steps only I can perform.
   Relay the WHAT MUST HAPPEN steps to me verbatim — including any FORWARDABLE
   text (that is written for whoever administers my GA4/Google Cloud, and I may
   need to send it to them). Do NOT retry data tools until I confirm a change.
4. If the client supports interactive prompts, call setup_ga4_access — it
   collects the missing value from me directly and reconnects without a restart.
5. For depth on a specific failure family, call
   get_troubleshooting_guide(topic='setup') for env/config issues,
   topic='iam' for 403/permission errors (including expired-credentials
   re-auth), or topic='schema' for field-name errors.
6. After I confirm a fix, retry the step-1 probe once to verify, and tell me
   plainly whether GA4 access now works."""


@mcp.prompt(
    name="explain-my-traffic-drop",
    title="Explain my traffic drop",
    description="Diagnose why traffic fell: isolate the drop by channel, source, page, "
                "geo, and device using the traffic-diagnosis methodology.",
)
def explain_my_traffic_drop() -> str:
    """Diagnose the cause of a traffic drop in this GA4 property."""
    _used("explain-my-traffic-drop", has_args=False)
    return """My traffic dropped — find out why, using this server's diagnosis methodology.

Work this sequence:

1. Call search_skills('traffic-diagnosis') FIRST and follow its methodology — it
   is the proven playbook for exactly this question.
2. Establish the shape: pull daily totalUsers/sessions for a window wide enough
   to see before-and-after (e.g. 28 days). Read period figures from `totals`,
   not by summing rows. Identify when the drop started and whether it is a step
   or a slide.
3. Compare periods with TWO separate get_ga4_data calls (the API does not do
   multi-period in one call): the drop window vs the same-length window before it.
4. Isolate the dimension that carries the drop, one query per cut:
   sessionDefaultChannelGroup (which channel fell), then within the fallen
   channel sessionSource/sessionMedium, then pagePath (specific pages losing
   traffic), then country and deviceCategory. Verify every field name with
   search_schema before querying — do not hand-type names from memory.
5. If organic search fell, consider bot/spam artifacts too:
   search_skills('bot-traffic-detection').
6. Pass `intent` on every get_ga4_data call (e.g. intent='isolating which
   channel caused the traffic drop').

Report: when the drop started, which segment(s) carry it (with the numbers),
the most likely cause labeled as fact vs inference, and what I should do next —
fix something, keep watching, or accept it as normal variance."""
