# hikuweb - Agent Development Guide

## Quick Start

```bash
# 1. Install dependencies
uv sync

# 2. Set environment (create .env or export)
export OPENROUTER_API_KEY="your-key-here"

# 3. Start server
uv run uvicorn hikuweb.main:app --reload

# 4. Create an API key
uv run python -c "
from hikuweb.db.connection import DatabaseConnection
from hikuweb.db.api_keys import create_api_keys_table
from hikuweb.services.api_key_service import create_api_key
with DatabaseConnection('hikuweb.db') as conn:
    create_api_keys_table(conn)
    print(create_api_key(conn, 'test-key'))
"

# 5. Test endpoints
curl http://127.0.0.1:8000/health
curl -H "X-API-Key: YOUR_KEY" http://127.0.0.1:8000/auth-test
curl -X POST http://127.0.0.1:8000/extract \
  -H "X-API-Key: YOUR_KEY" -H "Content-Type: application/json" \
  -d '{"url":"https://example.com","schema":{"type":"object","properties":{"title":{"type":"string"}}}}'
```

## Quick Reference Commands

```bash
# Dependencies
uv sync                              # install/sync dependencies

# Run server
uv run uvicorn hikuweb.main:app --reload

# Tests
uv run pytest                        # run all tests
uv run pytest -v                     # verbose output
uv run pytest tests/test_foo.py      # single test file
uv run pytest -k "test_name"         # tests matching pattern
uv run pytest -x                     # stop on first failure

# Linting & Formatting
uv run ruff check src/ tests/        # check for issues
uv run ruff check --fix src/ tests/  # auto-fix issues
uv run ruff format src/ tests/       # format code

# Pre-commit
pre-commit install                   # install hooks (required before first commit)
pre-commit run --all-files           # run all hooks manually
```

## Project Structure

```
hikuweb/
├── src/hikuweb/
│   ├── config.py              # Settings via pydantic-settings
│   ├── main.py                # FastAPI app entrypoint
│   ├── api/                   # Routes, dependencies, request/response models
│   ├── services/              # Business logic (api_key, extraction, rate_limiter, robots)
│   └── db/                    # SQLite data access layer
├── tests/                     # Pytest test suite
└── pyproject.toml             # Project config, ruff settings
```

## Code Style

### ABOUTME Comments
All Python source files MUST start with a 2-line comment explaining the file's purpose:
```python
# ABOUTME: Brief description of what this file does.
# ABOUTME: Additional context or purpose explanation.
```

### Ruff Configuration
- **Line length**: 100 characters
- **Target**: Python 3.11+
- **Lint rules**: E, F, I, N, W, UP, B, C4, SIM (E501 ignored)
- **Quote style**: Double quotes
- **Import sorting**: Handled automatically by ruff

### Import Order
```python
# 1. Standard library
import time
from typing import Any

# 2. Third-party
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# 3. Local
from hikuweb.config import get_settings
from hikuweb.db.connection import DatabaseConnection
```

### Type Annotations
All functions MUST have complete type annotations:
```python
def process_data(input_str: str, count: int = 10) -> dict[str, Any]:
    ...
```

### Naming Conventions
| Type | Convention | Example |
|------|------------|---------|
| Functions/variables | snake_case | `validate_api_key` |
| Classes | PascalCase | `DatabaseConnection` |
| Constants | UPPER_SNAKE_CASE | `TYPE_MAP` |
| Private members | _leading_underscore | `_last_request` |

### Docstrings (Google Style)
```python
def complex_function(param1: str, param2: int) -> bool:
    """Short one-line summary.

    Args:
        param1: Description of param1.
        param2: Description of param2.

    Returns:
        Description of return value.

    Raises:
        ValueError: When param2 is negative.
    """
```

## Error Handling Patterns

### Custom Exceptions
Define domain-specific exceptions inheriting from standard types:
```python
class SchemaValidationError(ValueError):
    """Raised when JSON Schema contains invalid or unsupported types."""
```

### API Errors (FastAPI)
Use `HTTPException` with appropriate status codes:
```python
raise HTTPException(status_code=400, detail="Schema must not be empty")
raise HTTPException(status_code=403, detail=f"Blocked by robots.txt: {reason}")
raise HTTPException(status_code=429, detail="Rate limit exceeded for this domain")
raise HTTPException(status_code=500, detail=f"Extraction failed: {e}") from e
```

### Internal State Errors
Use `RuntimeError` for programming errors / invalid state:
```python
if not self._cursor:
    raise RuntimeError("Connection not opened. Use 'with' statement.")
```

### Return None for "Not Found"
For lookup functions, return `None` instead of raising:
```python
def validate_api_key(conn: DatabaseConnection, raw_key: str) -> dict | None:
    ...
    if key_record is None:
        return None
```

## Testing Guidelines

### TDD Workflow
1. **RED**: Write failing test first
2. **GREEN**: Write minimal code to pass
3. **REFACTOR**: Improve while keeping tests green

### Test Structure (Arrange-Act-Assert)
```python
class TestGenerateApiKey:
    """Tests for generate_api_key function."""

    def test_returns_32_char_string(self):
        """Should return 32 character alphanumeric string."""
        # Arrange (if needed)

        # Act
        key = generate_api_key()

        # Assert
        assert isinstance(key, str)
        assert len(key) == 32
```

### Fixtures (in `tests/conftest.py`)
```python
@pytest.fixture
def db_connection():
    """Provides an in-memory database connection for testing."""
    with DatabaseConnection(":memory:") as conn:
        yield conn
```

### Async Tests
```python
@pytest.mark.asyncio
async def test_async_operation():
    result = await async_function()
    assert result is not None
```

### Mocking External Dependencies
```python
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_with_mock():
    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.get = AsyncMock(return_value=mock_response)
        result = await function_that_uses_httpx()
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_PATH` | `hikuweb.db` | SQLite database path |
| `OPENROUTER_API_KEY` | None | Required for extractions |
| `RATE_LIMIT_REQUESTS_PER_SECOND` | `1.0` | Per-domain rate limit |
| `ROBOTS_CACHE_TTL_SECONDS` | `3600` | robots.txt cache TTL |

Set in `.env` file or export in shell.

## Architecture Notes

### Layered Architecture
- **API Layer** (`src/hikuweb/api/`): FastAPI routes and request/response models
- **Service Layer** (`src/hikuweb/services/`): Business logic, validation, coordination
- **Database Layer** (`src/hikuweb/db/`): Data access, CRUD operations

### Key Services
- **API Key Service**: Secure generation, hashing (SHA-256), validation
- **Schema Translator**: JSON Schema → Pydantic models (dynamic model creation)
- **Robots Checker**: Fetches/parses/caches robots.txt, checks permissions
- **Rate Limiter**: Per-domain rate limiting with token bucket algorithm

### Database
- SQLite for simplicity and portability
- Two main tables: `api_keys` and `extraction_logs`
- Context manager pattern for connection handling
