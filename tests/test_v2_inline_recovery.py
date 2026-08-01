# SPDX-License-Identifier: Apache-2.0
"""MRTR inline recovery: when get_ga4_data is called on a born-broken config AND
the client can elicit, the missing property id is collected AT the failing call
(point of friction) — not bounced to a separate tool. Clients that cannot elicit
keep the proven born-broken brief unchanged. Run: python tests/test_v2_inline_recovery.py"""

import asyncio
import os
import sys

os.environ.setdefault("GA4_MCP_INTERNAL", "1")
os.environ.setdefault("DISABLE_TELEMETRY", "1")

import ga4_mcp.telemetry as t  # noqa: E402
import ga4_mcp.coordinator as coord  # noqa: E402
import ga4_mcp.server  # noqa: E402  metadata/reporting tools
import ga4_mcp.setup_flow  # noqa: E402  registers setup_ga4_access + run_inline_recovery

from mcp.client.client import Client  # noqa: E402
from mcp.types import Implementation, ElicitResult  # noqa: E402

_VALUE = "987654321"


async def _elicit_cb(context, params):
    return ElicitResult(action="accept", content={"property_id": _VALUE})


def _born_broken():
    os.environ.pop("GA4_PROPERTY_ID", None)
    os.environ.pop("GOOGLE_APPLICATION_CREDENTIALS", None)
    coord.SERVER_INIT_ERROR = "GA4_PROPERTY_ID not set."
    coord.SERVER_INIT_ERROR_CATEGORY = "InitError"


def _reset_identity():
    for k in t._RUNTIME_CLIENT:
        t._RUNTIME_CLIENT[k] = None


async def _call_get_ga4_data(elicitation):
    _reset_identity()
    _born_broken()
    kwargs = {}
    if elicitation:
        kwargs["elicitation_callback"] = _elicit_cb
    async with Client(
        coord.mcp, client_info=Implementation(name="claude-code", version="9.9.9"),
        mode="legacy", **kwargs,
    ) as client:
        res = await client.call_tool(
            "get_ga4_data", {"dimensions": ["date"], "metrics": ["totalUsers"]}
        )
        return res.content[0].text if res.content else ""


async def main():
    failures = []

    # 1) Elicitation-capable: recovery must trigger AT get_ga4_data — the elicited
    #    property id lands in the env (proof the prompt happened from the data tool).
    text = await _call_get_ga4_data(elicitation=True)
    if os.environ.get("GA4_PROPERTY_ID") != _VALUE:
        failures.append(
            f"inline recovery did not run from get_ga4_data "
            f"(env GA4_PROPERTY_ID={os.environ.get('GA4_PROPERTY_ID')!r}, expected {_VALUE!r})"
        )

    # 2) Non-elicitation client: unchanged proven behavior — the born-broken brief,
    #    NOT a silent failure or a crash.
    text2 = await _call_get_ga4_data(elicitation=False)
    if "GA4_PROPERTY_ID" not in text2 and "SETUP" not in text2 and "not set" not in text2:
        failures.append(f"non-elicitation client did not get the born-broken brief: {text2[:80]!r}")

    if failures:
        print("FAIL:")
        for f in failures:
            print("  -", f)
        sys.exit(1)
    print("PASS: inline recovery fires from get_ga4_data for elicit-capable clients; brief preserved otherwise")


if __name__ == "__main__":
    asyncio.run(main())
