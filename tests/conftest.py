# ABOUTME: Pytest fixtures and configuration for hikuweb tests.
# ABOUTME: Provides reusable test fixtures like db_connection.

import pytest

from hikuweb.db.connection import DatabaseConnection


@pytest.fixture
def db_connection():
    """Provides an in-memory database connection for testing.

    Yields:
        DatabaseConnection: In-memory SQLite connection that automatically closes.
    """
    with DatabaseConnection(":memory:") as conn:
        yield conn
