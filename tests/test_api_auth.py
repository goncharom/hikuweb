# ABOUTME: Tests for API key authentication dependency.
# ABOUTME: Verifies auth header validation and error responses.


class TestAuthDependency:
    """Tests for API key authentication FastAPI dependency."""

    def test_missing_api_key_returns_401(self, client):
        """Should return 401 when X-API-Key header is missing."""
        # Arrange/Act
        response = client.get("/auth-test")

        # Assert
        assert response.status_code == 401
        assert "API key" in response.json()["detail"]

    def test_invalid_api_key_returns_401(self, client):
        """Should return 401 when X-API-Key is invalid."""
        # Arrange/Act
        response = client.get("/auth-test", headers={"X-API-Key": "invalid-key-12345"})

        # Assert
        assert response.status_code == 401
        assert "Invalid" in response.json()["detail"] or "inactive" in response.json()["detail"]

    def test_inactive_api_key_returns_401(self, client, inactive_api_key):
        """Should return 401 when API key is deactivated."""
        # Arrange/Act
        response = client.get("/auth-test", headers={"X-API-Key": inactive_api_key})

        # Assert
        assert response.status_code == 401
        assert "Invalid" in response.json()["detail"] or "inactive" in response.json()["detail"]

    def test_valid_api_key_succeeds(self, client, test_api_key):
        """Should return 200 when valid API key is provided."""
        # Arrange/Act
        response = client.get("/auth-test", headers={"X-API-Key": test_api_key})

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["authenticated"] is True
        assert "key_name" in data

    def test_auth_injects_api_key_record(self, client, test_api_key):
        """Should inject api_key_record dict into route handler."""
        # Arrange/Act
        response = client.get("/auth-test", headers={"X-API-Key": test_api_key})

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["key_name"] == "test-key"  # From fixture

    def test_error_response_includes_message(self, client):
        """Should include appropriate error message in 401 response."""
        # Arrange/Act - missing key
        response = client.get("/auth-test")

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert len(data["detail"]) > 0

    def test_error_response_includes_message_for_invalid(self, client):
        """Should include appropriate error message for invalid key."""
        # Arrange/Act - invalid key
        response = client.get("/auth-test", headers={"X-API-Key": "bad-key"})

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert len(data["detail"]) > 0
