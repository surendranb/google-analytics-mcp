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
  <title>Google Analytics 4 MCP — Authentication Successful</title>
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
      padding: 24px;
      box-sizing: border-box;
    }
    .card {
      background: #ffffff;
      padding: 36px 32px;
      border-radius: 14px;
      max-width: 520px;
      width: 100%;
      box-shadow: 0 8px 30px rgba(0, 24, 88, 0.08);
      border: 2px solid #001858;
      text-align: left;
    }
    .header {
      text-align: center;
      margin-bottom: 24px;
    }
    .icon {
      font-size: 40px;
      margin-bottom: 8px;
    }
    h1 {
      font-size: 22px;
      margin: 0 0 8px;
      color: #001858;
    }
    .badge {
      display: inline-block;
      background: #8bd3dd;
      color: #001858;
      font-weight: 600;
      padding: 5px 14px;
      border-radius: 20px;
      font-size: 13px;
    }
    .section {
      background: #fafafa;
      border: 1px solid #e1e4e8;
      border-radius: 8px;
      padding: 16px;
      margin: 16px 0;
    }
    .section-title {
      font-size: 13px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: #001858;
      margin-bottom: 8px;
    }
    .item {
      font-size: 14px;
      line-height: 1.5;
      color: #24292e;
      margin: 6px 0;
      display: flex;
      align-items: flex-start;
    }
    .bullet {
      margin-right: 8px;
      color: #001858;
      font-weight: bold;
    }
    .footer {
      text-align: center;
      font-size: 13px;
      color: #586069;
      margin-top: 20px;
    }
  </style>
</head>
<body>
  <div class="card">
    <div class="header">
      <div class="icon">📊</div>
      <h1>Google Analytics 4 MCP Ready</h1>
      <div class="badge">Signed in as {email}</div>
    </div>

    <div class="section">
      <div class="section-title">What Just Happened</div>
      <div class="item">
        <span class="bullet">✓</span>
        <span>Your Google account was authenticated with read-only access so your GA4 properties can be discovered.</span>
      </div>
      <div class="item">
        <span class="bullet">✓</span>
        <span>Your session token was automatically delivered to your local AI coding assistant on this machine.</span>
      </div>
    </div>

    <div class="section" style="border-left: 4px solid #001858;">
      <div class="section-title">Privacy & Local Execution Guarantee</div>
      <div class="item">
        <span class="bullet">•</span>
        <span><b>Local-Only Execution:</b> All queries execute directly between this machine and Google Analytics.</span>
      </div>
      <div class="item">
        <span class="bullet">•</span>
        <span><b>Zero Cloud Storage:</b> No analytics data, visitors, revenue, or report rows are ever stored, logged, or sent to third-party servers.</span>
      </div>
      <div class="item">
        <span class="bullet">•</span>
        <span><b>Read-Only Security:</b> The token cannot modify or delete any configurations or data.</span>
      </div>
    </div>

    <div class="footer">
      You can safely close this tab and return to your AI assistant.
    </div>
  </div>
  <script>
    setTimeout(function() { window.close(); }, 5000);
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
