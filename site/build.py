#!/usr/bin/env python3
"""Pre-render ga4mcp.com into site/dist/ — every URL ships full HTML, no client-side rendering.

Build (markdown is the only third-party dep; fetched by uv if not already cached):

    uv run --no-project --with markdown python3 site/build.py

--no-project keeps uv from syncing the package env or rewriting uv.lock, so the
only thing this command touches is site/dist/.

Source of truth (site/dist/ is generated and committed, never hand-edited):

    docs/setup.md, docs/schema.md, docs/iam.md        -> /setup/ /schema/ /iam/
    skills/<slug>/SKILL.md  (15, YAML head stripped)  -> /skills/<slug>/
    skills/index.md                                   -> /skills/
    docs/privacy.html, docs/terms.html                -> /privacy/ /terms/ (text frozen)
    site/meta.json                                    -> per-URL title + description
    site/src-assets/                                  -> og.png, favicons, mark, font files
    site/style.css                                    -> /assets/style.css

The home page copy is the CMO landing draft of 2026-09-21 (memory/drafts/ga4mcp-revamp,
claim ledger included), held in this script as data so the rendered page and its markdown
twin cannot drift apart.

Every content page also emits a markdown twin at <url>index.md, advertised with
<link rel="alternate" type="text/markdown"> and served by the edge function on
Accept: text/markdown (netlify/edge-functions/negotiate.ts).

Machine surfaces: llms.txt, llms-full.txt, robots.txt, sitemap.xml, _redirects,
404.html, data/tools.json (11 tools from the package), data/skills.json.

The build fails (exit 1) on: a broken internal link, a missing or empty twin, a
page with no H1 without JS, a privacy/terms word change, a banned token, a
title over 60 chars, a description over 155 chars, or a sitemap entry with no page.
"""

from __future__ import annotations

import html
import json
import re
import shutil
import sys
from datetime import date
from html.parser import HTMLParser
from pathlib import Path

try:
    import markdown as mdlib
except ImportError:  # pragma: no cover - build-time guard
    sys.exit("markdown is missing. Run:  uv run --no-project --with markdown python3 site/build.py")

ROOT = Path(__file__).resolve().parents[1]
SITE_DIR = Path(__file__).resolve().parent
DIST = SITE_DIR / "dist"
ASSETS_OUT = DIST / "assets"
SRC_ASSETS = SITE_DIR / "src-assets"
DOCS = ROOT / "docs"
SKILLS_SRC = ROOT / "skills"
STYLE_SRC = SITE_DIR / "style.css"

SITE = "https://ga4mcp.com"
VERSION = "2.11.4"
REPO = "https://github.com/surendranb/google-analytics-mcp"
PYPI = "https://pypi.org/project/google-analytics-mcp/"
NPM = "https://www.npmjs.com/package/@surendranb/google-analytics-mcp"
INSTALL = "https://ga4.builditwithai.xyz/install"
GOOGLE_SERVER = "https://github.com/googleanalytics/google-analytics-mcp"
YEAR = 2026
BUILD_DATE = date.today().isoformat()

BANNED = ["balanced approach", "comprehensive", "seamless", "robust", "leverage", "utilize", "holistic"]
FROZEN_URLS = ("/privacy/", "/terms/")
# Served by site/dist/_redirects (and the edge function), not by a file on disk.
REDIRECT_ONLY = {"/install"}

TOOLS_COUNT = 11
SKILLS_COUNT = 15

CHIPS = ["v2.11.4", "MIT", "PyPI + npm + one-line installer", "Not affiliated with Google"]

CLIENTS = ["Claude Desktop", "Claude Code", "Cursor", "VS Code (Cline, Roo Code)", "Continue.dev",
           "Windsurf", "Zed", "Google Antigravity", "OpenCode", "Gemini CLI (extension in the repo)"]

WHY = [
    ("Field names checked against your property",
     "search_schema and the category browsers read a schema fetched from your own GA4 property at boot. "
     "get_ga4_data checks every dimension and metric before the API call, so an invalid name comes back "
     "with the fix instead of a raw 400."),
    ("15 analytical skills, loaded on request",
     "Traffic drops, channel acquisition, ecommerce, AI referrals, bot detection, field-name maps. Skills are "
     "fetched from the repo when asked, so adding one doesn't need a package release."),
    ("Totals computed by GA4, not your model",
     "Multi-row pulls return a totals block from GA4's own aggregation, plus a note telling the agent to read "
     "the period figure there instead of summing rows itself."),
    ("Defaults that stop runaway queries",
     "Row counts are estimated before the fetch by default. A query that would return more than 2,500 rows comes "
     "back with a warning and concrete ways to narrow it, unless you pass proceed_with_large_dataset=True. "
     "Common metric aliases (conversions → keyEvents) and filter-shape repairs fix the mistakes models actually make."),
    ("The boring failures have built-in fixes",
     "Setup, IAM, and schema guides ship inside the package and work offline. On clients that support prompts, "
     "setup_ga4_access collects a missing property ID or credentials path mid-session and reconnects without a restart."),
    ("Telemetry you can switch off",
     "Anonymous diagnostics only: no queries, no credentials, no analytics data. Set DISABLE_TELEMETRY=1 or "
     "DO_NOT_TRACK=1 and the server stops sending, and stops writing its local ID file. MIT licensed, no account."),
]

STATS = [("7,103", "PyPI downloads, last 30 days"), ("242", "GitHub stars"), ("48", "GitHub forks"),
         ("15", "Agent skills"), ("v2.11.4", "Current version"), ("MIT", "License")]

COMPARE_HEAD = ("", "This server", f"Google's server ({GOOGLE_SERVER.rsplit('/', 2)[-1]})")
COMPARE_ROWS = [
    ("Built by", "Community project by Surendran B (BuildItWithAI); not affiliated with Google",
     "Google's Analytics organization"),
    ("Status", "v2.11.4, MIT", 'Labeled "Experimental", Apache-2.0'),
    ("API coverage", "GA4 Data API: reporting + metadata",
     "Admin API + Data API: account and property info, Google Ads links, core, funnel, and realtime reports"),
    ("Setup", "One-line installer, or uvx / npx; property ID + credentials",
     "pipx run analytics-mcp; requires a Google Cloud project ID and enabling the Admin + Data APIs"),
    ("Extras", "15 skills loaded at call time, pre-flight schema checks, GA4-computed totals, row-cap guard, "
               "offline troubleshooting guides, in-session setup recovery",
     "Vendor-maintained reference toolset"),
]

INSTALL_BLOCKS = [
    ("Universal installer (auto-configures your client)",
     'curl -fsSL "https://ga4.builditwithai.xyz/install" | bash',
     "Detects Claude Desktop, Claude Code, Cursor, VS Code (Cline, Roo Code), Continue.dev, Windsurf, Zed, "
     "Google Antigravity, and OpenCode."),
    ("uvx", "uvx google-analytics-mcp", "Requires uv."),
    ("npx", "npx -y @surendranb/google-analytics-mcp",
     "The npm package launches the Python server through uvx, so uv is required here too."),
    ("Claude Code users", "claude mcp add google-analytics -- uvx google-analytics-mcp",
     "Adds the server to Claude Code in one command."),
]

QUICKSTEPS = [
    ("Get credentials and a property ID", """<p>Two options, both local to your machine.</p>
    <p><em>Service account (recommended for a persistent setup):</em> create a service account in Google Cloud
    Console, download its JSON key, then add the service account's <code>client_email</code> as a
    <strong>Viewer</strong> on your GA4 property (Admin → Property Access Management).</p>
    <p><em>gcloud:</em> run <code>gcloud auth application-default login</code> and use the generated credentials
    file. Then set both values:</p>
    <pre><code>export GA4_PROPERTY_ID="123456789"                      # numeric ID, Admin → Property details
export GOOGLE_APPLICATION_CREDENTIALS="/absolute/path/to/key.json"</code></pre>
    <p>Your property ID is the numeric one, not the <code>G-</code> measurement ID.</p>"""),
    ("Install and wire your client",
     f"""<pre><code>curl -fsSL "{INSTALL}" | bash</code></pre>
    <p>The installer detects your client and writes the config. Prefer manual? Add
    <code>uvx google-analytics-mcp</code> to your MCP config and pass the two env values above.</p>"""),
    ("Ask your first question",
     """<p>"What were my top channels last week?" · "Why did organic traffic drop in the last 7 days?" ·
    "How much traffic came from AI assistants?" The agent picks the dimensions and metrics, runs the report,
    and reads the totals GA4 computed.</p>"""),
]

FAQS = [
    ("What is MCP?",
     "Model Context Protocol is a standard for connecting AI apps to external tools. Your client launches this "
     "server, and the agent gets GA4 querying tools: reporting, schema search, skills, and troubleshooting."),
    ("Does it work with Claude? What about ChatGPT?",
     "Claude Desktop and Claude Code are both covered by the installer, along with Cursor, VS Code (Cline, Roo Code), "
     "Continue.dev, Windsurf, Zed, Google Antigravity, and OpenCode. Gemini CLI connects through the repo's extension. "
     "ChatGPT isn't in the supported list; this is a local stdio server, so it needs a client that can launch local "
     "MCP servers."),
    ("Service account or OAuth?",
     "Both patterns run locally. A service-account JSON key doesn't expire and suits fixed or shared setups. "
     "Google Application Default Credentials via gcloud auth application-default login use OAuth user credentials "
     "refreshed on your machine. The quick start uses a service account because it has the fewest moving parts."),
    ("Is it free?",
     "Yes. MIT licensed, no account, no seat pricing, no hosted service in the query path. Queries run from your "
     "machine straight to Google's GA4 Data API, and your use of Google's APIs is governed by Google's terms and quotas."),
    ("What does it collect, and can I turn telemetry off?",
     "Anonymous usage diagnostics: which tools ran, latency, error codes. No queries, no credentials, no analytics data, "
     "no file paths. Set DISABLE_TELEMETRY=1 or DO_NOT_TRACK=1 and nothing is sent; when opted out, the server also "
     "stops creating its local ID file. The privacy policy has the full detail."),
    ("How many tools does it ship?",
     "11 in v2.11.4: get_ga4_data for reports, six schema tools for field discovery (search, full schema, and category "
     "browsing), plus list_properties, search_skills, get_troubleshooting_guide, and setup_ga4_access."),
    ("How is this different from Google's official server?",
     "Google's is vendor-maintained and labeled experimental, with coverage that includes funnel reports and Google Ads "
     "links. This one focuses on agent workflow: schema checks before a query runs, 15 skills on call, GA4-computed "
     "totals, and guided setup recovery. The comparison above has the full split."),
    ("Does it support Universal Analytics?",
     'No. UA properties stopped processing data on 2023-07-01, and this server talks to GA4 only. If you\'re translating '
     "old field names, the ua-to-ga4 skill maps every common one."),
    ("Is it read-only?",
     "Yes. Every tool is annotated read-only, and the server reads metadata and reports from the GA4 Data API. "
     "It doesn't change your GA4 configuration."),
    ("I'm getting an error. Where do I start?",
     'Ask your agent to run get_troubleshooting_guide(topic="setup"), ("iam"), or ("schema"). The guides are bundled '
     "with the package and work offline. setup_ga4_access walks the fix mid-session, and this site's setup, IAM, and "
     "schema pages mirror the same steps."),
]

# Tools exactly as the package registers them (name, parameters, what it returns).
TOOLS = [
    ("get_ga4_data", "dimensions, metrics, date_range_start, date_range_end, dimension_filter, limit, estimate_only, "
                     "proceed_with_large_dataset, enable_aggregation, intent",
     "Runs a GA4 report and returns rows plus a server-computed totals block from GA4's own aggregation. Estimates row "
     "counts first and warns above 2,500 rows."),
    ("search_schema", "keyword",
     "Ranks dimension and metric API names for this property. Call it before typing a field name."),
    ("get_property_schema", "-",
     "The full dimension and metric schema for the property, standard and custom."),
    ("list_dimension_categories", "-", "Dimension categories with counts, for browsing instead of guessing."),
    ("list_metric_categories", "-", "Metric categories with counts."),
    ("get_dimensions_by_category", "category", "Every dimension in one category, with its description."),
    ("get_metrics_by_category", "category", "Every metric in one category, with its description."),
    ("list_properties", "account_id (optional)", "The GA4 properties the configured credentials can read."),
    ("search_skills", "query (slug or keyword; empty returns the index)",
     "Serves one analytical recipe as markdown."),
    ("get_troubleshooting_guide", "topic: setup | iam | schema",
     "The fix path for a boot error, a 403, or a filter-shape error. Bundled with the package, works offline."),
    ("setup_ga4_access", "-",
     "Collects a missing property ID or credentials path through the client and reconnects without a restart."),
]

TRACKING = """  <!-- PostHog Tracking -->
  <script>
    !function(t,e){var o,n,p,r;e.__SV||(window.posthog=e,e._i=[],e.init=function(i,s,a){function g(t,e){var o=e.split(".");2==o.length&&(t=t[o[0]],e=o[1]),t[e]=function(){t.push([e].concat(Array.prototype.slice.call(arguments,0)))}}(p=t.createElement("script")).type="text/javascript",p.async=!0,p.src=s.api_host.replace(".i.posthog.com","-assets.i.posthog.com")+"/static/array.js",(r=t.getElementsByTagName("script")[0]).parentNode.insertBefore(p,r);var u=e;for(void 0!==a?u=e[a]=[]:a="posthog",u.people=u.people||[],u.toString=function(){var t="posthog";return"posthog"!==a&&(t+="."+a),t||(t+=" (stub)")},u.people.toString=function(){return u.toString(1)+".people (stub)"},o="capture identify alias people.set people.set_once set_config register register_once unregister opt_out_capturing has_opted_out_capturing opt_in_capturing reset isFeatureEnabled onFeatureFlags getFeatureFlag getFeatureFlagPayload reloadFeatureFlags group updateEarlyAccessFeatureEnrollment getActiveMatchingSurveys getSurveys getNextSurveyStep onSessionId setPersonProperties".split(" "),n=0;n<o.length;n++)g(u,o[n]);e._i.push([i,s,a])},e.__SV=1)}(document,window.posthog||[]);
    posthog.init('phc_Aik6H3pf5P9dPBrWLjd6N3wzsVAD6tJnmmEhFwW8Pzsi',{api_host:'https://us.i.posthog.com', person_profiles: 'identified_only'})
  </script>

  <!-- Google tag (gtag.js) -->
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-RX65PWDDEQ"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){dataLayer.push(arguments);}
    gtag('js', new Date());

    gtag('config', 'G-RX65PWDDEQ');
  </script>
"""

MARKS = ('<svg class="mark" width="26" height="26" viewBox="0 0 100 100" aria-hidden="true" focusable="false">'
         '<rect x="14" y="54" width="16" height="38" rx="8" fill="#fdba74"/>'
         '<rect x="42" y="40" width="16" height="52" rx="8" fill="#ea580c"/>'
         '<rect x="70" y="26" width="16" height="66" rx="8" fill="#1e3a8a"/></svg>')

# Progressive enhancement only: the page is complete without this script.
WEBMCP_JS = """  <script>
  /* WebMCP: read-only tools for browser agents. Never required to read the page. */
  (function () {
    var INSTALL = {
      universal: 'curl -fsSL "https://ga4.builditwithai.xyz/install" | bash',
      uvx: 'uvx google-analytics-mcp',
      npx: 'npx -y @surendranb/google-analytics-mcp',
      claude_code: 'claude mcp add google-analytics -- uvx google-analytics-mcp',
      python: 'python -m ga4_mcp'
    };
    async function twin(path) {
      var res = await fetch(path, { headers: { accept: "text/markdown" } });
      if (!res.ok) throw new Error("fetch failed: " + path + " (" + res.status + ")");
      return await res.text();
    }
    var tools = {
      get_install_command: {
        description: "Return the install command for this GA4 MCP server. Optionally name a client: universal, uvx, npx, claude_code, python.",
        inputSchema: { type: "object", properties: { client: { type: "string" } } },
        execute: async function (args) {
          var key = (args && args.client ? String(args.client) : "universal").toLowerCase().replace(/[^a-z_]/g, "_");
          var command = INSTALL[key] || INSTALL.universal;
          return command + "\\nRequires GA4_PROPERTY_ID and GOOGLE_APPLICATION_CREDENTIALS before the first query.";
        }
      },
      list_skills: {
        description: "List the 15 GA4 analytical skills shipped with the server, as JSON.",
        inputSchema: { type: "object", properties: {} },
        execute: async function () { return await twin("/data/skills.json"); }
      },
      get_skill: {
        description: "Return one skill recipe as markdown. Slug example: traffic-diagnosis.",
        inputSchema: { type: "object", properties: { slug: { type: "string" } }, required: ["slug"] },
        execute: async function (args) {
          var slug = String((args && args.slug) || "").trim().toLowerCase();
          if (!/^[a-z0-9-]+$/.test(slug)) throw new Error("slug must be a skill slug, e.g. traffic-diagnosis");
          return await twin("/skills/" + slug + "/index.md");
        }
      },
      get_tool_reference: {
        description: "Return the 11 MCP tool definitions (names, parameters, descriptions) as JSON. Optionally filter by tool name.",
        inputSchema: { type: "object", properties: { name: { type: "string" } } },
        execute: async function (args) {
          var all = JSON.parse(await twin("/data/tools.json"));
          var name = args && args.name ? String(args.name) : "";
          var hit = all.tools.filter(function (t) { return t.name === name; });
          return JSON.stringify(name ? { tools: hit } : all, null, 2);
        }
      },
      get_doc: {
        description: "Return a troubleshooting guide as markdown. Topic must be setup, schema, or iam.",
        inputSchema: { type: "object", properties: { topic: { type: "string" } }, required: ["topic"] },
        execute: async function (args) {
          var topic = String((args && args.topic) || "").trim().toLowerCase();
          if (["setup", "schema", "iam"].indexOf(topic) === -1) throw new Error("topic must be setup, schema, or iam");
          return await twin("/" + topic + "/index.md");
        }
      }
    };
    window.ga4mcpTools = tools;
    var mc = navigator.modelContext || window.modelContext;
    if (!mc || typeof mc.registerTool !== "function") return;
    for (var name in tools) {
      try {
        mc.registerTool({
          name: name,
          description: tools[name].description,
          inputSchema: tools[name].inputSchema,
          execute: tools[name].execute,
          annotations: { readOnlyHint: true }
        });
      } catch (err) {
        console.warn("WebMCP registration failed:", name, err);
      }
    }
  })();
  </script>
"""

# Progressive enhancement only: without this script the rail is a plain link list.
RAIL_JS = """  <script>
  /* Rail filter: no-JS fallback is the full list, so the input ships hidden. */
  (function () {
    var input = document.querySelector('[data-rail-filter]');
    if (!input) return;
    var box = input.closest('.rail-filter');
    if (box) box.hidden = false;
    input.addEventListener('input', function () {
      var q = input.value.trim().toLowerCase();
      var sections = document.querySelectorAll('.rail-section');
      for (var i = 0; i < sections.length; i++) {
        var items = sections[i].querySelectorAll('li');
        var shown = 0;
        for (var j = 0; j < items.length; j++) {
          var hit = !q || items[j].textContent.toLowerCase().indexOf(q) !== -1;
          items[j].hidden = !hit;
          if (hit) shown++;
        }
        sections[i].hidden = shown === 0;
      }
    });
  })();
  </script>
"""


# --------------------------------------------------------------------------- helpers
def plain(text: str) -> str:
    """Markdown/HTML-ish text as a readable sentence (JSON-LD, meta descriptions)."""
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"[`*_]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def clip(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(" ", 1)[0].rstrip(",;:.") + "…"


def strip_frontmatter(text: str) -> tuple[dict[str, str], str]:
    meta: dict[str, str] = {}
    body = text
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) == 3:
            _, front, body = parts
            for line in front.strip().splitlines():
                if ":" in line:
                    key, value = line.split(":", 1)
                    meta[key.strip()] = value.strip().strip('"').strip("'")
    return meta, body.strip()


def render_markdown(text: str) -> str:
    out = mdlib.markdown(text, extensions=["tables", "fenced_code", "toc", "sane_lists"], output_format="html5")
    out = out.replace("<table>", '<div class="tscroll"><table>').replace("</table>", "</table></div>")
    out = re.sub(r'href="([a-z0-9-]+)\.md"', r'href="/\1/"', out)
    out = re.sub(r'href="\.\./([a-z0-9-]+)/"', r'href="/\1/"', out)
    return out


def visible_text(fragment: str) -> str:
    class Extractor(HTMLParser):
        def __init__(self) -> None:
            super().__init__(convert_charrefs=True)
            self.parts: list[str] = []
            self.skip = 0

        def handle_starttag(self, tag, attrs):
            if tag in ("script", "style"):
                self.skip += 1

        def handle_endtag(self, tag):
            if tag in ("script", "style") and self.skip:
                self.skip -= 1

        def handle_data(self, data):
            if not self.skip and data.strip():
                self.parts.append(data.split())

    ex = Extractor()
    ex.feed(fragment)
    return " ".join(" ".join(part) for part in ex.parts)


def twin_url(url: str) -> str:
    return "/index.md" if url == "/" else f"{url}index.md"


def load_meta() -> dict[str, dict[str, str]]:
    raw = json.loads((SITE_DIR / "meta.json").read_text(encoding="utf-8"))
    out: dict[str, dict[str, str]] = {}
    for key, value in raw.items():
        path = key if key.startswith("/") else f"/{key}"
        if path != "/" and not path.endswith("/"):
            path += "/"
        out[path] = {"title": value["title"], "description": value["description"],
                     "target_query": value.get("target_query", "")}
    return out


META = load_meta()
PAGES: dict[str, dict] = {}
SKILLS_NAV: list[dict] = []


def meta_for(url: str) -> dict[str, str]:
    base = META.get(url) or META.get(url.rstrip("/")) or {}
    return {"title": base.get("title", "GA4 MCP Server"), "description": base.get("description", "")}


def nav_item(href: str, label: str, url: str) -> str:
    active = url == href or (href != "/" and url.startswith(href))
    attr = ' aria-current="page"' if active else ""
    return f'<li><a href="{href}"{attr}>{label}</a></li>'


def rail(url: str) -> str:
    """Fixed workstation rail: brand, filter, sectioned nav, version foot.

    Geometry mirrors the Workbench theme (fixed header, fixed 360px rail with
    its own scroll, main column takes the rest). Every link marks the current
    page with aria-current.
    """
    def link(href: str, label: str, ext: bool = False) -> str:
        active = "" if ext else (' aria-current="page"' if url == href else "")
        arrow = ' <span class="ext" aria-hidden="true">↗</span>' if ext else ""
        return f'<li><a href="{href}"{active}>{label}{arrow}</a></li>'

    skills = "\n        ".join(
        link(f"/skills/{s['slug']}/", html.escape(s["title"])) for s in SKILLS_NAV)
    return f"""<aside class="rail" aria-label="Site">
  <div class="rail-head">
    <a class="brand" href="/">{MARKS}<span>GA4 MCP Server</span></a>
    <p class="rail-tagline">Google Analytics 4 for AI agents.</p>
  </div>
  <div class="rail-filter" hidden>
    <label class="sr-only" for="rail-filter">Filter pages</label>
    <input id="rail-filter" class="rail-search" type="search" placeholder="Filter pages…" data-rail-filter>
  </div>
  <nav class="rail-nav" aria-label="Pages" tabindex="0">
    <div class="rail-section">
      <p class="rail-label">Get started</p>
      <ul>
        {link("/", "Home")}
        {link("/setup/", "Setup")}
        {link(INSTALL, "Install", ext=True)}
      </ul>
    </div>
    <div class="rail-section">
      <p class="rail-label">Reference</p>
      <ul>
        {link("/schema/", "Schema")}
        {link("/iam/", "IAM")}
      </ul>
    </div>
    <div class="rail-section">
      <p class="rail-label">Skills</p>
      <ul>
        {link("/skills/", "All skills")}
        {skills}
      </ul>
    </div>
    <div class="rail-section">
      <p class="rail-label">Meta</p>
      <ul>
        {link(REPO, "GitHub", ext=True)}
        {link(PYPI, "PyPI", ext=True)}
        {link(NPM, "npm", ext=True)}
        {link("/privacy/", "Privacy")}
        {link("/terms/", "Terms")}
      </ul>
    </div>
  </nav>
  <div class="rail-foot"><p>v{VERSION} · MIT</p></div>
</aside>"""


def shell(url: str, body: str, jsonld: list[dict], md: str | None, og_type: str = "website",
          noindex: bool = False, extra_js: str = "") -> str:
    meta = meta_for(url)
    canonical = SITE + url
    head = [
        "<!DOCTYPE html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="UTF-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        '<meta name="color-scheme" content="light">',
        f"<title>{html.escape(meta['title'])}</title>",
        f'<meta name="description" content="{html.escape(meta["description"])}">',
        f'<link rel="canonical" href="{canonical}">',
        '<meta name="robots" content="noindex,follow">' if noindex else '<meta name="robots" content="index,follow">',
        '<meta name="theme-color" content="#fdf0e2">',
    ]
    if md is not None:
        head.append(f'<link rel="alternate" type="text/markdown" href="{SITE}{twin_url(url)}">')
    head += [
        f'<link rel="describedby" type="text/plain" href="{SITE}/llms.txt" title="llms.txt">',
        f'<meta property="og:type" content="{og_type}">',
        '<meta property="og:site_name" content="GA4 MCP Server">',
        f'<meta property="og:title" content="{html.escape(meta["title"])}">',
        f'<meta property="og:description" content="{html.escape(meta["description"])}">',
        f'<meta property="og:url" content="{canonical}">',
        f'<meta property="og:image" content="{SITE}/og.png">',
        '<meta property="og:image:width" content="1200">',
        '<meta property="og:image:height" content="630">',
        '<meta property="og:image:alt" content="GA4 MCP Server — Google Analytics 4 for AI agents">',
        '<meta name="twitter:card" content="summary_large_image">',
        f'<meta name="twitter:title" content="{html.escape(meta["title"])}">',
        f'<meta name="twitter:description" content="{html.escape(meta["description"])}">',
        f'<meta name="twitter:image" content="{SITE}/og.png">',
        '<link rel="icon" href="/favicon.svg" type="image/svg+xml">',
        '<link rel="icon" href="/favicon-32.png" sizes="32x32" type="image/png">',
        '<link rel="icon" href="/favicon-16.png" sizes="16x16" type="image/png">',
        '<link rel="apple-touch-icon" href="/apple-touch-icon-180.png">',
        '<link rel="stylesheet" href="/assets/style.css">',
    ]
    for node in jsonld:
        head.append('<script type="application/ld+json">'
                    + json.dumps(node, ensure_ascii=False, separators=(",", ":")) + "</script>")
    head.append(TRACKING.rstrip("\n"))
    head.append("</head>")

    header = f"""<body>
<a class="skip" href="#main">Skip to content</a>
<header class="site-header">
  <div class="bar">
    <a class="brand" href="/">{MARKS}<span>GA4 MCP</span></a>
    <nav class="main" aria-label="Main">
      <ul>
        <li><a href="{REPO}">GitHub <span class="ext" aria-hidden="true">↗</span></a></li>
        <li><a href="{PYPI}">PyPI <span class="ext" aria-hidden="true">↗</span></a></li>
        <li><a class="btn install" href="/install">Install</a></li>
      </ul>
    </nav>
  </div>
</header>
<div class="site-body">
{rail(url)}"""

    footer = f"""<footer class="site-footer">
  <div class="wrap">
    <p><strong>GA4 MCP Server</strong> — Model Context Protocol server for Google Analytics 4. MIT licensed.
    Not affiliated with Google. "Google Analytics" is a trademark of Google LLC.</p>
    <nav aria-label="Footer">
      <ul>
        <li><a href="/setup/">Setup</a></li>
        <li><a href="/schema/">Filter schema</a></li>
        <li><a href="/iam/">IAM</a></li>
        <li><a href="/skills/">Skills</a></li>
        <li><a href="/llms.txt">llms.txt</a></li>
        <li><a href="/llms-full.txt">llms-full.txt</a></li>
        <li><a href="/robots.txt">robots.txt</a></li>
        <li><a href="/sitemap.xml">Sitemap</a></li>
        <li><a href="/privacy/">Privacy</a></li>
        <li><a href="/terms/">Terms</a></li>
        <li><a href="{REPO}">GitHub</a></li>
        <li><a href="{PYPI}">PyPI</a></li>
        <li><a href="{NPM}">npm</a></li>
      </ul>
    </nav>
    <p class="foot-legal">&copy; {YEAR} Surendran Balachandran · GA4 MCP is open source under the MIT License.</p>
  </div>
</footer>"""
    body_end = (f"</div>\n</main>\n{footer}\n</div>\n{RAIL_JS}{extra_js}</body>\n</html>\n")
    return ("\n".join(head) + "\n" + header + "\n<main id=\"main\" class=\"main-col\">\n<div class=\"content\">\n"
            + body + "\n" + body_end)


def write_page(url: str, body: str, jsonld: list[dict], md: str | None = None, og_type: str = "website",
               noindex: bool = False, extra_js: str = "") -> None:
    page = shell(url, body, jsonld, md, og_type=og_type, noindex=noindex, extra_js=extra_js)
    target = DIST / "index.html" if url == "/" else DIST / url.strip("/") / "index.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(page, encoding="utf-8")
    entry = {"html": page, "file": target, "md_file": None}
    if md is not None:
        twin = DIST / twin_url(url).lstrip("/")
        twin.parent.mkdir(parents=True, exist_ok=True)
        twin.write_text(md, encoding="utf-8")
        entry["md_file"] = twin
    PAGES[url] = entry


def tech_article(url: str, headline: str, description: str) -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "TechArticle",
        "headline": headline,
        "description": description,
        "url": SITE + url,
        "inLanguage": "en",
        "license": "https://opensource.org/license/mit",
        "author": {"@type": "Person", "name": "Surendran B"},
        "isPartOf": {"@type": "WebSite", "name": "GA4 MCP Server", "url": SITE + "/"},
        "about": {"@type": "SoftwareApplication", "name": "GA4 MCP Server", "codeRepository": REPO},
    }


def web_page(url: str) -> dict:
    meta = meta_for(url)
    return {"@context": "https://schema.org", "@type": "WebPage", "name": meta["title"],
            "description": meta["description"], "url": SITE + url, "inLanguage": "en"}


# --------------------------------------------------------------------------- discovery
def discover_skills() -> list[dict]:
    found = []
    for skill_dir in sorted(SKILLS_SRC.iterdir()):
        skill_md = skill_dir / "SKILL.md"
        if not skill_dir.is_dir() or not skill_md.is_file():
            continue
        front, body_md = strip_frontmatter(skill_md.read_text(encoding="utf-8"))
        first_line = body_md.splitlines()[0] if body_md.startswith("#") else ""
        title = (re.sub(r"^#\s+", "", first_line).strip()
                 or front.get("name", skill_dir.name).replace("-", " ").title())
        summary = plain(front.get("description", ""))
        found.append({"slug": skill_dir.name, "title": title, "md": body_md, "summary": summary,
                      "front": front})
    found.sort(key=lambda s: s["title"].lower())
    return found


def legal_body(filename: str) -> str:
    """Verbatim content slice of docs/<file> — H1 through the last paragraph."""
    raw = (DOCS / filename).read_text(encoding="utf-8")
    start = raw.index("<h1")
    end = raw.index('<div class="footer">', start)
    return raw[start:end].rstrip()


def frontmatter(title: str, description: str, url: str, kind: str) -> str:
    return ("---\n"
            f"title: {title}\n"
            f"description: {description}\n"
            f"url: {SITE}{url}\n"
            f"type: {kind}\n"
            f"site: {SITE}\n"
            f"updated: {BUILD_DATE}\n"
            "license: MIT\n"
            "---\n\n")


def home_markdown(skills: list[dict]) -> str:
    compare = "\n".join(f"| {row[0]} | {row[1]} | {row[2]} |" for row in COMPARE_ROWS)
    commands = "\n".join(f"# {name}\n{cmd}\n" for name, cmd, _ in INSTALL_BLOCKS)
    why = "\n".join(f"### {title}\n\n{body}\n" for title, body in WHY)
    stats = "\n".join(f"- **{value}** — {label}" for value, label in STATS)
    faq = "\n".join(f"### {q}\n\n{a}\n" for q, a in FAQS)
    skill_list = "\n".join(f"- [{s['title']}]({SITE}/skills/{s['slug']}/index.md): {s['summary']}" for s in skills)
    return f"""{frontmatter(meta_for('/')['title'], meta_for('/')['description'], '/', 'website')}# GA4 MCP Server

> Google Analytics 4 for AI agents.

Point Claude, Cursor, or any MCP client at your GA4 property. The server reads your property's real schema
before it writes a query, asks GA4 for period totals instead of letting the model sum rows, and keeps 15
analytical skills one call away.

{" · ".join(CHIPS)}

- Install in one line: `#install` below
- Setup guide: {SITE}/setup/ · [markdown]({SITE}/setup/index.md)
- Repo: {REPO}

## Install

Three ways in. The installer finds your client and writes the config entry; the runtime commands drop into
any MCP client's config.

```bash
{commands}```

Before the first query, set `GA4_PROPERTY_ID` and `GOOGLE_APPLICATION_CREDENTIALS`. Both are covered in
Quick start below.

## Works with your client

No hand-edited JSON needed for most setups.

{chr(10).join(f'- {c}' for c in CLIENTS)}

The server speaks MCP over stdio. If your client can launch a local MCP server, a manual config snippet is
all it takes; the repo has snippets for each client above.

## Why this server

{why}
## In numbers

{stats}

npm wrapper: 138 downloads in the last 30 days. Numbers as of Sep 2026.

## This server vs Google's official Analytics MCP server

Both servers are real, and both are free to use. Google publishes its own Analytics MCP server (labeled
experimental, Apache-2.0). This one is community-built and MIT-licensed.

| | This server | Google's server |
|---|---|---|
{compare}

**Reach for Google's server if** you want the vendor-maintained baseline, funnel reports, or Google Ads
account links.

**Reach for this one if** you're driving an agent through day-to-day analysis and want it to stop guessing
field names, read period totals instead of summing rows, and follow a documented method per question.

GA4 MCP is an independent open-source project. It isn't affiliated with, endorsed by, or sponsored by Google.
"Google Analytics" is a trademark of Google LLC.

## Quick start

### 1. Get credentials and a property ID

Create a service account in Google Cloud Console, download its JSON key, then add the service account's
`client_email` as a **Viewer** on your GA4 property (Admin → Property Access Management). Or run
`gcloud auth application-default login` and use the generated credentials file.

```bash
export GA4_PROPERTY_ID="123456789"                      # numeric ID, Admin → Property details
export GOOGLE_APPLICATION_CREDENTIALS="/absolute/path/to/key.json"
```

Your property ID is the numeric one, not the `G-` measurement ID.

### 2. Install and wire your client

```bash
curl -fsSL "{INSTALL}" | bash
```

### 3. Ask your first question

"What were my top channels last week?" · "Why did organic traffic drop in the last 7 days?" · "How much
traffic came from AI assistants?"

## Tools

11 tools cover reporting, schema discovery, and the fix paths an agent hits during setup.

{chr(10).join(f'- `{name}({args})`: {desc}' for name, args, desc in TOOLS)}

Machine-readable: {SITE}/data/tools.json

## Skills

{skill_list}

Machine-readable: {SITE}/data/skills.json

## FAQ

{faq}
## Machine surfaces

- llms.txt: {SITE}/llms.txt
- llms-full.txt: {SITE}/llms-full.txt
- sitemap.xml: {SITE}/sitemap.xml
- tools.json: {SITE}/data/tools.json
- skills.json: {SITE}/data/skills.json

---

Open source, MIT, and local. Install it, then ask your first question.

GitHub: {REPO} · PyPI: {PYPI} · npm: {NPM} · Installer: {INSTALL}
"""


# --------------------------------------------------------------------------- pages
def build_home(skills: list[dict]) -> None:
    cards = "\n".join(
        f'      <li class="card"><h3><a href="/skills/{s["slug"]}/">{html.escape(s["title"])}</a></h3>'
        f'<p>{html.escape(s["summary"])}</p></li>' for s in skills)
    why = "\n".join(
        f'      <li class="card"><h3>{html.escape(title)}</h3><p>{html.escape(body)}</p></li>'
        for title, body in WHY)
    stats = "\n".join(f'      <li class="stat"><b>{html.escape(value)}</b><span>{html.escape(label)}</span></li>'
                      for value, label in STATS)
    compare = "\n".join(
        f'        <tr><th scope="row">{html.escape(label)}</th><td>{html.escape(mine)}</td>'
        f'<td>{html.escape(theirs)}</td></tr>' for label, mine, theirs in COMPARE_ROWS)
    install = "\n".join(
        f'    <figure class="cmd"><pre><code># {html.escape(name)}\n{html.escape(cmd)}</code></pre>'
        f'<figcaption>{caption}</figcaption></figure>' for name, cmd, caption in INSTALL_BLOCKS)
    steps = "\n".join(
        f'      <h3>{i}. {html.escape(title)}</h3>\n      {body}' for i, (title, body) in enumerate(QUICKSTEPS, 1))
    faq = "\n".join(f'      <h3>{html.escape(q)}</h3>\n      <p>{html.escape(a)}</p>' for q, a in FAQS)
    clients = "\n".join(f"      <li>{html.escape(c)}</li>" for c in CLIENTS)
    jump = " · ".join(f'<a href="#{anchor}">{label}</a>' for anchor, label in
                      (("install", "Install"), ("works-with", "Clients"), ("why", "Why"), ("traction", "In numbers"),
                       ("compare", "Compare"), ("quickstart", "Quick start"), ("faq", "FAQ")))

    body = f"""  <div class="wrap">
  <article>
    <section class="hero" id="hero">
      <div class="hero-grid">
      <div>
      <p class="eyebrow">Model Context Protocol · GA4 Data API v1beta</p>
      <h1>GA4 MCP Server</h1>
      <p class="lead">Google Analytics 4 for AI agents.</p>
      <p>Point Claude, Cursor, or any MCP client at your GA4 property. The server reads your property's real
      schema before it writes a query, asks GA4 for period totals instead of letting the model sum rows, and
      keeps 15 analytical skills one call away.</p>
      <div class="cta">
        <a class="btn" href="#install">Install in one line</a>
        <a class="btn ghost" href="/setup/">Read the setup guide</a>
      </div>
      <p class="trust">{" · ".join(CHIPS)}</p>
      </div>
      <div class="hero-mark" aria-hidden="true">{MARKS}</div>
      </div>
      <p class="mini">On this page: {jump}</p>
    </section>

    <section id="install">
      <h2>Install</h2>
      <p>Three ways in. The installer finds your client and writes the config entry; the runtime commands drop
      into any MCP client's config.</p>
{install}
      <div class="note"><p><strong>Before the first query,</strong> set two env values:
      <code>GA4_PROPERTY_ID</code> and <code>GOOGLE_APPLICATION_CREDENTIALS</code>. Both are covered in
      <a href="#quickstart">quick start</a> below. No installer run is required for the runtime commands;
      they fetch the package on first launch.</p></div>
    </section>

    <section id="works-with">
      <h2>Works with your client</h2>
      <p>No hand-edited JSON needed for most setups.</p>
      <ul class="client-list">
{clients}
      </ul>
      <p>The server speaks MCP over stdio. If your client can launch a local MCP server, a manual config
      snippet is all it takes; the repo has snippets for each client above.</p>
    </section>

    <section id="why">
      <h2>Why this server</h2>
      <ul class="grid">
{why}
      </ul>
    </section>

    <section id="traction">
      <h2>In numbers</h2>
      <ul class="stats">
{stats}
      </ul>
      <p class="mini">npm wrapper: 138 downloads in the last 30 days. Numbers as of Sep 2026.
      <a href="{REPO}">View the repo →</a></p>
    </section>

    <section id="compare">
      <h2>This server vs Google's official Analytics MCP server</h2>
      <p>Both servers are real, and both are free to use. Google publishes its own Analytics MCP server
      (labeled experimental, Apache-2.0). This one is community-built and MIT-licensed. Here's the split,
      without the sales gloss.</p>
      <div class="tscroll compare"><table>
        <caption class="sr-only">Feature comparison between this GA4 MCP server and Google's Analytics MCP server</caption>
        <thead><tr><th scope="col">{html.escape(COMPARE_HEAD[0])}</th>
        <th scope="col">{html.escape(COMPARE_HEAD[1])}</th><th scope="col">{html.escape(COMPARE_HEAD[2])}</th></tr></thead>
        <tbody>
{compare}
        </tbody>
      </table></div>
      <h3>When to use which</h3>
      <p><strong>Reach for Google's server if</strong> you want the vendor-maintained baseline, funnel reports,
      or Google Ads account links.</p>
      <p><strong>Reach for this one if</strong> you're driving an agent through day-to-day analysis and want it
      to stop guessing field names, read period totals instead of summing rows, and follow a documented method
      per question.</p>
      <p class="mini">GA4 MCP is an independent open-source project. It isn't affiliated with, endorsed by, or
      sponsored by Google. "Google Analytics" is a trademark of Google LLC.</p>
    </section>

    <section id="quickstart">
      <h2>Quick start</h2>
{steps}
      <div class="cta"><a class="btn" href="#install">Install now</a></div>
    </section>

    <section id="faq">
      <h2>FAQ</h2>
      <div class="faq">
{faq}
      </div>
      <div class="cta"><a class="btn" href="#install">Install GA4 MCP</a></div>
    </section>

    <section id="footer-cta">
      <h2>Open source, MIT, and local</h2>
      <p>Install it, then ask your first question. Repo, setup guides, and the skills library:</p>
      <p><a href="{REPO}">GitHub</a> · <a href="/setup/">Setup</a> · <a href="/schema/">Schema</a> ·
      <a href="/iam/">IAM</a> · <a href="/skills/">Skills</a> · <a href="/privacy/">Privacy</a> ·
      <a href="/terms/">Terms</a></p>
      <p class="mini">GA4 MCP is an independent project, not affiliated with Google. "Google Analytics" is a
      trademark of Google LLC.</p>
    </section>

    <section id="agents">
      <h2>For agents</h2>
      <p>Every page here has a markdown twin, and the browser exposes five read-only tools through
      <code>navigator.modelContext</code> when the client supports WebMCP. If you are an agent reading the
      HTML, the faster path is <a href="/llms.txt">llms.txt</a> for the map and
      <a href="/llms-full.txt">llms-full.txt</a> for every page in one file.
      Machine data: <a href="/data/tools.json">tools.json</a> (11 tools),
      <a href="/data/skills.json">skills.json</a> (15 skills).</p>
    </section>
  </article>
  </div>"""
    tool_jsonld = [
        {
            "@context": "https://schema.org",
            "@type": "SoftwareApplication",
            "name": "GA4 MCP Server",
            "alternateName": "google-analytics-mcp",
            "applicationCategory": "DeveloperApplication",
            "operatingSystem": "macOS, Linux, Windows",
            "description": ("MCP server that gives AI agents analysis-ready access to Google Analytics 4: "
                            "schema discovery, server-side aggregation, and 15 analytical skills over stdio."),
            "url": SITE + "/",
            "codeRepository": REPO,
            "license": "https://opensource.org/license/mit",
            "isAccessibleForFree": True,
            "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
            "softwareVersion": "2.11.4",
            "softwareRequirements": "Python 3.10+, or Node 16+ via the npx wrapper",
            "author": {"@type": "Person", "name": "Surendran B"},
            "keywords": ["GA4", "MCP", "Google Analytics 4", "AI agents", "llms.txt", "WebMCP"],
        },
        {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [
                {"@type": "Question", "name": q,
                 "acceptedAnswer": {"@type": "Answer", "text": plain(a)}}
                for q, a in FAQS
            ],
        },
        web_page("/"),
    ]
    write_page("/", body, tool_jsonld, md=home_markdown(skills), extra_js=WEBMCP_JS)


def build_docs() -> None:
    for slug, rel, resource in (("setup", "docs/setup.md", "docs://fix/setup"),
                                ("schema", "docs/schema.md", "docs://fix/schema"),
                                ("iam", "docs/iam.md", "docs://fix/iam")):
        url = f"/{slug}/"
        source = (ROOT / rel).read_text(encoding="utf-8")
        meta = meta_for(url)
        body = f"""  <div class="wrap">
  <article class="prose">
{render_markdown(source)}
    <p class="doc-note">Served inside the MCP as the <code>{resource}</code> resource and as
    <code>get_troubleshooting_guide("{slug}")</code>. Markdown twin:
    <a href="{twin_url(url)}">{twin_url(url)}</a> · Source:
    <a href="{REPO}/blob/main/{rel}">{rel}</a>.</p>
  </article>
  </div>"""
        md = frontmatter(meta["title"], meta["description"], url, "documentation") + source
        write_page(url, body, [tech_article(url, meta["title"], meta["description"]), web_page(url)],
                   md=md, og_type="article")


def build_skills(skills: list[dict]) -> None:
    url = "/skills/"
    meta = meta_for(url)
    rows = "\n".join(
        f'      <li class="card"><h3><a href="/skills/{s["slug"]}/">{html.escape(s["title"])}</a></h3>'
        f'<p>{html.escape(s["summary"])}</p><p class="tag">skill://{s["slug"]}</p></li>' for s in skills)

    index_src = (SKILLS_SRC / "index.md").read_text(encoding="utf-8")
    intro_md = index_src.split("| Skill |")[0]
    intro_md = intro_md.split("\n\n", 1)[1].strip() if "\n\n" in intro_md else intro_md.strip()
    body = f"""  <div class="wrap">
  <article class="prose">
    <h1>GA4 MCP Skills Library</h1>
    <p class="lead">{len(skills)} analytical recipes, each one a page plus an MCP resource at
    <code>skill://&lt;slug&gt;</code>. Load one in a session with <code>search_skills("&lt;slug&gt;")</code>;
    the text below is the same content the agent receives.</p>
{render_markdown(intro_md)}
    <ul class="grid">
{rows}
    </ul>
    <p class="doc-note">Machine-readable index: <a href="/data/skills.json">/data/skills.json</a>. Markdown twin:
    <a href="{twin_url(url)}">{twin_url(url)}</a>.</p>
  </article>
  </div>"""
    md_index = "\n".join(f"- [{s['title']}]({SITE}/skills/{s['slug']}/index.md): {s['summary']}" for s in skills)
    md = (frontmatter(meta["title"], meta["description"], url, "collection")
          + f"# GA4 MCP Skills Library\n\n{len(skills)} analytical recipes. Each one is an MCP resource at "
            f"`skill://<slug>`, loadable with `search_skills(\"<slug>\")`.\n\n{md_index}\n\n"
            f"Machine-readable index: {SITE}/data/skills.json\n")
    write_page(url, body, [tech_article(url, meta["title"], meta["description"]), web_page(url)],
               md=md, og_type="article")

    for s in skills:
        s_url = f"/skills/{s['slug']}/"
        if s_url not in META:
            META[s_url] = {"title": f"{s['title']}: GA4 MCP skill",
                           "description": clip(s["summary"] or f"GA4 analysis recipe: {s['title']}.", 155),
                           "target_query": ""}
        s_meta = meta_for(s_url)
        page_body = f"""  <div class="wrap">
  <article class="prose">
    <a class="back" href="/skills/">← All skills</a>
{render_markdown(s["md"])}
    <p class="doc-note">Load it in a session with <code>search_skills("{s['slug']}")</code>, or read the MCP
    resource <code>skill://{s['slug']}</code>. Markdown twin:
    <a href="{twin_url(s_url)}">{twin_url(s_url)}</a> · Source:
    <a href="{REPO}/blob/main/skills/{s['slug']}/SKILL.md">skills/{s['slug']}/SKILL.md</a>.</p>
  </article>
  </div>"""
        md = frontmatter(s_meta["title"], s_meta["description"], s_url, "skill") + s["md"] + "\n"
        write_page(s_url, page_body, [tech_article(s_url, s_meta["title"], s_meta["description"]), web_page(s_url)],
                   md=md, og_type="article")


def build_legal() -> None:
    for slug, filename in (("privacy", "privacy.html"), ("terms", "terms.html")):
        url = f"/{slug}/"
        fragment = legal_body(filename)
        body = f"""  <div class="wrap">
  <article class="prose legal" data-source="docs/{filename}">
{fragment}
  </article>
  </div>"""
        write_page(url, body, [web_page(url)], md=None, og_type="article")


def build_not_found() -> None:
    META["/404/"] = {"title": "Page not found - GA4 MCP Server",
                     "description": "That URL does not exist on ga4mcp.com. Start from the setup guide, the "
                                    "filter schema, or the skills library.",
                     "target_query": ""}
    body = f"""  <div class="wrap">
  <article class="prose">
    <h1>Page not found</h1>
    <p class="lead">That URL does not exist on ga4mcp.com. The documentation starts here:</p>
    <ul>
      <li><a href="/">Home</a></li>
      <li><a href="/setup/">Setup and troubleshooting</a></li>
      <li><a href="/schema/">Filter schema reference</a></li>
      <li><a href="/iam/">IAM permissions</a></li>
      <li><a href="/skills/">Skills library</a></li>
      <li><a href="/llms.txt">llms.txt</a> for agents</li>
    </ul>
  </article>
  </div>"""
    page = shell("/404/", body, [web_page("/")], None, noindex=True)
    (DIST / "404.html").write_text(page, encoding="utf-8")


# --------------------------------------------------------------------------- machine surfaces
def build_llms(skills: list[dict]) -> None:
    docs = "\n".join(
        f"- [{meta_for(f'/{slug}/')['title']}]({SITE}/{slug}/) · "
        f"[markdown]({SITE}/{slug}/index.md) — {meta_for(f'/{slug}/')['description']}"
        for slug in ("setup", "schema", "iam"))
    skill_lines = "\n".join(
        f"- [{s['title']}]({SITE}/skills/{s['slug']}/) · [markdown]({SITE}/skills/{s['slug']}/index.md): "
        f"{s['summary']}" for s in skills)
    tools = "\n".join(f"- `{name}({args})`: {desc}" for name, args, desc in TOOLS)
    llms = f"""# GA4 MCP Server

> Model Context Protocol server for Google Analytics 4: schema discovery before a query is built, totals
> computed by GA4 instead of the model, 11 tools, 15 analytical skills. MIT licensed, stdio, runs locally.

Canonical site: {SITE} · Version 2.11.4 · Updated {BUILD_DATE}

## Install

```bash
# universal installer (writes the client config)
curl -fsSL "{INSTALL}" | bash
# or run it directly
uvx google-analytics-mcp
npx -y @surendranb/google-analytics-mcp
```

Set `GA4_PROPERTY_ID` and `GOOGLE_APPLICATION_CREDENTIALS` before the first query. Details:
{SITE}/setup/ · [markdown]({SITE}/setup/index.md)

## Documentation

{docs}

## Skills ({len(skills)})

{skill_lines}

Skills index: {SITE}/skills/ · [markdown]({SITE}/skills/index.md)

## Tools ({len(TOOLS)})

{tools}

## Machine data

- [tools.json]({SITE}/data/tools.json): all 11 tools with parameters and descriptions
- [skills.json]({SITE}/data/skills.json): skill slugs, titles, one-line descriptions
- [llms-full.txt]({SITE}/llms-full.txt): every page above inlined as markdown
- [index.md]({SITE}/index.md): the home page as markdown
- [sitemap.xml]({SITE}/sitemap.xml) · [robots.txt]({SITE}/robots.txt)
- Content negotiation: send `Accept: text/markdown` to any content URL for its markdown twin

## Distribution

- Repository: {REPO}
- PyPI: {PYPI}
- npm: {NPM}
- Installer endpoint: {INSTALL}
- Google's official Analytics MCP server (for comparison): {GOOGLE_SERVER}

## Environment

- `GA4_PROPERTY_ID`: default GA4 property ID (numeric, not the `G-` measurement ID)
- `GOOGLE_APPLICATION_CREDENTIALS`: absolute path to a service-account JSON key
- `DISABLE_TELEMETRY=1` / `DO_NOT_TRACK=1`: stop anonymous diagnostics and the local ID file

GA4 MCP is an independent project, not affiliated with or endorsed by Google. "Google Analytics" is a
trademark of Google LLC.
"""
    (DIST / "llms.txt").write_text(llms, encoding="utf-8")

    skills_full = "\n\n".join(
        f"## Skill: {s['title']}\n\nSource: {SITE}/skills/{s['slug']}/index.md\n\n{s['md']}" for s in skills)
    docs_full = "\n\n".join(f"## {meta_for(f'/{slug}/')['title']}\n\n{(ROOT / rel).read_text(encoding='utf-8')}"
                            for slug, rel in (("setup", "docs/setup.md"), ("schema", "docs/schema.md"),
                                              ("iam", "docs/iam.md")))
    full = (f"""# GA4 MCP Server — full text

> Every documentation page and every skill in one file, for agents that would rather read once than crawl.
> Canonical: {SITE} · Updated {BUILD_DATE}

# Home

""" + home_markdown(skills).split("---\n\n", 1)[1]
           + "\n\n# Documentation\n\n" + docs_full
           + "\n\n# Skills\n\n" + skills_full)
    (DIST / "llms-full.txt").write_text(full, encoding="utf-8")


def build_robots(urls: list[str]) -> None:
    bots = ("GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-SearchBot", "PerplexityBot",
            "Google-Extended", "Applebot-Extended", "CCBot", "Amazonbot")
    robots = ("# https://ga4mcp.com/robots.txt\n"
              "User-agent: *\nAllow: /\n\n"
              "# Answer engines and AI assistants: read and cite the docs.\n"
              + "".join(f"User-agent: {bot}\nAllow: /\n" for bot in bots)
              + "\n# LLMs: https://ga4mcp.com/llms.txt\n"
              + "Sitemap: https://ga4mcp.com/sitemap.xml\n")
    (DIST / "robots.txt").write_text(robots, encoding="utf-8")

    priority = {"/": "1.0", "/setup/": "0.9", "/skills/": "0.9", "/schema/": "0.8", "/iam/": "0.8"}
    entries = "\n".join(
        f"  <url>\n    <loc>{SITE}{u}</loc>\n    <lastmod>{BUILD_DATE}</lastmod>\n"
        f"    <priority>{priority.get(u, '0.7')}</priority>\n  </url>" for u in urls)
    (DIST / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + entries + "\n</urlset>\n", encoding="utf-8")

    redirects = """# Legacy paths -> clean URLs (Netlify _redirects)
/setup.md            /setup/            301
/schema.md           /schema/           301
/iam.md              /iam/              301
/privacy.html        /privacy/          301
/terms.html          /terms/            301
# Old skill URLs -> skill pages
/skills/*/SKILL.md   /skills/:splat/    301
# No-trailing-slash variants of the directory URLs
/setup               /setup/            301
/schema              /schema/           301
/iam                 /iam/              301
/privacy             /privacy/          301
/terms               /terms/            301
/skills              /skills/           301
/skills/:slug        /skills/:slug/     301
# Installer endpoint (unchanged)
/install             https://ga4.builditwithai.xyz/?src=install  302
"""
    (DIST / "_redirects").write_text(redirects, encoding="utf-8")


def build_data(skills: list[dict]) -> None:
    tools = {"site": SITE, "updated": BUILD_DATE, "count": len(TOOLS), "tools": [
        {"name": name, "parameters": args, "description": plain(desc.split(". ")[0] + "."), "read_only": True,
         "documentation": f"{SITE}/#agents"}
        for name, args, desc in TOOLS]}
    (DIST / "data").mkdir(parents=True, exist_ok=True)
    (DIST / "data" / "tools.json").write_text(json.dumps(tools, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    skill_data = {"site": SITE, "updated": BUILD_DATE, "count": len(skills), "skills": [
        {"slug": s["slug"], "title": s["title"], "description": s["summary"],
         "url": f"{SITE}/skills/{s['slug']}/", "markdown_url": f"{SITE}/skills/{s['slug']}/index.md",
         "resource": f"skill://{s['slug']}"} for s in skills]}
    (DIST / "data" / "skills.json").write_text(json.dumps(skill_data, indent=2, ensure_ascii=False) + "\n",
                                               encoding="utf-8")


def copy_assets() -> list[str]:
    ASSETS_OUT.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(STYLE_SRC, ASSETS_OUT / "style.css")
    copied = ["assets/style.css"]
    (ASSETS_OUT / "fonts").mkdir(parents=True, exist_ok=True)
    for name in ("InterVariable.woff2", "newsreader-normal.woff2"):
        source = SRC_ASSETS / "fonts" / name
        if not source.is_file():
            sys.exit(f"site/src-assets/fonts/{name} is missing — copy it from the Workbench theme (OFL).")
        shutil.copyfile(source, ASSETS_OUT / "fonts" / name)
        copied.append(f"assets/fonts/{name}")
    for name in ("og.png", "favicon.svg", "favicon-32.png", "favicon-16.png", "apple-touch-icon-180.png"):
        source = SRC_ASSETS / name
        if not source.is_file():
            sys.exit(f"site/src-assets/{name} is missing — run site/tools/render-assets.py")
        shutil.copyfile(source, DIST / name)
        copied.append(name)
    return copied


# --------------------------------------------------------------------------- checks
def check_links() -> tuple[list[str], list[str]]:
    failures, warnings = [], []
    for url, entry in PAGES.items():
        for target, frag in re.findall(r'href="(/[^"#?]*)(?:#([^"]*))?"', entry["html"]):
            if target.endswith(".md"):
                continue  # twins are linked on purpose
            if target in REDIRECT_ONLY:
                continue  # served by _redirects / the edge function, not a file
            resolved = None
            for candidate in (DIST / target.lstrip("/"), DIST / target.lstrip("/") / "index.html"):
                if candidate.is_file():
                    resolved = candidate
                    break
            if not resolved:
                failures.append(f"{url} -> {target} (no file in site/dist/)")
            elif frag and f'id="{frag}"' not in resolved.read_text(encoding="utf-8"):
                warnings.append(f"{url} -> {target}#{frag} (anchor not found)")
    return failures, warnings


def check_twins() -> list[str]:
    problems = []
    for url, entry in PAGES.items():
        twin = twin_url(url)
        declared = f'rel="alternate" type="text/markdown"' in entry["html"]
        if entry["md_file"] is None:
            if declared:
                problems.append(f"{url}: declares a markdown twin but has none")
            continue
        if not declared and url not in FROZEN_URLS:
            problems.append(f"{url}: markdown twin exists but is not advertised in <head>")
        text = entry["md_file"].read_text(encoding="utf-8")
        if not text.startswith("---\n"):
            problems.append(f"{twin}: twin is missing YAML frontmatter")
        if len(text.split()) < 60:
            problems.append(f"{twin}: twin has under 60 words")
        if "# " not in text:
            problems.append(f"{twin}: twin has no markdown H1")
    return problems


def check_legal() -> list[str]:
    problems = []
    for url, filename in (("/privacy/", "privacy.html"), ("/terms/", "terms.html")):
        source = DOCS / filename
        if not source.is_file():
            problems.append(f"{filename}: source missing, text check skipped")
            continue
        expected = legal_body(filename)
        page = PAGES[url]["html"]
        got = page[page.index("<h1"):page.index("</article>")].rstrip()
        if got != expected:
            if visible_text(got) == visible_text(expected):
                problems.append(f"{url}: markup differs from docs/{filename} (words identical)")
            else:
                exp, act = visible_text(expected).split(), visible_text(got).split()
                first = next((i for i, (a, b) in enumerate(zip(exp, act)) if a != b), min(len(exp), len(act)))
                problems.append(f"{url}: TEXT CHANGED vs docs/{filename} at word {first}: "
                                f"{' '.join(exp[first:first + 6])!r} -> {' '.join(act[first:first + 6])!r}")
    return problems


def check_nojs() -> list[str]:
    problems = []
    for url, entry in PAGES.items():
        stripped = re.sub(r"<script.*?</script>", "", entry["html"], flags=re.S)
        if not re.search(r"<h1[^>]*>\s*\S", stripped):
            problems.append(f"{url}: no H1 text without scripts")
        if len(re.sub(r"<[^>]+>", " ", stripped).split()) < 60:
            problems.append(f"{url}: under 60 words of text without scripts")
    return problems


def check_meta() -> list[str]:
    problems = []
    for url in PAGES:
        meta = meta_for(url)
        if len(meta["title"]) > 60:
            problems.append(f"{url}: title is {len(meta['title'])} chars (>60): {meta['title']!r}")
        if len(meta["description"]) > 155:
            problems.append(f"{url}: description is {len(meta['description'])} chars (>155)")
        if not meta["description"]:
            problems.append(f"{url}: no description in site/meta.json")
    return problems


def check_banned() -> list[str]:
    problems = []
    for url, entry in PAGES.items():
        if url in FROZEN_URLS:
            continue
        low = entry["html"].lower()
        for token in BANNED:
            if re.search(rf"\b{re.escape(token)}", low):
                problems.append(f"{url}: banned token {token!r} in generated HTML")
    return problems


def check_sitemap(urls: list[str]) -> list[str]:
    problems = []
    text = (DIST / "sitemap.xml").read_text(encoding="utf-8")
    for url in urls:
        if f"<loc>{SITE}{url}</loc>" not in text:
            problems.append(f"sitemap.xml is missing {url}")
    if len(urls) != len(set(urls)):
        problems.append("sitemap URL list has duplicates")
    for url in urls:
        if url not in PAGES:
            problems.append(f"sitemap lists {url} but no page was built")
    return problems


def check_counts(skills: list[dict]) -> list[str]:
    problems = []
    if len(TOOLS) != TOOLS_COUNT:
        problems.append(f"expected {TOOLS_COUNT} tools, build has {len(TOOLS)}")
    if len(skills) != SKILLS_COUNT:
        problems.append(f"expected {SKILLS_COUNT} skills, found {len(skills)}")
    for url in ("/llms.txt", "/llms-full.txt", "/robots.txt", "/sitemap.xml", "/_redirects", "/404.html",
                "/og.png", "/favicon.svg", "/data/tools.json", "/data/skills.json", "/assets/style.css",
                "/assets/fonts/InterVariable.woff2", "/assets/fonts/newsreader-normal.woff2"):
        if not (DIST / url.lstrip("/")).is_file():
            problems.append(f"{url} was not written")
    return problems


def main() -> int:
    if not (SITE_DIR / "meta.json").is_file():
        return print("site/meta.json is missing") or 1
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)

    skills = discover_skills()
    SKILLS_NAV.extend(skills)
    copied = copy_assets()

    build_home(skills)
    build_docs()
    build_skills(skills)
    build_legal()
    build_not_found()

    urls = ["/"] + [f"/{s}/" for s in ("setup", "schema", "iam")] + ["/skills/"] + \
           [f"/skills/{s['slug']}/" for s in skills] + ["/privacy/", "/terms/"]
    build_llms(skills)
    build_robots(urls)
    build_data(skills)

    problems = (check_links()[0] + check_twins() + check_legal() + check_nojs() + check_meta()
                + check_banned() + check_sitemap(urls) + check_counts(skills))

    print("\nURL                                  bytes  twin  file")
    for url in urls:
        entry = PAGES[url]
        twin = f"{entry['md_file'].stat().st_size:>6}" if entry["md_file"] else "     -"
        print(f"{url:<36} {entry['file'].stat().st_size:>6}  {twin}  {entry['file'].relative_to(ROOT)}")
    for name in ("index.md", "llms.txt", "llms-full.txt", "robots.txt", "sitemap.xml", "_redirects", "404.html",
                 "og.png", "favicon.svg", "favicon-16.png", "favicon-32.png", "apple-touch-icon-180.png",
                 "data/tools.json", "data/skills.json", "assets/style.css"):
        print(f"{'/' + name:<36} {(DIST / name).stat().st_size:>6}        site/dist/{name}")
    print("assets:", ", ".join(copied))

    warnings = check_links()[1]
    for warning in warnings:
        print("warn:", warning)
    for problem in problems:
        print("FAIL:", problem)
    if problems:
        return 1
    twins = sum(1 for e in PAGES.values() if e["md_file"])
    print(f"\nOK — {len(PAGES)} pages ({twins} with markdown twins), {len(TOOLS)} tools, {len(skills)} skills, "
          f"{len(urls)} sitemap URLs, legal text byte-identical, {len(warnings)} warnings.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
