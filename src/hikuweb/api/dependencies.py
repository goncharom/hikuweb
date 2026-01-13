# ABOUTME: FastAPI dependencies for database and authentication.
# ABOUTME: Provides get_db() and get_api_key() for dependency injection.
# ruff: noqa: B008

from collections.abc import Generator
from functools import lru_cache

from fastapi import Depends, HTTPException
from fastapi.security import APIKeyHeader

from hikuweb.config import get_settings
from hikuweb.db.connection import DatabaseConnection, get_db_connection
from hikuweb.services.api_key_service import validate_api_key
from hikuweb.services.extraction import ExtractionService
from hikuweb.services.rate_limiter import DomainRateLimiter
from hikuweb.services.robots import RobotsChecker

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def get_db() -> Generator[DatabaseConnection, None, None]:
    """Provides database connection for dependency injection.

    Yields:
        DatabaseConnection: Context-managed database connection.
    """
    settings = get_settings()
    with get_db_connection(settings.database_path) as conn:
        yield conn


def get_api_key(
    api_key: str | None = Depends(api_key_header),
    db: DatabaseConnection = Depends(get_db),
) -> dict:
    """Validates API key and returns key record.

    Args:
        api_key: API key from X-API-Key header.
        db: Database connection from dependency injection.

    Returns:
        dict: API key record with id, name, created_at, last_used_at, is_active.

    Raises:
        HTTPException: 401 if API key missing, invalid, or inactive.
    """
    if not api_key:
        raise HTTPException(status_code=401, detail="API key required")

    record = validate_api_key(db, api_key)
    if not record:
        raise HTTPException(status_code=401, detail="Invalid or inactive API key")

    return record


@lru_cache
def get_robots_checker() -> RobotsChecker:
    """Provides singleton RobotsChecker instance.

    Returns:
        RobotsChecker: Singleton robots.txt checker with TTL cache.
    """
    settings = get_settings()
    return RobotsChecker(cache_ttl_seconds=settings.robots_cache_ttl_seconds)


@lru_cache
def get_rate_limiter() -> DomainRateLimiter:
    """Provides singleton DomainRateLimiter instance.

    Returns:
        DomainRateLimiter: Singleton rate limiter for domain throttling.
    """
    settings = get_settings()
    return DomainRateLimiter(requests_per_second=settings.rate_limit_requests_per_second)


@lru_cache
def get_extraction_service() -> ExtractionService:
    """Provides singleton ExtractionService instance.

    Returns:
        ExtractionService: Singleton extraction service configured with API key.

    Raises:
        RuntimeError: If OPENROUTER_API_KEY not configured.
    """
    settings = get_settings()
    # Use a dummy API key for testing if OPENROUTER_API_KEY not set
    api_key = settings.openrouter_api_key or "test-api-key"
    return ExtractionService(openrouter_api_key=api_key)
