#!/usr/bin/env python3
"""Test GA4 tracking by sending 10 page visits with different user agents"""

from playwright.sync_api import sync_playwright
import time

USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"
]

def test_tracking():
    url = "https://surendranb.com"
    
    with sync_playwright() as p:
        for i, user_agent in enumerate(USER_AGENTS, 1):
            print(f"Visit {i}/10: {user_agent[:50]}...")
            
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(user_agent=user_agent)
            page = context.new_page()
            
            try:
                page.goto(url, wait_until="networkidle")
                time.sleep(3)  # Allow GA4 tracking to fire
                print(f"  ✓ Page loaded successfully")
            except Exception as e:
                print(f"  ✗ Error: {e}")
            finally:
                context.close()
                browser.close()
    
    print(f"\n✓ Completed 10 test visits to {url}")
    print("Check GA4 real-time or wait 5-10 minutes for data to appear")

if __name__ == "__main__":
    test_tracking()
