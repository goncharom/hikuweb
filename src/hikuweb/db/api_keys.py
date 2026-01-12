# ABOUTME: Database operations for api_keys table.
# ABOUTME: Handles CRUD operations for API key storage and validation.

from datetime import UTC, datetime

from hikuweb.db.connection import DatabaseConnection


def create_api_keys_table(conn: DatabaseConnection) -> None:
    """Create the api_keys table if it doesn't exist.

    Table schema:
    - id: INTEGER PRIMARY KEY AUTOINCREMENT
    - key_hash: TEXT UNIQUE NOT NULL (SHA-256 hash of the raw key)
    - name: TEXT NOT NULL (friendly name for the key)
    - created_at: TEXT NOT NULL (ISO 8601 timestamp)
    - last_used_at: TEXT (nullable, updated on each use)
    - is_active: INTEGER NOT NULL DEFAULT 1 (1=active, 0=inactive)

    Args:
        conn: Database connection instance.
    """
    conn.execute("""
        CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key_hash TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            created_at TEXT NOT NULL,
            last_used_at TEXT,
            is_active INTEGER NOT NULL DEFAULT 1
        )
    """)
    conn.commit()


def insert_api_key(conn: DatabaseConnection, key_hash: str, name: str) -> int:
    """Insert a new API key record.

    Args:
        conn: Database connection instance.
        key_hash: SHA-256 hash of the raw API key.
        name: Friendly name for the key.

    Returns:
        The auto-generated id of the inserted key.

    Raises:
        Exception: If key_hash already exists (UNIQUE constraint violation).
    """
    created_at = datetime.now(UTC).isoformat()
    conn.execute(
        "INSERT INTO api_keys (key_hash, name, created_at) VALUES (?, ?, ?)",
        (key_hash, name, created_at),
    )
    conn.commit()
    # Get the last inserted row id
    conn.execute("SELECT last_insert_rowid()")
    result = conn.fetchone()
    return result[0]


def get_api_key_by_hash(conn: DatabaseConnection, key_hash: str) -> dict | None:
    """Retrieve API key record by hash.

    Args:
        conn: Database connection instance.
        key_hash: SHA-256 hash of the raw API key.

    Returns:
        Dictionary containing key record fields, or None if not found.
    """
    conn.execute("SELECT * FROM api_keys WHERE key_hash = ?", (key_hash,))
    row = conn.fetchone()
    if row is None:
        return None
    return _row_to_dict(row)


def get_api_key_by_id(conn: DatabaseConnection, key_id: int) -> dict | None:
    """Retrieve API key record by ID.

    Args:
        conn: Database connection instance.
        key_id: Primary key of the API key record.

    Returns:
        Dictionary containing key record fields, or None if not found.
    """
    conn.execute("SELECT * FROM api_keys WHERE id = ?", (key_id,))
    row = conn.fetchone()
    if row is None:
        return None
    return _row_to_dict(row)


def update_last_used(conn: DatabaseConnection, key_id: int) -> None:
    """Update the last_used_at timestamp for an API key.

    Args:
        conn: Database connection instance.
        key_id: Primary key of the API key record.
    """
    now = datetime.now(UTC).isoformat()
    conn.execute("UPDATE api_keys SET last_used_at = ? WHERE id = ?", (now, key_id))
    conn.commit()


def deactivate_api_key(conn: DatabaseConnection, key_id: int) -> None:
    """Deactivate an API key by setting is_active to 0.

    Args:
        conn: Database connection instance.
        key_id: Primary key of the API key record.
    """
    conn.execute("UPDATE api_keys SET is_active = 0 WHERE id = ?", (key_id,))
    conn.commit()


def list_api_keys(conn: DatabaseConnection) -> list[dict]:
    """List all API keys (both active and inactive).

    Args:
        conn: Database connection instance.

    Returns:
        List of dictionaries containing key record fields.
    """
    conn.execute("SELECT * FROM api_keys")
    rows = conn.fetchall()
    return [_row_to_dict(row) for row in rows]


def _row_to_dict(row: tuple) -> dict:
    """Convert a database row tuple to a dictionary.

    Args:
        row: Tuple from database query (id, key_hash, name, created_at, last_used_at, is_active).

    Returns:
        Dictionary with named fields.
    """
    return {
        "id": row[0],
        "key_hash": row[1],
        "name": row[2],
        "created_at": row[3],
        "last_used_at": row[4],
        "is_active": row[5],
    }
