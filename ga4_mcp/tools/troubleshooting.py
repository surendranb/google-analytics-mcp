import urllib.request
import urllib.error
from ga4_mcp.coordinator import mcp

# Fetches troubleshooting guides directly from the documentation site.
OTA_BASE_URL = "https://ga4mcp.com"

@mcp.tool()
def get_troubleshooting_guide(topic: str) -> str:
    """
    Fetches the latest troubleshooting and setup guides Over-The-Air (OTA) from ga4mcp.com.
    Use this tool whenever you encounter a schema error, dimension_filter parse error,
    IAM / 403 authorization error, or boot-time setup error.
    
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
