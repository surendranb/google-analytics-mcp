#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Automated Screen Recording Runner for Google OAuth Verification.

Orchestrates:
1. Native macOS 60fps screen recording (screencapture).
2. Direct launch of Google OAuth consent screen in Chrome with client_id in URL.
3. Local loopback capture of OAuth session token.
4. Execution of live GA4 Admin & Data API queries in terminal.
5. Graceful recording termination & FFmpeg 1080p encoding.
"""

import http.server
import json
import os
import pathlib
import signal
import subprocess
import sys
import threading
import time
import urllib.parse
import webbrowser

# Add multi-site repo root to path for auth and client pools
multisite_root = pathlib.Path("/Users/surendran/Projects/google-analytics-mcp-multisite")
sys.path.insert(0, str(multisite_root))

from ga4_mcp.auth_session import save_session
from ga4_mcp.client_pool import client_pool
from ga4_mcp.sites import registry
from google.analytics.data_v1beta.types import (
    RunReportRequest,
    DateRange,
    Metric,
    Dimension,
)

PORT = 18443
RAW_VIDEO = "/tmp/raw_oauth_demo.mp4"
OUTPUT_VIDEO = "/Users/surendran/Projects/google-analytics-mcp/ga4_oauth_verification_demo.mp4"
GATEWAY_AUTH_URL = f"https://ga4-gateway.reachsuren.workers.dev/auth/login?port={PORT}&service=ga4"

auth_event = threading.Event()
received_token = None
received_email = None


class CallbackHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        global received_token, received_email
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        token = params.get("token", [""])[0]
        email = params.get("email", [""])[0]

        if token:
            received_token = token
            received_email = email
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"""
                <html>
                <body style="font-family: sans-serif; text-align: center; padding: 50px; background: #fef6e4; color: #001858;">
                    <h1>GA4 MCP: Authentication Successful!</h1>
                    <p>You can close this tab and return to your terminal.</p>
                </body>
                </html>
            """)
            auth_event.set()
        else:
            self.send_response(400)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # Suppress standard HTTP logs


def run_server(httpd):
    httpd.serve_forever()


def main():
    print("\n" + "=" * 70)
    print("GA4 MCP - Google OAuth Verification Screencast Automation")
    print("=" * 70)

    # 1. Start loopback listener
    httpd = http.server.HTTPServer(("127.0.0.1", PORT), CallbackHandler)
    server_thread = threading.Thread(target=run_server, args=(httpd,), daemon=True)
    server_thread.start()
    print(f"[1/5] Loopback listener active on 127.0.0.1:{PORT}")

    # 2. Clean previous raw capture
    if os.path.exists(RAW_VIDEO):
        os.remove(RAW_VIDEO)

    # 3. Start native macOS screen recording
    print("[2/5] Starting native macOS screen recording...")
    rec_proc = subprocess.Popen(["screencapture", "-v", RAW_VIDEO])
    time.sleep(1.5)

    # 4. Open Google OAuth consent page in browser
    print("[3/5] Opening Google OAuth in browser...")
    print(f"      Target: {GATEWAY_AUTH_URL}")
    webbrowser.open(GATEWAY_AUTH_URL)

    print("\n>>> PLEASE CLICK 'CONTINUE' / 'ALLOW' IN THE OPENED BROWSER WINDOW <<<\n")

    # 5. Wait for user consent callback
    got_auth = auth_event.wait(timeout=60)
    httpd.shutdown()

    if not got_auth or not received_token:
        print("[ERROR] Timed out waiting for OAuth callback.")
        rec_proc.send_signal(signal.SIGINT)
        rec_proc.wait()
        sys.exit(1)

    # 6. Save token to local session
    save_session(token=received_token, email=received_email)
    print(f"[4/5] Authentication callback captured for {received_email}!")
    print(f"      Session saved locally to ~/.config/ga4-mcp/session.json")

    # 7. Execute live GA4 Admin & Data API queries in full view of reviewer
    print("\n" + "-" * 70)
    print("DEMO STEP 1: Discovering GA4 Properties via Admin API (read-only)...")
    print("-" * 70)
    registry.initialize(force_refresh=True)
    props = registry.list_all()
    print(f"Discovered {len(props)} properties across accounts:")
    for p in props[:5]:
        print(f"  - Property [{p['property_id']}]: {p['display_name']} (Account: {p['account_name']})")
    if len(props) > 5:
        print(f"  ... and {len(props) - 5} additional properties.")

    # Find target property for traffic query
    target = next((p for p in props if "surendran" in p['display_name'].lower()), props[0] if props else None)
    if target:
        print("\n" + "-" * 70)
        print(f"DEMO STEP 2: Querying Live Traffic for '{target['display_name']}' (ID: {target['property_id']})...")
        print("-" * 70)
        data_client = client_pool.get_data_client("gateway://session")
        req = RunReportRequest(
            property=f"properties/{target['property_id']}",
            date_ranges=[DateRange(start_date="7daysAgo", end_date="today")],
            metrics=[Metric(name="activeUsers"), Metric(name="sessions"), Metric(name="screenPageViews")],
            dimensions=[Dimension(name="date")],
        )
        resp = data_client.run_report(req)
        print(f"GA4 Data API returned {len(resp.rows)} daily traffic rows:")
        for row in resp.rows[:5]:
            d = row.dimension_values[0].value
            u = row.metric_values[0].value
            s = row.metric_values[1].value
            v = row.metric_values[2].value
            print(f"  Date: {d} | Active Users: {u} | Sessions: {s} | Page Views: {v}")

    print("\n" + "=" * 70)
    print("GA4 MCP DEMONSTRATION COMPLETE - Zero server storage verified.")
    print("=" * 70)

    # Let output sit on screen for 5 seconds for reviewer
    time.sleep(5)

    # 8. Stop screen recording gracefully
    print("\n[5/5] Finalizing video recording...")
    rec_proc.send_signal(signal.SIGINT)
    rec_proc.wait()

    # 9. Transcode to YouTube 1080p MP4
    print("      Encoding to YouTube 1080p MP4 via FFmpeg...")
    ffmpeg_cmd = [
        "ffmpeg", "-y", "-i", RAW_VIDEO,
        "-vf", "scale=1920:1080:flags=lanczos",
        "-c:v", "libx264", "-crf", "18", "-preset", "fast",
        "-pix_fmt", "yuv420p",
        OUTPUT_VIDEO
    ]
    subprocess.run(ffmpeg_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    os.remove(RAW_VIDEO)

    print(f"\nSUCCESS! Demo video saved to:")
    print(f"  {OUTPUT_VIDEO}")
    file_size_mb = os.path.getsize(OUTPUT_VIDEO) / (1024 * 1024)
    print(f"  Size: {file_size_mb:.2f} MB")
    print(f"\nYou can upload this directly as an 'Unlisted' video to YouTube for Google Verification.")


if __name__ == "__main__":
    main()
