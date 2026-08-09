# SPDX-License-Identifier: Apache-2.0
"""Integration test: client identity + tools_listed telemetry must survive the
MCP v2 (stateless, 2026-07-28) migration. Real in-memory client<->server, no
mocks. Covers both eras: legacy initialize-handshake clients (today's fleet)
and 2026 per-request-meta clients. Run: python tests/test_v2_telemetry.py

Intercepts at the network boundary (urlopen) so the real send_telemetry
enrichment runs — mcp_client_name / mcp_protocol_version are added there, not by
the caller, so patching send_telemetry itself would hide the very fields we
assert on."""

import asyncio
import json
import os
import sys

os.environ.setdefault("GA4_MCP_INTERNAL", "1")

import ga4_mcp.telemetry as t  # noqa: E402

# Enable telemetry regardless of the ambient env, and capture the outbound
# payloads instead of sending them over the wire.
t.TELEMETRY_DISABLED = False
_PAYLOADS = []


class _FakeResp:
    def read(self):
        return b""

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _fake_urlopen(req, *a, **k):
    try:
        _PAYLOADS.append(json.loads(req.data.decode("utf-8")))
    except Exception:
        pass
    return _FakeResp()


t.urllib.request.urlopen = _fake_urlopen

import ga4_mcp.coordinator as c  # noqa: E402
import ga4_mcp.server  # noqa: E402  registers tools
from mcp.client.client import Client  # noqa: E402
from mcp.types import Implementation  # noqa: E402


async def _run_session(client_name, mode):
    _PAYLOADS.clear()
    for k in t._RUNTIME_CLIENT:
        t._RUNTIME_CLIENT[k] = None
    c._TOOLS_LISTED["fired"] = False
    c._DISCOVERED["fired"] = False
    async with Client(
        c.mcp, client_info=Implementation(name=client_name, version="9.9.9"), mode=mode
    ) as client:
        await client.list_tools()
        try:
            await client.call_tool("list_dimension_categories", {})
        except Exception:
            pass
    t._drain_pending_sends(3.0)
    return [p for p in _PAYLOADS]


def _check(era, client_name, payloads):
    failures = []
    events = [(p.get("event"), p.get("properties", {})) for p in payloads]
    tool_events = [pr for (e, pr) in events if e == "tool_executed"]
    listed_events = [pr for (e, pr) in events if e == "tools_listed"]

    if not tool_events:
        failures.append(f"[{era}] no tool_executed event fired")
    else:
        names = {pr.get("mcp_client_name") for pr in tool_events}
        if client_name not in names:
            failures.append(
                f"[{era}] mcp_client_name not captured on tool_executed "
                f"(got {names!r}, expected {client_name!r})"
            )
        if not any(pr.get("mcp_protocol_version") for pr in tool_events):
            failures.append(f"[{era}] mcp_protocol_version not captured")
        for pr in tool_events:
            if not (isinstance(pr.get("result_chars"), int) and pr["result_chars"] > 0):
                failures.append(f"[{era}] result_chars missing or not a positive int on tool_executed")
                break
        if not any(pr.get("mcp_request_id") for pr in tool_events):
            failures.append(f"[{era}] mcp_request_id not captured on tool_executed")

    if not listed_events:
        failures.append(f"[{era}] tools_listed event never fired")

    # Envelope contract (Client Contract v2): schema_version 2, legacy fields gone.
    for p in payloads:
        pr = p.get("properties", {})
        if pr.get("schema_version") != 2:
            failures.append(f"[{era}] schema_version != 2 on {p.get('event')!r}")
        if "launch_channel" in pr:
            failures.append(f"[{era}] legacy launch_channel still sent on {p.get('event')!r}")
        if "has_ever_worked" in pr:
            failures.append(f"[{era}] legacy has_ever_worked still sent on {p.get('event')!r}")
    return failures


def _check_session_end(payloads):
    """session_end shape (Standard §3): duration, ordered tool names, counts, total."""
    failures = []
    ends = [p.get("properties", {}) for p in payloads if p.get("event") == "session_end"]
    if not ends:
        return ["session_end event never fired"]
    pr = ends[0]
    if not isinstance(pr.get("session_duration_s"), int):
        failures.append("session_end.session_duration_s missing or not an int")
    seq = pr.get("tool_sequence")
    if not (isinstance(seq, list) and "list_dimension_categories" in seq and len(seq) <= 100):
        failures.append(f"session_end.tool_sequence wrong shape: {seq!r}")
    counts = pr.get("tool_counts")
    if not (isinstance(counts, dict) and counts.get("list_dimension_categories", 0) >= 1):
        failures.append(f"session_end.tool_counts wrong shape: {counts!r}")
    if pr.get("calls_total") != sum((counts or {}).values()):
        failures.append(f"session_end.calls_total != sum(tool_counts): {pr.get('calls_total')!r}")
    return failures


async def main():
    all_failures = []
    for era, mode in (("legacy", "legacy"), ("2026-era", "auto")):
        payloads = await _run_session("claude-code", mode)
        all_failures += _check(era, "claude-code", payloads)

    # session_end fires via atexit in production (LIFO, before the sender drain);
    # here we invoke the emitter directly against the same network intercept.
    _PAYLOADS.clear()
    t._emit_session_end()
    t._drain_pending_sends(3.0)
    all_failures += _check_session_end(list(_PAYLOADS))

    if all_failures:
        print("FAIL:")
        for f in all_failures:
            print("  -", f)
        sys.exit(1)
    print("PASS: identity + tools_listed + protocol_version captured in both eras; "
          "v2 envelope (schema_version 2, legacy fields dropped) + result_chars + "
          "mcp_request_id + session_end shape verified")


if __name__ == "__main__":
    asyncio.run(main())
