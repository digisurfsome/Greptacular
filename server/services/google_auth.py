"""Google OAuth Service — handles OAuth 2.0 for Google Sheets/Drive APIs.

ALL functions are [ROBOT] — standard HTTP OAuth flow, no LLM calls.
Credentials: ~/.autoforge/google_credentials.json (user downloads from GCP console)
Token: ~/.autoforge/google_token.json (auto-generated after OAuth flow)
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
]

AUTOFORGE_DIR = Path.home() / ".autoforge"
CREDENTIALS_PATH = AUTOFORGE_DIR / "google_credentials.json"
TOKEN_PATH = AUTOFORGE_DIR / "google_token.json"

# Module-level flow storage — keeps the flow instance alive between
# start_oauth_flow() and handle_oauth_callback() so the PKCE code_verifier
# matches. Without this, each call creates a new flow with a different
# verifier and the token exchange fails.
_active_flow = None


def get_credentials():
    """Load stored OAuth token, auto-refresh if expired.

    Returns:
        google.oauth2.credentials.Credentials or None if not authenticated.
    """
    if not TOKEN_PATH.exists():
        return None

    try:
        from google.oauth2.credentials import Credentials

        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

        if creds and creds.expired and creds.refresh_token:
            from google.auth.transport.requests import Request
            creds.refresh(Request())
            _save_token(creds)

        if creds and creds.valid:
            return creds

        return None
    except Exception as e:
        logger.warning("Failed to load Google credentials: %s", e)
        return None


def start_oauth_flow(redirect_uri: str = "urn:ietf:wg:oauth:2.0:oob") -> str:
    """Generate OAuth URL for user to visit.

    Args:
        redirect_uri: OAuth redirect URI. Defaults to OOB (copy-paste) flow.

    Returns:
        Authorization URL string.

    Raises:
        FileNotFoundError: If google_credentials.json doesn't exist.
    """
    global _active_flow

    if not CREDENTIALS_PATH.exists():
        raise FileNotFoundError(
            f"Google credentials not found at {CREDENTIALS_PATH}. "
            "Download OAuth 2.0 credentials from Google Cloud Console "
            "and save as ~/.autoforge/google_credentials.json"
        )

    from google_auth_oauthlib.flow import InstalledAppFlow

    _active_flow = InstalledAppFlow.from_client_secrets_file(
        str(CREDENTIALS_PATH),
        scopes=SCOPES,
        redirect_uri=redirect_uri,
    )

    auth_url, _ = _active_flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )

    return auth_url


def handle_oauth_callback(code: str, redirect_uri: str = "urn:ietf:wg:oauth:2.0:oob") -> bool:
    """Exchange authorization code for token and save.

    Uses the stored flow from start_oauth_flow() to preserve the PKCE
    code_verifier. Falls back to creating a new flow if none exists.

    Args:
        code: Authorization code from OAuth redirect.
        redirect_uri: Must match the redirect_uri used in start_oauth_flow.

    Returns:
        True if token saved successfully, False otherwise.
    """
    global _active_flow

    if not CREDENTIALS_PATH.exists():
        logger.error("Cannot handle callback: credentials file missing")
        return False

    try:
        # Use the stored flow (has matching PKCE code_verifier)
        if _active_flow is not None:
            flow = _active_flow
            _active_flow = None  # Clear after use
        else:
            # Fallback: create new flow (won't work with PKCE but try anyway)
            logger.warning("No stored OAuth flow — creating new instance (PKCE may fail)")
            from google_auth_oauthlib.flow import InstalledAppFlow
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_PATH),
                scopes=SCOPES,
                redirect_uri=redirect_uri,
            )

        flow.fetch_token(code=code)
        creds = flow.credentials
        _save_token(creds)
        logger.info("Google OAuth token saved successfully")
        return True
    except Exception as e:
        logger.error("OAuth callback failed: %s", e)
        _active_flow = None  # Clear on failure too
        return False


def is_authenticated() -> bool:
    """Check if valid token exists."""
    creds = get_credentials()
    return creds is not None and creds.valid


def revoke() -> None:
    """Delete stored token."""
    if TOKEN_PATH.exists():
        TOKEN_PATH.unlink()
        logger.info("Google OAuth token revoked")


def _save_token(creds) -> None:
    """Write credentials to token file."""
    AUTOFORGE_DIR.mkdir(parents=True, exist_ok=True)
    TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")
