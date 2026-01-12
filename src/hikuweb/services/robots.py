# ABOUTME: Service for robots.txt compliance checking.
# ABOUTME: Fetches, parses, caches, and checks URL permissions against robots.txt rules.

import time
from urllib.parse import urlparse

import httpx


def parse_robots_txt(content: str) -> dict[str, list[str]]:
    """Parse robots.txt content into a dict of user-agent -> disallowed paths.

    Args:
        content: Raw robots.txt file content.

    Returns:
        Dict mapping user-agent names to list of disallowed path prefixes.
        Example: {"*": ["/private/", "/admin/"], "googlebot": ["/secret/"]}
    """
    rules: dict[str, list[str]] = {}
    current_agent: str | None = None

    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        # Parse directives (case-insensitive)
        if ":" in line:
            key, value = line.split(":", 1)
            key = key.strip().lower()
            value = value.strip()

            if key == "user-agent":
                current_agent = value.lower()
                if current_agent not in rules:
                    rules[current_agent] = []
            elif key == "disallow" and current_agent is not None:
                # Only add non-empty disallow rules
                if value:
                    rules[current_agent].append(value)

    return rules


def is_path_allowed(rules: dict[str, list[str]], path: str, user_agent: str = "*") -> bool:
    """Check if a path is allowed according to robots.txt rules.

    Args:
        rules: Parsed robots.txt rules (from parse_robots_txt).
        path: The URL path to check (e.g., "/public/page.html").
        user_agent: User agent to check rules for (default: "*").

    Returns:
        True if path is allowed, False if disallowed.
        Defaults to True if no matching rules found.
    """
    if not rules:
        return True

    # Check user-agent specific rules first, then fall back to wildcard
    agents_to_check = [user_agent.lower(), "*"] if user_agent != "*" else ["*"]

    for agent in agents_to_check:
        if agent in rules:
            for disallowed_prefix in rules[agent]:
                # Handle wildcard patterns
                if "*" in disallowed_prefix:
                    # Simple wildcard matching: convert to prefix check
                    prefix = disallowed_prefix.split("*")[0]
                    if path.startswith(prefix):
                        return False
                else:
                    # Standard prefix matching - must match exactly or be followed by /
                    if path == disallowed_prefix or path.startswith(disallowed_prefix + "/"):
                        return False
                    # Also check if disallowed_prefix ends with / and path starts with it
                    if disallowed_prefix.endswith("/") and path.startswith(disallowed_prefix):
                        return False

    # Default to allowing if no matching disallow rules
    return True


class RobotsChecker:
    """Fetches, caches, and checks robots.txt compliance for URLs."""

    USER_AGENT = "hikuweb/0.1"

    def __init__(self, cache_ttl_seconds: int = 3600):
        """Initialize the robots checker with caching.

        Args:
            cache_ttl_seconds: Time-to-live for cached robots.txt entries (default: 3600s).
        """
        self.cache_ttl_seconds = cache_ttl_seconds
        self._cache: dict[str, tuple[dict[str, list[str]], float]] = {}

    async def fetch_robots_txt(self, domain: str) -> str | None:
        """Fetch robots.txt for a domain.

        Args:
            domain: The domain to fetch robots.txt from (e.g., "example.com").

        Returns:
            robots.txt content as string, or None if not found or error.
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://{domain}/robots.txt",
                    timeout=10.0,
                    follow_redirects=True,
                )
                if response.status_code == 200:
                    return response.text
        except Exception:
            # Fail open - assume allowed on any error
            pass
        return None

    def _is_cache_valid(self, domain: str) -> bool:
        """Check if cached entry for domain is still valid.

        Args:
            domain: The domain to check.

        Returns:
            True if cache entry exists and is not expired.
        """
        if domain not in self._cache:
            return False

        _, timestamp = self._cache[domain]
        return (time.time() - timestamp) < self.cache_ttl_seconds

    async def check_url(self, url: str) -> tuple[bool, str | None]:
        """Check if a URL is allowed according to robots.txt.

        Fetches and caches robots.txt for the domain, then checks if the path is allowed.

        Args:
            url: Full URL to check (e.g., "https://example.com/page").

        Returns:
            Tuple of (allowed: bool, reason: str | None).
            - allowed: True if URL can be scraped, False if blocked.
            - reason: Explanation string or None.
        """
        # Parse URL to extract domain and path
        parsed = urlparse(url)
        domain = parsed.netloc
        path = parsed.path or "/"

        # Check cache first
        if self._is_cache_valid(domain):
            rules, _ = self._cache[domain]
        else:
            # Fetch robots.txt
            content = await self.fetch_robots_txt(domain)

            if content is None:
                # No robots.txt or error - cache empty rules and allow all
                rules = {}
                self._cache[domain] = (rules, time.time())
                return True, "No robots.txt found"

            # Parse and cache
            rules = parse_robots_txt(content)
            self._cache[domain] = (rules, time.time())

        # Check if path is allowed
        allowed = is_path_allowed(rules, path, user_agent=self.USER_AGENT)
        reason = None if allowed else "Blocked by robots.txt"

        return allowed, reason
