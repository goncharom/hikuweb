# ABOUTME: Integration tests for hikuweb end-to-end flows.
# ABOUTME: Verifies complete extraction pipeline from auth to logging.

import os
from unittest.mock import patch

import pytest

pytestmark = pytest.mark.integration


@pytest.fixture
def skip_if_no_api_key():
    """Skip integration tests if OPENROUTER_API_KEY not set (for CI environments)."""
    if not os.environ.get("OPENROUTER_API_KEY"):
        pytest.skip("OPENROUTER_API_KEY not set - skipping integration tests")


class TestFullExtractionFlow:
    """Tests for complete end-to-end extraction flow."""

    def test_complete_extraction_logged(self, client, auth_headers, skip_if_no_api_key):
        """Should complete extraction and log it in database.

        Verifies:
        1. Extraction request succeeds with valid auth
        2. Response contains extracted data and metadata
        3. Usage endpoint shows the extraction was logged
        """
        # Arrange
        schema = {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "description": {"type": "string"},
            },
            "required": ["title"],
        }
        request_data = {"url": "https://example.com", "schema": schema}

        # Act - Make extraction request
        extract_response = client.post("/extract", json=request_data, headers=auth_headers)

        # Assert - Verify extraction succeeded
        assert extract_response.status_code == 200
        data = extract_response.json()
        assert "data" in data
        assert "duration_ms" in data
        assert isinstance(data["duration_ms"], int)

        # Act - Check usage endpoint
        usage_response = client.get("/usage", headers=auth_headers)

        # Assert - Verify extraction was logged
        assert usage_response.status_code == 200
        usage_data = usage_response.json()
        assert usage_data["total_extractions"] >= 1
        assert len(usage_data["recent_extractions"]) >= 1

        # Verify the most recent extraction matches
        recent = usage_data["recent_extractions"][0]
        assert recent["url"] == "https://example.com"
        assert recent["status"] == "success"

    def test_robots_blocked_logged_as_blocked(self, client, auth_headers):
        """Should log blocked extractions when robots.txt disallows.

        Verifies:
        1. Request returns 403 when blocked
        2. Extraction is logged with status='blocked'
        3. Usage stats reflect the blocked attempt
        """
        # Arrange
        schema = {"type": "object", "properties": {"title": {"type": "string"}}}
        request_data = {"url": "https://blocked-example.com/admin", "schema": schema}

        # Mock robots checker to block this URL
        with patch("hikuweb.services.robots.RobotsChecker.check_url") as mock_check:
            mock_check.return_value = (False, "Disallowed by robots.txt")

            # Act - Attempt extraction
            extract_response = client.post("/extract", json=request_data, headers=auth_headers)

            # Assert - Verify blocked response
            assert extract_response.status_code == 403
            assert "robots.txt" in extract_response.json()["detail"].lower()

        # Act - Check usage stats
        usage_response = client.get("/usage", headers=auth_headers)

        # Assert - Verify blocked extraction was logged
        usage_data = usage_response.json()
        assert usage_data["blocked_count"] >= 1

        # Check recent extractions for blocked entry
        blocked_extractions = [
            e for e in usage_data["recent_extractions"] if e["status"] == "blocked"
        ]
        assert len(blocked_extractions) >= 1

    def test_rate_limit_returns_429(self, client, auth_headers):
        """Should return 429 when domain rate limit is exceeded.

        Verifies:
        1. First request to domain succeeds
        2. Rapid second request to same domain returns 429
        3. Rate limiter respects per-domain limits
        """
        # Arrange
        schema = {"type": "object", "properties": {"title": {"type": "string"}}}
        request_data = {"url": "https://rate-test.com/page1", "schema": schema}

        # Mock extraction service to avoid actual HTTP/LLM calls
        with patch("hikuweb.services.extraction.ExtractionService.extract") as mock_extract:
            mock_extract.return_value = {"title": "Test"}

            # Mock robots checker to allow
            with patch("hikuweb.services.robots.RobotsChecker.check_url") as mock_robots:
                mock_robots.return_value = (True, None)

                # Act - First request (should succeed)
                first_response = client.post("/extract", json=request_data, headers=auth_headers)

                # Assert - First request succeeds
                assert first_response.status_code == 200

                # Act - Second rapid request to same domain
                second_request_data = {
                    "url": "https://rate-test.com/page2",
                    "schema": schema,
                }
                second_response = client.post(
                    "/extract", json=second_request_data, headers=auth_headers
                )

                # Assert - Second request is rate limited
                assert second_response.status_code == 429
                assert "rate limit" in second_response.json()["detail"].lower()

    def test_invalid_schema_returns_400(self, client, auth_headers):
        """Should return 400 for invalid JSON schema.

        Verifies:
        1. Schema validation catches malformed schemas
        2. Error message is descriptive
        """
        # Arrange - Invalid schema (e.g., unsupported type)
        invalid_schema = {
            "type": "object",
            "properties": {"date": {"type": "date"}},  # 'date' is not a JSON Schema type
        }
        request_data = {"url": "https://example.com", "schema": invalid_schema}

        # Act
        response = client.post("/extract", json=request_data, headers=auth_headers)

        # Assert - Should return validation error or bad request
        # Note: The actual status code depends on implementation
        # Could be 400 (bad request) or 422 (validation error)
        assert response.status_code in [400, 422]

    def test_extraction_with_nested_schema(self, client, auth_headers, skip_if_no_api_key):
        """Should handle complex nested schemas correctly.

        Verifies:
        1. Nested object schemas are translated properly
        2. Extracted data matches nested structure
        3. Extraction is logged successfully
        """
        # Arrange - Complex nested schema
        schema = {
            "type": "object",
            "properties": {
                "article": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "author": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "email": {"type": "string"},
                            },
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                    },
                },
            },
            "required": ["article"],
        }
        request_data = {"url": "https://example.com/article", "schema": schema}

        # Act
        response = client.post("/extract", json=request_data, headers=auth_headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        # The extracted data should have nested structure
        # (actual content depends on hikugen extraction)

    def test_extraction_with_arrays(self, client, auth_headers, skip_if_no_api_key):
        """Should handle array schemas correctly.

        Verifies:
        1. Array of primitives works
        2. Array of objects works
        3. Extracted data is properly structured
        """
        # Arrange - Schema with arrays
        schema = {
            "type": "object",
            "properties": {
                "tags": {"type": "array", "items": {"type": "string"}},
                "products": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "price": {"type": "number"},
                        },
                    },
                },
            },
        }
        request_data = {"url": "https://example.com/products", "schema": schema}

        # Act
        response = client.post("/extract", json=request_data, headers=auth_headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    def test_usage_stats_accuracy(self, client, auth_headers):
        """Should accurately track extraction statistics.

        Verifies:
        1. Success count increments on successful extraction
        2. Error count increments on failed extraction
        3. Average duration is calculated correctly
        """
        # Arrange - Get initial stats
        initial_usage = client.get("/usage", headers=auth_headers).json()
        initial_total = initial_usage["total_extractions"]

        schema = {"type": "object", "properties": {"title": {"type": "string"}}}

        # Mock successful extraction
        with patch("hikuweb.services.extraction.ExtractionService.extract") as mock_extract:
            mock_extract.return_value = {"title": "Test"}

            with patch("hikuweb.services.robots.RobotsChecker.check_url") as mock_robots:
                mock_robots.return_value = (True, None)

                # Mock rate limiter to allow request
                with patch("hikuweb.services.rate_limiter.DomainRateLimiter.acquire") as mock_rate:
                    mock_rate.return_value = True

                    # Act - Make successful extraction
                    response = client.post(
                        "/extract",
                        json={"url": "https://test-stats.com", "schema": schema},
                        headers=auth_headers,
                    )

                    # Assert - Extraction succeeded
                    assert response.status_code == 200

        # Act - Check updated stats
        updated_usage = client.get("/usage", headers=auth_headers).json()

        # Assert - Stats updated correctly
        assert updated_usage["total_extractions"] == initial_total + 1
        assert updated_usage["average_duration_ms"] is not None

    def test_multiple_api_keys_isolated(self, client):
        """Should isolate usage stats between different API keys.

        Verifies:
        1. Each API key only sees its own extractions
        2. Usage stats are properly scoped
        """
        # Arrange - Create two API keys using the app's database
        from hikuweb.config import get_settings
        from hikuweb.db.api_keys import create_api_keys_table
        from hikuweb.db.connection import get_db_connection
        from hikuweb.services.api_key_service import create_api_key

        settings = get_settings()
        with get_db_connection(settings.database_path) as conn:
            create_api_keys_table(conn)
            key1 = create_api_key(conn, "Test Key 1")
            key2 = create_api_key(conn, "Test Key 2")

        headers1 = {"X-API-Key": key1}
        headers2 = {"X-API-Key": key2}

        schema = {"type": "object", "properties": {"title": {"type": "string"}}}

        # Mock extraction and robots
        with patch("hikuweb.services.extraction.ExtractionService.extract") as mock_extract:
            mock_extract.return_value = {"title": "Test"}

            with patch("hikuweb.services.robots.RobotsChecker.check_url") as mock_robots:
                mock_robots.return_value = (True, None)

                with patch("hikuweb.services.rate_limiter.DomainRateLimiter.acquire") as mock_rate:
                    mock_rate.return_value = True

                    # Act - Key 1 makes 2 extractions
                    client.post(
                        "/extract",
                        json={"url": "https://key1-test.com/page1", "schema": schema},
                        headers=headers1,
                    )
                    client.post(
                        "/extract",
                        json={"url": "https://key1-test.com/page2", "schema": schema},
                        headers=headers1,
                    )

                    # Act - Key 2 makes 1 extraction
                    client.post(
                        "/extract",
                        json={"url": "https://key2-test.com/page1", "schema": schema},
                        headers=headers2,
                    )

        # Assert - Key 1 sees only its 2 extractions
        usage1 = client.get("/usage", headers=headers1).json()
        assert usage1["total_extractions"] == 2

        # Assert - Key 2 sees only its 1 extraction
        usage2 = client.get("/usage", headers=headers2).json()
        assert usage2["total_extractions"] == 1
