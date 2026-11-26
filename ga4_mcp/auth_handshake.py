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
import sys

from mcp.types import ToolAnnotations
from mcp.server.mcpserver import Context
from .coordinator import mcp
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
      padding: 24px;
      box-sizing: border-box;
    }
    .card {
      background: #ffffff;
      padding: 36px 32px;
      border-radius: 14px;
      max-width: 480px;
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
      padding: 18px 16px;
      margin: 20px 0;
    }
    .item {
      font-size: 14px;
      line-height: 1.55;
      color: #24292e;
      margin: 10px 0;
      display: flex;
      align-items: flex-start;
    }
    .item:first-child {
      margin-top: 0;
    }
    .item:last-child {
      margin-bottom: 0;
    }
    .bullet {
      margin-right: 10px;
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
      <h1>Connected to Google Analytics</h1>
      <div class="badge">Signed in as {email}</div>
    </div>

    <div class="section">
      <div class="item">
        <span class="bullet">•</span>
        <span>This is a one-time sign-in so your AI assistant on this machine can find and access your analytics properties.</span>
      </div>
      <div class="item">
        <span class="bullet">•</span>
        <span>All queries run directly from this machine to Google Analytics. Your data remains on this machine.</span>
      </div>
      <div class="item">
        <span class="bullet">•</span>
        <span>This connection is read-only. It cannot change or delete any of your settings or reports.</span>
      </div>
    </div>

    <div class="footer">
      You can safely close this tab and return to your editor.
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
    login_url = f"{base_gw}/auth/login?port={assigned_port}&state={expected_state}&service=ga4"

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


@mcp.tool(annotations=ToolAnnotations(read_only_hint=False, idempotent_hint=True, open_world_hint=True))
def connect_google_analytics(ctx: Context = None) -> dict:
    """
    Connect to Google Analytics 4 via official Google OAuth in your browser.
    Opens the Google OAuth consent screen to grant read-only access (analytics.readonly),
    captures the session token, and auto-discovers all accessible GA4 properties.
    Call this whenever you need to sign in or reconnect your Google account.
    """
    from ga4_mcp.sites import registry
    import ga4_mcp.coordinator as coordinator

    session, err = start_login_flow(open_browser=True)
    if err:
        return {"status": "error", "error": err}

    registry.initialize(force_refresh=True)
    coordinator.SERVER_INIT_ERROR = None
    coordinator.SERVER_INIT_BRIEF_VERSION = None

    props = registry.list_all()
    default_prop = next((p for p in props if p.get("is_default")), props[0] if props else None)
    return {
        "status": "connected",
        "email": session.get("email"),
        "total_properties": len(props),
        "active_property": f"{default_prop.get('display_name')} (ID: {default_prop.get('property_id')})" if default_prop else "None",
        "properties": props[:10],
        "message": "Successfully connected to Google Analytics! You can now query your data using get_ga4_data."
    }


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("GA4 MCP - Google OAuth Browser Sign-In")
    print("=" * 60)
    print("Opening browser for Google OAuth sign-in...")
    sess, error = start_login_flow(open_browser=True)
    if error:
        print(f"\n[ERROR] Authentication failed: {error}", file=sys.stderr)
        sys.exit(1)
    print(f"\n[SUCCESS] Connected to Google Analytics!")
    print(f"Signed in as: {sess.get('email')}")
    print(f"Session saved to ~/.config/ga4-mcp/session.json")

