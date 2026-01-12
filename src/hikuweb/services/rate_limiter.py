# ABOUTME: Per-domain rate limiter service.
# ABOUTME: Thread-safe rate limiting using token bucket algorithm.

import threading
import time
from urllib.parse import urlparse


class DomainRateLimiter:
    """Thread-safe rate limiter that tracks requests per domain.

    Uses a simple token bucket algorithm where each domain can make
    one request per (1/requests_per_second) seconds.

    Args:
        requests_per_second: Maximum requests per second per domain (default: 1.0)

    Example:
        limiter = DomainRateLimiter(requests_per_second=2.0)
        if limiter.acquire("https://example.com/page"):
            # Make request
        else:
            wait = limiter.wait_time("https://example.com/page")
            print(f"Rate limited. Wait {wait:.2f} seconds")
    """

    def __init__(self, requests_per_second: float = 1.0):
        """Initialize rate limiter with requests per second limit.

        Args:
            requests_per_second: Maximum requests per second per domain.
        """
        self.min_interval = 1.0 / requests_per_second
        self._last_request: dict[str, float] = {}
        self._lock = threading.Lock()

    def extract_domain(self, url: str) -> str:
        """Extract domain (netloc) from URL.

        Args:
            url: Full URL to extract domain from.

        Returns:
            Domain string (netloc part of URL).

        Example:
            extract_domain("https://example.com/page") -> "example.com"
        """
        return urlparse(url).netloc

    def acquire(self, url: str) -> bool:
        """Attempt to acquire permission to make a request to the URL's domain.

        Args:
            url: URL to check rate limit for.

        Returns:
            True if request is allowed (updates last request timestamp),
            False if rate limited.
        """
        domain = self.extract_domain(url)
        with self._lock:
            now = time.time()
            last = self._last_request.get(domain, 0)
            if now - last >= self.min_interval:
                self._last_request[domain] = now
                return True
            return False

    def wait_time(self, url: str) -> float:
        """Calculate seconds until next request to URL's domain is allowed.

        Args:
            url: URL to check wait time for.

        Returns:
            Seconds until next request allowed (0.0 if ready now).
        """
        domain = self.extract_domain(url)
        with self._lock:
            now = time.time()
            last = self._last_request.get(domain, 0)
            elapsed = now - last
            if elapsed >= self.min_interval:
                return 0.0
            return self.min_interval - elapsed

    def cleanup(self, max_age_seconds: float = 3600) -> int:
        """Remove old entries from cache to prevent memory leaks.

        Args:
            max_age_seconds: Remove entries older than this many seconds.

        Returns:
            Number of entries removed.
        """
        with self._lock:
            now = time.time()
            to_remove = [
                domain
                for domain, last_time in self._last_request.items()
                if now - last_time > max_age_seconds
            ]
            for domain in to_remove:
                del self._last_request[domain]
            return len(to_remove)
