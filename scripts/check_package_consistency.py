#!/usr/bin/env python3

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def fail(errors: list[str]) -> None:
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    sys.exit(1)


pyproject_text = read_text("pyproject.toml")
server_text = read_text("server.json")
readme_text = read_text("README.md")
template_text = read_text("claude-config-template.json")
pkg_info_path = ROOT / "google_analytics_mcp.egg-info" / "PKG-INFO"
pkg_info_text = pkg_info_path.read_text(encoding="utf-8") if pkg_info_path.exists() else ""
license_path = ROOT / "LICENSE"

version_match = re.search(r'^version = "([^"]+)"$', pyproject_text, re.MULTILINE)
if not version_match:
    fail(["Could not determine the project version from pyproject.toml"])
version = version_match.group(1)

errors: list[str] = []

if 'ga4-mcp-server = "ga4_mcp.server:main"' not in pyproject_text:
    errors.append("pyproject.toml must expose ga4-mcp-server = ga4_mcp.server:main")
if 'license = "Apache-2.0"' not in pyproject_text:
    errors.append('pyproject.toml must declare license = "Apache-2.0"')

server = json.loads(server_text)
if server.get("version") != version:
    errors.append(f"server.json version {server.get('version')} does not match pyproject.toml version {version}")

packages = server.get("packages", [])
if len(packages) != 1:
    errors.append("server.json must declare exactly one package entry")
else:
    package = packages[0]
    if package.get("identifier") != "google-analytics-mcp":
        errors.append("server.json package identifier must be google-analytics-mcp")
    if package.get("version") != version:
        errors.append(
            f"server.json package version {package.get('version')} does not match pyproject.toml version {version}"
        )
    expected_env_names = ["GOOGLE_APPLICATION_CREDENTIALS", "GA4_PROPERTY_ID"]
    actual_env_names = [item.get("name") for item in package.get("environment_variables", [])]
    if actual_env_names != expected_env_names:
        errors.append(
            "server.json environment variables must be GOOGLE_APPLICATION_CREDENTIALS followed by GA4_PROPERTY_ID"
        )

if "[describe what your server does]" in server.get("description", ""):
    errors.append("server.json still contains the placeholder description")
if not license_path.exists():
    errors.append("LICENSE file is missing")

banned_terms = ["ga4_mcp_server", "ga4_mcp_server.py"]
for relative_path, text in {
    "README.md": readme_text,
    "claude-config-template.json": template_text,
    "server.json": server_text,
    "RELEASING.md": read_text("RELEASING.md"),
}.items():
    for banned_term in banned_terms:
        if banned_term in text:
            errors.append(f"{relative_path} still references {banned_term}")

for required_term in ["ga4-mcp-server", "python -m ga4_mcp"]:
    if required_term not in readme_text:
        errors.append(f"README.md must document {required_term}")
if "Apache License 2.0" not in readme_text:
    errors.append("README.md must state Apache License 2.0")

template = json.loads(template_text)
template_server = template.get("mcpServers", {}).get("ga4-analytics", {})
if template_server.get("args") != ["-m", "ga4_mcp"]:
    errors.append("claude-config-template.json must launch the package with ['-m', 'ga4_mcp']")

if pkg_info_text:
    if f"Version: {version}" not in pkg_info_text:
        errors.append("google_analytics_mcp.egg-info/PKG-INFO version is out of date")
    for banned_term in banned_terms:
        if banned_term in pkg_info_text:
            errors.append(f"google_analytics_mcp.egg-info/PKG-INFO still references {banned_term}")

if errors:
    fail(errors)

print(f"Package consistency checks passed for version {version}.")
