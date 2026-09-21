#!/usr/bin/env python3
"""Serve dist/ with the same clean-URL resolution Netlify uses.

    python3 scripts/serve_site.py [port]     # default 8899

/ resolves to index.html, /setup to setup.html, /skills/ to skills/index.html,
and anything missing falls back to 404.html with a 404 status.
"""

import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

DIST = Path(__file__).resolve().parents[1] / "dist"


class Handler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        rel = path.split("?", 1)[0].split("#", 1)[0].strip("/")
        target = DIST / rel
        for candidate in (target, DIST / f"{rel}.html", target / "index.html"):
            if candidate.is_file():
                self._fallback = False
                return str(candidate)
        self._fallback = True
        return str(DIST / "404.html")

    def send_response(self, code, message=None):
        # clean URLs resolve to a file; everything else is a real 404 that renders 404.html
        if getattr(self, "_fallback", False):
            code = 404
        super().send_response(code, message)


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8899
    print(f"serving {DIST} on http://127.0.0.1:{port} (clean URLs, 404.html fallback)")
    ThreadingHTTPServer(("127.0.0.1", port), partial(Handler, directory=str(DIST))).serve_forever()
