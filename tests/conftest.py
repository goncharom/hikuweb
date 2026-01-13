# ABOUTME: Pytest fixtures and configuration for hikuweb tests.
# ABOUTME: Provides reusable test fixtures like db_connection and client.

import pytest
from fastapi.testclient import TestClient

from hikuweb.db.api_keys import create_api_keys_table, deactivate_api_key
from hikuweb.db.connection import DatabaseConnection
from hikuweb.services.api_key_service import create_api_key


@pytest.fixture
def db_connection():
    """Provides an in-memory database connection for testing.

    Yields:
        DatabaseConnection: In-memory SQLite connection that automatically closes.
    """
    with DatabaseConnection(":memory:") as conn:
        yield conn


@pytest.fixture
def client():
    """Provides a FastAPI TestClient for API endpoint testing.

    Yields:
        TestClient: FastAPI test client for making HTTP requests.
    """
    from hikuweb.main import app

    with TestClient(app) as c:
        yield c


@pytest.fixture
def test_api_key(client):
    """Provides a valid test API key stored in the database.

    Returns:
        str: Raw API key string for use in X-API-Key header.
    """
    from hikuweb.config import get_settings
    from hikuweb.db.connection import get_db_connection

    settings = get_settings()
    with get_db_connection(settings.database_path) as conn:
        create_api_keys_table(conn)
        raw_key = create_api_key(conn, "test-key")
    return raw_key


@pytest.fixture
def inactive_api_key(client):
    """Provides an inactive test API key stored in the database.

    Returns:
        str: Raw API key string that has been deactivated.
    """
    from hikuweb.config import get_settings
    from hikuweb.db.connection import get_db_connection

    settings = get_settings()
    with get_db_connection(settings.database_path) as conn:
        create_api_keys_table(conn)
        raw_key = create_api_key(conn, "inactive-key")
        # Get the key ID to deactivate it
        from hikuweb.services.api_key_service import hash_api_key

        key_hash = hash_api_key(raw_key)
        from hikuweb.db.api_keys import get_api_key_by_hash

        key_record = get_api_key_by_hash(conn, key_hash)
        if key_record:
            deactivate_api_key(conn, key_record["id"])
    return raw_key


@pytest.fixture
def auth_headers(test_api_key):
    """Provides HTTP headers with valid API key for authenticated requests.

    Args:
        test_api_key: Raw API key from test_api_key fixture.

    Returns:
        dict: Headers dict with X-API-Key set to valid test key.
    """
    return {"X-API-Key": test_api_key}
