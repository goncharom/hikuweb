# ABOUTME: Tests for extraction_logs table CRUD operations.
# ABOUTME: Verifies logging, pagination, and usage statistics.


from hikuweb.db.extraction_logs import (
    count_logs_by_api_key,
    create_extraction_logs_table,
    get_logs_by_api_key,
    get_usage_stats,
    insert_extraction_log,
)


class TestCreateExtractionLogsTable:
    """Tests for extraction_logs table creation."""

    def test_creates_table(self, db_connection):
        """Should create extraction_logs table with correct schema."""
        # Arrange/Act
        create_extraction_logs_table(db_connection)

        # Assert - Query schema
        db_connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='extraction_logs'"
        )
        result = db_connection.fetchone()
        assert result is not None
        assert result[0] == "extraction_logs"

        # Verify columns
        db_connection.execute("PRAGMA table_info(extraction_logs)")
        columns = db_connection.fetchall()
        column_names = [col[1] for col in columns]

        expected_columns = [
            "id",
            "api_key_id",
            "url",
            "schema_hash",
            "status",
            "error_message",
            "created_at",
            "duration_ms",
        ]
        assert column_names == expected_columns


class TestInsertExtractionLog:
    """Tests for inserting extraction logs."""

    def test_inserts_and_returns_id(self, db_connection):
        """Should insert log and return auto-generated ID."""
        # Arrange
        create_extraction_logs_table(db_connection)

        # Act
        log_id = insert_extraction_log(
            db_connection,
            api_key_id=1,
            url="https://example.com",
            schema_hash="abc123",
            status="success",
            error_message=None,
            duration_ms=250,
        )

        # Assert
        assert isinstance(log_id, int)
        assert log_id > 0

    def test_stores_all_fields(self, db_connection):
        """Should store all log fields correctly."""
        # Arrange
        create_extraction_logs_table(db_connection)

        # Act
        log_id = insert_extraction_log(
            db_connection,
            api_key_id=42,
            url="https://example.com/page",
            schema_hash="hash456",
            status="error",
            error_message="Connection timeout",
            duration_ms=5000,
        )

        # Assert
        db_connection.execute("SELECT * FROM extraction_logs WHERE id = ?", (log_id,))
        row = db_connection.fetchone()
        assert row is not None
        assert row[1] == 42  # api_key_id
        assert row[2] == "https://example.com/page"  # url
        assert row[3] == "hash456"  # schema_hash
        assert row[4] == "error"  # status
        assert row[5] == "Connection timeout"  # error_message
        assert row[7] == 5000  # duration_ms

    def test_allows_null_error_message(self, db_connection):
        """Should allow NULL error_message for successful extractions."""
        # Arrange
        create_extraction_logs_table(db_connection)

        # Act
        log_id = insert_extraction_log(
            db_connection,
            api_key_id=1,
            url="https://example.com",
            schema_hash="abc",
            status="success",
            error_message=None,
            duration_ms=100,
        )

        # Assert
        db_connection.execute("SELECT error_message FROM extraction_logs WHERE id = ?", (log_id,))
        result = db_connection.fetchone()
        assert result[0] is None


class TestGetLogsByApiKey:
    """Tests for retrieving logs by API key."""

    def test_returns_logs_for_api_key(self, db_connection):
        """Should return logs for specific API key."""
        # Arrange
        create_extraction_logs_table(db_connection)
        insert_extraction_log(db_connection, 1, "https://example.com/1", "h1", "success", None, 100)
        insert_extraction_log(db_connection, 1, "https://example.com/2", "h2", "error", "Fail", 200)
        insert_extraction_log(db_connection, 2, "https://example.com/3", "h3", "success", None, 150)

        # Act
        logs = get_logs_by_api_key(db_connection, api_key_id=1)

        # Assert
        assert len(logs) == 2
        assert all(log["api_key_id"] == 1 for log in logs)

    def test_returns_empty_list_for_nonexistent_key(self, db_connection):
        """Should return empty list when API key has no logs."""
        # Arrange
        create_extraction_logs_table(db_connection)

        # Act
        logs = get_logs_by_api_key(db_connection, api_key_id=999)

        # Assert
        assert logs == []

    def test_supports_pagination_with_limit(self, db_connection):
        """Should support pagination with limit parameter."""
        # Arrange
        create_extraction_logs_table(db_connection)
        for i in range(5):
            insert_extraction_log(
                db_connection, 1, f"https://example.com/{i}", f"h{i}", "success", None, 100
            )

        # Act
        logs = get_logs_by_api_key(db_connection, api_key_id=1, limit=2)

        # Assert
        assert len(logs) == 2

    def test_supports_pagination_with_offset(self, db_connection):
        """Should support pagination with offset parameter."""
        # Arrange
        create_extraction_logs_table(db_connection)
        for i in range(5):
            insert_extraction_log(
                db_connection, 1, f"https://example.com/{i}", f"h{i}", "success", None, 100
            )

        # Act
        logs_page1 = get_logs_by_api_key(db_connection, api_key_id=1, limit=2, offset=0)
        logs_page2 = get_logs_by_api_key(db_connection, api_key_id=1, limit=2, offset=2)

        # Assert
        assert len(logs_page1) == 2
        assert len(logs_page2) == 2
        assert logs_page1[0]["id"] != logs_page2[0]["id"]

    def test_returns_dict_with_all_fields(self, db_connection):
        """Should return dicts with all log fields."""
        # Arrange
        create_extraction_logs_table(db_connection)
        insert_extraction_log(
            db_connection, 1, "https://example.com", "hash1", "success", None, 250
        )

        # Act
        logs = get_logs_by_api_key(db_connection, api_key_id=1)

        # Assert
        assert len(logs) == 1
        log = logs[0]
        assert "id" in log
        assert "api_key_id" in log
        assert "url" in log
        assert "schema_hash" in log
        assert "status" in log
        assert "error_message" in log
        assert "created_at" in log
        assert "duration_ms" in log


class TestCountLogsByApiKey:
    """Tests for counting logs by API key."""

    def test_returns_correct_count(self, db_connection):
        """Should return total count of logs for API key."""
        # Arrange
        create_extraction_logs_table(db_connection)
        for i in range(3):
            insert_extraction_log(
                db_connection, 1, f"https://example.com/{i}", f"h{i}", "success", None, 100
            )
        insert_extraction_log(
            db_connection, 2, "https://example.com/other", "h99", "success", None, 100
        )

        # Act
        count = count_logs_by_api_key(db_connection, api_key_id=1)

        # Assert
        assert count == 3

    def test_returns_zero_for_nonexistent_key(self, db_connection):
        """Should return 0 when API key has no logs."""
        # Arrange
        create_extraction_logs_table(db_connection)

        # Act
        count = count_logs_by_api_key(db_connection, api_key_id=999)

        # Assert
        assert count == 0


class TestGetUsageStats:
    """Tests for aggregated usage statistics."""

    def test_returns_all_stat_fields(self, db_connection):
        """Should return dict with total, success_count, error_count, blocked_count, avg_duration_ms."""
        # Arrange
        create_extraction_logs_table(db_connection)
        insert_extraction_log(db_connection, 1, "https://example.com/1", "h1", "success", None, 100)

        # Act
        stats = get_usage_stats(db_connection, api_key_id=1)

        # Assert
        assert "total" in stats
        assert "success_count" in stats
        assert "error_count" in stats
        assert "blocked_count" in stats
        assert "avg_duration_ms" in stats

    def test_calculates_counts_correctly(self, db_connection):
        """Should calculate correct counts for each status type."""
        # Arrange
        create_extraction_logs_table(db_connection)
        insert_extraction_log(db_connection, 1, "https://example.com/1", "h1", "success", None, 100)
        insert_extraction_log(db_connection, 1, "https://example.com/2", "h2", "success", None, 200)
        insert_extraction_log(
            db_connection, 1, "https://example.com/3", "h3", "error", "Failed", 150
        )
        insert_extraction_log(
            db_connection, 1, "https://example.com/4", "h4", "blocked", "Robots.txt", 50
        )

        # Act
        stats = get_usage_stats(db_connection, api_key_id=1)

        # Assert
        assert stats["total"] == 4
        assert stats["success_count"] == 2
        assert stats["error_count"] == 1
        assert stats["blocked_count"] == 1

    def test_calculates_average_duration(self, db_connection):
        """Should calculate correct average duration_ms."""
        # Arrange
        create_extraction_logs_table(db_connection)
        insert_extraction_log(db_connection, 1, "https://example.com/1", "h1", "success", None, 100)
        insert_extraction_log(db_connection, 1, "https://example.com/2", "h2", "success", None, 200)
        insert_extraction_log(db_connection, 1, "https://example.com/3", "h3", "success", None, 300)

        # Act
        stats = get_usage_stats(db_connection, api_key_id=1)

        # Assert
        assert stats["avg_duration_ms"] == 200.0  # (100 + 200 + 300) / 3

    def test_returns_zeros_for_nonexistent_key(self, db_connection):
        """Should return zero stats when API key has no logs."""
        # Arrange
        create_extraction_logs_table(db_connection)

        # Act
        stats = get_usage_stats(db_connection, api_key_id=999)

        # Assert
        assert stats["total"] == 0
        assert stats["success_count"] == 0
        assert stats["error_count"] == 0
        assert stats["blocked_count"] == 0
        assert stats["avg_duration_ms"] == 0.0

    def test_only_counts_logs_for_specific_api_key(self, db_connection):
        """Should only include logs for the specified API key in stats."""
        # Arrange
        create_extraction_logs_table(db_connection)
        insert_extraction_log(db_connection, 1, "https://example.com/1", "h1", "success", None, 100)
        insert_extraction_log(db_connection, 2, "https://example.com/2", "h2", "success", None, 200)

        # Act
        stats = get_usage_stats(db_connection, api_key_id=1)

        # Assert
        assert stats["total"] == 1
        assert stats["avg_duration_ms"] == 100.0
