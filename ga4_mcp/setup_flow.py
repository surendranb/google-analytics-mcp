# SPDX-License-Identifier: Apache-2.0

"""Interactive setup recovery. When config is broken, uses MCP elicitation to
collect the missing value (or confirm a terminal fix) and re-initialize in
session, avoiding a client restart. Falls back to guided text if the client
doesn't support elicitation."""

import os

from pydantic import BaseModel, Field
from mcp.server.fastmcp import Context

from .coordinator import mcp
from . import coordinator


class _PropertyId(BaseModel):
    property_id: str = Field(description="Your numeric GA4 Property ID, e.g. 123456789")


class _CredentialsPath(BaseModel):
    credentials_path: str = Field(description="Absolute path to your service-account JSON key")


class _Confirm(BaseModel):
    done: bool = Field(description="Set true once you have completed the step")


def _persist_hint(var, value):
    return (f"This is set for the current session only. To make it permanent, add "
            f'"{var}": "{value}" to the env block of this server in your MCP client config.')


@mcp.tool()
async def setup_ga4_access(ctx: Context) -> str:
    """
    Interactively fix a broken GA4 MCP setup (missing property ID, missing or
    expired credentials, or missing GA4 access) by asking the user for the
    needed input through the client, then re-initializing without a restart.
    Call this whenever a configuration or authentication error is reported.
    """
    if not coordinator.SERVER_INIT_ERROR:
        return "GA4 access is already configured and working. No setup needed."

    category = coordinator.SERVER_INIT_ERROR_CATEGORY
    creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    prop = os.getenv("GA4_PROPERTY_ID")

    try:
        # Missing Property ID — collect it.
        if not prop:
            r = await ctx.elicit(
                "What is your GA4 Property ID? Find it at analytics.google.com > Admin > "
                "Property details (a numeric id like 123456789).",
                _PropertyId,
            )
            if r.action != "accept" or not r.data:
                return "Setup paused — no Property ID provided. Re-run setup_ga4_access when ready."
            os.environ["GA4_PROPERTY_ID"] = r.data.property_id.strip()

        # Missing/invalid credentials path — collect it.
        elif not creds or (creds and not os.path.exists(creds)):
            r = await ctx.elicit(
                "Where is your Google service-account JSON key on this machine? "
                "Paste its absolute path. (Or, to use gcloud instead, run "
                "'gcloud auth application-default login' in a terminal and then answer 'adc'.)",
                _CredentialsPath,
            )
            if r.action != "accept" or not r.data:
                return "Setup paused — no credentials path provided. Re-run setup_ga4_access when ready."
            path = r.data.credentials_path.strip()
            if path.lower() != "adc":
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = path

        # Expired credentials (ADC) — confirm the terminal fix.
        elif category == "ADCExpired":
            r = await ctx.elicit(
                "Your Google credentials have expired. In a terminal run:\n\n"
                "    gcloud auth application-default login\n\n"
                "Set 'done' to true once it completes and I'll reconnect.",
                _Confirm,
            )
            if r.action != "accept" or not r.data or not r.data.done:
                return "Setup paused — run 'gcloud auth application-default login', then re-run setup_ga4_access."

        # Missing GA4 access (IAM) — confirm the console fix.
        elif category == "IAMError":
            sa_hint = "the service account email (the client_email inside your JSON key)"
            r = await ctx.elicit(
                "The service account lacks access to this GA4 property. At analytics.google.com > "
                f"Admin > Property Access Management, add {sa_hint} with the Viewer role. "
                "Set 'done' to true once added and I'll reconnect.",
                _Confirm,
            )
            if r.action != "accept" or not r.data or not r.data.done:
                return "Setup paused — grant Viewer access, then re-run setup_ga4_access."

        else:
            # Other init error — confirm and retry.
            r = await ctx.elicit(
                f"Setup issue: {coordinator.SERVER_INIT_ERROR}. Fix it, then set 'done' to true to retry.",
                _Confirm,
            )
            if r.action != "accept" or not r.data or not r.data.done:
                return "Setup paused. Re-run setup_ga4_access after fixing the issue above."

    except Exception:
        # Client lacks elicitation — fall back to guided text.
        return (f"This client can't prompt interactively. To fix setup manually: {coordinator.SERVER_INIT_ERROR} "
                "See https://ga4.builditwithai.xyz/setup, then restart your MCP client.")

    # Retry init with the updated environment.
    ok, cat, detail = coordinator.reinitialize()
    if ok:
        msg = "✅ GA4 access is now working — you can query your analytics. "
        if os.getenv("GA4_PROPERTY_ID") and cat != "adc":
            msg += _persist_hint("GA4_PROPERTY_ID", os.getenv("GA4_PROPERTY_ID"))
        return msg
    return (f"Still not connected ({cat}): {detail}. Re-run setup_ga4_access to try again, "
            "or see https://ga4.builditwithai.xyz/setup.")
