# ABOUTME: Tests for POST /extract endpoint.
# ABOUTME: Verifies extraction with auth, validation, and compliance checks.

from unittest.mock import patch


class TestExtractEndpointAuth:
    """Tests for authentication on /extract endpoint."""

    def test_extract_without_auth_returns_401(self, client):
        """Should return 401 when X-API-Key header is missing."""
        # Arrange
        request_data = {
            "url": "https://example.com",
            "schema": {"type": "object", "properties": {"title": {"type": "string"}}},
        }

        # Act
        response = client.post("/extract", json=request_data)

        # Assert
        assert response.status_code == 401
        assert "API key" in response.json()["detail"]


class TestExtractEndpointValidation:
    """Tests for request validation on /extract endpoint."""

    def test_extract_missing_url_returns_422(self, client, auth_headers):
        """Should return 422 when url field is missing."""
        # Arrange
        request_data = {"schema": {"type": "object", "properties": {}}}

        # Act
        response = client.post("/extract", json=request_data, headers=auth_headers)

        # Assert
        assert response.status_code == 422

    def test_extract_missing_schema_returns_422(self, client, auth_headers):
        """Should return 422 when schema field is missing."""
        # Arrange
        request_data = {"url": "https://example.com"}

        # Act
        response = client.post("/extract", json=request_data, headers=auth_headers)

        # Assert
        assert response.status_code == 422

    def test_extract_invalid_url_format_returns_422(self, client, auth_headers):
        """Should return 422 when URL format is invalid."""
        # Arrange
        request_data = {
            "url": "not-a-valid-url",
            "schema": {"type": "object", "properties": {}},
        }

        # Act
        response = client.post("/extract", json=request_data, headers=auth_headers)

        # Assert
        assert response.status_code == 422

    def test_extract_empty_schema_returns_400(self, client, auth_headers):
        """Should return 400 when schema is empty dict."""
        # Arrange
        request_data = {"url": "https://example.com", "schema": {}}

        # Act
        response = client.post("/extract", json=request_data, headers=auth_headers)

        # Assert
        assert response.status_code == 400
        assert "schema" in response.json()["detail"].lower()


class TestExtractEndpointRobots:
    """Tests for robots.txt compliance on /extract endpoint."""

    @patch("hikuweb.services.robots.RobotsChecker.check_url")
    def test_extract_robots_blocked_returns_403(self, mock_check_url, client, auth_headers):
        """Should return 403 when URL is blocked by robots.txt."""
        # Arrange
        mock_check_url.return_value = (False, "Blocked by robots.txt")
        request_data = {
            "url": "https://example.com/private",
            "schema": {"type": "object", "properties": {"title": {"type": "string"}}},
        }

        # Act
        response = client.post("/extract", json=request_data, headers=auth_headers)

        # Assert
        assert response.status_code == 403
        assert "robots" in response.json()["detail"].lower()
        mock_check_url.assert_called_once()

    @patch("hikuweb.services.robots.RobotsChecker.check_url")
    def test_extract_robots_allowed_proceeds(self, mock_check_url, client, auth_headers):
        """Should proceed when URL is allowed by robots.txt."""
        # Arrange
        mock_check_url.return_value = (True, None)
        request_data = {
            "url": "https://example.com",
            "schema": {"type": "object", "properties": {"title": {"type": "string"}}},
        }

        # Act
        # Note: This will fail during extraction (expected in TDD RED) but should pass robots check
        response = client.post("/extract", json=request_data, headers=auth_headers)

        # Assert
        # Should NOT be 403 (robots blocked)
        assert response.status_code != 403
        mock_check_url.assert_called_once()


class TestExtractEndpointRateLimit:
    """Tests for rate limiting on /extract endpoint."""

    @patch("hikuweb.services.rate_limiter.DomainRateLimiter.acquire")
    def test_extract_rate_limited_returns_429(self, mock_acquire, client, auth_headers):
        """Should return 429 when domain is rate limited."""
        # Arrange
        mock_acquire.return_value = False
        request_data = {
            "url": "https://example.com",
            "schema": {"type": "object", "properties": {"title": {"type": "string"}}},
        }

        # Act
        response = client.post("/extract", json=request_data, headers=auth_headers)

        # Assert
        assert response.status_code == 429
        assert "rate limit" in response.json()["detail"].lower()
        mock_acquire.assert_called_once()

    @patch("hikuweb.services.rate_limiter.DomainRateLimiter.acquire")
    @patch("hikuweb.services.robots.RobotsChecker.check_url")
    def test_extract_rate_limit_allowed_proceeds(
        self, mock_check_url, mock_acquire, client, auth_headers
    ):
        """Should proceed when rate limit allows request."""
        # Arrange
        mock_acquire.return_value = True
        mock_check_url.return_value = (True, None)
        request_data = {
            "url": "https://example.com",
            "schema": {"type": "object", "properties": {"title": {"type": "string"}}},
        }

        # Act
        response = client.post("/extract", json=request_data, headers=auth_headers)

        # Assert
        # Should NOT be 429 (rate limited)
        assert response.status_code != 429
        mock_acquire.assert_called_once()


class TestExtractEndpointSuccess:
    """Tests for successful extraction on /extract endpoint."""

    @patch("hikuweb.services.extraction.ExtractionService.extract")
    @patch("hikuweb.services.rate_limiter.DomainRateLimiter.acquire")
    @patch("hikuweb.services.robots.RobotsChecker.check_url")
    def test_extract_success_returns_200(
        self, mock_check_url, mock_acquire, mock_extract, client, auth_headers
    ):
        """Should return 200 with extracted data on success."""
        # Arrange
        mock_check_url.return_value = (True, None)
        mock_acquire.return_value = True
        mock_extract.return_value = {"title": "Test Article", "author": "John Doe"}
        request_data = {
            "url": "https://example.com/article",
            "schema": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "author": {"type": "string"},
                },
            },
        }

        # Act
        response = client.post("/extract", json=request_data, headers=auth_headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert data["data"]["title"] == "Test Article"
        assert data["data"]["author"] == "John Doe"

    @patch("hikuweb.services.extraction.ExtractionService.extract")
    @patch("hikuweb.services.rate_limiter.DomainRateLimiter.acquire")
    @patch("hikuweb.services.robots.RobotsChecker.check_url")
    def test_extract_includes_metadata(
        self, mock_check_url, mock_acquire, mock_extract, client, auth_headers
    ):
        """Should include extraction metadata in response."""
        # Arrange
        mock_check_url.return_value = (True, None)
        mock_acquire.return_value = True
        mock_extract.return_value = {"title": "Test"}
        request_data = {
            "url": "https://example.com",
            "schema": {"type": "object", "properties": {"title": {"type": "string"}}},
        }

        # Act
        response = client.post("/extract", json=request_data, headers=auth_headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "duration_ms" in data
        assert isinstance(data["duration_ms"], int)
        assert data["duration_ms"] >= 0

    @patch("hikuweb.services.extraction.ExtractionService.extract")
    @patch("hikuweb.services.rate_limiter.DomainRateLimiter.acquire")
    @patch("hikuweb.services.robots.RobotsChecker.check_url")
    def test_extract_error_returns_500(
        self, mock_check_url, mock_acquire, mock_extract, client, auth_headers
    ):
        """Should return 500 when extraction service fails."""
        # Arrange
        mock_check_url.return_value = (True, None)
        mock_acquire.return_value = True
        mock_extract.side_effect = Exception("Extraction failed")
        request_data = {
            "url": "https://example.com",
            "schema": {"type": "object", "properties": {"title": {"type": "string"}}},
        }

        # Act
        response = client.post("/extract", json=request_data, headers=auth_headers)

        # Assert
        assert response.status_code == 500
        assert "detail" in response.json()


class TestExtractEndpointLogging:
    """Tests for extraction logging on /extract endpoint."""

    @patch("hikuweb.services.extraction.ExtractionService.extract")
    @patch("hikuweb.services.rate_limiter.DomainRateLimiter.acquire")
    @patch("hikuweb.services.robots.RobotsChecker.check_url")
    def test_extract_success_logged_to_database(
        self, mock_check_url, mock_acquire, mock_extract, client, auth_headers
    ):
        """Should log successful extraction to database."""
        # Arrange
        mock_check_url.return_value = (True, None)
        mock_acquire.return_value = True
        mock_extract.return_value = {"title": "Test"}
        request_data = {
            "url": "https://example.com",
            "schema": {"type": "object", "properties": {"title": {"type": "string"}}},
        }

        # Act
        response = client.post("/extract", json=request_data, headers=auth_headers)

        # Assert
        assert response.status_code == 200
        # Verify via /usage endpoint that extraction was logged
        usage_response = client.get("/usage", headers=auth_headers)
        assert usage_response.status_code == 200
        usage_data = usage_response.json()
        assert usage_data["total_extractions"] > 0

    @patch("hikuweb.services.rate_limiter.DomainRateLimiter.acquire")
    @patch("hikuweb.services.robots.RobotsChecker.check_url")
    def test_extract_blocked_logged_to_database(
        self, mock_check_url, mock_acquire, client, auth_headers
    ):
        """Should log blocked extraction to database."""
        # Arrange
        mock_check_url.return_value = (False, "Blocked by robots.txt")
        mock_acquire.return_value = True
        request_data = {
            "url": "https://example.com/private",
            "schema": {"type": "object", "properties": {"title": {"type": "string"}}},
        }

        # Act
        response = client.post("/extract", json=request_data, headers=auth_headers)

        # Assert
        assert response.status_code == 403
        # Verify via /usage endpoint that blocked extraction was logged
        usage_response = client.get("/usage", headers=auth_headers)
        assert usage_response.status_code == 200
        usage_data = usage_response.json()
        assert usage_data["blocked_count"] > 0

    @patch("hikuweb.services.extraction.ExtractionService.extract")
    @patch("hikuweb.services.rate_limiter.DomainRateLimiter.acquire")
    @patch("hikuweb.services.robots.RobotsChecker.check_url")
    def test_extract_error_logged_to_database(
        self, mock_check_url, mock_acquire, mock_extract, client, auth_headers
    ):
        """Should log error extraction to database."""
        # Arrange
        mock_check_url.return_value = (True, None)
        mock_acquire.return_value = True
        mock_extract.side_effect = Exception("Extraction failed")
        request_data = {
            "url": "https://example.com",
            "schema": {"type": "object", "properties": {"title": {"type": "string"}}},
        }

        # Act
        response = client.post("/extract", json=request_data, headers=auth_headers)

        # Assert
        assert response.status_code == 500
        # Verify via /usage endpoint that error extraction was logged
        usage_response = client.get("/usage", headers=auth_headers)
        assert usage_response.status_code == 200
        usage_data = usage_response.json()
        assert usage_data["error_count"] > 0
