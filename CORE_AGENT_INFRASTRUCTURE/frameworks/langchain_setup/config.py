"""
Central configuration for LangChain-based agents.

Loads settings from environment variables (.env) with sane defaults.
All agents should import settings from here so model routing,
temperature and memory settings stay consistent across the agency.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # --- LLM providers -----------------------------------------------------
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    default_llm: str = "openai"                 # openai | anthropic | azure
    fast_model: str = "gpt-4o-mini"             # classification, extraction
    quality_model: str = "gpt-4o"               # generation, negotiation
    embedding_model: str = "text-embedding-3-small"
    temperature_default: float = 0.2

    # --- Infra ---------------------------------------------------------------
    redis_url: str = "redis://localhost:6379/0"
    database_url: str = "postgresql+psycopg2://agent:agent@localhost:5432/stratum"
    environment: str = "development"            # development | staging | production
    log_level: str = "INFO"

    # --- Agency defaults -----------------------------------------------------
    default_timezone: str = "America/Denver"
    max_retries: int = 3
    request_timeout_seconds: int = 30


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
