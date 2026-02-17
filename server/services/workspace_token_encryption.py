"""
Workspace Token Encryption
===========================

Encrypts and stores GitHub personal access tokens using Fernet symmetric
encryption. The encryption key is derived from the machine's MAC address,
making tokens non-portable between machines (intentional security measure).

Tokens are stored in ~/.autoforge/workspace/.tokens (JSON file).
Only encrypted values are persisted; plaintext tokens never touch disk.
"""

import base64
import hashlib
import json
import logging
import uuid
from pathlib import Path
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)

TOKENS_FILE = Path.home() / ".autoforge" / "workspace" / ".tokens"


def _get_machine_key() -> bytes:
    """
    Derive a Fernet-compatible encryption key from the machine's MAC address.

    Uses SHA-256 hash of the MAC address (uuid.getnode()) to produce
    a 32-byte key, then base64url-encodes it for Fernet compatibility.
    """
    machine_id = str(uuid.getnode())
    key_bytes = hashlib.sha256(machine_id.encode()).digest()
    return base64.urlsafe_b64encode(key_bytes)


def encrypt_token(token: str) -> str:
    """Encrypt a plaintext token string. Returns the encrypted ciphertext."""
    f = Fernet(_get_machine_key())
    return f.encrypt(token.encode()).decode()


def decrypt_token(encrypted: str) -> str:
    """
    Decrypt an encrypted token string. Returns plaintext.

    Raises:
        ValueError: If decryption fails (wrong machine, corrupted data).
    """
    try:
        f = Fernet(_get_machine_key())
        return f.decrypt(encrypted.encode()).decode()
    except InvalidToken:
        raise ValueError("Failed to decrypt token -- was it encrypted on a different machine?")


def store_token(ref_id: str, token: str) -> None:
    """
    Encrypt and store a token with a reference ID.

    Creates the .tokens file and parent directories if they don't exist.
    """
    TOKENS_FILE.parent.mkdir(parents=True, exist_ok=True)

    tokens = _load_tokens_file()
    tokens[ref_id] = encrypt_token(token)
    _save_tokens_file(tokens)
    logger.info("Stored encrypted token with ref_id=%s", ref_id)


def retrieve_token(ref_id: str) -> Optional[str]:
    """
    Retrieve and decrypt a token by reference ID.

    Returns None if the ref_id is not found.
    """
    tokens = _load_tokens_file()
    encrypted = tokens.get(ref_id)
    if encrypted is None:
        return None
    return decrypt_token(encrypted)


def delete_token(ref_id: str) -> bool:
    """Delete a token by reference ID. Returns True if found and deleted."""
    tokens = _load_tokens_file()
    if ref_id not in tokens:
        return False
    del tokens[ref_id]
    _save_tokens_file(tokens)
    logger.info("Deleted token with ref_id=%s", ref_id)
    return True


def _load_tokens_file() -> dict[str, str]:
    """Load the tokens JSON file. Returns empty dict if file doesn't exist."""
    if not TOKENS_FILE.exists():
        return {}
    try:
        return json.loads(TOKENS_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Failed to load tokens file: %s", e)
        return {}


def _save_tokens_file(tokens: dict[str, str]) -> None:
    """Save tokens dict to the JSON file with restricted permissions."""
    TOKENS_FILE.write_text(json.dumps(tokens, indent=2), encoding="utf-8")
    # Restrict file permissions (owner read/write only)
    try:
        TOKENS_FILE.chmod(0o600)
    except OSError:
        pass  # Windows doesn't support Unix permissions
