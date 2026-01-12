# ABOUTME: Configuration management for hikuweb using pydantic-settings.
# ABOUTME: Loads settings from environment variables with sensible defaults.

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    database_path: str = "hikuweb.db"
    openrouter_api_key: str | None = None
    rate_limit_requests_per_second: float = 1.0
    robots_cache_ttl_seconds: int = 3600

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    """Return cached Settings instance (singleton pattern)."""
    return Settings()
