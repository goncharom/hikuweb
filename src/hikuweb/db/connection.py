# ABOUTME: SQLite database connection manager with context management.
# ABOUTME: Provides execute, fetchone, fetchall methods for database operations.

import sqlite3
from typing import Any


class DatabaseConnection:
    """SQLite database connection with context manager support."""

    def __init__(self, db_path: str):
        """Initialize database connection with given path.

        Args:
            db_path: Path to SQLite database file or ":memory:" for in-memory database.
        """
        self.db_path = db_path
        self._conn: sqlite3.Connection | None = None
        self._cursor: sqlite3.Cursor | None = None

    def __enter__(self) -> "DatabaseConnection":
        """Open database connection when entering context."""
        # check_same_thread=False allows FastAPI threadpool usage
        # This is safe because each endpoint call gets its own connection
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._cursor = self._conn.cursor()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Close database connection when exiting context."""
        if self._cursor:
            self._cursor.close()
            self._cursor = None
        if self._conn:
            self._conn.close()
            self._conn = None

    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """Execute a SQL query.

        Args:
            query: SQL query string.
            params: Query parameters tuple.

        Returns:
            Cursor object with query results.

        Raises:
            RuntimeError: If connection not opened via context manager.
        """
        if not self._cursor:
            raise RuntimeError("Connection not opened. Use 'with' statement.")
        self._cursor.execute(query, params)
        return self._cursor

    def executemany(self, query: str, params_list: list) -> sqlite3.Cursor:
        """Execute a SQL query with multiple parameter sets.

        Args:
            query: SQL query string.
            params_list: List of parameter tuples.

        Returns:
            Cursor object.

        Raises:
            RuntimeError: If connection not opened via context manager.
        """
        if not self._cursor:
            raise RuntimeError("Connection not opened. Use 'with' statement.")
        self._cursor.executemany(query, params_list)
        return self._cursor

    def fetchone(self) -> tuple | None:
        """Fetch one row from the last query.

        Returns:
            Row tuple or None if no more rows.

        Raises:
            RuntimeError: If connection not opened via context manager.
        """
        if not self._cursor:
            raise RuntimeError("Connection not opened. Use 'with' statement.")
        return self._cursor.fetchone()

    def fetchall(self) -> list[tuple]:
        """Fetch all rows from the last query.

        Returns:
            List of row tuples.

        Raises:
            RuntimeError: If connection not opened via context manager.
        """
        if not self._cursor:
            raise RuntimeError("Connection not opened. Use 'with' statement.")
        return self._cursor.fetchall()

    def commit(self) -> None:
        """Commit current transaction.

        Raises:
            RuntimeError: If connection not opened via context manager.
        """
        if not self._conn:
            raise RuntimeError("Connection not opened. Use 'with' statement.")
        self._conn.commit()

    def rollback(self) -> None:
        """Rollback current transaction.

        Raises:
            RuntimeError: If connection not opened via context manager.
        """
        if not self._conn:
            raise RuntimeError("Connection not opened. Use 'with' statement.")
        self._conn.rollback()


def get_db_connection(db_path: str) -> DatabaseConnection:
    """Get a database connection instance.

    Args:
        db_path: Path to SQLite database file or ":memory:" for in-memory database.

    Returns:
        DatabaseConnection instance.
    """
    return DatabaseConnection(db_path)
