# SPDX-License-Identifier: Apache-2.0

"""Guards README's tool table against the server's actual registered tools.

Drift here is a documented-but-missing tool, which competitors cite. Parses the
"Tools & Capabilities" table and compares it to the in-process MCP registry, so a
renamed/removed/added tool fails this test until the README is updated.
"""

import asyncio
import re
from pathlib import Path

import ga4_mcp.tools.metadata  # noqa: F401
import ga4_mcp.tools.reporting  # noqa: F401
import ga4_mcp.tools.troubleshooting  # noqa: F401
import ga4_mcp.tools.skills  # noqa: F401
import ga4_mcp.setup_flow  # noqa: F401
from ga4_mcp.coordinator import mcp

README = Path(__file__).resolve().parent.parent / "README.md"


def _readme_tools() -> set[str]:
    text = README.read_text(encoding="utf-8")
    start = text.index("## \U0001f6e0")  # "## 🛠️ Tools & Capabilities"
    section = text[start:].split("\n---", 1)[0]
    return set(re.findall(r"^\|\s*`([a-z0-9_]+)`\s*\|", section, flags=re.MULTILINE))


def _registered_tools() -> set[str]:
    return {t.name for t in asyncio.run(mcp.list_tools())}


def test_readme_tool_table_matches_registry():
    documented, registered = _readme_tools(), _registered_tools()
    missing = registered - documented  # real tool not documented
    ghost = documented - registered  # documented tool that does not exist
    assert not ghost, f"README documents non-existent tools: {sorted(ghost)}"
    assert not missing, f"README omits registered tools: {sorted(missing)}"
