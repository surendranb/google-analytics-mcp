#!/usr/bin/env python3
"""Test GA4 tracking on deployed site"""

from playwright.sync_api import sync_playwright
import time

def test_tracking():
    url = "https://surendranb.com"  # Production domain
    
    with sync_playwright() as p:
        print(f"Testing GA4 tracking on {url}")
        
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        try:
            page.goto(url, wait_until="networkidle")
            time.sleep(5)  # Allow GA4 tracking to fire
            
            # Check if GA4 script is present
            ga4_script = page.evaluate('''() => {
                return !!window.dataLayer && !!window.gtag;
            }''')
            
            print(f"GA4 script present: {ga4_script}")
            
            # Check dataLayer for events
            events = page.evaluate('''() => {
                return window.dataLayer || [];
            }''')
            
            print(f"DataLayer events: {len(events)}")
            if events:
                for event in events[-3:]:  # Show last 3 events
                    print(f"  Event: {event}")
            
            print(f"✓ Page loaded successfully")
        except Exception as e:
            print(f"✗ Error: {e}")
        finally:
            context.close()
            browser.close()
    
    print(f"\nWait 5-10 minutes for GA4 data to appear, then check property G-C95WM9L8JB")

if __name__ == "__main__":
    test_tracking()
