# SPDX-License-Identifier: Apache-2.0

"""Remote skills library — analytical recipes for GA4 queries.

Skills live in the /skills directory of the public repo and are fetched at
call time. Adding a new skill requires no PyPI release — just a commit."""

import urllib.request
import urllib.error

from mcp.types import ToolAnnotations
from mcp.server.fastmcp import Context
from ga4_mcp.coordinator import mcp, fire_skill_tip

_READ_ONLY_EXTERNAL = ToolAnnotations(readOnlyHint=True, openWorldHint=True)

_SKILLS_BASE = "https://raw.githubusercontent.com/surendranb/google-analytics-mcp/main/skills"
_TIMEOUT = 8


def _fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "google-analytics-mcp"})
    with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
        return resp.read().decode("utf-8")


@mcp.tool(annotations=_READ_ONLY_EXTERNAL)
def search_skills(query: str, ctx: Context = None) -> str:
    """
    Fetch analytical recipes and how-to guides from the GA4 skills library.

    Skills are domain-specific playbooks for common GA4 analysis patterns —
    exact dimensions, metrics, filters, and interpretation logic for each use case.
    Call this BEFORE querying get_ga4_data for any domain-specific analysis.

    Available skills: traffic-diagnosis, attribution-scope, channel-acquisition,
    content-performance, geo-device-segmentation, ecommerce-analysis,
    ai-referral-analysis, bot-traffic-detection, common-metric-names,
    filter-structures, custom-dimensions, compatible-combinations, ua-to-ga4,
    date-ranges, ga4-limitations.

    Usage:
    - search_skills("")              → returns full index of all skills
    - search_skills("ecommerce")     → returns the ecommerce-analysis skill
    - search_skills("ua-to-ga4")     → returns the UA→GA4 field name mapping

    Args:
        query: A skill name (exact slug) or empty string to browse the full index.
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
            fire_skill_tip(ctx, f"💡 Skill '{slug}' loaded. Follow the methodology above, then call get_ga4_data with the exact dimensions and metrics specified in the skill.", skill=slug, trigger="skill_fetched", tool_name="search_skills")
            return content
        except urllib.error.HTTPError as e:
            if e.code == 404:
                pass  # Not an exact match — fall through to return index
            else:
                return f"Error fetching skill '{slug}': {e}"
        except Exception:
            pass

    fire_skill_tip(ctx, "💡 Skills index loaded. Pick a skill name from the table and call search_skills('<name>') again to get the full methodology. Skills give you proven query patterns and interpretation guidance.", skill=None, trigger="skill_index", tool_name="search_skills")
    return index
