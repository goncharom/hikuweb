# ABOUTME: Tests for API key service business logic.
# ABOUTME: Verifies key generation, hashing, and validation.


from hikuweb.db.api_keys import create_api_keys_table
from hikuweb.services.api_key_service import (
    create_api_key,
    generate_api_key,
    hash_api_key,
    validate_api_key,
)


class TestGenerateApiKey:
    """Tests for generate_api_key function."""

    def test_returns_32_char_string(self):
        """Should return 32 character alphanumeric string."""
        # Act
        key = generate_api_key()

        # Assert
        assert isinstance(key, str)
        assert len(key) == 32

    def test_returns_alphanumeric_only(self):
        """Should return only alphanumeric characters (a-zA-Z0-9)."""
        # Act
        key = generate_api_key()

        # Assert
        assert key.isalnum()

    def test_returns_different_keys(self):
        """Should return different keys on each call."""
        # Act
        key1 = generate_api_key()
        key2 = generate_api_key()
        key3 = generate_api_key()

        # Assert
        assert key1 != key2
        assert key2 != key3
        assert key1 != key3


class TestHashApiKey:
    """Tests for hash_api_key function."""

    def test_consistent_hash(self):
        """Should return same hash for same input."""
        # Arrange
        raw_key = "test_key_12345"

        # Act
        hash1 = hash_api_key(raw_key)
        hash2 = hash_api_key(raw_key)

        # Assert
        assert hash1 == hash2

    def test_different_hashes_for_different_inputs(self):
        """Should return different hashes for different inputs."""
        # Arrange
        key1 = "test_key_1"
        key2 = "test_key_2"

        # Act
        hash1 = hash_api_key(key1)
        hash2 = hash_api_key(key2)

        # Assert
        assert hash1 != hash2

    def test_returns_sha256_hex_digest(self):
        """Should return SHA-256 hex digest (64 characters)."""
        # Arrange
        raw_key = "test_key"

        # Act
        result = hash_api_key(raw_key)

        # Assert
        assert isinstance(result, str)
        assert len(result) == 64  # SHA-256 hex digest is 64 chars
        assert all(c in "0123456789abcdef" for c in result)


class TestCreateApiKey:
    """Tests for create_api_key function."""

    def test_stores_hash_returns_raw(self, db_connection):
        """Should store hash in DB and return raw key."""
        # Arrange
        create_api_keys_table(db_connection)
        name = "Test Key"

        # Act
        raw_key = create_api_key(db_connection, name)

        # Assert
        assert isinstance(raw_key, str)
        assert len(raw_key) == 32

        # Verify hash is stored in DB
        key_hash = hash_api_key(raw_key)
        db_connection.execute("SELECT * FROM api_keys WHERE key_hash = ?", (key_hash,))
        row = db_connection.fetchone()
        assert row is not None
        assert row[2] == name  # name column

    def test_creates_unique_keys(self, db_connection):
        """Should create different keys on each call."""
        # Arrange
        create_api_keys_table(db_connection)

        # Act
        key1 = create_api_key(db_connection, "Key 1")
        key2 = create_api_key(db_connection, "Key 2")

        # Assert
        assert key1 != key2

    def test_stores_name_correctly(self, db_connection):
        """Should store the provided name in the database."""
        # Arrange
        create_api_keys_table(db_connection)
        name = "Production API Key"

        # Act
        raw_key = create_api_key(db_connection, name)

        # Assert
        key_hash = hash_api_key(raw_key)
        db_connection.execute("SELECT name FROM api_keys WHERE key_hash = ?", (key_hash,))
        row = db_connection.fetchone()
        assert row[0] == name


class TestValidateApiKey:
    """Tests for validate_api_key function."""

    def test_valid_key_returns_record(self, db_connection):
        """Should return record for valid active key."""
        # Arrange
        create_api_keys_table(db_connection)
        raw_key = create_api_key(db_connection, "Test Key")

        # Act
        result = validate_api_key(db_connection, raw_key)

        # Assert
        assert result is not None
        assert isinstance(result, dict)
        assert result["name"] == "Test Key"
        assert result["is_active"] == 1

    def test_invalid_key_returns_none(self, db_connection):
        """Should return None if key doesn't exist."""
        # Arrange
        create_api_keys_table(db_connection)

        # Act
        result = validate_api_key(db_connection, "nonexistent_key_12345678901234")

        # Assert
        assert result is None

    def test_inactive_key_returns_none(self, db_connection):
        """Should return None if key is inactive."""
        # Arrange
        create_api_keys_table(db_connection)
        raw_key = create_api_key(db_connection, "Test Key")

        # Deactivate the key
        key_hash = hash_api_key(raw_key)
        db_connection.execute("UPDATE api_keys SET is_active = 0 WHERE key_hash = ?", (key_hash,))
        db_connection.commit()

        # Act
        result = validate_api_key(db_connection, raw_key)

        # Assert
        assert result is None

    def test_updates_last_used_at(self, db_connection):
        """Should update last_used_at on successful validation."""
        # Arrange
        create_api_keys_table(db_connection)
        raw_key = create_api_key(db_connection, "Test Key")

        # Check initial state (last_used_at should be None)
        key_hash = hash_api_key(raw_key)
        db_connection.execute("SELECT last_used_at FROM api_keys WHERE key_hash = ?", (key_hash,))
        row = db_connection.fetchone()
        assert row[0] is None

        # Act
        result = validate_api_key(db_connection, raw_key)

        # Assert
        assert result is not None

        # Check that last_used_at was updated
        db_connection.execute("SELECT last_used_at FROM api_keys WHERE key_hash = ?", (key_hash,))
        row = db_connection.fetchone()
        assert row[0] is not None  # Should now have a timestamp

    def test_validation_updates_timestamp_each_time(self, db_connection):
        """Should update timestamp on each validation."""
        # Arrange
        create_api_keys_table(db_connection)
        raw_key = create_api_key(db_connection, "Test Key")

        # Act - validate twice
        validate_api_key(db_connection, raw_key)

        key_hash = hash_api_key(raw_key)
        db_connection.execute("SELECT last_used_at FROM api_keys WHERE key_hash = ?", (key_hash,))
        first_timestamp = db_connection.fetchone()[0]

        # Small delay to ensure different timestamp
        import time

        time.sleep(0.01)

        validate_api_key(db_connection, raw_key)

        db_connection.execute("SELECT last_used_at FROM api_keys WHERE key_hash = ?", (key_hash,))
        second_timestamp = db_connection.fetchone()[0]

        # Assert
        assert second_timestamp >= first_timestamp
