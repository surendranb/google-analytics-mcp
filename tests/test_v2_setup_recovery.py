# SPDX-License-Identifier: Apache-2.0
"""The elicitation-based setup recovery (setup_ga4_access) is the 'ask the user
for the missing config' capability. MCP 2.0 replaced server-initiated
elicitation with multi-round-trip requests; the SDK maps ctx.elicit onto it, so
this flow must still collect a value from the user and act on it. Real in-memory
client drives the elicitation. Run: python tests/test_v2_setup_recovery.py"""

import asyncio
import os
import sys

os.environ.setdefault("GA4_MCP_INTERNAL", "1")
os.environ.setdefault("DISABLE_TELEMETRY", "1")
# Born-broken: missing property id, no creds.
os.environ.pop("GA4_PROPERTY_ID", None)
os.environ.pop("GOOGLE_APPLICATION_CREDENTIALS", None)

import ga4_mcp.coordinator as coord  # noqa: E402
import ga4_mcp.server  # noqa: E402  imports metadata/reporting tools
import ga4_mcp.setup_flow  # noqa: E402  registers setup_ga4_access (main() imports it lazily)

from mcp.client.client import Client  # noqa: E402
from mcp.types import Implementation, ElicitResult  # noqa: E402

_COLLECTED_VALUE = "123456789"


async def _elicit_cb(context, params):
    # Accept every elicitation (form or url) with the property id.
    return ElicitResult(action="accept", content={"property_id": _COLLECTED_VALUE})


async def main():
    failures = []
    # Simulate the born-broken state the boot sequence sets.
    coord.SERVER_INIT_ERROR = "GA4_PROPERTY_ID not set."
    coord.SERVER_INIT_ERROR_CATEGORY = "InitError"

    async with Client(
        coord.mcp,
        client_info=Implementation(name="claude-code", version="9.9.9"),
        mode="legacy",
        elicitation_callback=_elicit_cb,
    ) as client:
        res = await client.call_tool("setup_ga4_access", {})
        text = res.content[0].text if res.content else ""

    # The elicitation must have collected the value and applied it to the env —
    # proof the ask-the-user path works under v2's MRTR-backed elicitation.
    if os.environ.get("GA4_PROPERTY_ID") != _COLLECTED_VALUE:
        failures.append(
            f"elicitation did not apply the collected property id "
            f"(env GA4_PROPERTY_ID={os.environ.get('GA4_PROPERTY_ID')!r})"
        )
    # It should return a coherent string to the model (not crash).
    if not text or "setup" not in text.lower() and "connect" not in text.lower():
        failures.append(f"unexpected recovery result text: {text!r}")

    if failures:
        print("FAIL:")
        for f in failures:
            print("  -", f)
        sys.exit(1)
    print("PASS: v2 elicitation recovery collects the missing property id and acts on it")


if __name__ == "__main__":
    asyncio.run(main())
