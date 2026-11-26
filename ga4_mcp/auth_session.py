# SPDX-License-Identifier: Apache-2.0
"""Session management for GA4 MCP Gateway authentication.
Stores session tokens in ~/.config/ga4-mcp/session.json.
"""

import json
import os
import pathlib
import time
from typing import Optional, Dict, Any

DEFAULT_GATEWAY_URL = "https://ga4-gateway.reachsuren.workers.dev"


def get_gateway_url() -> str:
    """Returns the configured Cloudflare Gateway URL."""
    return os.environ.get("GA4_GATEWAY_URL", DEFAULT_GATEWAY_URL).rstrip("/")


def get_session_dir() -> pathlib.Path:
    """Returns the directory where session files are stored."""
    custom_dir = os.environ.get("GA4_CONFIG_DIR")
    if custom_dir:
        p = pathlib.Path(custom_dir).expanduser()
    else:
        p = pathlib.Path.home() / ".config" / "ga4-mcp"
    p.mkdir(parents=True, exist_ok=True)
    return p


def get_session_file() -> pathlib.Path:
    """Returns the path to the session.json file."""
    custom_file = os.environ.get("GA4_SESSION_FILE")
    if custom_file:
        return pathlib.Path(custom_file).expanduser()
    return get_session_dir() / "session.json"


def load_session() -> Optional[Dict[str, Any]]:
    """Loads existing session data from disk if valid."""
    # Check env var override first
    env_token = os.environ.get("GA4_API_KEY") or os.environ.get("GA4_SESSION_TOKEN")
    if env_token:
        return {
            "token": env_token,
            "email": os.environ.get("GA4_USER_EMAIL", "env_user"),
            "gateway_url": get_gateway_url(),
            "source": "environment",
        }

    session_path = get_session_file()
    if not session_path.is_file():
        return None

    try:
        data = json.loads(session_path.read_text(encoding="utf-8"))
        if isinstance(data, dict) and data.get("token"):
            return data
    except Exception:
        pass
    return None


def save_session(token: str, email: str = "", gateway_url: Optional[str] = None) -> Dict[str, Any]:
    """Persists a session token to disk."""
    session_data = {
        "token": token,
        "email": email,
        "gateway_url": gateway_url or get_gateway_url(),
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    session_path = get_session_file()
    session_path.write_text(json.dumps(session_data, indent=2), encoding="utf-8")
    return session_data


def clear_session() -> bool:
    """Deletes the stored session file."""
    session_path = get_session_file()
    if session_path.is_file():
        try:
            session_path.unlink()
            return True
        except Exception:
            return False
    return False


def is_authenticated() -> bool:
    """Returns True if a valid session exists."""
    return load_session() is not None
