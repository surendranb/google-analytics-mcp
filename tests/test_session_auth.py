# SPDX-License-Identifier: Apache-2.0

import json
import os
from unittest.mock import patch, MagicMock

from ga4_mcp import coordinator


def test_get_session_credentials_missing(tmp_path):
    fake_path = tmp_path / "nonexistent.json"
    with patch.dict(os.environ, {"GA4_SESSION_FILE": str(fake_path)}):
        creds, prop = coordinator.get_session_credentials()
        assert creds is None
        assert prop is None


def test_get_session_credentials_success(tmp_path):
    session_file = tmp_path / "session.json"
    session_file.write_text(json.dumps({
        "token": "ga4_test_token_123",
        "gateway_url": "https://test-gateway.example.com",
        "property_id": "999888777",
        "email": "test@example.com"
    }))

    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps({
        "access_token": "ya29.test_access_token",
        "expires_in": 3600
    }).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    with patch.dict(os.environ, {"GA4_SESSION_FILE": str(session_file)}), \
         patch("urllib.request.urlopen", return_value=mock_resp):
        coordinator._SESSION_ACCESS_TOKEN = None
        coordinator._SESSION_TOKEN_EXPIRY = 0.0
        creds, prop = coordinator.get_session_credentials()
        assert creds is not None
        assert creds.token == "ya29.test_access_token"
        assert prop == "999888777"
