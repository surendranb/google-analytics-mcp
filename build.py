#!/usr/bin/env python3
"""Pre-render ga4mcp.com into dist/ — every URL ships full HTML, no client-side rendering.

Build (markdown is the only third-party dep; fetched by uv if not already cached):

    uv run --no-project --with markdown python3 build.py

--no-project keeps uv from syncing the package env or rewriting uv.lock, so the
only thing this command touches is dist/.

Source of truth (dist/ is generated, never hand-edit it):

    docs/setup.md, docs/schema.md, docs/iam.md   -> /setup /schema /iam
    skills/<slug>/SKILL.md  (15, YAML head stripped) -> /skills/<slug>/
    skills/index.md                              -> /skills/
    docs/privacy.html, docs/terms.html           -> /privacy /terms (text frozen)
    llms.txt                                     -> /llms.txt
    README.md, pyproject.toml, npm/package.json  -> untouched by this script

Generated into dist/ (committed, so the Netlify deploy is the same bytes every time):
    22 HTML pages, assets/style.css, favicon.svg, favicon-16/32.png,
    apple-touch-icon-180.png, og.png, robots.txt, sitemap.xml, _redirects, 404.html

Designer overrides: drop og.png / favicon.svg / logo.svg into the asset dir
(default: ~/Projects/Studio-CMO/memory/drafts/ga4mcp-revamp/assets, or point
GA4MCP_ASSETS at it) and this script copies them over the generated placeholders.
Copy overrides into dist/ itself before building if the build must run offline
without that directory.

Meta overrides: set GA4MCP_META_JSON (or add site-meta.json at the repo root) to
a JSON map of {"/path": {"title": ..., "description": ...}} and it wins over the
placeholder titles in META below.

Legal text: /privacy and /terms are transplanted verbatim from docs/*.html —
the build fails if the visible words change.
"""

from __future__ import annotations

import html
import json
import os
import re
import shutil
import struct
import sys
import zlib
from datetime import date
from html.parser import HTMLParser
from pathlib import Path

try:
    import markdown as mdlib
except ImportError:  # pragma: no cover - build-time guard
    sys.exit("markdown is missing. Run:  uv run --with markdown python3 build.py")

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
SKILLS_SRC = ROOT / "skills"
DOCS_SRC = ROOT / "docs"
ASSETS_OUT = DIST / "assets"

SITE = "https://ga4mcp.com"
REPO = "https://github.com/surendranb/google-analytics-mcp"
PYPI = "https://pypi.org/project/google-analytics-mcp/"
NPM = "https://www.npmjs.com/package/@surendranb/google-analytics-mcp"
INSTALL = "https://ga4.builditwithai.xyz/install"
SITE_YEAR = 2026

CREAM = (254, 246, 228)
NAVY = (0, 24, 88)
PINK = (245, 130, 174)
TEAL = (139, 211, 221)
WHITE = (255, 255, 255)

TRACKING = """  <!-- PostHog Tracking -->
  <script>
    !function(t,e){var o,n,p,r;e.__SV||(window.posthog=e,e._i=[],e.init=function(i,s,a){function g(t,e){var o=e.split(".");2==o.length&&(t=t[o[0]],e=o[1]),t[e]=function(){t.push([e].concat(Array.prototype.slice.call(arguments,0)))}}(p=t.createElement("script")).type="text/javascript",p.async=!0,p.src=s.api_host.replace(".i.posthog.com","-assets.i.posthog.com")+"/static/array.js",(r=t.getElementsByTagName("script")[0]).parentNode.insertBefore(p,r);var u=e;for(void 0!==a?u=e[a]=[]:a="posthog",u.people=u.people||[],u.toString=function(t){var e="posthog";return"posthog"!==a&&(e+="."+a),t||(e+=" (stub)"),e},u.people.toString=function(){return u.toString(1)+".people (stub)"},o="capture identify alias people.set people.set_once set_config register register_once unregister opt_out_capturing has_opted_out_capturing opt_in_capturing reset isFeatureEnabled onFeatureFlags getFeatureFlag getFeatureFlagPayload reloadFeatureFlags group updateEarlyAccessFeatureEnrollment getActiveEarlyAccessFeatures getActiveMatchingSurveys getSurveys getNextSurveyStep onSessionId setPersonProperties".split(" "),n=0;n<o.length;n++)g(u,o[n]);e._i.push([i,s,a])},e.__SV=1)}(document,window.posthog||[]);
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

MARK = ('<svg class="mark" width="26" height="26" viewBox="0 0 100 100" aria-hidden="true" focusable="false">'
        '<rect x="14" y="54" width="16" height="38" rx="8" fill="#8bd3dd"/>'
        '<rect x="42" y="40" width="16" height="52" rx="8" fill="#f582ae"/>'
        '<rect x="70" y="26" width="16" height="66" rx="8" fill="#001858"/></svg>')

MARK_DESC = "rising bars — three capsule bars on a common baseline"


def brand_mark() -> str:
    """Inline header mark. A designer mark.svg (fallback logo.svg) wins over the built-in bars."""
    for name in ("mark.svg", "logo.svg"):
        override = ASSETS_IN / name if ASSETS_IN else None
        if override and override.is_file():
            svg = re.sub(r"<\?xml[^>]*\?>", "", override.read_text(encoding="utf-8"))
            svg = re.sub(r"<title>.*?</title>", "", svg, flags=re.S).strip()
            tag = re.search(r"<svg[^>]*>", svg)
            if tag:
                # keep viewBox (dropping it renders the bars off-canvas); set our own size + a11y
                new_tag = re.sub(r'\s(?:role|aria-label|width|height)="[^"]*"', "", tag.group(0))
                new_tag = new_tag.replace(
                    "<svg", '<svg class="mark" width="26" height="26" aria-hidden="true" focusable="false"', 1)
                svg = svg[:tag.start()] + new_tag + svg[tag.end():]
            return re.sub(r"\s+", " ", svg).strip()
    return MARK

CSS = """/* GA4 MCP — Happy Hues #17. Cream field, navy type, pink + teal accents. */
:root {
  --cream: #fef6e4;
  --navy: #001858;
  --pink: #f582ae;
  --teal: #8bd3dd;
  --muted: #41508a;
  --surface: #ffffff;
  --soft: #fdf0dc;
  --shadow: 4px 4px 0 var(--navy);
  --shadow-sm: 3px 3px 0 var(--navy);
  --radius: 10px;
  --font: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  --mono: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Monaco, Consolas, monospace;
  --wrap: 1080px;
  --prose: 74ch;
}
*, *::before, *::after { box-sizing: border-box; }
html { -webkit-text-size-adjust: 100%; }
body {
  margin: 0;
  background: var(--cream);
  color: var(--navy);
  font-family: var(--font);
  font-size: 17px;
  line-height: 1.65;
  -webkit-font-smoothing: antialiased;
}
.wrap { width: 100%; max-width: var(--wrap); margin: 0 auto; padding: 0 1.25rem; }

/* skip link */
.skip {
  position: absolute; left: -9999px; top: 0; z-index: 30;
  background: var(--navy); color: var(--cream);
  padding: .7rem 1rem; font-weight: 700; text-decoration: none;
}
.skip:focus { left: .5rem; top: .5rem; outline: 3px solid var(--pink); outline-offset: 2px; }

/* header */
.site-header { position: sticky; top: 0; z-index: 20; background: var(--cream); border-bottom: 2px solid var(--navy); }
.bar { display: flex; align-items: center; justify-content: space-between; gap: 1rem; flex-wrap: wrap; padding-top: .55rem; padding-bottom: .55rem; }
.brand { display: inline-flex; align-items: center; gap: .55rem; font-weight: 800; letter-spacing: -.01em; font-size: 1.05rem; color: var(--navy); text-decoration: none; }
.brand .mark { display: block; }
nav.main ul, footer nav ul { list-style: none; margin: 0; padding: 0; display: flex; flex-wrap: wrap; align-items: center; gap: .15rem .35rem; }
nav.main a, footer nav a {
  display: inline-block; padding: .45rem .55rem; min-height: 40px;
  color: var(--navy); text-decoration: none; font-weight: 600; font-size: .95rem;
  border-radius: 6px; border: 2px solid transparent;
}
nav.main a:hover, footer nav a:hover { background: var(--teal); }
nav.main a[aria-current="page"] { border-color: var(--navy); background: var(--pink); }

/* focus */
a:focus-visible, button:focus-visible, summary:focus-visible {
  outline: 3px solid var(--pink); outline-offset: 2px; border-radius: 4px;
}

/* main + prose */
main { display: block; padding: 2.25rem 0 3.5rem; }
.prose { max-width: var(--prose); }
h1 { font-size: clamp(1.75rem, 4.5vw, 2.5rem); line-height: 1.2; letter-spacing: -.02em; margin: 0 0 1rem; }
h2 { font-size: clamp(1.25rem, 2.4vw, 1.55rem); line-height: 1.3; margin: 2.4rem 0 .8rem; padding-bottom: .35rem; border-bottom: 2px solid var(--navy); }
h3 { font-size: 1.12rem; margin: 1.8rem 0 .5rem; }
h4 { font-size: 1rem; margin: 1.4rem 0 .4rem; }
p, ul, ol { margin: 0 0 1.1rem; }
ul, ol { padding-left: 1.4rem; }
li { margin-bottom: .4rem; }
strong { font-weight: 700; }
hr { border: 0; border-top: 2px solid var(--navy); margin: 2.5rem 0; }
blockquote { margin: 1.4rem 0; padding: .2rem 1rem; border-left: 6px solid var(--teal); }

a { color: var(--navy); text-decoration: underline; text-decoration-color: var(--pink); text-decoration-thickness: 2px; text-underline-offset: 3px; }
a:hover { background: rgba(245, 130, 174, .28); }

code { font-family: var(--mono); font-size: .88em; background: var(--surface); border: 1px solid var(--navy); border-radius: 5px; padding: .08em .34em; }
pre { background: var(--navy); color: var(--cream); padding: 1rem 1.1rem; border-radius: var(--radius); overflow-x: auto; margin: 0 0 1.4rem; font-size: .86rem; line-height: 1.55; box-shadow: var(--shadow-sm); }
pre code { background: none; border: 0; padding: 0; color: inherit; font-size: 1em; }
pre a { color: var(--teal); }

.tscroll { overflow-x: auto; margin: 1.5rem 0; border: 2px solid var(--navy); border-radius: var(--radius); background: var(--surface); box-shadow: var(--shadow-sm); }
.tscroll table { margin: 0; }
table { width: 100%; border-collapse: collapse; font-size: .93rem; }
/* long unbreakable tokens (OAuth scope URLs, hostnames) wrap instead of widening the page */
.prose, .prose p, .prose li, .prose td, .prose th, .summary-table { overflow-wrap: anywhere; }
code { overflow-wrap: anywhere; }
pre code { overflow-wrap: normal; white-space: pre; }
th, td { text-align: left; vertical-align: top; padding: .6rem .75rem; border-bottom: 1px solid rgba(0, 24, 88, .22); border-right: 1px solid rgba(0, 24, 88, .22); }
th { background: var(--teal); font-weight: 700; }
tbody tr:nth-child(even) td { background: var(--soft); }
th:last-child, td:last-child { border-right: 0; }
tbody tr:last-child td { border-bottom: 0; }
td code, th code { border: 0; background: rgba(0, 24, 88, .06); }

/* home */
.eyebrow { margin: 0 0 .7rem; font-size: .82rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; color: var(--muted); }
.lead { font-size: 1.13rem; max-width: 62ch; }
.chips { list-style: none; padding: 0; margin: 1.5rem 0 0; display: flex; flex-wrap: wrap; gap: .5rem; }
.chip { border: 2px solid var(--navy); border-radius: 999px; background: var(--surface); padding: .22rem .7rem; font-size: .8rem; font-weight: 700; }
.cta { display: flex; flex-wrap: wrap; gap: .7rem; margin: 1.6rem 0 0; }
.btn { display: inline-block; padding: .68rem 1.1rem; border: 2px solid var(--navy); border-radius: 8px; background: var(--pink); color: var(--navy); font-weight: 700; text-decoration: none; box-shadow: var(--shadow-sm); }
.btn:hover { background: var(--teal); }
.btn.ghost { background: var(--surface); }
.grid { list-style: none; padding: 0; margin: 1.5rem 0 0; display: grid; gap: 1rem; grid-template-columns: repeat(auto-fill, minmax(min(100%, 270px), 1fr)); }
.card { background: var(--surface); border: 2px solid var(--navy); border-radius: var(--radius); padding: 1rem 1.1rem; box-shadow: var(--shadow-sm); }
.card h3 { margin: 0 0 .35rem; font-size: 1.02rem; }
.card p { margin: 0; font-size: .92rem; color: var(--muted); }
.sr-only { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }
.faq h3 { margin-top: 1.9rem; }
.faq p { color: var(--muted); }
.note { border-left: 6px solid var(--teal); background: var(--surface); border-radius: 0 var(--radius) var(--radius) 0; padding: .9rem 1.1rem; margin: 1.5rem 0; }
.doc-note { font-size: .88rem; color: var(--muted); border-top: 1px solid rgba(0, 24, 88, .25); margin-top: 2.5rem; padding-top: .8rem; }
.back { display: inline-block; margin: 0 0 1rem; font-weight: 700; font-size: .92rem; }
.section-head { display: flex; flex-wrap: wrap; align-items: baseline; justify-content: space-between; gap: .5rem; }

/* legal pages keep the source markup; these classes come from docs/*.html */
.container { max-width: var(--prose); }
.meta { font-size: .9rem; color: var(--muted); margin: 0 0 2rem; padding-bottom: 1rem; border-bottom: 1px solid rgba(0, 24, 88, .3); }
.callout { background: var(--surface); border-left: 6px solid var(--pink); border-radius: 0 var(--radius) var(--radius) 0; padding: 1.1rem 1.3rem; margin: 1.6rem 0; font-family: var(--mono); font-size: .88rem; line-height: 1.6; }
.summary-card { background: var(--surface); border: 2px solid var(--navy); border-radius: var(--radius); box-shadow: var(--shadow-sm); padding: 1.3rem 1.4rem; margin: 2rem 0 2.5rem; }
.summary-card h2 { margin-top: 0; }
.summary-table { border: 2px solid var(--navy); border-radius: 6px; table-layout: fixed; }
.summary-table th { width: 38%; }
.footer { margin-top: 3rem; padding-top: 1.2rem; border-top: 1px solid rgba(0, 24, 88, .3); font-size: .88rem; color: var(--muted); display: flex; flex-wrap: wrap; justify-content: space-between; gap: .8rem; }

/* footer */
.site-footer { border-top: 2px solid var(--navy); background: var(--cream); padding: 1.6rem 0 2.2rem; font-size: .92rem; }
.site-footer p { margin: 0 0 .7rem; }
.foot-legal { color: var(--muted); font-size: .85rem; }

@media (max-width: 640px) {
  body { font-size: 16px; }
  .bar { padding-top: .5rem; padding-bottom: .5rem; }
  nav.main a { padding: .45rem .5rem; font-size: .9rem; }
  pre { font-size: .78rem; }
  th, td { padding: .5rem .55rem; }
  .summary-table { font-size: .82rem; }
  .summary-table th { width: 45%; }
}
@media (prefers-reduced-motion: reduce) {
  * { transition: none !important; animation: none !important; scroll-behavior: auto !important; }
}
"""

# 5x7 bitmap font for the generated OG card and nothing else (no webfonts ship).
FONT: dict[str, str] = {
    "A": "01110/10001/10001/11111/10001/10001/10001",
    "B": "11110/10001/10001/11110/10001/10001/11110",
    "C": "01111/10000/10000/10000/10000/10000/01111",
    "D": "11110/10001/10001/10001/10001/10001/11110",
    "E": "11111/10000/10000/11110/10000/10000/11111",
    "F": "11111/10000/10000/11110/10000/10000/10000",
    "G": "01111/10000/10000/10111/10001/10001/01111",
    "H": "10001/10001/10001/11111/10001/10001/10001",
    "I": "11111/00100/00100/00100/00100/00100/11111",
    "J": "00111/00010/00010/00010/00010/10010/01100",
    "K": "10001/10010/10100/11000/10100/10010/10001",
    "L": "10000/10000/10000/10000/10000/10000/11111",
    "M": "10001/11011/10101/10101/10001/10001/10001",
    "N": "10001/11001/10101/10011/10001/10001/10001",
    "O": "01110/10001/10001/10001/10001/10001/01110",
    "P": "11110/10001/10001/11110/10000/10000/10000",
    "Q": "01110/10001/10001/10001/10101/10010/01101",
    "R": "11110/10001/10001/11110/10100/10010/10001",
    "S": "01111/10000/10000/01110/00001/00001/11110",
    "T": "11111/00100/00100/00100/00100/00100/00100",
    "U": "10001/10001/10001/10001/10001/10001/01110",
    "V": "10001/10001/10001/10001/10001/01010/00100",
    "W": "10001/10001/10001/10101/10101/11011/10001",
    "X": "10001/10001/01010/00100/01010/10001/10001",
    "Y": "10001/10001/01010/00100/00100/00100/00100",
    "Z": "11111/00001/00010/00100/01000/10000/11111",
    "0": "01110/10011/10101/10101/10101/11001/01110",
    "1": "00100/01100/00100/00100/00100/00100/01110",
    "2": "01110/10001/00001/00110/01000/10000/11111",
    "3": "11111/00010/00100/00010/00001/10001/01110",
    "4": "00010/00110/01010/10010/11111/00010/00010",
    "5": "11111/10000/11110/00001/00001/10001/01110",
    "6": "00110/01000/10000/11110/10001/10001/01110",
    "7": "11111/00001/00010/00100/01000/01000/01000",
    "8": "01110/10001/10001/01110/10001/10001/01110",
    "9": "01110/10001/10001/01111/00001/00010/01100",
    ".": "00000/00000/00000/00000/00000/01100/01100",
    ":": "00000/01100/01100/00000/01100/01100/00000",
    "-": "00000/00000/00000/11111/00000/00000/00000",
    "/": "00001/00010/00010/00100/01000/01000/10000",
    "+": "00000/00100/00100/11111/00100/00100/00000",
    " ": "",
}


class Canvas:
    """Minimal RGB canvas — stdlib zlib + struct, so the build stays offline."""

    def __init__(self, width: int, height: int, bg: tuple[int, int, int] = CREAM):
        self.w = width
        self.h = height
        self.px = bytearray(bytes(bg) * (width * height))

    def rect(self, x: int, y: int, w: int, h: int, color: tuple[int, int, int]) -> None:
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(color) * (x1 - x0)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            self.px[i:i + len(row)] = row

    def text(self, s: str, x: int, y: int, scale: int, color: tuple[int, int, int], tracking: int = 1) -> int:
        cx = x
        for ch in s.upper():
            glyph = FONT.get(ch)
            if glyph:
                for ry, row in enumerate(glyph.split("/")):
                    for rx, bit in enumerate(row):
                        if bit == "1":
                            self.rect(cx + rx * scale, y + ry * scale, scale, scale, color)
            cx += (5 + tracking) * scale
        return cx

    def save(self, path: Path) -> None:
        raw = b"".join(b"\x00" + bytes(self.px[y * self.w * 3:(y + 1) * self.w * 3]) for y in range(self.h))

        def chunk(tag: bytes, data: bytes) -> bytes:
            return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

        blob = (b"\x89PNG\r\n\x1a\n"
                + chunk(b"IHDR", struct.pack(">IIBBBBB", self.w, self.h, 8, 2, 0, 0, 0))
                + chunk(b"IDAT", zlib.compress(raw, 9))
                + chunk(b"IEND", b""))
        path.write_bytes(blob)


def badge(c: Canvas, x: int, y: int, size: int) -> None:
    """Badge form of the mark: navy tile, bars inverted to teal / pink / cream (designer system)."""
    c.rect(x, y, size, size, NAVY)
    for bx, by, bh, color in ((26.5, 50, 24, TEAL), (44.5, 40, 34, PINK), (62.5, 30, 44, CREAM)):
        c.rect(round(x + size * bx / 100), round(y + size * by / 100),
               max(2, round(size * 11 / 100)), max(2, round(size * bh / 100)), color)


def build_og() -> None:
    """Placeholder OG card; the designer og.png in the asset dir replaces it byte for byte."""
    W, H = 1200, 630
    c = Canvas(W, H, CREAM)
    for x, y, w, h in ((0, 0, W, 10), (0, H - 10, W, 10), (0, 0, 10, H), (W - 10, 0, 10, H)):
        c.rect(x, y, w, h, NAVY)
    badge(c, 72, 84, 132)
    c.text("GA4 MCP SERVER", 240, 88, 9, NAVY)
    c.text("GOOGLE ANALYTICS 4 FOR AI AGENTS", 240, 176, 4, NAVY)
    c.rect(72, 262, W - 144, 12, PINK)
    c.text("QUERY GA4 FROM CLAUDE, CURSOR, VS CODE", 72, 316, 4, NAVY)
    c.text("SCHEMA DISCOVERY + SERVER-SIDE TOTALS", 72, 366, 4, NAVY)
    c.text("11 TOOLS. 15 SKILLS. MIT LICENSED.", 72, 416, 4, NAVY)
    c.text("GA4MCP.COM", 72, 508, 6, NAVY)
    for i, color in enumerate((TEAL, PINK, NAVY)):
        c.rect(W - 300 + i * 64, 504, 48, 48, color)
    c.save(DIST / "og.png")


def build_icons() -> None:
    favicon_svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" role="img" aria-label="GA4 MCP Server">'
                   '<rect x="0" y="0" width="100" height="100" rx="19" fill="#001858"/>'
                   '<rect x="26.5" y="50" width="11" height="24" rx="5.5" fill="#8bd3dd"/>'
                   '<rect x="44.5" y="40" width="11" height="34" rx="5.5" fill="#f582ae"/>'
                   '<rect x="62.5" y="30" width="11" height="44" rx="5.5" fill="#fef6e4"/></svg>\n')
    (DIST / "favicon.svg").write_text(favicon_svg, encoding="utf-8")
    for size, name in ((16, "favicon-16.png"), (32, "favicon-32.png"), (180, "apple-touch-icon-180.png")):
        c = Canvas(size, size, NAVY)
        badge(c, 0, 0, size)
        c.save(DIST / name)


# --------------------------------------------------------------------------- pages
META: dict[str, dict[str, str]] = {
    "/": {
        "title": "GA4 MCP Server: Google Analytics 4 for AI agents",
        "description": ("MCP server that gives AI agents analysis-ready access to Google Analytics 4 — "
                        "schema discovery, server-side totals, 11 tools, 15 analytical skills. MIT licensed, runs locally."),
    },
    "/setup": {
        "title": "Setup and troubleshooting: GA4 MCP Server",
        "description": ("Fix GA4 MCP setup errors: missing GA4_PROPERTY_ID, missing "
                        "GOOGLE_APPLICATION_CREDENTIALS, and expired Application Default Credentials."),
    },
    "/schema": {
        "title": "Filter schema reference: GA4 MCP Server",
        "description": ("Exact JSON shapes for dimension_filter and metric_filter in get_ga4_data: string, inList, "
                        "numeric, andGroup, orGroup, notExpression — camelCase and snake_case."),
    },
    "/iam": {
        "title": "IAM permissions: GA4 MCP Server",
        "description": ("Grant a service account Viewer access in Google Analytics: Property Access Management "
                        "steps, the exact role, and what to do when the 403 clears late."),
    },
    "/skills/": {
        "title": "GA4 MCP skills library: 15 analytical recipes",
        "description": ("15 GA4 analysis recipes with the exact dimensions, metrics, filters, and interpretation "
                        "rules — traffic diagnosis, attribution, ecommerce, AI referrals, bot filtering."),
    },
    "/privacy": {
        "title": "Privacy Policy: GA4 MCP",
        "description": ("GA4 MCP privacy policy and Google API Limited Use disclosure: zero server storage, "
                        "local token storage, deletion and revocation steps."),
    },
    "/terms": {
        "title": "Terms of Service: GA4 MCP",
        "description": ("GA4 MCP terms: MIT license text, Google APIs terms, the stateless OAuth relay, "
                        "warranty disclaimers, and contact details."),
    },
    "/404": {
        "title": "Page not found: GA4 MCP Server",
        "description": "That URL does not exist on ga4mcp.com. Start from the GA4 MCP setup guide, filter schema, or agent skills library.",
    },
}

META_OVERRIDES: dict[str, dict[str, str]] = {}

# Doc page -> the in-server resource that carries the same guidance.
DOC_SOURCES = {
    "/setup": ("docs/setup.md", "docs://fix/setup"),
    "/schema": ("docs/schema.md", "docs://fix/schema"),
    "/iam": ("docs/iam.md", "docs://fix/iam"),
}


def find_override(candidates: list[Path], env: str) -> Path | None:
    env_path = os.environ.get(env)
    if env_path and Path(env_path).exists():
        return Path(env_path)
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


ASSETS_IN = find_override(
    [Path.home() / "Projects/Studio-CMO/memory/drafts/ga4mcp-revamp/assets", ROOT / "site-assets"],
    "GA4MCP_ASSETS",
)
META_IN = find_override([ROOT / "site-meta.json",
                         Path.home() / "Projects/Studio-CMO/memory/drafts/ga4mcp-revamp/meta.json"],
                        "GA4MCP_META_JSON")


def load_meta_overrides() -> dict[str, dict[str, str]]:
    if not META_IN:
        return {}
    raw = json.loads(META_IN.read_text(encoding="utf-8"))
    raw = raw.get("pages", raw) if isinstance(raw, dict) else {}
    out: dict[str, dict[str, str]] = {}
    for key, value in raw.items():
        if not isinstance(value, dict):
            continue
        path = key if key.startswith("/") else "/" + key
        out[path] = {"title": value.get("title", ""), "description": value.get("description", "")}
    return out


def meta_for(url: str) -> dict[str, str]:
    overrides = META_OVERRIDES.get(url) or META_OVERRIDES.get(url.rstrip("/")) or {}
    base = dict(META.get(url, {}))
    base.update({k: v for k, v in overrides.items() if v})
    return base


def nav_item(href: str, label: str, url: str) -> str:
    active = url == href or (href != "/" and url.startswith(href))
    attr = ' aria-current="page"' if active else ""
    return f'<li><a href="{href}"{attr}>{label}</a></li>'


def shell(url: str, body: str, jsonld: list[dict], og_type: str = "website", noindex: bool = False) -> str:
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
        f'<meta name="theme-color" content="#fef6e4">',
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
        f'<link rel="alternate" type="text/plain" href="{SITE}/llms.txt" title="llms.txt">',
    ]
    for node in jsonld:
        head.append('<script type="application/ld+json">'
                    + json.dumps(node, ensure_ascii=False, separators=(",", ":")) + "</script>")
    head.append(TRACKING.rstrip("\n"))
    head.append("</head>")

    header = f"""<body>
<a class="skip" href="#main">Skip to content</a>
<header class="site-header">
  <div class="wrap bar">
    <a class="brand" href="/">{brand_mark()}<span>GA4 MCP</span></a>
    <nav class="main" aria-label="Main">
      <ul>
        {nav_item("/setup", "Setup", url)}
        {nav_item("/schema", "Filter schema", url)}
        {nav_item("/iam", "IAM", url)}
        {nav_item("/skills/", "Skills", url)}
        <li><a href="{REPO}">GitHub</a></li>
      </ul>
    </nav>
  </div>
</header>"""

    footer = f"""<footer class="site-footer">
  <div class="wrap">
    <p><strong>GA4 MCP Server</strong> — Model Context Protocol server for Google Analytics 4. MIT licensed. Not affiliated with Google.</p>
    <nav aria-label="Footer">
      <ul>
        <li><a href="/setup">Setup</a></li>
        <li><a href="/schema">Filter schema</a></li>
        <li><a href="/iam">IAM</a></li>
        <li><a href="/skills/">Skills</a></li>
        <li><a href="/llms.txt">llms.txt</a></li>
        <li><a href="/robots.txt">robots.txt</a></li>
        <li><a href="/sitemap.xml">Sitemap</a></li>
        <li><a href="/privacy">Privacy</a></li>
        <li><a href="/terms">Terms</a></li>
        <li><a href="{REPO}">GitHub</a></li>
        <li><a href="{PYPI}">PyPI</a></li>
        <li><a href="{NPM}">npm</a></li>
      </ul>
    </nav>
    <p class="foot-legal">&copy; {SITE_YEAR} Surendran Balachandran · GA4 MCP is open source under the MIT License.</p>
  </div>
</footer>"""
    return "\n".join(head) + "\n" + header + "\n<main id=\"main\">\n" + body + "\n</main>\n" + footer + "\n</body>\n</html>\n"


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


def plain(text: str) -> str:
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"[`*_]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def clip(text: str, limit: int = 155) -> str:
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0]
    return cut.rstrip(",;:.") + "…"


def render_markdown(text: str) -> str:
    out = mdlib.markdown(text, extensions=["tables", "fenced_code", "toc"], output_format="html5")
    out = out.replace("<table>", '<div class="tscroll"><table>').replace("</table>", "</table></div>")
    out = re.sub(r'href="([a-z0-9-]+)\.md"', r'href="/\1"', out)
    return out


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


def legal_body(filename: str) -> str:
    """Verbatim content slice of docs/<file> — H1 through the last paragraph."""
    raw = (DOCS_SRC / filename).read_text(encoding="utf-8")
    start = raw.index("<h1")
    end = raw.index('<div class="footer">', start)
    return raw[start:end].rstrip()


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


def write_page(url: str, body: str, jsonld: list[dict], og_type: str = "website", noindex: bool = False) -> str:
    page = shell(url, body, jsonld, og_type=og_type, noindex=noindex)
    target = DIST / "index.html" if url == "/" else (
        DIST / url.strip("/") / "index.html" if url.endswith("/") else DIST / (url.strip("/") + ".html"))
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(page, encoding="utf-8")
    PAGES[url] = page
    return page


# --------------------------------------------------------------------------- content
CHIPS = ["MIT License", "Python 3.10+", "stdio / JSON-RPC", "11 tools", "15 skills", "No server-side data store"]

TOOLS = [
    ("get_ga4_data", "dimensions, metrics, date_range_start, date_range_end, dimension_filter, limit, estimate_only, enable_aggregation, intent",
     "Runs a report and returns rows plus a server-computed <code>totals</code> block, so no caller has to sum rows."),
    ("search_schema", "keyword",
     "Ranks dimension and metric API names for this property. Call it before typing a field name."),
    ("get_property_schema", "—", "Full dimension and metric schema for the property, standard and custom."),
    ("list_dimension_categories", "—", "Dimension categories with counts, for browsing instead of guessing."),
    ("list_metric_categories", "—", "Metric categories with counts."),
    ("get_dimensions_by_category", "category", "Every dimension in one category, with descriptions."),
    ("get_metrics_by_category", "category", "Every metric in one category, with descriptions."),
    ("list_properties", "account_id (optional)", "GA4 properties the credentials can read."),
    ("search_skills", "query (slug or keyword; empty returns the index)", "Serves one analytical recipe as markdown."),
    ("get_troubleshooting_guide", "topic: setup, iam, schema", "The fix path for a boot error, a 403, or a filter-shape error."),
    ("setup_ga4_access", "—", "Collects a missing value interactively and reconnects without a client restart."),
]

FAQS = [
    ("Is GA4 MCP free?",
     "Yes. The package is MIT licensed with no paid tier, no account, and no seat count. It queries the GA4 Data API with your own Google credentials."),
    ("Does my analytics data pass through a third-party server?",
     "No. Queries run from your machine to Google's Analytics Data API over TLS. The optional browser sign-in relay performs one atomic code exchange and keeps no database, cache, or credential log."),
    ("Which analyses can it run, and which can it not?",
     "It runs Data API reporting: dimensions, metrics, filters, period-over-period comparisons, realtime active users, and metadata. Funnel, cohort, path, and raw event-level analysis are not in the Data API — those need GA4 Explorations or a BigQuery export."),
    ("Do I need a service account?",
     "Pick either path: a Google Cloud service account JSON key (<code>GOOGLE_APPLICATION_CREDENTIALS</code>), which is fully offline, or 1-click browser sign-in. Both need Viewer access on the property."),
    ("Why does a query fail with \"Invalid dimension\" or \"Invalid metric\"?",
     "GA4 API names differ from the labels in the GA4 interface, so a hand-typed name is usually wrong. Call <code>search_schema</code> first and query with the name it returns; the filter shape rules live in the filter schema guide."),
    ("Which MCP clients work?",
     "Any client that speaks stdio: Claude Desktop, Claude Code, Cursor, VS Code with Cline or Continue, Windsurf, Antigravity, and Zed. The 1-line installer writes the config for the clients it detects."),
    ("Does the server send telemetry?",
     "Anonymous diagnostics only: installation ID, MCP client name and version, tool name, latency, and error codes. Opt out with <code>DO_NOT_TRACK=1</code>, <code>DISABLE_TELEMETRY=1</code>, or <code>GA_MCP_TELEMETRY=false</code>."),
]


def build_home(skills: list[dict]) -> None:
    tool_rows = "\n".join(
        f"<tr><td><code>{name}</code></td><td>{plain(args)}</td><td>{desc}</td></tr>"
        for name, args, desc in TOOLS)
    cards = "\n".join(
        f'<li class="card"><h3><a href="/skills/{s["slug"]}/">{html.escape(s["title"])}</a></h3>'
        f'<p>{html.escape(s["summary"])}</p></li>' for s in skills)
    faq = "\n".join(f"<h3>{html.escape(q)}</h3>\n<p>{a}</p>" for q, a in FAQS)
    chips = "\n".join(f'<li class="chip">{c}</li>' for c in CHIPS)

    body = f"""  <div class="wrap">
  <article>
    <section class="hero">
      <p class="eyebrow">Model Context Protocol · GA4 Data API v1beta</p>
      <h1>Google Analytics 4 MCP Server</h1>
      <p class="lead">An MCP server that gives AI agents analysis-ready access to Google Analytics 4: schema lookup before a query is built, totals computed on Google's side, and 15 analytical recipes that carry the method with the data. It runs as a local stdio process against your own Google credentials.</p>
      <ul class="chips">{chips}</ul>
      <div class="cta">
        <a class="btn" href="/setup">Setup and troubleshooting</a>
        <a class="btn ghost" href="{REPO}">GitHub repository</a>
      </div>
    </section>

    <h2>Install</h2>
    <pre><code># 1-line installer — writes config for Claude Desktop, Claude Code, Cursor, VS Code, Windsurf, Zed
curl -fsSL "{INSTALL}" | bash

# or run one of these directly (same server, different runtimes)
uvx google-analytics-mcp
uvx --from google-analytics-mcp ga4-mcp-server
python -m ga4_mcp
npx -y @surendranb/google-analytics-mcp</code></pre>
    <p>Then set <code>GA4_PROPERTY_ID</code> and <code>GOOGLE_APPLICATION_CREDENTIALS</code> in the client config. If a boot error appears, the <a href="/setup">setup guide</a> maps each error to its fix.</p>
    <div class="note"><p><strong>Where the 1-line installer points.</strong> <code>{INSTALL}</code> is the installer endpoint; this site is the documentation. The installer is unchanged by this release.</p></div>

    <h2>Tools</h2>
    <p>Eleven tools cover reporting, schema discovery, and the fix paths an agent hits during setup:</p>
    <div class="tscroll"><table>
      <caption class="sr-only">GA4 MCP tools</caption>
      <thead><tr><th>Tool</th><th>Arguments</th><th>What it returns</th></tr></thead>
      <tbody>
{tool_rows}
      </tbody>
    </table></div>
    <p>Also exposed: resources <code>docs://setup_guide</code>, <code>docs://fix/setup</code>, <code>docs://fix/iam</code>, <code>docs://fix/schema</code>, and <code>skill://&lt;slug&gt;</code> for each recipe; prompts <code>traffic_deep_dive</code>, <code>find_whats_broken</code>, and <code>explain_my_traffic_drop</code>.</p>

    <h2>Skills</h2>
    <p>Each skill is a recipe with the dimensions, metrics, filters, and interpretation rules for one question. <a href="/skills/">Browse all 15</a> or load one with <code>search_skills("traffic-diagnosis")</code>.</p>
    <ul class="grid">
{cards}
    </ul>

    <h2>Authentication</h2>
    <p>Two paths, same server. A service account JSON key keeps everything offline; 1-click browser sign-in trades one OAuth hop for fewer steps. Either way the service account or Google account needs <strong>Viewer</strong> on the property — the <a href="/iam">IAM guide</a> walks the Property Access Management screens.</p>

    <h2>FAQ</h2>
    <div class="faq">
{faq}
    </div>

    <p class="doc-note">Source: <a href="{REPO}">github.com/surendranb/google-analytics-mcp</a> · PyPI <a href="{PYPI}">google-analytics-mcp</a> · npm <a href="{NPM}">@surendranb/google-analytics-mcp</a> · <a href="/llms.txt">llms.txt</a> for agents.</p>
  </article>
  </div>"""

    jsonld = [
        {
            "@context": "https://schema.org",
            "@type": "SoftwareApplication",
            "name": "GA4 MCP Server",
            "alternateName": "google-analytics-mcp",
            "applicationCategory": "DeveloperApplication",
            "operatingSystem": "macOS, Linux, Windows",
            "description": "MCP server that gives AI agents analysis-ready access to Google Analytics 4: schema discovery, server-side aggregation, and 15 analytical skills over stdio.",
            "url": SITE + "/",
            "codeRepository": REPO,
            "license": "https://opensource.org/license/mit",
            "isAccessibleForFree": True,
            "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
            "softwareRequirements": "Python 3.10+, or Node 16+ via the npx wrapper",
            "author": {"@type": "Person", "name": "Surendran B"},
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
    ]
    write_page("/", body, jsonld)


def build_docs() -> None:
    for url, (rel, resource) in DOC_SOURCES.items():
        markdown_text = (ROOT / rel).read_text(encoding="utf-8")
        meta = meta_for(url)
        body = f"""  <div class="wrap">
  <article class="prose">
{render_markdown(markdown_text)}
    <p class="doc-note">Served live inside the MCP as the <code>{resource}</code> resource and as <code>get_troubleshooting_guide("&lt;topic&gt;")</code>. Source: <a href="{REPO}/blob/main/{rel}">{rel}</a>.</p>
  </article>
  </div>"""
        write_page(url, body, [tech_article(url, meta["title"], meta["description"])], og_type="article")


def discover_skills() -> list[dict]:
    """One pass over skills/<slug>/SKILL.md — title, summary, and body for pages."""
    found = []
    for skill_dir in sorted(SKILLS_SRC.iterdir()):
        skill_md = skill_dir / "SKILL.md"
        if not skill_dir.is_dir() or not skill_md.is_file():
            continue
        front, body_md = strip_frontmatter(skill_md.read_text(encoding="utf-8"))
        first_line = body_md.splitlines()[0] if body_md.startswith("#") else ""
        title = (re.sub(r"^#\s+", "", first_line).strip()
                 or front.get("name", skill_dir.name).replace("-", " ").title())
        found.append({"slug": skill_dir.name, "title": title, "md": body_md,
                      "summary": clip(plain(front.get("description") or ""), 190)})
    found.sort(key=lambda s: s["title"].lower())
    return found


def build_skills() -> None:
    skills = discover_skills()

    rows = "\n".join(
        f'<li class="card"><h3><a href="/skills/{s["slug"]}/">{html.escape(s["title"])}</a></h3>'
        f'<p>{html.escape(s["summary"])}</p></li>' for s in skills)

    intro_md = (SKILLS_SRC / "index.md").read_text(encoding="utf-8").split("| Skill |")[0]
    intro_md = intro_md.split("\n\n", 1)[1].strip() if "\n\n" in intro_md else intro_md.strip()
    intro = render_markdown(intro_md)

    html_body = f"""  <div class="wrap">
  <article class="prose">
    <h1>GA4 MCP Skills Library</h1>
    <p class="lead">{len(skills)} analytical recipes, each one a page plus an MCP resource at <code>skill://&lt;slug&gt;</code>. Load one in a session with <code>search_skills("&lt;slug&gt;")</code>; the text below is the same content the agent receives.</p>
    <ul class="grid">
{rows}
    </ul>
    {intro}
  </article>
  </div>"""
    write_page("/skills/", html_body, [
        tech_article("/skills/", meta_for("/skills/")["title"], meta_for("/skills/")["description"])])

    for s in skills:
        url = f"/skills/{s['slug']}/"
        META[url] = {"title": f"{s['title']}: GA4 MCP skill",
                     "description": clip(s["summary"] or f"GA4 analysis recipe: {s['title']}.")}
        meta = meta_for(url)
        body = f"""  <div class="wrap">
  <article class="prose">
    <a class="back" href="/skills/">← All skills</a>
{render_markdown(s["md"])}
    <p class="doc-note">Load it in a session with <code>search_skills("{s['slug']}")</code>, or read the MCP resource <code>skill://{s['slug']}</code>. Source: <a href="{REPO}/blob/main/skills/{s['slug']}/SKILL.md">skills/{s['slug']}/SKILL.md</a>.</p>
  </article>
  </div>"""
        write_page(url, body, [tech_article(url, meta["title"], meta["description"])], og_type="article")


def build_legal() -> None:
    for url, filename in (("/privacy", "privacy.html"), ("/terms", "terms.html")):
        fragment = legal_body(filename)
        body = f"""  <div class="wrap">
  <article class="prose legal" data-source="docs/{filename}">
{fragment}
  </article>
  </div>"""
        write_page(url, body, [web_page(url)], og_type="article")


def build_not_found() -> None:
    body = f"""  <div class="wrap">
  <article class="prose">
    <h1>Page not found</h1>
    <p class="lead">That URL does not exist on ga4mcp.com. The documentation starts here:</p>
    <ul>
      <li><a href="/setup">Setup and troubleshooting</a></li>
      <li><a href="/schema">Filter schema reference</a></li>
      <li><a href="/iam">IAM permissions</a></li>
      <li><a href="/skills/">Skills library</a></li>
      <li><a href="/">{SITE}</a></li>
    </ul>
  </article>
  </div>"""
    write_page("/404", body, [web_page("/")], noindex=True)


def build_machine_surfaces(urls: list[str]) -> None:
    llms = (ROOT / "llms.txt").read_text(encoding="utf-8")
    (DIST / "llms.txt").write_text(llms, encoding="utf-8")

    robots = """# https://ga4mcp.com/robots.txt
User-agent: *
Allow: /

# Answer engines and AI assistants: read and cite the docs.
User-agent: GPTBot
Allow: /
User-agent: OAI-SearchBot
Allow: /
User-agent: ChatGPT-User
Allow: /
User-agent: ClaudeBot
Allow: /
User-agent: Claude-User
Allow: /
User-agent: PerplexityBot
Allow: /
User-agent: Google-Extended
Allow: /
User-agent: Applebot-Extended
Allow: /
User-agent: CCBot
Allow: /

Sitemap: https://ga4mcp.com/sitemap.xml
"""
    (DIST / "robots.txt").write_text(robots, encoding="utf-8")

    today = date.today().isoformat()
    entries = "\n".join(
        f"  <url>\n    <loc>{SITE}{u}</loc>\n    <lastmod>{today}</lastmod>\n"
        f"    <priority>{'1.0' if u == '/' else '0.8' if u in ('/setup', '/skills/') else '0.5'}</priority>\n  </url>"
        for u in urls)
    (DIST / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + entries + "\n</urlset>\n", encoding="utf-8")

    redirects = """# Legacy docsify paths -> clean paths
/setup.md          /setup        301
/schema.md         /schema       301
/iam.md            /iam          301
/privacy.html      /privacy      301
/terms.html        /terms        301
# Old skill URLs -> skill pages
/skills/*/SKILL.md /skills/:splat/  301
# Clean paths: rewritten, not redirected, so every listed URL answers 200
/setup             /setup.html   200
/schema            /schema.html  200
/iam               /iam.html     200
/privacy           /privacy.html 200
/terms             /terms.html   200
# Installer endpoint (unchanged)
/install           https://ga4.builditwithai.xyz/?src=install  302
"""
    (DIST / "_redirects").write_text(redirects, encoding="utf-8")


def copy_overrides() -> list[str]:
    copied = []
    if not ASSETS_IN:
        return copied
    for name in ("og.png", "favicon.svg", "favicon-32.png", "favicon-16.png",
                 "apple-touch-icon-180.png", "style.css"):
        src = ASSETS_IN / name
        if src.is_file():
            dest = (ASSETS_OUT / "style.css") if name == "style.css" else (DIST / name)
            dest.write_bytes(src.read_bytes())
            copied.append(name)
    return copied


# --------------------------------------------------------------------------- checks
PAGES: dict[str, str] = {}


def check_links() -> tuple[list[str], list[str]]:
    failures, warnings = [], []
    for url, page in PAGES.items():
        for target, frag in re.findall(r'href="(/[^"]*?)(?:#([^"]*))?"', page):
            if target.endswith(".md"):
                failures.append(f"{url} -> {target} (markdown path leaked into HTML)")
                continue
            plain_path = target.lstrip("/")
            resolved = None
            for candidate in (DIST / plain_path, DIST / (plain_path + ".html"), DIST / plain_path / "index.html"):
                if candidate.is_file():
                    resolved = candidate
                    break
            if not resolved:
                failures.append(f"{url} -> {target} (no file in dist/)")
            elif frag and f'id="{frag}"' not in resolved.read_text(encoding="utf-8"):
                warnings.append(f"{url} -> {target}#{frag} (anchor not found)")
    return failures, warnings


def check_legal() -> list[str]:
    problems = []
    for url, filename in (("/privacy", "privacy.html"), ("/terms", "terms.html")):
        src = DOCS_SRC / filename
        if not src.is_file():
            problems.append(f"{filename}: source missing, text check skipped")
            continue
        expected = legal_body(filename)
        page = PAGES[url]
        got = page[page.index("<h1"):page.index("</article>")].rstrip()
        if got != expected:
            if visible_text(got) == visible_text(expected):
                problems.append(f"{url}: markup differs from docs/{filename} (words identical)")
            else:
                exp_words, got_words = visible_text(expected).split(), visible_text(got).split()
                first = next((i for i, (a, b) in enumerate(zip(exp_words, got_words)) if a != b), min(len(exp_words), len(got_words)))
                problems.append(f"{url}: TEXT CHANGED vs docs/{filename} at word {first}: "
                                f"{' '.join(exp_words[first:first + 6])!r} -> {' '.join(got_words[first:first + 6])!r}")
    return problems


def check_nojs(pages: dict[str, str]) -> list[str]:
    """A page must carry its heading text in the raw HTML (curl sees no JS)."""
    problems = []
    for url, page in pages.items():
        if url == "/404":
            continue
        stripped = re.sub(r"<script.*?</script>", "", page, flags=re.S)
        if not re.search(r"<h1[^>]*>\s*\S", stripped):
            problems.append(f"{url}: no H1 text without scripts")
        if len(re.sub(r"<[^>]+>", " ", stripped).split()) < 60:
            problems.append(f"{url}: under 60 words of text without scripts")
    return problems


def main() -> int:
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)
    ASSETS_OUT.mkdir(parents=True, exist_ok=True)

    META_OVERRIDES.update(load_meta_overrides())
    if META_IN:
        print(f"meta overrides: {META_IN}")
    if ASSETS_IN:
        print(f"designer assets: {ASSETS_IN}")

    build_og()
    build_icons()
    (ASSETS_OUT / "style.css").write_text(CSS, encoding="utf-8")

    # skill metadata is needed by the home page as well as /skills/
    skills = discover_skills()

    build_home(skills)
    build_docs()
    build_skills()
    build_legal()
    build_not_found()

    urls = ["/", "/setup", "/schema", "/iam", "/skills/"] + \
           [f"/skills/{s['slug']}/" for s in skills] + ["/privacy", "/terms"]
    build_machine_surfaces(urls)
    copied = copy_overrides()

    failures, warnings = check_links()
    legal_problems = check_legal()
    nojs_problems = check_nojs(PAGES)

    print("\nURL                              bytes   file")
    for url in urls:
        path = DIST / "index.html" if url == "/" else (
            DIST / url.strip("/") / "index.html" if url.endswith("/") else DIST / (url.strip("/") + ".html"))
        print(f"{url:<32} {path.stat().st_size:>6}  {path.relative_to(ROOT)}")
    for name in ("llms.txt", "robots.txt", "sitemap.xml", "_redirects", "og.png", "favicon.svg",
                 "favicon-32.png", "favicon-16.png", "apple-touch-icon-180.png", "assets/style.css", "404.html"):
        print(f"{'/' + name:<32} {(DIST / name).stat().st_size:>6}  dist/{name}")
    if copied:
        print("overrides applied:", ", ".join(copied))

    problems = failures + legal_problems + nojs_problems
    for warning in warnings:
        print("warn:", warning)
    for problem in problems:
        print("FAIL:", problem)
    if problems:
        return 1
    print(f"\nOK — {len(PAGES)} pages, {len(warnings)} warnings, legal text byte-identical.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
