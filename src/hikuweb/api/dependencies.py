# ABOUTME: FastAPI dependencies for database and authentication.
# ABOUTME: Provides get_db() and get_api_key() for dependency injection.
# ruff: noqa: B008

from collections.abc import Generator

from fastapi import Depends, HTTPException
from fastapi.security import APIKeyHeader

from hikuweb.config import get_settings
from hikuweb.db.connection import DatabaseConnection, get_db_connection
from hikuweb.services.api_key_service import validate_api_key

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
