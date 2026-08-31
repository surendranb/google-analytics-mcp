# SPDX-License-Identifier: Apache-2.0
"""Tests for ephemeral loopback OAuth handshake and session management.
Run: python tests/test_auth_handshake.py"""

import os
import sys
import time
import urllib.request
import urllib.error
import threading
import tempfile
import pathlib

# Configure temp config dir for test isolation
temp_dir = tempfile.mkdtemp()
os.environ["GA4_CONFIG_DIR"] = temp_dir

from ga4_mcp.auth_session import load_session, save_session, clear_session, is_authenticated
from ga4_mcp.auth_handshake import _LoopbackServer


def _run():
    failures = []

    # 1. Test session persistence & loading
    clear_session()
    if is_authenticated():
        failures.append("Expected is_authenticated() to be False when no session exists")

    save_session(token="ga4_live_sample123", email="user@agency.com")
    sess = load_session()
    if not sess or sess.get("token") != "ga4_live_sample123" or sess.get("email") != "user@agency.com":
        failures.append(f"Failed to load saved session: {sess}")

    if not is_authenticated():
        failures.append("Expected is_authenticated() to be True after saving session")

    clear_session()
    if is_authenticated():
        failures.append("Expected is_authenticated() to be False after clear_session()")

    # 2. Test Ephemeral Loopback Server with Valid State & Token
    test_state = "secret_state_abc"
    server = _LoopbackServer(expected_state=test_state)
    assigned_port = server.server_address[1]

    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    time.sleep(0.1)

    try:
        # Simulate browser redirect with valid token
        callback_url = f"http://127.0.0.1:{assigned_port}/callback?token=ga4_live_handshake999&state={test_state}&email=dev@company.com"
        req = urllib.request.Request(callback_url)
        with urllib.request.urlopen(req, timeout=5) as resp:
            body = resp.read().decode("utf-8")
            if resp.status != 200:
                failures.append(f"Expected HTTP 200 from callback, got {resp.status}")
            if "Connected to Google Analytics" not in body or "dev@company.com" not in body:
                failures.append("Expected success HTML page in callback response")

        server.done_event.wait(timeout=2)
        if not server.result or server.result.get("token") != "ga4_live_handshake999":
            failures.append(f"Server result token mismatch: {server.result}")

        # Check session was saved to disk
        disk_sess = load_session()
        if not disk_sess or disk_sess.get("token") != "ga4_live_handshake999":
            failures.append(f"Session not saved to disk after loopback: {disk_sess}")

    finally:
        server.shutdown()
        server.server_close()

    # 3. Test Security: State Mismatch Rejection (CSRF / Replay Protection)
    state_server = _LoopbackServer(expected_state="legit_state_123")
    sec_port = state_server.server_address[1]

    sec_thread = threading.Thread(target=state_server.serve_forever, daemon=True)
    sec_thread.start()

    time.sleep(0.1)

    try:
        bad_callback_url = f"http://127.0.0.1:{sec_port}/callback?token=ga4_live_bad&state=attacker_state&email=hacker@evil.com"
        try:
            urllib.request.urlopen(bad_callback_url, timeout=5)
            failures.append("Expected HTTP error for state mismatch, but request succeeded!")
        except urllib.error.HTTPError as e:
            if e.code != 400:
                failures.append(f"Expected HTTP 400 for state mismatch, got {e.code}")

        state_server.done_event.wait(timeout=2)
        if state_server.error != "State mismatch (possible CSRF or replay)":
            failures.append(f"Expected state mismatch error, got: {state_server.error}")

    finally:
        state_server.shutdown()
        state_server.server_close()

    if failures:
        print("FAIL:")
        for f in failures:
            print("  -", f)
        sys.exit(1)

    print("PASS: Ephemeral loopback OAuth handshake and session persistence verified successfully")


if __name__ == "__main__":
    _run()
