# ABOUTME: Pytest fixtures and configuration for hikuweb tests.
# ABOUTME: Provides reusable test fixtures like db_connection and client.

import pytest
from fastapi.testclient import TestClient

from hikuweb.db.connection import DatabaseConnection


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
