#!/usr/bin/env python3
"""Serve site/dist/ with the clean-URL rules Netlify applies, for local checks.

    python3 scripts/serve_site.py [port]     # default 8899

/ serves index.html, /setup/ serves setup/index.html, /setup redirects to
/setup/ (as Netlify does), and anything missing renders 404.html with a 404.
Markdown twins are served as plain files, which is what the edge function hands
back when a client sends Accept: text/markdown.
"""

import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

DIST = Path(__file__).resolve().parents[1] / "site" / "dist"


class Handler(SimpleHTTPRequestHandler):
    _fallback = False

    def send_head(self):
        rel = self.path.split("?", 1)[0].split("#", 1)[0].lstrip("/")
        if rel and not rel.endswith("/") and (DIST / rel).is_dir():
            self.send_response(301)
            self.send_header("Location", f"/{rel}/")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return None
        return super().send_head()

    def translate_path(self, path):
        rel = path.split("?", 1)[0].split("#", 1)[0].strip("/")
        target = DIST / rel
        for candidate in (target, target / "index.html"):
            if candidate.is_file():
                self._fallback = False
                return str(candidate)
        self._fallback = True
        return str(DIST / "404.html")

    def send_response(self, code, message=None):
        if self._fallback:
            code = 404
        super().send_response(code, message)


if __name__ == "__main__":
    if not DIST.is_dir():
        sys.exit(f"{DIST} does not exist — run: uv run --no-project --with markdown python3 site/build.py")
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8899
    print(f"serving {DIST} on http://127.0.0.1:{port} (clean URLs, 404.html fallback)")
    ThreadingHTTPServer(("127.0.0.1", port), partial(Handler, directory=str(DIST))).serve_forever()
