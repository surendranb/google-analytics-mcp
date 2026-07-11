# SPDX-License-Identifier: Apache-2.0

"""Interactive setup recovery. When config is broken, uses MCP elicitation to
collect the missing value (or confirm a terminal fix) and re-initialize in
session, avoiding a client restart. Falls back to guided text if the client
doesn't support elicitation."""

import os
import uuid

from pydantic import BaseModel, Field
from mcp.server.fastmcp import Context

from .coordinator import mcp
from .telemetry import send_telemetry, client_supports_url_elicitation
from . import coordinator

# Pages we own or that land the user exactly where the fix happens. URL-mode
# elicitation opens these at the client; no OAuth, no secrets — guided navigation.
_GA4_ADMIN_URL = "https://analytics.google.com/analytics/web/#/admin"
_SETUP_PAGE_URL = "https://ga4.builditwithai.xyz/setup"


async def _offer_page(ctx, message, url, branch):
    """URL-mode elicitation: ask the client to open a helpful page before we
    collect the value. No-op on clients without URL elicitation (falls through
    to the existing form/text). Records whether the offer was accepted."""
    if not client_supports_url_elicitation():
        return None
    try:
        r = await ctx.request_context.session.elicit_url(
            message=message,
            url=url,
            elicitation_id=f"setup_{uuid.uuid4().hex[:12]}",
            related_request_id=ctx.request_id,
        )
        action = str(getattr(r, "action", None))
        send_telemetry("setup_flow", {
            "flow_branch": branch, "flow_outcome": "url_offered",
            "url_elicit_action": action,
            "error_category_at_entry": coordinator.SERVER_INIT_ERROR_CATEGORY,
        })
        return action
    except Exception:
        return None


class _PropertyId(BaseModel):
    property_id: str = Field(description="Your numeric GA4 Property ID, e.g. 123456789")


class _CredentialsPath(BaseModel):
    credentials_path: str = Field(description="Absolute path to your service-account JSON key")


class _Confirm(BaseModel):
    done: bool = Field(description="Set true once you have completed the step")


def _persist_hint(var, value):
    return (f"This is set for the current session only. To make it permanent, add "
            f'"{var}": "{value}" to the env block of this server in your MCP client config.')


def _emit_flow(branch, action, outcome, reinit_category=None):
    """Recovery-funnel telemetry: which branch ran, what the user chose, how it
    ended. Outcomes only — elicited values are never sent."""
    send_telemetry("setup_flow", {
        "flow_branch": branch,
        "elicit_action": str(action) if action is not None else None,
        "flow_outcome": outcome,
        "reinit_category": reinit_category,
        "error_category_at_entry": coordinator.SERVER_INIT_ERROR_CATEGORY,
    })


@mcp.tool()
async def setup_ga4_access(ctx: Context) -> str:
    """
    Interactively fix a broken GA4 MCP setup (missing property ID, missing or
    expired credentials, or missing GA4 access) by asking the user for the
    needed input through the client, then re-initializing without a restart.
    Call this whenever a configuration or authentication error is reported.
    """
    if not coordinator.SERVER_INIT_ERROR:
        _emit_flow("none_needed", None, "already_ok")
        return "GA4 access is already configured and working. No setup needed."

    category = coordinator.SERVER_INIT_ERROR_CATEGORY
    creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    prop = os.getenv("GA4_PROPERTY_ID")
    branch = "other"

    try:
        # Missing Property ID — offer to open GA4 Admin, then collect it.
        if not prop:
            branch = "property_id"
            await _offer_page(
                ctx,
                "I'll open Google Analytics Admin so you can copy your Property ID "
                "(Admin > Property details, a numeric id like 123456789).",
                _GA4_ADMIN_URL, "property_id_open_admin",
            )
            r = await ctx.elicit(
                "What is your GA4 Property ID? Find it at analytics.google.com > Admin > "
                "Property details (a numeric id like 123456789).",
                _PropertyId,
            )
            if r.action != "accept" or not r.data:
                _emit_flow(branch, r.action, "paused")
                return "Setup paused — no Property ID provided. Re-run setup_ga4_access when ready."
            os.environ["GA4_PROPERTY_ID"] = r.data.property_id.strip()

        # Missing/invalid credentials path — offer the setup page, then collect.
        elif not creds or (creds and not os.path.exists(creds)):
            branch = "credentials"
            await _offer_page(
                ctx,
                "I'll open the setup guide — it walks through creating a service-account "
                "key or using gcloud, with the exact steps.",
                _SETUP_PAGE_URL, "credentials_open_setup",
            )
            r = await ctx.elicit(
                "Where is your Google service-account JSON key on this machine? "
                "Paste its absolute path. (Or, to use gcloud instead, run "
                "'gcloud auth application-default login' in a terminal and then answer 'adc'.)",
                _CredentialsPath,
            )
            if r.action != "accept" or not r.data:
                _emit_flow(branch, r.action, "paused")
                return "Setup paused — no credentials path provided. Re-run setup_ga4_access when ready."
            path = r.data.credentials_path.strip()
            if path.lower() != "adc":
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = path

        # Expired credentials (ADC) — confirm the terminal fix.
        elif category == "ADCExpired":
            branch = "adc_expired"
            r = await ctx.elicit(
                "Your Google credentials have expired. In a terminal run:\n\n"
                "    gcloud auth application-default login\n\n"
                "Set 'done' to true once it completes and I'll reconnect.",
                _Confirm,
            )
            if r.action != "accept" or not r.data or not r.data.done:
                _emit_flow(branch, r.action, "paused")
                return "Setup paused — run 'gcloud auth application-default login', then re-run setup_ga4_access."

        # Missing GA4 access (IAM) — confirm the console fix.
        elif category == "IAMError":
            branch = "iam"
            sa_hint = "the service account email (the client_email inside your JSON key)"
            r = await ctx.elicit(
                "The service account lacks access to this GA4 property. At analytics.google.com > "
                f"Admin > Property Access Management, add {sa_hint} with the Viewer role. "
                "Set 'done' to true once added and I'll reconnect.",
                _Confirm,
            )
            if r.action != "accept" or not r.data or not r.data.done:
                _emit_flow(branch, r.action, "paused")
                return "Setup paused — grant Viewer access, then re-run setup_ga4_access."

        else:
            # Other init error — confirm and retry.
            branch = "other"
            r = await ctx.elicit(
                f"Setup issue: {coordinator.SERVER_INIT_ERROR}. Fix it, then set 'done' to true to retry.",
                _Confirm,
            )
            if r.action != "accept" or not r.data or not r.data.done:
                _emit_flow(branch, r.action, "paused")
                return "Setup paused. Re-run setup_ga4_access after fixing the issue above."

    except Exception:
        # Client lacks elicitation — fall back to guided text.
        _emit_flow(branch, None, "elicit_unsupported")
        return (f"This client can't prompt interactively. To fix setup manually: {coordinator.SERVER_INIT_ERROR} "
                "See https://ga4.builditwithai.xyz/setup, then restart your MCP client.")

    # Retry init with the updated environment.
    ok, cat, detail = coordinator.reinitialize()
    if ok:
        _emit_flow(branch, "accept", "fixed", cat)
        msg = "✅ GA4 access is now working — you can query your analytics. "
        if os.getenv("GA4_PROPERTY_ID") and cat != "adc":
            msg += _persist_hint("GA4_PROPERTY_ID", os.getenv("GA4_PROPERTY_ID"))
        return msg
    _emit_flow(branch, "accept", "still_broken", cat)
    return (f"Still not connected ({cat}): {detail}. Re-run setup_ga4_access to try again, "
            "or see https://ga4.builditwithai.xyz/setup.")
