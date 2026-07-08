# Telemetry

google-analytics-mcp collects anonymous usage telemetry to understand how the
server is discovered, installed, and used — and to improve it. This document
is the complete contract: what is collected, how it flows, how identity works,
and how to opt out. The entire pipeline is open source in this repository, so
every claim below is auditable.

## Principles

- **Free forever, open source forever.** Telemetry exists only to understand
  and improve the server — never for monetization or identification.
- **Anonymous by design.** No accounts, no fingerprinting, no hardware-derived
  identifiers. If a property could identify a person, it doesn't ship.
- **Opt-out is absolute.** When any opt-out flag is set, nothing is sent
  anywhere — not to our gateway, not to any analytics vendor.
- **IPs are never stored.** Events flow through our own gateway, which strips
  the IP before forwarding and stamps only a coarse country/continent.
- **Capture, then curate.** We keep raw signals and apply definitions at query
  time; classifications are added as tags, never used to silently drop data.

## Architecture

```
MCP server (this package)                Cloudflare Worker (workers/install-telemetry/)
  scrub PII → POST /e  ────────────────▶   strip IP, stamp coarse geo, tag  ──▶  PostHog (US)
```

The client contains no analytics vendor keys. The gateway source is in this
repository (`workers/install-telemetry/src/index.js`); the deployed worker
matches the published source.

## Identity contract (frozen)

- The only identity is a **random UUID** (`inst_…`) written to
  `~/.ga4_mcp/installation_id` on first run. It is never derived from
  hardware, usernames, or anything about you or your machine.
- **Delete the `~/.ga4_mcp/` folder to reset it entirely.**
- Each server process additionally gets a random per-session id (`sess_…`).
- This contract is versioned (`schema_version` on every event) and evolves
  additively only. Early versions of this package (≤2.5.0) used different,
  less careful identity schemes; this contract has been frozen since 2.5.1
  and will not change.

## Events

| Event | When | Purpose |
|---|---|---|
| `server_first_install` | first run ever | count installations |
| `package_download` | first run of each new version | install/upgrade funnel (PyPI has no install hooks) |
| `mcp_started` | server boot | version adoption, config health |
| `tool_executed` | each tool call | usage, latency, error taxonomy |
| `resource_read` | MCP resource read | usage |
| `install_intent` / `install_completed` | 1-line installer runs | installer funnel (fired by the worker, not this package) |

## Properties collected

- Package version, OS name, CPU architecture, Python version, virtualenv flag,
  timezone *offset*, install channel (uvx/pip/brew/npx/direct).
- Which MCP client is connecting (e.g. `claude_code`, `cursor`) — from the MCP
  handshake `clientInfo` or env-var *presence*. Env var **values** are never read.
- A coarse run context (`terminal | desktop | cloud | ci | headless`) derived
  from env-var presence only.
- Tool name, latency, success/error status, error category, row counts, and
  query *shape* (number of dimensions/metrics, whether a filter was used) —
  never the query values or results.
- Optional self-declared install source (`GA4_MCP_SOURCE`, set by install
  snippets) so we can tell which docs/directory a setup came from.
- Country and continent, stamped by the gateway from request metadata. The IP
  itself is discarded and never forwarded or stored.

**Never collected:** file paths or contents, environment variable values,
credentials, IP addresses, GA4 property IDs, dimension/metric values, report
data, prompts, usernames, emails. As defense in depth, every outgoing string
passes through a PII scrubber (`_scrub` in `ga4_mcp/telemetry.py`) that
redacts paths, emails, URLs, keys, and property IDs — and the gateway applies
tagging and IP-stripping on top.

## Opt out

Set any one of these before starting the server:

```
DISABLE_TELEMETRY=1
GA_MCP_TELEMETRY=false
DO_NOT_TRACK=1
NO_TELEMETRY=1
```

Precedence: **any disable flag wins over everything else.** The check happens
before any event is constructed; opted-out processes make no telemetry network
calls at all. The 1-line installer honors the same flags, and the gateway
additionally honors `DNT: 1` / `Sec-GPC: 1` headers. A one-time notice is
printed to stderr on first run, before anything is sent.

## Retention and correction

Events are retained in PostHog (US cloud). Because telemetry is anonymous we
cannot look up "your" data, but the identity file is yours: deleting
`~/.ga4_mcp/` unlinks all future events from past ones. If you believe
something identifying was ever captured despite the safeguards above, open an
issue — scrubbing rules ship in this repo and gateway-side rules can be
updated immediately, without waiting for a package release.
