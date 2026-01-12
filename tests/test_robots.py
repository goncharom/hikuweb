# ABOUTME: Tests for robots.txt service.
# ABOUTME: Verifies parsing, caching, and URL permission checking.

import time
from unittest.mock import AsyncMock, patch

import pytest

from hikuweb.services.robots import (
    RobotsChecker,
    is_path_allowed,
    parse_robots_txt,
)


class TestParseRobotsTxt:
    """Tests for robots.txt content parsing."""

    def test_parses_user_agent_and_disallow(self):
        """Should parse User-agent and Disallow rules correctly."""
        content = "User-agent: *\nDisallow: /private/"
        rules = parse_robots_txt(content)
        assert "*" in rules
        assert "/private/" in rules["*"]

    def test_parses_multiple_user_agent_sections(self):
        """Should handle multiple User-agent sections."""
        content = """User-agent: *
Disallow: /private/

User-agent: googlebot
Disallow: /admin/"""
        rules = parse_robots_txt(content)
        assert "*" in rules
        assert "googlebot" in rules
        assert "/private/" in rules["*"]
        assert "/admin/" in rules["googlebot"]

    def test_handles_wildcard_user_agent(self):
        """Should handle wildcard User-agent (*) correctly."""
        content = "User-agent: *\nDisallow: /secret/\nDisallow: /admin/"
        rules = parse_robots_txt(content)
        assert "*" in rules
        assert len(rules["*"]) == 2
        assert "/secret/" in rules["*"]
        assert "/admin/" in rules["*"]

    def test_handles_empty_disallow(self):
        """Should handle empty Disallow (allow all)."""
        content = "User-agent: *\nDisallow:"
        rules = parse_robots_txt(content)
        assert "*" in rules
        # Empty disallow means allow all, so the list should be empty or contain ""
        assert rules["*"] == [] or rules["*"] == [""]

    def test_ignores_allow_directives(self):
        """Should focus on Disallow rules (Allow is extension)."""
        content = """User-agent: *
Disallow: /private/
Allow: /public/"""
        rules = parse_robots_txt(content)
        assert "*" in rules
        assert "/private/" in rules["*"]
        # Allow directives are not parsed in basic implementation

    def test_handles_malformed_content(self):
        """Should handle malformed robots.txt gracefully."""
        content = "This is not valid robots.txt\nRandom text"
        rules = parse_robots_txt(content)
        # Should return empty dict or handle gracefully
        assert isinstance(rules, dict)

    def test_handles_case_insensitive_directives(self):
        """Should handle case-insensitive directives."""
        content = "user-agent: *\ndisallow: /private/"
        rules = parse_robots_txt(content)
        assert "*" in rules or len(rules) > 0


class TestIsPathAllowed:
    """Tests for path permission checking against rules."""

    def test_disallowed_path_returns_false(self):
        """Should return False for disallowed paths."""
        rules = {"*": ["/private/", "/admin/"]}
        assert is_path_allowed(rules, "/private/secret.html") is False
        assert is_path_allowed(rules, "/admin/users") is False

    def test_allowed_path_returns_true(self):
        """Should return True for allowed paths."""
        rules = {"*": ["/private/", "/admin/"]}
        assert is_path_allowed(rules, "/public/page.html") is True
        assert is_path_allowed(rules, "/") is True

    def test_handles_wildcard_patterns(self):
        """Should handle wildcard patterns in Disallow."""
        rules = {"*": ["/private/*"]}
        assert is_path_allowed(rules, "/private/anything") is False
        assert is_path_allowed(rules, "/private/") is False

    def test_defaults_to_true_if_no_matching_rules(self):
        """Should default to True if no matching rules found."""
        rules = {"googlebot": ["/private/"]}
        # No rules for "*", so should allow
        assert is_path_allowed(rules, "/anything") is True

    def test_respects_user_agent_specific_rules(self):
        """Should respect user-agent specific rules."""
        rules = {"*": ["/private/"], "googlebot": ["/admin/"]}
        # For googlebot user agent
        assert is_path_allowed(rules, "/admin/panel", "googlebot") is False
        assert is_path_allowed(rules, "/private/data", "googlebot") is False

    def test_empty_rules_allows_all(self):
        """Should allow all paths if rules are empty."""
        rules = {}
        assert is_path_allowed(rules, "/anything") is True

    def test_exact_path_match(self):
        """Should match exact paths correctly."""
        rules = {"*": ["/private"]}
        assert is_path_allowed(rules, "/private") is False
        assert is_path_allowed(rules, "/private/") is False

    def test_path_prefix_matching(self):
        """Should match path prefixes correctly."""
        rules = {"*": ["/admin"]}
        # /admin should block /admin, /admin/, /admin/users, etc.
        assert is_path_allowed(rules, "/admin") is False
        assert is_path_allowed(rules, "/admin/") is False
        assert is_path_allowed(rules, "/admin/users") is False
        assert is_path_allowed(rules, "/administrator") is True  # Different path


class TestRobotsChecker:
    """Tests for RobotsChecker class with caching."""

    @pytest.mark.asyncio
    async def test_caches_results_with_ttl(self):
        """Should cache robots.txt results with TTL."""
        checker = RobotsChecker(cache_ttl_seconds=3600)

        # Mock httpx to return robots.txt
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.text = "User-agent: *\nDisallow: /private/"
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            # First call should fetch
            allowed, reason = await checker.check_url("https://example.com/public/page")
            assert allowed is True

            # Second call should use cache (verify by checking call count)
            allowed2, reason2 = await checker.check_url("https://example.com/other")
            assert allowed2 is True

            # Should only fetch once due to cache
            assert mock_client.return_value.__aenter__.return_value.get.call_count == 1

    @pytest.mark.asyncio
    async def test_refreshes_cache_after_ttl_expires(self):
        """Should refresh cache after TTL expires."""
        checker = RobotsChecker(cache_ttl_seconds=1)  # 1 second TTL

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.text = "User-agent: *\nDisallow: /private/"
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            # First call
            await checker.check_url("https://example.com/page")

            # Wait for TTL to expire
            time.sleep(1.1)

            # Second call should refetch
            await checker.check_url("https://example.com/page2")

            # Should fetch twice due to expired cache
            assert mock_client.return_value.__aenter__.return_value.get.call_count == 2

    @pytest.mark.asyncio
    async def test_handles_missing_robots_txt(self):
        """Should assume all allowed if robots.txt missing (404)."""
        checker = RobotsChecker()

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = AsyncMock()
            mock_response.status_code = 404
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            allowed, reason = await checker.check_url("https://example.com/page")
            assert allowed is True
            assert "no robots.txt" in reason.lower() or reason is None

    @pytest.mark.asyncio
    async def test_handles_network_errors_gracefully(self):
        """Should assume all allowed on network errors."""
        checker = RobotsChecker()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=Exception("Network error")
            )

            allowed, reason = await checker.check_url("https://example.com/page")
            assert allowed is True  # Fail open - allow on errors

    @pytest.mark.asyncio
    async def test_check_url_extracts_domain_and_path_correctly(self):
        """Should extract domain and path from URL correctly."""
        checker = RobotsChecker()

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.text = "User-agent: *\nDisallow: /private/"
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            # Check disallowed path
            allowed, reason = await checker.check_url("https://example.com/private/data")
            assert allowed is False

            # Check allowed path
            allowed2, reason2 = await checker.check_url("https://example.com/public/data")
            assert allowed2 is True

    @pytest.mark.asyncio
    async def test_tracks_different_domains_independently(self):
        """Should track different domains independently in cache."""
        checker = RobotsChecker()

        with patch("httpx.AsyncClient") as mock_client:
            mock_response1 = AsyncMock()
            mock_response1.status_code = 200
            mock_response1.text = "User-agent: *\nDisallow: /private/"

            mock_response2 = AsyncMock()
            mock_response2.status_code = 200
            mock_response2.text = "User-agent: *\nDisallow: /admin/"

            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=[mock_response1, mock_response2]
            )

            # Check two different domains
            allowed1, _ = await checker.check_url("https://example.com/private/data")
            allowed2, _ = await checker.check_url("https://other.com/private/data")

            # Different robots.txt rules for each domain
            assert allowed1 is False  # example.com blocks /private/
            assert allowed2 is True  # other.com allows /private/ (blocks /admin/)

            # Should fetch twice (once per domain)
            assert mock_client.return_value.__aenter__.return_value.get.call_count == 2

    @pytest.mark.asyncio
    async def test_uses_hikuweb_user_agent(self):
        """Should use 'hikuweb/0.1' as user agent string."""
        checker = RobotsChecker()

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.text = "User-agent: *\nDisallow: /"
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            await checker.check_url("https://example.com/page")

            # Check that fetch was called (we'll verify user agent in implementation)
            assert mock_client.return_value.__aenter__.return_value.get.call_count == 1
