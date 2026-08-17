"""
Encryption at rest — AES-256-GCM.
"""
import os

import pytest

from CORE_AGENT_INFRASTRUCTURE.db import crypto


@pytest.fixture()
def key(monkeypatch):
    monkeypatch.setenv("ENCRYPTION_KEY", "ab" * 32)  # 32 bytes
    crypto._KEY = None
    crypto._EPHEMERAL = False
    yield
    crypto._KEY = None
    crypto._EPHEMERAL = False


def test_roundtrip(key):
    blob = crypto.encrypt("super-secret-api-key-12345")
    assert blob.startswith("v1:")
    assert "super-secret" not in blob          # plaintext never stored
    assert crypto.decrypt(blob) == "super-secret-api-key-12345"


def test_tamper_detected(key):
    blob = crypto.encrypt("secret")
    nonce, ct = blob.split(":", 2)[1], blob.split(":", 2)[2]
    corrupted = "v1:" + nonce + ":" + "A" * len(ct)
    with pytest.raises(crypto.CryptoError):
        crypto.decrypt(corrupted)


def test_missing_key_fails_in_production(monkeypatch):
    monkeypatch.setenv("STRATUM_ENV", "production")
    monkeypatch.delenv("ENCRYPTION_KEY", raising=False)
    crypto._KEY = None
    with pytest.raises(crypto.CryptoError):
        crypto.get_master_key()
    crypto._KEY = None
