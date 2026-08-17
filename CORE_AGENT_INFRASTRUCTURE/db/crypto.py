"""
Encryption at rest — AES-256-GCM for sensitive DB fields.

Master key comes from ENCRYPTION_KEY (64 hex chars = 32 bytes), provided
via environment / secret store. NEVER hardcoded. Generate one with:
    python -c "import secrets; print(secrets.token_hex(32))"
or  scripts/setup_env.sh

Blob format: "v1:<nonce_b64>:<ciphertext_b64>" — authenticated, tamper-evident.
"""
import base64
import binascii
import logging
import os
from typing import Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

logger = logging.getLogger("stratum.crypto")

_KEY: Optional[bytes] = None
_EPHEMERAL = False


class CryptoError(RuntimeError):
    pass


def get_master_key() -> bytes:
    """Return the 32-byte master key (from env, or ephemeral in dev)."""
    global _KEY, _EPHEMERAL
    if _KEY is not None:
        return _KEY
    raw = os.getenv("ENCRYPTION_KEY", "")
    if raw:
        try:
            _KEY = bytes.fromhex(raw)
        except ValueError as exc:
            raise CryptoError("ENCRYPTION_KEY must be 64 hex chars (32 bytes)") from exc
        if len(_KEY) != 32:
            raise CryptoError("ENCRYPTION_KEY must be 64 hex chars (32 bytes)")
        return _KEY
    if os.getenv("STRATUM_ENV", "development") == "production":
        raise CryptoError("ENCRYPTION_KEY is required in production (set it in the secret store)")
    # dev-only ephemeral key
    import secrets
    _KEY = secrets.token_bytes(32)
    _EPHEMERAL = True
    logger.warning("Using EPHEMERAL dev encryption key — secrets will not survive restarts. Set ENCRYPTION_KEY.")
    return _KEY


def is_ephemeral() -> bool:
    get_master_key()
    return _EPHEMERAL


def encrypt(plaintext: str) -> str:
    """Encrypt a string; returns 'v1:nonce:ciphertext' (b64)."""
    if plaintext is None:
        plaintext = ""
    nonce = os.urandom(12)
    ciphertext = AESGCM(get_master_key()).encrypt(nonce, plaintext.encode("utf-8"), None)
    return "v1:" + base64.b64encode(nonce).decode() + ":" + base64.b64encode(ciphertext).decode()


def decrypt(blob: str) -> str:
    """Decrypt a 'v1:...' blob. Raises CryptoError on tampering."""
    if not blob:
        return ""
    try:
        version, nonce_b64, ct_b64 = blob.split(":", 2)
        if version != "v1":
            raise ValueError("unknown version")
        nonce = base64.b64decode(nonce_b64)
        ciphertext = base64.b64decode(ct_b64)
        plaintext = AESGCM(get_master_key()).decrypt(nonce, ciphertext, None)
        return plaintext.decode("utf-8")
    except (ValueError, binascii.Error, Exception) as exc:  # noqa: BLE001
        raise CryptoError(f"Failed to decrypt value: {exc}") from exc


from sqlalchemy import Text
from sqlalchemy.types import TypeDecorator


class EncryptedText(TypeDecorator):
    """Encrypted-at-rest string column (AES-256-GCM).

    Usage:
        api_key = mapped_column(EncryptedText(1024))
    Stored as TEXT containing 'v1:nonce:ciphertext'; plaintext never
    touches the database and is never returned by the API.
    """

    impl = Text
    cache_ok = True

    def __init__(self, length: int = 1024):
        super().__init__(length=length)

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return encrypt(str(value))

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return decrypt(value)
