#!/usr/bin/env python3
"""Re-render the committed raster assets (og.png, favicons) from HTML + SVG sources.

    uv run --no-project --with playwright --with pillow python3 site/tools/render-assets.py

Why: the binaries in site/src-assets/ are committed, so the site build stays a
single dependency-free python step. This script is the provenance for those
binaries — run it only when the palette or the headline copy changes.

Palette: Workbench "sunset". Bars run light -> accent -> ink: #fdba74 -> #ea580c
-> #1e3a8a on light grounds; the badge inverts the top bar to peach on ink.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "src-assets"

MARKS = {
    "mark.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100" height="100" role="img" aria-label="GA4 MCP Server">
  <title>GA4 MCP Server</title>
  <!-- rising report series, capsule ends, flat fills -->
  <rect x="14" y="54" width="16" height="38" rx="8" fill="#fdba74"/>
  <rect x="42" y="40" width="16" height="52" rx="8" fill="#ea580c"/>
  <rect x="70" y="26" width="16" height="66" rx="8" fill="#1e3a8a"/>
</svg>
""",
    "favicon.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" role="img" aria-label="GA4 MCP Server">
  <title>GA4 MCP Server</title>
  <rect x="0" y="0" width="100" height="100" rx="19" fill="#140b04"/>
  <rect x="26.5" y="50" width="11" height="24" rx="5.5" fill="#fdba74"/>
  <rect x="44.5" y="40" width="11" height="34" rx="5.5" fill="#ea580c"/>
  <rect x="62.5" y="30" width="11" height="44" rx="5.5" fill="#fdf0e2"/>
</svg>
""",
}

OG_HTML = """<!doctype html>
<html><head><meta charset="utf-8"><title>ga4mcp.com — OG card 1200x630</title>
<style>
  :root{--page:#fdf0e2;--ink:#140b04;--lede:#382518;--accent:#ea580c;--secondary:#1e3a8a}
  *{margin:0;padding:0;box-sizing:border-box}
  html,body{width:1200px;height:630px}
  body{background:var(--page);color:var(--ink);overflow:hidden;position:relative;
       font-family:-apple-system,BlinkMacSystemFont,"Inter","Segoe UI",Helvetica,Arial,sans-serif;
       -webkit-font-smoothing:antialiased}
  .mono{font-family:"SF Mono",ui-monospace,Menlo,Consolas,monospace}
  .dots{position:absolute;inset:0;background-image:radial-gradient(rgba(30,58,138,.13) 1.3px,transparent 1.3px);background-size:26px 26px}
  .pad{position:absolute;inset:0;padding:64px 80px 52px;display:flex;flex-direction:column}
  .mid{margin:auto 0;max-width:640px}
  h1{font-size:80px;font-weight:640;letter-spacing:-.022em;line-height:1;font-family:Georgia,"Times New Roman",serif}
  .sub{margin-top:20px;font-size:30px;color:rgba(56,37,24,.82)}
  .chip{display:inline-block;margin-top:32px;border:2px solid var(--secondary);border-radius:9px;background:#fff;
        box-shadow:5px 5px 0 rgba(234,88,12,.16);font-size:17px;padding:10px 16px;color:var(--secondary)}
  .foot{margin-top:auto}
  .rule{border-top:1.5px solid rgba(30,58,138,.26);margin-bottom:16px}
  .footrow{display:flex;justify-content:space-between;align-items:baseline}
  .footrow .url{font-size:19px;font-weight:700}
  .footrow .lic{font-size:15.5px;color:rgba(56,37,24,.62)}
  .hero{position:absolute;right:100px;top:50%;transform:translateY(-50%)}
  .hero svg{display:block;width:320px;height:320px;filter:drop-shadow(16px 16px 0 rgba(30,58,138,.14))}
</style></head>
<body>
  <div class="dots"></div>
  <div class="pad">
    <div class="mid">
      <h1>GA4 MCP Server</h1>
      <div class="sub">Google Analytics 4 for AI agents</div>
      <div class="mono chip">uvx google-analytics-mcp</div>
    </div>
    <div class="foot">
      <div class="rule"></div>
      <div class="footrow">
        <span class="mono url">ga4mcp.com</span>
        <span class="mono lic">open source · MIT</span>
      </div>
    </div>
  </div>
  <div class="hero">{mark}</div>
</body></html>
"""

ICONS_HTML = """<!doctype html>
<html><head><meta charset="utf-8"><title>badge</title>
<style>html,body{margin:0}body{display:flex;gap:40px;padding:40px;background:transparent}
 .b{width:400px;height:400px;border-radius:19%;background:#140b04;position:relative}
 .b i{position:absolute;display:block;border-radius:99px}
 .b .a{left:26.5%;bottom:26%;width:11%;height:24%;background:#fdba74}
 .b .b2{left:44.5%;bottom:26%;width:11%;height:34%;background:#ea580c}
 .b .c{left:62.5%;bottom:26%;width:11%;height:44%;background:#fdf0e2}
</style></head>
<body>
  <div class="b" id="badge"><i class="a"></i><i class="b2"></i><i class="c"></i></div>
</body></html>
"""

ICONS = [("#badge", "apple-touch-icon-180", (180, 180)),
         ("#badge", "favicon-32", (32, 32)),
         ("#badge", "favicon-16", (16, 16))]


def downscale(source: Path, dest: Path, size: tuple[int, int]) -> None:
    image = Image.open(source)
    image = image.convert("RGBA") if image.mode in ("P", "LA", "RGBA") else image.convert("RGB")
    image.resize(size, Image.LANCZOS).save(dest)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, svg in MARKS.items():
        (OUT / name).write_text(svg, encoding="utf-8")

    tmp = Path("/tmp/ga4mcp-assets")
    tmp.mkdir(parents=True, exist_ok=True)
    (tmp / "og.html").write_text(OG_HTML.replace("{mark}", MARKS["mark.svg"]), encoding="utf-8")
    (tmp / "icons.html").write_text(ICONS_HTML, encoding="utf-8")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1200, "height": 630}, device_scale_factor=2)
        page.goto((tmp / "og.html").as_uri())
        page.wait_for_timeout(300)
        page.locator("body").screenshot(path=str(tmp / "og-2x.png"))
        page.close()

        icons = browser.new_page(viewport={"width": 560, "height": 480}, device_scale_factor=2)
        icons.goto((tmp / "icons.html").as_uri())
        icons.wait_for_timeout(200)
        for element, name, size in ICONS:
            icons.locator(element).screenshot(path=str(tmp / f"{name}-2x.png"), omit_background=True)
            downscale(tmp / f"{name}-2x.png", OUT / f"{name}.png", size)
            print(f"{name}.png {(OUT / f'{name}.png').stat().st_size} bytes")
        icons.close()
        browser.close()

    downscale(tmp / "og-2x.png", OUT / "og.png", (1200, 630))
    print(f"og.png {(OUT / 'og.png').stat().st_size} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
