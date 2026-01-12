# ABOUTME: Database operations for extraction_logs table.
# ABOUTME: Handles logging extractions and computing usage statistics.

import datetime

from hikuweb.db.connection import DatabaseConnection


def create_extraction_logs_table(conn: DatabaseConnection) -> None:
    """Create extraction_logs table if it doesn't exist.

    Args:
        conn: Database connection instance.
    """
    conn.execute("""
        CREATE TABLE IF NOT EXISTS extraction_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            api_key_id INTEGER NOT NULL,
            url TEXT NOT NULL,
            schema_hash TEXT NOT NULL,
            status TEXT NOT NULL,
            error_message TEXT,
            created_at TEXT NOT NULL,
            duration_ms INTEGER NOT NULL
        )
    """)
    conn.commit()


def insert_extraction_log(
    conn: DatabaseConnection,
    api_key_id: int,
    url: str,
    schema_hash: str,
    status: str,
    error_message: str | None,
    duration_ms: int,
) -> int:
    """Insert a new extraction log entry.

    Args:
        conn: Database connection instance.
        api_key_id: ID of the API key used for extraction.
        url: The URL that was extracted.
        schema_hash: Hash of the JSON schema used.
        status: Status of extraction ("success", "error", or "blocked").
        error_message: Error message if status is "error" or "blocked", None otherwise.
        duration_ms: Duration of extraction in milliseconds.

    Returns:
        The auto-generated ID of the inserted log entry.
    """
    created_at = datetime.datetime.now(datetime.UTC).isoformat()

    conn.execute(
        """
        INSERT INTO extraction_logs
            (api_key_id, url, schema_hash, status, error_message, created_at, duration_ms)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (api_key_id, url, schema_hash, status, error_message, created_at, duration_ms),
    )
    conn.commit()

    conn.execute("SELECT last_insert_rowid()")
    result = conn.fetchone()
    return result[0] if result else 0


def get_logs_by_api_key(
    conn: DatabaseConnection,
    api_key_id: int,
    limit: int = 100,
    offset: int = 0,
) -> list[dict]:
    """Retrieve extraction logs for a specific API key with pagination.

    Args:
        conn: Database connection instance.
        api_key_id: ID of the API key to filter by.
        limit: Maximum number of logs to return (default: 100).
        offset: Number of logs to skip for pagination (default: 0).

    Returns:
        List of log entries as dicts with all fields.
    """
    conn.execute(
        """
        SELECT id, api_key_id, url, schema_hash, status, error_message, created_at, duration_ms
        FROM extraction_logs
        WHERE api_key_id = ?
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
        """,
        (api_key_id, limit, offset),
    )

    rows = conn.fetchall()
    return [_row_to_dict(row) for row in rows]


def count_logs_by_api_key(conn: DatabaseConnection, api_key_id: int) -> int:
    """Count total number of logs for a specific API key.

    Args:
        conn: Database connection instance.
        api_key_id: ID of the API key to count logs for.

    Returns:
        Total count of log entries for the API key.
    """
    conn.execute(
        "SELECT COUNT(*) FROM extraction_logs WHERE api_key_id = ?",
        (api_key_id,),
    )
    result = conn.fetchone()
    return result[0] if result else 0


def get_usage_stats(conn: DatabaseConnection, api_key_id: int) -> dict:
    """Get aggregated usage statistics for an API key.

    Args:
        conn: Database connection instance.
        api_key_id: ID of the API key to get stats for.

    Returns:
        Dict with keys: total, success_count, error_count, blocked_count, avg_duration_ms.
    """
    conn.execute(
        """
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_count,
            SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as error_count,
            SUM(CASE WHEN status = 'blocked' THEN 1 ELSE 0 END) as blocked_count,
            AVG(duration_ms) as avg_duration_ms
        FROM extraction_logs
        WHERE api_key_id = ?
        """,
        (api_key_id,),
    )

    row = conn.fetchone()
    if not row or row[0] == 0:
        return {
            "total": 0,
            "success_count": 0,
            "error_count": 0,
            "blocked_count": 0,
            "avg_duration_ms": 0.0,
        }

    return {
        "total": row[0],
        "success_count": row[1],
        "error_count": row[2],
        "blocked_count": row[3],
        "avg_duration_ms": row[4] if row[4] is not None else 0.0,
    }


def _row_to_dict(row: tuple) -> dict:
    """Convert a database row tuple to a dict with named fields.

    Args:
        row: Tuple with 8 fields from extraction_logs table.

    Returns:
        Dict with keys: id, api_key_id, url, schema_hash, status, error_message,
        created_at, duration_ms.
    """
    return {
        "id": row[0],
        "api_key_id": row[1],
        "url": row[2],
        "schema_hash": row[3],
        "status": row[4],
        "error_message": row[5],
        "created_at": row[6],
        "duration_ms": row[7],
    }
