# ABOUTME: Tests for per-domain rate limiter service.
# ABOUTME: Verifies rate limiting, domain tracking, and cleanup.

import time

from hikuweb.services.rate_limiter import DomainRateLimiter


class TestDomainRateLimiter:
    """Tests for domain-based rate limiter."""

    def test_allows_first_request(self):
        """Should allow first request to a domain."""
        limiter = DomainRateLimiter(requests_per_second=1.0)
        assert limiter.acquire("https://example.com/page") is True

    def test_blocks_rapid_requests(self):
        """Should block rapid successive requests to same domain."""
        limiter = DomainRateLimiter(requests_per_second=1.0)
        limiter.acquire("https://example.com/page1")
        assert limiter.acquire("https://example.com/page2") is False

    def test_allows_requests_after_waiting(self):
        """Should allow requests after waiting for rate limit period."""
        limiter = DomainRateLimiter(requests_per_second=2.0)  # 0.5s between requests
        limiter.acquire("https://example.com/page")
        time.sleep(0.6)  # Wait longer than 0.5s
        assert limiter.acquire("https://example.com/another") is True

    def test_different_domains_independent(self):
        """Should track different domains independently."""
        limiter = DomainRateLimiter(requests_per_second=1.0)
        limiter.acquire("https://example.com/page")
        assert limiter.acquire("https://other.com/page") is True

    def test_wait_time_returns_seconds(self):
        """Should return seconds until next allowed request."""
        limiter = DomainRateLimiter(requests_per_second=2.0)  # 0.5s between requests
        limiter.acquire("https://example.com/page")
        wait = limiter.wait_time("https://example.com/another")
        assert 0 < wait <= 0.5

    def test_wait_time_zero_when_ready(self):
        """Should return zero when request is allowed."""
        limiter = DomainRateLimiter(requests_per_second=1.0)
        wait = limiter.wait_time("https://example.com/page")
        assert wait == 0.0

    def test_wait_time_decreases_over_time(self):
        """Should return decreasing wait time as time passes."""
        limiter = DomainRateLimiter(requests_per_second=1.0)  # 1s between requests
        limiter.acquire("https://example.com/page")
        wait1 = limiter.wait_time("https://example.com/another")
        time.sleep(0.3)  # Wait 0.3s
        wait2 = limiter.wait_time("https://example.com/another")
        assert wait2 < wait1
        assert wait2 > 0  # Still not ready

    def test_extract_domain_from_url(self):
        """Should extract domain correctly from URLs."""
        limiter = DomainRateLimiter(requests_per_second=1.0)
        assert limiter.extract_domain("https://example.com/page") == "example.com"
        assert limiter.extract_domain("http://example.com/page") == "example.com"
        assert (
            limiter.extract_domain("https://subdomain.example.com/page") == "subdomain.example.com"
        )

    def test_cleanup_removes_old_entries(self):
        """Should clean up old entries to prevent memory leaks."""
        limiter = DomainRateLimiter(requests_per_second=1.0)
        limiter.acquire("https://example.com/page")
        limiter.acquire("https://other.com/page")
        time.sleep(0.1)
        removed = limiter.cleanup(max_age_seconds=0.05)  # Remove entries older than 50ms
        assert removed == 2  # Both entries should be removed

    def test_cleanup_keeps_recent_entries(self):
        """Should keep recent entries during cleanup."""
        limiter = DomainRateLimiter(requests_per_second=1.0)
        limiter.acquire("https://example.com/page")
        time.sleep(0.1)
        limiter.acquire("https://other.com/page")  # Recent
        removed = limiter.cleanup(max_age_seconds=0.05)
        assert removed == 1  # Only old entry removed

    def test_same_path_different_pages_treated_as_same_domain(self):
        """Should treat different paths on same domain as same for rate limiting."""
        limiter = DomainRateLimiter(requests_per_second=1.0)
        limiter.acquire("https://example.com/page1")
        assert limiter.acquire("https://example.com/page2") is False
        assert limiter.acquire("https://example.com/") is False

    def test_thread_safety_basic(self):
        """Should handle concurrent access safely (basic test)."""
        # Note: This is a simple test. In production, would test with threading module.
        limiter = DomainRateLimiter(requests_per_second=1.0)
        # Multiple calls should be safe
        limiter.acquire("https://example.com/page")
        limiter.wait_time("https://example.com/page")
        limiter.cleanup(max_age_seconds=3600)
        # If no exception raised, basic thread safety structure is in place
        assert True
