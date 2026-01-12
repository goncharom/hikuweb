# ABOUTME: Tests for FastAPI health endpoint.
# ABOUTME: Verifies health check returns correct status and version.


class TestHealthEndpoint:
    """Tests for GET /health endpoint."""

    def test_health_returns_200(self, client):
        """Should return 200 status code for health check."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_returns_status_and_version(self, client):
        """Should return status 'healthy' and version '0.1.0'."""
        response = client.get("/health")
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "0.1.0"

    def test_health_no_auth_required(self, client):
        """Should not require authentication (no X-API-Key header)."""
        # No X-API-Key header provided
        response = client.get("/health")
        assert response.status_code == 200

    def test_openapi_docs_available(self, client):
        """Should have OpenAPI docs available at /docs."""
        response = client.get("/docs")
        assert response.status_code == 200
