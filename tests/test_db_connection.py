# ABOUTME: Tests for SQLite database connection manager.
# ABOUTME: Verifies context management, queries, and connection lifecycle.

import os
import tempfile


class TestDatabaseConnection:
    """Tests for database connection manager."""

    def test_connection_created_with_path(self):
        """Should create connection with given path."""
        from hikuweb.db.connection import DatabaseConnection

        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        try:
            conn = DatabaseConnection(db_path)
            assert conn.db_path == db_path
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_context_manager_closes_connection(self):
        """Should close connection when context exits."""
        from hikuweb.db.connection import DatabaseConnection

        db_path = ":memory:"
        conn = DatabaseConnection(db_path)

        with conn:
            # Connection should be open inside context
            assert conn._conn is not None

        # Connection should be closed after context exits
        assert conn._conn is None or not conn._conn

    def test_execute_runs_query(self):
        """Should execute SQL queries."""
        from hikuweb.db.connection import DatabaseConnection

        with DatabaseConnection(":memory:") as conn:
            conn.execute("CREATE TABLE test (id INTEGER, name TEXT)")
            conn.commit()
            conn.execute("INSERT INTO test VALUES (?, ?)", (1, "Alice"))
            conn.commit()

            conn.execute("SELECT * FROM test WHERE id = ?", (1,))
            result = conn.fetchone()
            assert result is not None
            assert result[0] == 1
            assert result[1] == "Alice"

    def test_executemany_runs_batch_operations(self):
        """Should execute batch operations."""
        from hikuweb.db.connection import DatabaseConnection

        with DatabaseConnection(":memory:") as conn:
            conn.execute("CREATE TABLE test (id INTEGER, name TEXT)")
            conn.commit()

            data = [(1, "Alice"), (2, "Bob"), (3, "Charlie")]
            conn.executemany("INSERT INTO test VALUES (?, ?)", data)
            conn.commit()

            conn.execute("SELECT COUNT(*) FROM test")
            result = conn.fetchone()
            assert result[0] == 3

    def test_fetchone_returns_single_row(self):
        """Should return single row."""
        from hikuweb.db.connection import DatabaseConnection

        with DatabaseConnection(":memory:") as conn:
            conn.execute("CREATE TABLE test (id INTEGER)")
            conn.execute("INSERT INTO test VALUES (1)")
            conn.commit()

            conn.execute("SELECT * FROM test")
            result = conn.fetchone()
            assert result == (1,)

    def test_fetchall_returns_all_rows(self):
        """Should return all rows."""
        from hikuweb.db.connection import DatabaseConnection

        with DatabaseConnection(":memory:") as conn:
            conn.execute("CREATE TABLE test (id INTEGER)")
            conn.executemany("INSERT INTO test VALUES (?)", [(1,), (2,), (3,)])
            conn.commit()

            conn.execute("SELECT * FROM test ORDER BY id")
            results = conn.fetchall()
            assert len(results) == 3
            assert results[0] == (1,)
            assert results[1] == (2,)
            assert results[2] == (3,)

    def test_commit_persists_changes(self):
        """Should commit changes to database."""
        from hikuweb.db.connection import DatabaseConnection

        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        try:
            # Insert data and commit
            with DatabaseConnection(db_path) as conn:
                conn.execute("CREATE TABLE test (id INTEGER)")
                conn.execute("INSERT INTO test VALUES (1)")
                conn.commit()

            # Verify data persists in new connection
            with DatabaseConnection(db_path) as conn:
                conn.execute("SELECT * FROM test")
                result = conn.fetchone()
                assert result == (1,)
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_rollback_reverts_changes(self):
        """Should rollback changes."""
        from hikuweb.db.connection import DatabaseConnection

        with DatabaseConnection(":memory:") as conn:
            conn.execute("CREATE TABLE test (id INTEGER)")
            conn.commit()

            conn.execute("INSERT INTO test VALUES (1)")
            conn.rollback()

            conn.execute("SELECT COUNT(*) FROM test")
            result = conn.fetchone()
            assert result[0] == 0

    def test_in_memory_database_works(self):
        """Should work with in-memory database."""
        from hikuweb.db.connection import DatabaseConnection

        with DatabaseConnection(":memory:") as conn:
            conn.execute("CREATE TABLE test (name TEXT)")
            conn.execute("INSERT INTO test VALUES ('test')")
            conn.commit()

            conn.execute("SELECT name FROM test")
            result = conn.fetchone()
            assert result[0] == "test"

    def test_multiple_queries_in_session(self):
        """Should handle multiple queries in one session."""
        from hikuweb.db.connection import DatabaseConnection

        with DatabaseConnection(":memory:") as conn:
            # Create multiple tables
            conn.execute("CREATE TABLE users (id INTEGER, name TEXT)")
            conn.execute("CREATE TABLE posts (id INTEGER, user_id INTEGER, title TEXT)")
            conn.commit()

            # Insert data
            conn.execute("INSERT INTO users VALUES (1, 'Alice')")
            conn.execute("INSERT INTO posts VALUES (1, 1, 'Hello')")
            conn.commit()

            # Query with join
            conn.execute("""
                SELECT users.name, posts.title
                FROM users
                JOIN posts ON users.id = posts.user_id
            """)
            result = conn.fetchone()
            assert result[0] == "Alice"
            assert result[1] == "Hello"


class TestGetDbConnection:
    """Tests for get_db_connection function."""

    def test_returns_working_connection(self):
        """Should return working database connection."""
        from hikuweb.db.connection import get_db_connection

        with get_db_connection(":memory:") as conn:
            conn.execute("CREATE TABLE test (id INTEGER)")
            conn.execute("INSERT INTO test VALUES (42)")
            conn.commit()

            conn.execute("SELECT id FROM test")
            result = conn.fetchone()
            assert result[0] == 42
