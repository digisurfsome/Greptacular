"""Unit tests for google_auth.py — all [ROBOT] functions."""

import json
from unittest.mock import MagicMock, patch

import pytest

from server.services.google_auth import (
    handle_oauth_callback,
    is_authenticated,
    revoke,
    start_oauth_flow,
)


class TestIsAuthenticated:
    def test_is_authenticated_no_token(self, tmp_path):
        """Returns False when no token file exists."""
        with patch("server.services.google_auth.TOKEN_PATH", tmp_path / "nonexistent.json"):
            assert is_authenticated() is False

    def test_is_authenticated_valid_token(self, tmp_path):
        """Returns True with valid mock token."""
        mock_creds = MagicMock()
        mock_creds.valid = True
        mock_creds.expired = False

        with patch("server.services.google_auth.get_credentials", return_value=mock_creds):
            assert is_authenticated() is True


class TestStartOAuthFlow:
    def test_start_oauth_flow_no_credentials(self, tmp_path):
        """Raises FileNotFoundError when credentials file missing."""
        with patch("server.services.google_auth.CREDENTIALS_PATH", tmp_path / "missing.json"):
            with pytest.raises(FileNotFoundError, match="Google credentials not found"):
                start_oauth_flow()

    def test_start_oauth_flow_returns_url(self, tmp_path):
        """Returns valid URL string when credentials exist."""
        creds_file = tmp_path / "creds.json"
        creds_file.write_text(json.dumps({
            "installed": {
                "client_id": "test.apps.googleusercontent.com",
                "client_secret": "test-secret",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob"],
            }
        }))

        with patch("server.services.google_auth.CREDENTIALS_PATH", creds_file):
            url = start_oauth_flow()
            assert url.startswith("https://accounts.google.com")
            assert "scope" in url


class TestHandleCallback:
    def test_handle_callback_no_credentials(self, tmp_path):
        """Returns False when credentials file missing."""
        with patch("server.services.google_auth.CREDENTIALS_PATH", tmp_path / "missing.json"):
            assert handle_oauth_callback("some-code") is False

    def test_handle_callback_saves_token(self, tmp_path):
        """Token file created after successful callback."""
        creds_file = tmp_path / "creds.json"
        creds_file.write_text(json.dumps({
            "installed": {
                "client_id": "test.apps.googleusercontent.com",
                "client_secret": "test-secret",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob"],
            }
        }))

        token_file = tmp_path / "token.json"
        mock_creds = MagicMock()
        mock_creds.to_json.return_value = '{"token": "test"}'

        mock_flow = MagicMock()
        mock_flow.credentials = mock_creds

        with (
            patch("server.services.google_auth.CREDENTIALS_PATH", creds_file),
            patch("server.services.google_auth.TOKEN_PATH", token_file),
            patch("server.services.google_auth.AUTOFORGE_DIR", tmp_path),
            patch("google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file", return_value=mock_flow),
        ):
            result = handle_oauth_callback("test-code")
            assert result is True
            assert token_file.exists()


class TestRevoke:
    def test_revoke_deletes_token(self, tmp_path):
        """Token file is deleted on revoke."""
        token_file = tmp_path / "token.json"
        token_file.write_text('{"token": "test"}')

        with patch("server.services.google_auth.TOKEN_PATH", token_file):
            revoke()
            assert not token_file.exists()

    def test_revoke_no_token(self, tmp_path):
        """No error when revoking with no token file."""
        with patch("server.services.google_auth.TOKEN_PATH", tmp_path / "nonexistent.json"):
            revoke()  # Should not raise
