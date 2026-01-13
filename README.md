# hikuweb

REST API service for AI-powered web scraping. Uses [hikugen](https://github.com/yourusername/hikugen) to extract structured data from web pages based on JSON Schema definitions.

## Features

- **Structured Extraction**: Define what you want with JSON Schema, get structured data back
- **Robots.txt Compliance**: Automatically respects robots.txt rules
- **Rate Limiting**: Per-domain rate limiting to be a good citizen
- **API Key Auth**: Secure access with API key authentication
- **Usage Tracking**: Built-in extraction logging and usage statistics

## Quick Start

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) package manager
- OpenRouter API key (for LLM-powered extraction)

### Installation

```bash
# Clone the repo
git clone https://github.com/yourusername/hikuweb.git
cd hikuweb

# Install dependencies
uv sync
```

### Configuration

Create a `.env` file or export environment variables:

```bash
# Required
export OPENROUTER_API_KEY="your-openrouter-api-key"

# Optional (with defaults)
export DATABASE_PATH="hikuweb.db"
export RATE_LIMIT_REQUESTS_PER_SECOND="1.0"
export ROBOTS_CACHE_TTL_SECONDS="3600"
```

### Running the Server

```bash
uv run uvicorn hikuweb.main:app --reload
```

Server starts at `http://127.0.0.1:8000`

### Create an API Key

```bash
uv run python -c "
from hikuweb.db.connection import DatabaseConnection
from hikuweb.db.api_keys import create_api_keys_table
from hikuweb.services.api_key_service import create_api_key
with DatabaseConnection('hikuweb.db') as conn:
    create_api_keys_table(conn)
    print(create_api_key(conn, 'my-key'))
"
```

Save the returned key - it's only shown once!

## API Reference

### Health Check

```bash
GET /health
```

Returns service status. No authentication required.

```json
{"status": "healthy", "version": "0.1.0"}
```

### Test Authentication

```bash
GET /auth-test
X-API-Key: your-api-key
```

Verify your API key is valid.

```json
{"authenticated": true, "key_name": "my-key"}
```

### Extract Data

```bash
POST /extract
X-API-Key: your-api-key
Content-Type: application/json
```

Extract structured data from a URL using a JSON Schema.

**Request:**

```json
{
  "url": "https://example.com/product",
  "schema": {
    "type": "object",
    "properties": {
      "title": {"type": "string"},
      "price": {"type": "number"},
      "in_stock": {"type": "boolean"}
    }
  }
}
```

**Response:**

```json
{
  "data": {
    "title": "Example Product",
    "price": 29.99,
    "in_stock": true
  },
  "duration_ms": 1234
}
```

**Status Codes:**
- `200` - Success
- `400` - Invalid schema
- `401` - Missing or invalid API key
- `403` - Blocked by robots.txt
- `429` - Rate limit exceeded
- `500` - Extraction failed

### Usage Statistics

```bash
GET /usage
X-API-Key: your-api-key
```

Get extraction statistics for your API key.

```json
{
  "total_extractions": 150,
  "success_count": 142,
  "error_count": 5,
  "blocked_count": 3,
  "average_duration_ms": 1523.4,
  "recent_extractions": [
    {
      "url": "https://example.com",
      "status": "success",
      "created_at": "2024-01-15T10:30:00Z",
      "duration_ms": 1200
    }
  ]
}
```

## Development

### Run Tests

```bash
uv run pytest           # all tests
uv run pytest -v        # verbose
uv run pytest -x        # stop on first failure
```

### Linting & Formatting

```bash
uv run ruff check src/ tests/        # check for issues
uv run ruff check --fix src/ tests/  # auto-fix
uv run ruff format src/ tests/       # format code
```

### Pre-commit Hooks

```bash
pre-commit install           # install hooks (do this once)
pre-commit run --all-files   # run manually
```

## Project Structure

```
hikuweb/
├── src/hikuweb/
│   ├── main.py              # FastAPI app entrypoint
│   ├── config.py            # Settings (pydantic-settings)
│   ├── api/
│   │   ├── routes.py        # API endpoints
│   │   └── dependencies.py  # FastAPI dependencies
│   ├── services/
│   │   ├── api_key_service.py   # Key generation & validation
│   │   ├── extraction.py        # hikugen wrapper
│   │   ├── rate_limiter.py      # Per-domain rate limiting
│   │   ├── robots.py            # robots.txt checker
│   │   └── schema_translator.py # JSON Schema to Pydantic
│   └── db/
│       ├── connection.py        # SQLite connection manager
│       ├── api_keys.py          # API keys table
│       └── extraction_logs.py   # Extraction logs table
├── tests/                   # Test suite
└── pyproject.toml           # Project config
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENROUTER_API_KEY` | (required) | API key for OpenRouter LLM access |
| `DATABASE_PATH` | `hikuweb.db` | Path to SQLite database |
| `RATE_LIMIT_REQUESTS_PER_SECOND` | `1.0` | Max requests per second per domain |
| `ROBOTS_CACHE_TTL_SECONDS` | `3600` | How long to cache robots.txt (seconds) |

## License

MIT
