import os
import json
import datetime
from google.cloud import bigquery
from playwright.sync_api import sync_playwright

def main():
    # 1. Query BigQuery
    client = bigquery.Client()
    query = """
    SELECT
      DATE(timestamp) as dl_date,
      SUM(CASE WHEN details.ci = true OR details.installer.name IN ('bandersnatch', 'Nexus', 'devpi', 'Artifactory') THEN 1 ELSE 0 END) as bot_downloads,
      SUM(CASE WHEN (details.installer.name = 'uv' AND IFNULL(details.ci, false) = false) OR details.installer.name IN ('Browser', 'poetry') THEN 1 ELSE 0 END) as human_downloads,
      SUM(CASE WHEN (details.installer.name = 'pip' AND IFNULL(details.ci, false) = false) OR details.installer.name IN ('requests') OR details.installer.name IS NULL OR (IFNULL(details.ci, false) = false AND details.installer.name NOT IN ('uv', 'Browser', 'poetry', 'bandersnatch', 'Nexus', 'devpi', 'Artifactory', 'pip', 'requests')) THEN 1 ELSE 0 END) as ambig_downloads
    FROM `bigquery-public-data.pypi.file_downloads`
    WHERE file.project = 'google-analytics-mcp'
    GROUP BY dl_date
    ORDER BY dl_date ASC
    """
    
    print("Running BigQuery query...")
    query_job = client.query(query)
    results = query_job.result()

    labels = []
    cumulative_human_data = []
    cumulative_ambig_data = []
    cumulative_bot_data = []
    
    total_human = 0
    total_ambig = 0
    total_bot = 0

    for row in results:
        labels.append(row.dl_date.strftime("%Y-%m-%d"))
        
        h = row.human_downloads or 0
        a = row.ambig_downloads or 0
        b = row.bot_downloads or 0
        
        total_human += h
        total_ambig += a
        total_bot += b
        
        cumulative_human_data.append(total_human)
        cumulative_ambig_data.append(total_ambig)
        cumulative_bot_data.append(total_bot)

    total_downloads = total_human + total_ambig + total_bot
    if total_downloads == 0:
        print("No downloads found.")
        return

    human_percent = round((total_human / total_downloads) * 100) if total_downloads > 0 else 0
    bot_percent = round((total_bot / total_downloads) * 100) if total_downloads > 0 else 0
    ambig_percent = 100 - human_percent - bot_percent # ensure it adds to 100
    days = len(labels)
    timestamp = "Live Snapshot: " + datetime.datetime.now(datetime.UTC).strftime("%b %d, %Y")

    # 2. Inject into HTML
    script_dir = os.path.dirname(os.path.abspath(__file__))
    template_path = os.path.join(script_dir, "banner-template.html")
    output_html_path = os.path.join(script_dir, "banner-rendered.html")
    
    print(f"Injecting data into {template_path}...")
    with open(template_path, "r", encoding="utf-8") as f:
        html = f.read()

    html = html.replace("{{HERO_NUMBER}}", f"{total_downloads:,}")
    html = html.replace("{{DAYS}}", str(days))
    html = html.replace("{{HUMAN_COUNT}}", f"{total_human:,}")
    html = html.replace("{{HUMAN_PERCENT}}", str(human_percent))
    html = html.replace("{{AMBIG_COUNT}}", f"{total_ambig:,}")
    html = html.replace("{{AMBIG_PERCENT}}", str(ambig_percent))
    html = html.replace("{{BOT_COUNT}}", f"{total_bot:,}")
    html = html.replace("{{BOT_PERCENT}}", str(bot_percent))
    html = html.replace("{{TIMESTAMP}}", timestamp)
    html = html.replace("{{CHART_LABELS}}", json.dumps(labels))
    html = html.replace("{{CHART_HUMAN_DATA}}", json.dumps(cumulative_human_data))
    html = html.replace("{{CHART_AMBIG_DATA}}", json.dumps(cumulative_ambig_data))
    html = html.replace("{{CHART_BOT_DATA}}", json.dumps(cumulative_bot_data))

    with open(output_html_path, "w", encoding="utf-8") as f:
        f.write(html)

    # 3. Screenshot with Playwright
    assets_dir = os.path.join(os.path.dirname(script_dir), "assets")
    os.makedirs(assets_dir, exist_ok=True)
    screenshot_path = os.path.join(assets_dir, "downloads-banner.png")

    print("Taking screenshot with Playwright...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Set viewport to exactly 1080x1080 to match our layout
        page = browser.new_page(viewport={"width": 1080, "height": 1080})
        # Use file:// protocol to load local HTML
        page.goto(f"file://{output_html_path}")
        # Wait for Chart.js animation to complete
        page.wait_for_timeout(2000) 
        
        # Take screenshot of the .frame specifically, or the whole viewport
        # Since our body is yellow, let's just snapshot the viewport so we get the padding and yellow background
        page.screenshot(path=screenshot_path, full_page=False)
        browser.close()

    print(f"Banner generated successfully: {screenshot_path}")

if __name__ == "__main__":
    main()
