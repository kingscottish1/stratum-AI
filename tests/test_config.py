"""
Config behavior: dev boots with ephemeral secrets; production refuses.
"""
import pytest

from CORE_AGENT_INFRASTRUCTURE.config import AppConfig, ConfigError


def test_dev_defaults_allow_ephemeral():
    cfg = AppConfig()
    cfg.generate_ephemeral()
    assert cfg.jwt_secret
    assert cfg.encryption_key
    assert cfg.is_production() is False


def test_production_validation_fails_without_secrets(monkeypatch):
    monkeypatch.setenv("STRATUM_ENV", "production")
    for var in ("JWT_SECRET", "ENCRYPTION_KEY", "DATABASE_URL", "LLM_PROVIDER", "LLM_API_KEY"):
        monkeypatch.delenv(var, raising=False)
    cfg = AppConfig()
    with pytest.raises(ConfigError):
        cfg.validate()


def test_production_validation_passes_with_secrets(monkeypatch):
    monkeypatch.setenv("STRATUM_ENV", "production")
    monkeypatch.setenv("JWT_SECRET", "x" * 32)
    monkeypatch.setenv("ENCRYPTION_KEY", "ab" * 32)
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@h/db")
    monkeypatch.setenv("LLM_PROVIDER", "ollama")  # no key required
    cfg = AppConfig()
    cfg.validate()  # should not raise
