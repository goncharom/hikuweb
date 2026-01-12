# ABOUTME: Tests for api_keys table CRUD operations.
# ABOUTME: Verifies table creation, insert, query, update, and constraints.

import sqlite3

import pytest

from hikuweb.db.api_keys import (
    create_api_keys_table,
    deactivate_api_key,
    get_api_key_by_hash,
    get_api_key_by_id,
    insert_api_key,
    list_api_keys,
    update_last_used,
)


class TestCreateApiKeysTable:
    """Tests for api_keys table creation."""

    def test_creates_table(self, db_connection):
        """Should create api_keys table with correct schema."""
        # Arrange/Act
        create_api_keys_table(db_connection)

        # Assert - verify table exists and has expected columns
        db_connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='api_keys'"
        )
        result = db_connection.fetchone()
        assert result is not None
        assert result[0] == "api_keys"

        # Verify schema
        db_connection.execute("PRAGMA table_info(api_keys)")
        columns = db_connection.fetchall()
        column_names = [col[1] for col in columns]
        assert "id" in column_names
        assert "key_hash" in column_names
        assert "name" in column_names
        assert "created_at" in column_names
        assert "last_used_at" in column_names
        assert "is_active" in column_names


class TestInsertApiKey:
    """Tests for inserting API keys."""

    def test_inserts_and_returns_id(self, db_connection):
        """Should insert API key and return auto-generated id."""
        # Arrange
        create_api_keys_table(db_connection)
        key_hash = "abc123hash"
        name = "Test Key"

        # Act
        key_id = insert_api_key(db_connection, key_hash, name)

        # Assert
        assert key_id is not None
        assert isinstance(key_id, int)
        assert key_id > 0

    def test_stores_all_fields(self, db_connection):
        """Should store all fields correctly."""
        # Arrange
        create_api_keys_table(db_connection)
        key_hash = "test_hash_456"
        name = "Production Key"

        # Act
        key_id = insert_api_key(db_connection, key_hash, name)

        # Assert - retrieve and verify
        db_connection.execute("SELECT * FROM api_keys WHERE id = ?", (key_id,))
        row = db_connection.fetchone()
        assert row is not None
        # id, key_hash, name, created_at, last_used_at, is_active
        assert row[0] == key_id
        assert row[1] == key_hash
        assert row[2] == name
        assert row[3] is not None  # created_at should be set
        assert row[4] is None  # last_used_at should be NULL initially
        assert row[5] == 1  # is_active should default to 1

    def test_rejects_duplicate_hash(self, db_connection):
        """Should reject duplicate key_hash (unique constraint)."""
        # Arrange
        create_api_keys_table(db_connection)
        key_hash = "duplicate_hash"
        insert_api_key(db_connection, key_hash, "First Key")

        # Act/Assert
        with pytest.raises(sqlite3.IntegrityError):  # Should raise UNIQUE constraint error
            insert_api_key(db_connection, key_hash, "Second Key")


class TestGetApiKeyByHash:
    """Tests for retrieving API key by hash."""

    def test_returns_key_by_hash(self, db_connection):
        """Should retrieve key record by hash."""
        # Arrange
        create_api_keys_table(db_connection)
        key_hash = "lookup_hash_789"
        name = "Lookup Test"
        key_id = insert_api_key(db_connection, key_hash, name)

        # Act
        result = get_api_key_by_hash(db_connection, key_hash)

        # Assert
        assert result is not None
        assert isinstance(result, dict)
        assert result["id"] == key_id
        assert result["key_hash"] == key_hash
        assert result["name"] == name
        assert result["is_active"] == 1

    def test_returns_none_for_nonexistent_hash(self, db_connection):
        """Should return None if hash not found."""
        # Arrange
        create_api_keys_table(db_connection)

        # Act
        result = get_api_key_by_hash(db_connection, "nonexistent_hash")

        # Assert
        assert result is None


class TestGetApiKeyById:
    """Tests for retrieving API key by ID."""

    def test_returns_key_by_id(self, db_connection):
        """Should retrieve key record by id."""
        # Arrange
        create_api_keys_table(db_connection)
        key_hash = "id_lookup_hash"
        name = "ID Test"
        key_id = insert_api_key(db_connection, key_hash, name)

        # Act
        result = get_api_key_by_id(db_connection, key_id)

        # Assert
        assert result is not None
        assert isinstance(result, dict)
        assert result["id"] == key_id
        assert result["key_hash"] == key_hash
        assert result["name"] == name

    def test_returns_none_for_nonexistent_id(self, db_connection):
        """Should return None if id not found."""
        # Arrange
        create_api_keys_table(db_connection)

        # Act
        result = get_api_key_by_id(db_connection, 99999)

        # Assert
        assert result is None


class TestUpdateLastUsed:
    """Tests for updating last_used_at timestamp."""

    def test_updates_timestamp(self, db_connection):
        """Should update last_used_at timestamp."""
        # Arrange
        create_api_keys_table(db_connection)
        key_id = insert_api_key(db_connection, "update_hash", "Update Test")

        # Verify initially NULL
        result_before = get_api_key_by_id(db_connection, key_id)
        assert result_before["last_used_at"] is None

        # Act
        update_last_used(db_connection, key_id)

        # Assert
        result_after = get_api_key_by_id(db_connection, key_id)
        assert result_after["last_used_at"] is not None
        assert isinstance(result_after["last_used_at"], str)  # ISO timestamp

    def test_updates_multiple_times(self, db_connection):
        """Should update timestamp on multiple calls."""
        # Arrange
        create_api_keys_table(db_connection)
        key_id = insert_api_key(db_connection, "multi_update", "Multi Test")

        # Act
        update_last_used(db_connection, key_id)
        first_timestamp = get_api_key_by_id(db_connection, key_id)["last_used_at"]

        update_last_used(db_connection, key_id)
        second_timestamp = get_api_key_by_id(db_connection, key_id)["last_used_at"]

        # Assert - timestamps should be valid (may be same if very fast)
        assert first_timestamp is not None
        assert second_timestamp is not None


class TestDeactivateApiKey:
    """Tests for deactivating API keys."""

    def test_sets_is_active_to_false(self, db_connection):
        """Should set is_active to 0 (False)."""
        # Arrange
        create_api_keys_table(db_connection)
        key_id = insert_api_key(db_connection, "deactivate_hash", "Deactivate Test")

        # Verify initially active
        result_before = get_api_key_by_id(db_connection, key_id)
        assert result_before["is_active"] == 1

        # Act
        deactivate_api_key(db_connection, key_id)

        # Assert
        result_after = get_api_key_by_id(db_connection, key_id)
        assert result_after["is_active"] == 0


class TestListApiKeys:
    """Tests for listing all API keys."""

    def test_returns_all_keys(self, db_connection):
        """Should return list of all API keys."""
        # Arrange
        create_api_keys_table(db_connection)
        id1 = insert_api_key(db_connection, "hash1", "Key 1")
        id2 = insert_api_key(db_connection, "hash2", "Key 2")
        id3 = insert_api_key(db_connection, "hash3", "Key 3")

        # Act
        results = list_api_keys(db_connection)

        # Assert
        assert isinstance(results, list)
        assert len(results) == 3
        assert all(isinstance(key, dict) for key in results)

        # Verify all keys are present
        key_ids = [key["id"] for key in results]
        assert id1 in key_ids
        assert id2 in key_ids
        assert id3 in key_ids

    def test_returns_empty_list_when_no_keys(self, db_connection):
        """Should return empty list if no keys exist."""
        # Arrange
        create_api_keys_table(db_connection)

        # Act
        results = list_api_keys(db_connection)

        # Assert
        assert isinstance(results, list)
        assert len(results) == 0

    def test_includes_active_and_inactive_keys(self, db_connection):
        """Should return both active and inactive keys."""
        # Arrange
        create_api_keys_table(db_connection)
        id1 = insert_api_key(db_connection, "active_hash", "Active Key")
        id2 = insert_api_key(db_connection, "inactive_hash", "Inactive Key")
        deactivate_api_key(db_connection, id2)

        # Act
        results = list_api_keys(db_connection)

        # Assert
        assert len(results) == 2
        active_key = next(k for k in results if k["id"] == id1)
        inactive_key = next(k for k in results if k["id"] == id2)
        assert active_key["is_active"] == 1
        assert inactive_key["is_active"] == 0
