# ABOUTME: Service layer for API key operations.
# ABOUTME: Handles secure key generation, hashing, and validation.

import hashlib
import secrets
import string

from hikuweb.db.api_keys import get_api_key_by_hash, insert_api_key, update_last_used
from hikuweb.db.connection import DatabaseConnection


def generate_api_key() -> str:
    """Generate a secure random API key.

    Returns:
        A 32-character alphanumeric string using cryptographically secure random generation.
    """
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(32))


def hash_api_key(raw_key: str) -> str:
    """Hash an API key using SHA-256.

    Args:
        raw_key: The raw API key string to hash.

    Returns:
        The SHA-256 hex digest (64 characters).
    """
    return hashlib.sha256(raw_key.encode()).hexdigest()


def create_api_key(conn: DatabaseConnection, name: str) -> str:
    """Create a new API key and store its hash in the database.

    This is the only time the raw key is available. The key is generated,
    hashed, stored in the database, and the raw key is returned to the caller.
    The raw key must be securely communicated to the user and cannot be
    retrieved later.

    Args:
        conn: Database connection context manager.
        name: Friendly name for the API key.

    Returns:
        The raw API key string (32 characters). This is the only time it's available!
    """
    raw_key = generate_api_key()
    key_hash = hash_api_key(raw_key)
    insert_api_key(conn, key_hash, name)
    return raw_key


def validate_api_key(conn: DatabaseConnection, raw_key: str) -> dict | None:
    """Validate an API key and update its last_used_at timestamp.

    Args:
        conn: Database connection context manager.
        raw_key: The raw API key to validate.

    Returns:
        The API key record dict if valid and active, None otherwise.
    """
    key_hash = hash_api_key(raw_key)
    key_record = get_api_key_by_hash(conn, key_hash)

    if key_record is None:
        return None

    if key_record["is_active"] != 1:
        return None

    update_last_used(conn, key_record["id"])

    return key_record
