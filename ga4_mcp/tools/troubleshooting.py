import urllib.request
import urllib.error
from ga4_mcp.coordinator import mcp

# Use raw.githubusercontent.com for OTA updates for now.
# This can be swapped to docs.ga4mcp.com in the future.
OTA_BASE_URL = "https://raw.githubusercontent.com/surendranb/google-analytics-mcp/main/docs"

@mcp.tool()
def get_troubleshooting_guide(topic: str) -> str:
    """
    Fetches the latest troubleshooting and setup guides Over-The-Air (OTA).
    Use this tool whenever you encounter a schema error, IAM error, or setup error.
    
    Args:
        topic: The topic of the guide to fetch. Valid options are "setup", "iam", or "schema".
    """
    if topic not in ["setup", "iam", "schema"]:
        return "Invalid topic. Please choose 'setup', 'iam', or 'schema'."

    url = f"{OTA_BASE_URL}/{topic}.md"
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            content = response.read().decode('utf-8')
            return f"--- {topic.upper()} GUIDE ---\n\n{content}"
    except urllib.error.URLError as e:
        # Fallback if network is completely unreachable (rare, since GA4 needs network anyway)
        return f"Warning: Could not fetch OTA guide for '{topic}' due to network error: {e}. Please use your best judgment based on generic GA4 API documentation."
