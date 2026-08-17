"""
Stratum AI — central application configuration.

Everything sensitive comes from environment variables (.env file or the
deployment's secret store). Nothing is hardcoded. In production the config
validates itself and refuses to boot with missing required secrets.

Required in production:  DATABASE_URL, JWT_SECRET, ENCRYPTION_KEY,
                         LLM_PROVIDER (+ provider key where applicable)
"""
import os
import secrets as _secrets
from functools import lru_cache
from pathlib import Path


def _load_dotenv() -> None:
    """Load .env from the repo root if present (real env vars win)."""
    try:
        from dotenv import load_dotenv

        load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    except ImportError:
        pass


_load_dotenv()


class ConfigError(RuntimeError):
    """Raised when configuration is missing or invalid."""


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


class AppConfig:
    def __init__(self) -> None:
        self.environment = _env("STRATUM_ENV", "development")          # development | production
        self.demo_mode = _env("DEMO_MODE", "false").lower() in ("1", "true", "yes")
        self.log_level = _env("LOG_LEVEL", "INFO")

        # --- database -------------------------------------------------------
        self.database_url = _env(
            "DATABASE_URL",
            "sqlite:///./stratum.db" if self.environment != "production" else "",
        )

        # --- secrets (never defaulted in production) -------------------------
        self.jwt_secret = _env("JWT_SECRET", "")
        self.encryption_key = _env("ENCRYPTION_KEY", "")   # 64 hex chars = 32 bytes AES-256

        # --- BYO-LLM ----------------------------------------------------------
        self.llm_provider = _env("LLM_PROVIDER", "openai")  # openai|anthropic|azure|openrouter|groq|together|ollama|openai_compatible
        self.llm_api_key = _env("LLM_API_KEY", "")
        self.llm_base_url = _env("LLM_BASE_URL", "")
        self.llm_model_fast = _env("LLM_MODEL_FAST", "gpt-4o-mini")
        self.llm_model_quality = _env("LLM_MODEL_QUALITY", "gpt-4o")
        self.llm_embedding_model = _env("LLM_EMBEDDING_MODEL", "")
        self.llm_timeout = int(_env("LLM_TIMEOUT", "60"))
        self.llm_max_tokens = int(_env("LLM_MAX_TOKENS", "2048"))
        self.llm_extra_headers = _env("LLM_EXTRA_HEADERS", "")  # JSON object, e.g. {"HTTP-Referer": "..."}
        self.llm_fallback_provider = _env("LLM_FALLBACK_PROVIDER", "")  # second provider for failover

        # --- web ---------------------------------------------------------------
        self.cors_origins = [o.strip() for o in _env("CORS_ORIGINS", "*").split(",") if o.strip()]
        self.api_prefix = _env("API_PREFIX", "/api")
        self.token_ttl_hours = int(_env("TOKEN_TTL_HOURS", "8"))

        # --- demo-mode owner account (only used when DEMO_MODE=true) ------------
        self.demo_admin_email = _env("DEMO_ADMIN_EMAIL", "admin@stratum.local")
        self.demo_admin_password = _env("DEMO_ADMIN_PASSWORD", "")

    # -- helpers ----------------------------------------------------------------
    def is_production(self) -> bool:
        return self.environment == "production"

    def is_demo(self) -> bool:
        return self.demo_mode

    def generate_ephemeral(self) -> None:
        """Dev-mode only: generate throwaway secrets so the app boots instantly."""
        self.jwt_secret = _secrets.token_hex(32)
        self.encryption_key = _secrets.token_hex(32)

    def validate(self) -> None:
        """Hard-fail in production when required config is missing."""
        missing = []
        for name, value in [
            ("DATABASE_URL", self.database_url),
            ("JWT_SECRET", self.jwt_secret),
            ("ENCRYPTION_KEY", self.encryption_key),
            ("LLM_PROVIDER", self.llm_provider),
        ]:
            if not value:
                missing.append(name)

        keyed = {"openai", "anthropic", "azure", "openrouter", "groq", "together", "openai_compatible"}
        if self.llm_provider in keyed and not self.llm_api_key:
            missing.append("LLM_API_KEY")

        if missing:
            raise ConfigError(
                "Missing required configuration in production: "
                + ", ".join(missing)
                + ". Set them in the environment / secret store (see .env.example)."
            )

    def describe(self) -> dict:
        """Non-sensitive system status for /api/system/status."""
        return {
            "environment": self.environment,
            "demo_mode": self.demo_mode,
            "llm_provider": self.llm_provider,
            "llm_base_url": self.llm_base_url or ("https://api.openai.com/v1" if self.llm_provider == "openai" else ""),
            "llm_model_fast": self.llm_model_fast,
            "llm_model_quality": self.llm_model_quality,
            "llm_fallback_provider": self.llm_fallback_provider or None,
            "llm_configured": bool(self.llm_api_key) or self.llm_provider == "ollama",
            "db": self.database_url.split(":", 1)[0].split("+", 1)[0] + "://",
        }


@lru_cache
def get_config() -> AppConfig:
    return AppConfig()


def resolve_config() -> AppConfig:
    """App startup: load config, auto-generate dev secrets, validate prod."""
    cfg = get_config()
    if cfg.is_production():
        cfg.validate()
    else:
        if not cfg.jwt_secret or not cfg.encryption_key:
            cfg.generate_ephemeral()
    return cfg
