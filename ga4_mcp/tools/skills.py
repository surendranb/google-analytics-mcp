# SPDX-License-Identifier: Apache-2.0

"""Remote skills library — analytical recipes for GA4 queries.

Skills live in the /skills directory of the public repo and are fetched at
call time. Adding a new skill requires no PyPI release — just a commit."""

import urllib.request
import urllib.error

from mcp.types import ToolAnnotations
from ga4_mcp.coordinator import mcp

_READ_ONLY_EXTERNAL = ToolAnnotations(readOnlyHint=True, openWorldHint=True)

_SKILLS_BASE = "https://raw.githubusercontent.com/surendranb/google-analytics-mcp/main/skills"
_TIMEOUT = 8


def _fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "google-analytics-mcp"})
    with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
        return resp.read().decode("utf-8")


@mcp.tool(annotations=_READ_ONLY_EXTERNAL)
def search_skills(query: str) -> str:
    """
    Search the GA4 skills library for analytical recipes and how-to guides.
    Skills are domain-specific instructions for common GA4 analysis patterns
    (bot traffic detection, AI referral analysis, ecommerce funnels, etc.).

    Call with a plain-English query to browse available skills. If you find
    a skill that matches, call this tool again with the exact skill name
    (e.g. "bot-traffic-detection") to get the full instructions.

    Args:
        query: What you're trying to analyse, OR an exact skill name to fetch
               its full content (e.g. "bot-traffic-detection").
    """
    try:
        index = _fetch(f"{_SKILLS_BASE}/index.md")
    except urllib.error.URLError as e:
        return f"Skills library unavailable: {e}. Proceed with your best judgement."
    except Exception as e:
        return f"Could not load skills index: {e}."

    # If the query looks like an exact skill slug, try fetching it directly
    slug = query.strip().lower().replace(" ", "-")
    if slug and all(c.isalnum() or c == "-" for c in slug):
        try:
            content = _fetch(f"{_SKILLS_BASE}/{slug}.md")
            return content
        except urllib.error.HTTPError as e:
            if e.code == 404:
                # Not an exact match — fall through to return index
                pass
            else:
                return f"Error fetching skill '{slug}': {e}"
        except Exception:
            pass

    return index
