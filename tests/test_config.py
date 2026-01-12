# ABOUTME: Tests for configuration management using pydantic-settings.
# ABOUTME: Verifies loading environment variables with defaults for hikuweb settings.

import os
from unittest.mock import patch

from hikuweb.config import Settings, get_settings


class TestSettings:
    """Tests for configuration management."""

    def test_default_values_when_no_env_vars(self):
        """Should use defaults when no environment variables are set."""
        # Arrange
        with patch.dict(os.environ, {}, clear=True):
            # Act
            settings = Settings()

            # Assert
            assert settings.database_path == "hikuweb.db"
            assert settings.openrouter_api_key is None
            assert settings.rate_limit_requests_per_second == 1.0
            assert settings.robots_cache_ttl_seconds == 3600

    def test_loads_database_path_from_env(self):
        """Should load DATABASE_PATH from environment."""
        # Arrange
        test_path = "/custom/path/to/db.sqlite"
        with patch.dict(os.environ, {"DATABASE_PATH": test_path}):
            # Act
            settings = Settings()

            # Assert
            assert settings.database_path == test_path

    def test_loads_openrouter_api_key_from_env(self):
        """Should load OPENROUTER_API_KEY from environment."""
        # Arrange
        test_key = "test-api-key-12345"
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": test_key}):
            # Act
            settings = Settings()

            # Assert
            assert settings.openrouter_api_key == test_key

    def test_loads_rate_limit_from_env(self):
        """Should load RATE_LIMIT_REQUESTS_PER_SECOND from environment."""
        # Arrange
        test_rate = "2.5"
        with patch.dict(os.environ, {"RATE_LIMIT_REQUESTS_PER_SECOND": test_rate}):
            # Act
            settings = Settings()

            # Assert
            assert settings.rate_limit_requests_per_second == 2.5

    def test_loads_robots_cache_ttl_from_env(self):
        """Should load ROBOTS_CACHE_TTL_SECONDS from environment."""
        # Arrange
        test_ttl = "7200"
        with patch.dict(os.environ, {"ROBOTS_CACHE_TTL_SECONDS": test_ttl}):
            # Act
            settings = Settings()

            # Assert
            assert settings.robots_cache_ttl_seconds == 7200

    def test_openrouter_api_key_optional(self):
        """Should allow OPENROUTER_API_KEY to be None."""
        # Arrange
        with patch.dict(os.environ, {}, clear=True):
            # Act
            settings = Settings()

            # Assert
            assert settings.openrouter_api_key is None


class TestGetSettings:
    """Tests for get_settings singleton function."""

    def test_returns_settings_instance(self):
        """Should return a Settings instance."""
        # Act
        settings = get_settings()

        # Assert
        assert isinstance(settings, Settings)

    def test_returns_same_instance_on_multiple_calls(self):
        """Should return the same cached instance on repeated calls."""
        # Act
        settings1 = get_settings()
        settings2 = get_settings()

        # Assert
        assert settings1 is settings2
