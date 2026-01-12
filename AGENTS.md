# hikuweb - Agent Development Guide

## Quick Reference Commands

```bash
# Install/sync dependencies
uv sync

# Run tests
uv run pytest
uv run pytest -v  # verbose
uv run pytest tests/test_foo.py  # specific test file
uv run pytest -k "test_name"  # specific test

# Linting and formatting
uv run ruff check src/ tests/  # check for issues
uv run ruff check --fix src/ tests/  # auto-fix issues
uv run ruff format src/ tests/  # format code

# Pre-commit hooks
pre-commit install  # install hooks
pre-commit run --all-files  # run hooks on all files
```

## Project Structure

```
hikuweb/
├── src/hikuweb/
│   ├── __init__.py
│   ├── config.py              # Configuration management
│   ├── api/                   # FastAPI routes and endpoints
│   ├── services/              # Business logic layer
│   │   ├── api_key_service.py
│   │   ├── schema_translator.py
│   │   ├── robots.py
│   │   └── rate_limiter.py
│   └── db/                    # Database layer
│       ├── connection.py
│       ├── api_keys.py
│       └── extraction_logs.py
├── tests/                     # Test suite
└── pyproject.toml             # Project configuration
```

## Code Style Guidelines

### ABOUTME Comments
All Python source files MUST start with a 2-line comment explaining the file's purpose:

```python
# ABOUTME: Brief description of what this file does.
# ABOUTME: Additional context or purpose explanation.
```

This format makes it easy to grep for file purposes: `grep "ABOUTME:" src/**/*.py`

### Import Ordering
Organize imports in three groups (ruff handles this automatically):
1. Standard library imports
2. Third-party imports
3. Local/application imports

```python
# Standard library
import time
from typing import Optional

# Third-party
from fastapi import APIRouter
from pydantic import BaseModel

# Local
from hikuweb.config import get_settings
from hikuweb.db.connection import DatabaseConnection
```

### Type Annotations
All function signatures MUST include type annotations:

```python
def process_data(input_str: str, count: int = 10) -> dict[str, Any]:
    """Process input data and return results."""
    ...
```

### Docstrings
Use Google-style docstrings for functions and classes:

```python
def complex_function(param1: str, param2: int) -> bool:
    """Short one-line summary.

    Longer description if needed, explaining what the function does,
    any important considerations, etc.

    Args:
        param1: Description of param1.
        param2: Description of param2.

    Returns:
        Description of return value.

    Raises:
        ValueError: When param2 is negative.
    """
    ...
```

### Naming Conventions
- **Functions/variables**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private members**: `_leading_underscore`

## Testing Guidelines

### TDD Workflow
We follow Test-Driven Development:
1. **RED**: Write failing tests first
2. **GREEN**: Write minimal code to pass tests
3. **REFACTOR**: Improve code while keeping tests green

### Test Structure
Use the Arrange-Act-Assert pattern:

```python
def test_something(db_connection):
    """Should do something specific when condition is met."""
    # Arrange
    setup_data = prepare_test_data()
    
    # Act
    result = function_under_test(setup_data)
    
    # Assert
    assert result == expected_value
```

### Fixtures
Use pytest fixtures for reusable test setup (defined in `tests/conftest.py`):

```python
@pytest.fixture
def db_connection():
    """Provides an in-memory database connection for testing."""
    conn = DatabaseConnection(":memory:")
    yield conn
    # Cleanup happens here
```

### Async Tests
Mark async tests with `@pytest.mark.asyncio`:

```python
@pytest.mark.asyncio
async def test_async_operation():
    """Test asynchronous operation."""
    result = await async_function()
    assert result is not None
```

### Mocking
Use `unittest.mock` for external dependencies:

```python
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_with_mock():
    """Test with mocked HTTP client."""
    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.get = AsyncMock(return_value=mock_response)
        result = await function_that_uses_httpx()
        assert result == expected
```

## Environment Variables

The following environment variables are used by hikuweb:

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_PATH` | `hikuweb.db` | Path to SQLite database file |
| `OPENROUTER_API_KEY` | None | API key for OpenRouter (required for extractions) |
| `RATE_LIMIT_REQUESTS_PER_SECOND` | `1.0` | Rate limit for requests per domain |
| `ROBOTS_CACHE_TTL_SECONDS` | `3600` | Cache TTL for robots.txt files |

Set these in a `.env` file or export them in your shell:

```bash
export OPENROUTER_API_KEY="your-api-key-here"
export DATABASE_PATH="./data/hikuweb.db"
```

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
