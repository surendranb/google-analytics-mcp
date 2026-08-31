# SPDX-License-Identifier: Apache-2.0
"""Ephemeral loopback HTTP server for zero-copy OAuth handshake.
Captures session tokens redirected from https://ga4.builditwithai.xyz/auth/callback.
"""

import http.server
import secrets
import socketserver
import threading
import urllib.parse
import webbrowser
from typing import Optional, Dict, Any, Tuple

from ga4_mcp.auth_session import save_session, get_gateway_url

SUCCESS_HTML = """<!DOCTYPE html>
<html>
<head>
  <title>Connected to Google Analytics</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background: #fef6e4;
      color: #001858;
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 100vh;
      margin: 0;
      padding: 20px;
      box-sizing: border-box;
    }
    .card {
      background: #ffffff;
      padding: 40px;
      border-radius: 12px;
      max-width: 460px;
      width: 100%;
      box-shadow: 0 8px 24px rgba(0, 24, 88, 0.08);
      border: 2px solid #001858;
      text-align: center;
    }
    .icon {
      font-size: 48px;
      margin-bottom: 16px;
    }
    h1 {
      font-size: 22px;
      margin: 0 0 12px;
      color: #001858;
    }
    p {
      font-size: 15px;
      line-height: 1.5;
      color: #172b4d;
      margin: 0 0 20px;
    }
    .badge {
      display: inline-block;
      background: #8bd3dd;
      color: #001858;
      font-weight: 600;
      padding: 6px 14px;
      border-radius: 20px;
      font-size: 13px;
      margin-bottom: 20px;
    }
    .note {
      font-size: 13px;
      color: #6b778c;
    }
  </style>
</head>
<body>
  <div class="card">
    <div class="icon">📊</div>
    <h1>Connected to Google Analytics</h1>
    <div class="badge">Signed in as {email}</div>
    <p>Your session token was automatically delivered to your local AI coding assistant.</p>
    <p class="note">You can close this tab and return to your editor.</p>
  </div>
  <script>
    setTimeout(function() { window.close(); }, 3500);
  </script>
</body>
</html>
"""


class _LoopbackHandler(http.server.BaseHTTPRequestHandler):
    server: "_LoopbackServer"

    def log_message(self, format, *args):
        # Suppress standard HTTP server stdout spam
        pass

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path != "/callback":
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")
            return

        params = urllib.parse.parse_qs(parsed.query)
        token = params.get("token", [""])[0]
        state = params.get("state", [""])[0]
        email = params.get("email", [""])[0]
        error = params.get("error", [""])[0]

        if error:
            self.server.error = f"OAuth error: {error}"
            self.send_response(400)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(f"<h3>Authentication Failed</h3><p>{error}</p>".encode("utf-8"))
            self.server.done_event.set()
            return

        if not state or state != self.server.expected_state:
            self.server.error = "State mismatch (possible CSRF or replay)"
            self.send_response(400)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"<h3>Security verification failed (state mismatch).</h3>")
            self.server.done_event.set()
            return

        if not token:
            self.server.error = "No session token received"
            self.send_response(400)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"<h3>No session token received.</h3>")
            self.server.done_event.set()
            return

        # Success: Save session to disk
        saved = save_session(token=token, email=email)
        self.server.result = saved
        self.server.error = None

        # Respond with styled HTML
        rendered_html = SUCCESS_HTML.replace("{email}", email or "Google User")
        body = rendered_html.encode("utf-8")

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

        # Notify server to stop
        self.server.done_event.set()


class _LoopbackServer(socketserver.TCPServer):
    allow_reuse_address = True

    def __init__(self, expected_state: str):
        super().__init__(("127.0.0.1", 0), _LoopbackHandler)
        self.expected_state = expected_state
        self.result: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None
        self.done_event = threading.Event()


def start_login_flow(
    open_browser: bool = True,
    timeout_seconds: int = 120,
    gateway_url: Optional[str] = None,
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Starts the ephemeral loopback OAuth server, opens the browser to login,
    and blocks until authentication completes or timeout expires.

    Returns:
        (session_dict, error_message)
    """
    expected_state = secrets.token_urlsafe(32)
    server = _LoopbackServer(expected_state=expected_state)
    assigned_port = server.server_address[1]

    base_gw = (gateway_url or get_gateway_url()).rstrip("/")
    login_url = f"{base_gw}/auth/login?port={assigned_port}&state={expected_state}"

    # Run server loop in background thread
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    if open_browser:
        try:
            webbrowser.open(login_url)
        except Exception as e:
            # Fallback if headless or browser failed to launch
            pass

    try:
        finished = server.done_event.wait(timeout=timeout_seconds)
        if not finished:
            return None, f"Login timed out after {timeout_seconds}s. URL was: {login_url}"
        if server.error:
            return None, server.error
        return server.result, None
    finally:
        server.shutdown()
        server.server_close()
