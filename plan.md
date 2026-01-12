# hikuweb Implementation Plan

> **hikuweb** - A REST API service exposing hikugen's AI-powered web scraping capabilities

---

## TDD Protocol (MANDATORY)

**Every prompt in this plan follows strict Test-Driven Development. This is non-negotiable.**

### The TDD Cycle

```
┌─────────────────────────────────────────────────────────────┐
│  1. RED    → Write a failing test first                     │
│  2. GREEN  → Write minimal code to make test pass           │
│  3. REFACTOR → Clean up while keeping tests green           │
│  4. REPEAT → Next test case                                 │
└─────────────────────────────────────────────────────────────┘
```

### TDD Rules for This Project

1. **NEVER write implementation code before tests exist**
2. **Run tests after EVERY change** - `uv run pytest <test_file> -v`
3. **One test at a time** - Write one test, make it pass, then write the next
4. **Tests must fail first** - If a new test passes immediately, something is wrong
5. **Commit after each green state** - Small, incremental commits

### Test Structure Pattern

```python
class TestFeatureName:
    """Tests for <feature description>."""

    def test_<behavior>_<scenario>(self):
        """Should <expected behavior> when <condition>."""
        # Arrange - set up test data
        # Act - call the function/method
        # Assert - verify the result
```

### Before Moving to Next Prompt

- [ ] All tests pass (`uv run pytest -v`)
- [ ] No linting errors (`uv run ruff check src/ tests/`)
- [ ] Code is formatted (`uv run ruff format src/ tests/`)
- [ ] Commit made with descriptive message

---

## Project Overview

### What We're Building
A FastAPI-based REST API that allows users to extract structured data from websites using JSON Schema definitions. The service wraps the hikugen library, adding authentication, compliance features (robots.txt), rate limiting, and usage tracking.

### Tech Stack
- **Framework**: FastAPI
- **Database**: SQLite
- **Auth**: API Keys (manually provisioned)
- **Schema Input**: JSON Schema → Pydantic via `create_model()`
- **Processing**: Synchronous
- **Linting**: Ruff
- **Package Manager**: uv

### Key Features (MVP)
1. `POST /extract` - Extract data from URL using JSON Schema
2. `GET /health` - Health check
3. `GET /usage` - Usage statistics for authenticated user
4. API key authentication
5. robots.txt compliance (block disallowed URLs)
6. Per-domain rate limiting
7. Extraction logging/audit trail

---

## Architecture

```
┌─────────────────┐     ┌──────────────────────────────────────────────────┐
│   Client/User   │────▶│              hikuweb API (FastAPI)               │
│  (API request)  │     │                                                  │
└─────────────────┘     │  ┌────────────────────────────────────────────┐  │
                        │  │  Auth Layer (API Key validation)           │  │
                        │  └────────────────────────────────────────────┘  │
                        │                      │                           │
                        │  ┌────────────────────────────────────────────┐  │
                        │  │  Compliance Layer                          │  │
                        │  │  - robots.txt checker                      │  │
                        │  │  - Domain rate limiter                     │  │
                        │  └────────────────────────────────────────────┘  │
                        │                      │                           │
                        │  ┌────────────────────────────────────────────┐  │
                        │  │  Schema Translation                        │  │
                        │  │  - JSON Schema → Pydantic model            │  │
                        │  └────────────────────────────────────────────┘  │
                        │                      │                           │
                        │  ┌────────────────────────────────────────────┐  │
                        │  │  Extraction Service (hikugen wrapper)      │  │
                        │  │  - Fetch HTML                              │  │
                        │  │  - Generate extraction code (LLM)          │  │
                        │  │  - Execute & validate                      │  │
                        │  └────────────────────────────────────────────┘  │
                        │                      │                           │
                        │  ┌────────────────────────────────────────────┐  │
                        │  │  Database Layer (SQLite)                   │  │
                        │  │  - api_keys table                          │  │
                        │  │  - extraction_logs table                   │  │
                        │  └────────────────────────────────────────────┘  │
                        └──────────────────────────────────────────────────┘
```

---

## File Structure

```
hikuweb/
├── pyproject.toml
├── AGENTS.md
├── plan.md
├── todo.md
├── .pre-commit-config.yaml
├── pytest.ini
├── src/
│   └── hikuweb/
│       ├── __init__.py
│       ├── main.py                 # FastAPI app entry point
│       ├── config.py               # Settings via pydantic-settings
│       ├── api/
│       │   ├── __init__.py
│       │   ├── routes.py           # API route definitions
│       │   └── dependencies.py     # Auth, rate limiting deps
│       ├── services/
│       │   ├── __init__.py
│       │   ├── api_key_service.py  # API key operations
│       │   ├── extraction.py       # hikugen wrapper
│       │   ├── schema_translator.py # JSON Schema → Pydantic
│       │   ├── robots.py           # robots.txt service
│       │   └── rate_limiter.py     # Domain rate limiting
│       └── db/
│           ├── __init__.py
│           ├── connection.py       # SQLite connection manager
│           ├── api_keys.py         # api_keys table operations
│           └── extraction_logs.py  # extraction_logs table operations
└── tests/
    ├── __init__.py
    ├── conftest.py                 # Shared fixtures
    ├── test_config.py
    ├── test_db_connection.py
    ├── test_db_api_keys.py
    ├── test_db_extraction_logs.py
    ├── test_api_key_service.py
    ├── test_schema_translator.py
    ├── test_robots.py
    ├── test_rate_limiter.py
    ├── test_api_health.py
    ├── test_api_auth.py
    ├── test_api_extract.py
    ├── test_api_usage.py
    └── test_integration.py
```

---

## Prompt Sequence

Each prompt is designed to be executed by an LLM in a TDD manner. They build incrementally on each other with no orphaned code.

---

## PROMPT 1: Project Initialization

**Goal**: Initialize the project with uv, create basic folder structure, pyproject.toml

**Prerequisites**: None (starting fresh)

**Builds on**: Nothing

**Output**: 
- `pyproject.toml` with dependencies
- `src/hikuweb/__init__.py`
- `tests/__init__.py`
- Working `uv sync` and `uv run pytest`

```text
You are building hikuweb, a FastAPI REST API that exposes hikugen (an AI-powered web scraping library) as a service.

TASK: Initialize the project structure

1. Create pyproject.toml with:
   - name: "hikuweb"
   - version: "0.1.0"
   - description: "REST API service for AI-powered web scraping with hikugen"
   - requires-python: ">=3.11"
   - dependencies:
     - fastapi>=0.115.0
     - uvicorn>=0.32.0
     - pydantic>=2.10.0
     - pydantic-settings>=2.6.0
     - httpx>=0.28.0 (for async HTTP, robots.txt fetching)
     - hikugen (from local path: ../hikugen)
   - dev dependencies (in [project.optional-dependencies] dev):
     - pytest>=8.0.0
     - pytest-asyncio>=0.24.0
     - ruff>=0.8.0

2. Create the folder structure:
   - src/hikuweb/__init__.py (with __version__ = "0.1.0")
   - src/hikuweb/api/__init__.py (empty)
   - src/hikuweb/services/__init__.py (empty)
   - src/hikuweb/db/__init__.py (empty)
   - tests/__init__.py (empty)
   - tests/conftest.py (empty for now)

3. Create pytest.ini with:
   - testpaths = tests
   - asyncio_mode = auto
   - pythonpath = src

4. All source files must start with a 2-line ABOUTME comment explaining the file's purpose.

5. After creating files, run:
   - uv sync
   - uv run pytest (should pass with "no tests collected")

DO NOT create any other files yet. This is just project initialization.
```

---

## PROMPT 2: Tooling Setup

**Goal**: Set up pre-commit hooks with ruff, create AGENTS.md

**Prerequisites**: Prompt 1 completed

**Builds on**: Prompt 1 (project structure exists)

**Output**:
- `.pre-commit-config.yaml`
- `AGENTS.md`
- ruff configuration in pyproject.toml
- Working `pre-commit run --all-files`

```text
You are continuing to build hikuweb. The project structure from Prompt 1 exists.

TASK: Set up development tooling

1. Add ruff configuration to pyproject.toml:
   [tool.ruff]
   line-length = 100
   target-version = "py311"
   src = ["src", "tests"]

   [tool.ruff.lint]
   select = ["E", "F", "I", "N", "W", "UP", "B", "C4", "SIM"]
   ignore = ["E501"]  # line length handled separately

   [tool.ruff.format]
   quote-style = "double"

2. Create .pre-commit-config.yaml:
   - Use ruff for linting (ruff check --fix)
   - Use ruff for formatting (ruff format)
   - Hook into pre-commit

3. Create AGENTS.md with project conventions:
   - Quick reference commands (uv sync, pytest, ruff)
   - Project structure overview
   - Code style guidelines (matching hikugen's AGENTS.md style):
     - ABOUTME comments on all files
     - Import ordering (stdlib, third-party, local)
     - Type annotations required
     - Google-style docstrings
     - Naming conventions
   - Testing guidelines (TDD, fixtures, mocking)
   - Environment variables section

4. Run pre-commit install and pre-commit run --all-files to verify setup.

5. Fix any linting issues in existing files.

All files must follow the ABOUTME comment convention.
```

---

## PROMPT 3: Configuration Management

**Goal**: Create config module with pydantic-settings for environment variables

**Prerequisites**: Prompt 2 completed

**Builds on**: Prompt 2 (tooling works)

**Output**:
- `src/hikuweb/config.py`
- `tests/test_config.py`
- All tests passing

```text
You are continuing to build hikuweb. Project structure and tooling from Prompts 1-2 exist.

TASK: Create configuration management using pydantic-settings

## TDD WORKFLOW (Follow this exact order):

STEP 1: Write ALL tests first (they will fail - this is expected)
STEP 2: Run tests to confirm they fail: uv run pytest tests/test_config.py -v
STEP 3: Implement the code to make tests pass
STEP 4: Run tests again to confirm they pass
STEP 5: Refactor if needed (keep tests green)
STEP 6: Run ruff check and format

## TEST SPECIFICATIONS:

1. Create tests/test_config.py with tests for:
   - Settings loads default values when no env vars set
   - Settings loads DATABASE_PATH from environment
   - Settings loads OPENROUTER_API_KEY from environment  
   - Settings loads RATE_LIMIT_REQUESTS_PER_SECOND from environment (default: 1.0)
   - Settings loads ROBOTS_CACHE_TTL_SECONDS from environment (default: 3600)
   - Settings has a computed property for database URL

---

## PROMPT 4: Database Connection

**Goal**: Create SQLite connection manager with context management

**Prerequisites**: Prompt 3 completed

**Builds on**: Prompt 3 (config exists for database_path)

**Output**:
- `src/hikuweb/db/connection.py`
- `tests/test_db_connection.py`
- All tests passing

```text
You are continuing to build hikuweb. Config module from Prompt 3 exists.

TASK: Create SQLite database connection manager

## TDD WORKFLOW (Follow this exact order):

STEP 1: Write ALL tests first (they will fail - this is expected)
STEP 2: Run tests to confirm they fail: uv run pytest tests/test_db_connection.py -v
STEP 3: Implement the code to make tests pass
STEP 4: Run tests again to confirm they pass
STEP 5: Refactor if needed (keep tests green)
STEP 6: Run ruff check and format

## TEST SPECIFICATIONS:

1. Create tests/test_db_connection.py with tests for:
   - Database connection can be created with path
   - Database connection works as context manager
   - Connection is closed after context exits
   - get_db_connection() returns working connection
   - In-memory database works (":memory:")
   - Tables can be created and queried

## IMPLEMENTATION:

2. Create src/hikuweb/db/connection.py:
   - DatabaseConnection class that:
     - Takes db_path in __init__
     - Implements __enter__ and __exit__ for context manager
     - Has execute() method for running queries
     - Has executemany() method for batch operations
     - Has fetchone() and fetchall() methods
     - Properly handles commits and rollbacks
   - get_db_connection(db_path: str) function that returns DatabaseConnection
   - Consider thread safety (SQLite and threading)

3. Update tests/conftest.py:
   - Add fixture for in-memory database connection
   - This fixture will be reused by other test modules

## VERIFICATION:

4. Run tests: uv run pytest tests/test_db_connection.py -v
5. Run linter: uv run ruff check src/hikuweb/db/ tests/test_db_connection.py
6. Format code: uv run ruff format src/hikuweb/db/ tests/test_db_connection.py
7. ALL tests must pass before moving to Prompt 5

Remember: ABOUTME comments, type annotations, proper error handling.
```

---

## PROMPT 5: API Keys Table

**Goal**: Create api_keys table schema and CRUD operations

**Prerequisites**: Prompt 4 completed

**Builds on**: Prompt 4 (database connection works)

**Output**:
- `src/hikuweb/db/api_keys.py`
- `tests/test_db_api_keys.py`
- All tests passing

```text
You are continuing to build hikuweb. Database connection from Prompt 4 exists.

TASK: Create api_keys table and CRUD operations

## TDD WORKFLOW (Follow this exact order):

STEP 1: Write ALL tests first (they will fail - this is expected)
STEP 2: Run tests to confirm they fail: uv run pytest tests/test_db_api_keys.py -v
STEP 3: Implement the code to make tests pass
STEP 4: Run tests again to confirm they pass
STEP 5: Refactor if needed (keep tests green)
STEP 6: Run ruff check and format

## TEST SPECIFICATIONS:

1. Create tests/test_db_api_keys.py with tests for:
   - create_api_keys_table() creates the table
   - insert_api_key() stores a new key record
   - get_api_key_by_hash() retrieves key by hash
   - get_api_key_by_id() retrieves key by ID
   - update_last_used() updates the last_used_at timestamp
   - deactivate_api_key() sets is_active to False
   - list_api_keys() returns all keys (for admin use)
   - Duplicate key_hash is rejected (unique constraint)

## IMPLEMENTATION:

2. Create src/hikuweb/db/api_keys.py:
   - Table schema for api_keys:
     - id: INTEGER PRIMARY KEY AUTOINCREMENT
     - key_hash: TEXT UNIQUE NOT NULL (we store hash, not raw key)
     - name: TEXT NOT NULL (friendly name for the key)
     - created_at: TEXT NOT NULL (ISO timestamp)
     - last_used_at: TEXT (nullable, ISO timestamp)
     - is_active: INTEGER NOT NULL DEFAULT 1 (boolean as int)
   - Functions:
     - create_api_keys_table(conn: DatabaseConnection) -> None
     - insert_api_key(conn, key_hash: str, name: str) -> int (returns id)
     - get_api_key_by_hash(conn, key_hash: str) -> Optional[dict]
     - get_api_key_by_id(conn, key_id: int) -> Optional[dict]
     - update_last_used(conn, key_id: int) -> None
     - deactivate_api_key(conn, key_id: int) -> None
     - list_api_keys(conn) -> list[dict]

3. Use the in-memory database fixture from conftest.py for tests.

## VERIFICATION:

4. Run tests: uv run pytest tests/test_db_api_keys.py -v
5. Run linter: uv run ruff check src/hikuweb/db/api_keys.py tests/test_db_api_keys.py
6. Format code: uv run ruff format src/hikuweb/db/api_keys.py tests/test_db_api_keys.py
7. ALL tests must pass before moving to Prompt 6

Remember: ABOUTME comments, type annotations. Return dicts from queries for flexibility.
```

---

## PROMPT 6: Extraction Logs Table

**Goal**: Create extraction_logs table schema and CRUD operations

**Prerequisites**: Prompt 5 completed

**Builds on**: Prompt 5 (api_keys table pattern established)

**Output**:
- `src/hikuweb/db/extraction_logs.py`
- `tests/test_db_extraction_logs.py`
- All tests passing

```text
You are continuing to build hikuweb. Database connection and api_keys table from Prompts 4-5 exist.

TASK: Create extraction_logs table and CRUD operations

## TDD WORKFLOW (Follow this exact order):

STEP 1: Write ALL tests first (they will fail - this is expected)
STEP 2: Run tests to confirm they fail: uv run pytest tests/test_db_extraction_logs.py -v
STEP 3: Implement the code to make tests pass
STEP 4: Run tests again to confirm they pass
STEP 5: Refactor if needed (keep tests green)
STEP 6: Run ruff check and format

## TEST SPECIFICATIONS:

1. Create tests/test_db_extraction_logs.py with tests for:
   - create_extraction_logs_table() creates the table
   - insert_extraction_log() stores a new log entry
   - get_logs_by_api_key() retrieves logs for a specific API key
   - get_logs_by_api_key() supports pagination (limit, offset)
   - count_logs_by_api_key() returns total count for an API key
   - get_usage_stats() returns aggregated stats (total extractions, success rate, avg duration)

## IMPLEMENTATION:

2. Create src/hikuweb/db/extraction_logs.py:
   - Table schema for extraction_logs:
     - id: INTEGER PRIMARY KEY AUTOINCREMENT
     - api_key_id: INTEGER NOT NULL (foreign key to api_keys)
     - url: TEXT NOT NULL (URL that was scraped)
     - schema_hash: TEXT NOT NULL (hash of the JSON schema used)
     - status: TEXT NOT NULL ("success", "error", "blocked")
     - error_message: TEXT (nullable, error details if failed)
     - created_at: TEXT NOT NULL (ISO timestamp)
     - duration_ms: INTEGER NOT NULL (extraction time in milliseconds)
   - Functions:
     - create_extraction_logs_table(conn: DatabaseConnection) -> None
     - insert_extraction_log(conn, api_key_id: int, url: str, schema_hash: str, status: str, error_message: Optional[str], duration_ms: int) -> int
     - get_logs_by_api_key(conn, api_key_id: int, limit: int = 100, offset: int = 0) -> list[dict]
     - count_logs_by_api_key(conn, api_key_id: int) -> int
     - get_usage_stats(conn, api_key_id: int) -> dict (total, success_count, error_count, avg_duration_ms)

3. Use the in-memory database fixture from conftest.py for tests.

## VERIFICATION:

4. Run tests: uv run pytest tests/test_db_extraction_logs.py -v
5. Run linter: uv run ruff check src/hikuweb/db/extraction_logs.py tests/test_db_extraction_logs.py
6. Format code: uv run ruff format src/hikuweb/db/extraction_logs.py tests/test_db_extraction_logs.py
7. ALL tests must pass before moving to Prompt 7

Remember: ABOUTME comments, type annotations.
```

---

## PROMPT 7: API Key Service

**Goal**: Create service layer for API key operations (hashing, creation, validation)

**Prerequisites**: Prompt 6 completed

**Builds on**: Prompt 5-6 (database tables exist)

**Output**:
- `src/hikuweb/services/api_key_service.py`
- `tests/test_api_key_service.py`
- All tests passing

```text
You are continuing to build hikuweb. Database layer from Prompts 4-6 exists.

TASK: Create API key service with hashing and validation logic

## TDD WORKFLOW (Follow this exact order):

STEP 1: Write ALL tests first (they will fail - this is expected)
STEP 2: Run tests to confirm they fail: uv run pytest tests/test_api_key_service.py -v
STEP 3: Implement the code to make tests pass
STEP 4: Run tests again to confirm they pass
STEP 5: Refactor if needed (keep tests green)
STEP 6: Run ruff check and format

## TEST SPECIFICATIONS:

1. Create tests/test_api_key_service.py with tests for:
   - generate_api_key() returns a random key string (32 chars, alphanumeric)
   - hash_api_key() returns consistent SHA-256 hash for same input
   - hash_api_key() returns different hashes for different inputs
   - create_api_key() generates key, stores hash in DB, returns raw key
   - validate_api_key() returns key record if valid and active
   - validate_api_key() returns None if key doesn't exist
   - validate_api_key() returns None if key is inactive
   - validate_api_key() updates last_used_at on successful validation

## IMPLEMENTATION:

2. Create src/hikuweb/services/api_key_service.py:
   - Functions:
     - generate_api_key() -> str (use secrets module, 32 chars)
     - hash_api_key(raw_key: str) -> str (SHA-256 hex digest)
     - create_api_key(conn: DatabaseConnection, name: str) -> str (returns raw key)
     - validate_api_key(conn: DatabaseConnection, raw_key: str) -> Optional[dict]
   - The raw API key is only returned once at creation time
   - We only store the hash, never the raw key

3. Use the in-memory database fixture from conftest.py for tests.
   - Make sure to create the api_keys table in the fixture before tests run.

## VERIFICATION:

4. Run tests: uv run pytest tests/test_api_key_service.py -v
5. Run linter: uv run ruff check src/hikuweb/services/api_key_service.py tests/test_api_key_service.py
6. Format code: uv run ruff format src/hikuweb/services/api_key_service.py tests/test_api_key_service.py
7. ALL tests must pass before moving to Prompt 8

Remember: ABOUTME comments, type annotations. Use secrets module for secure random generation.
```

---

## PROMPT 8: Schema Translation - Primitives

**Goal**: Create JSON Schema to Pydantic translator for primitive types

**Prerequisites**: Prompt 7 completed

**Builds on**: Nothing specific, but fits in services layer

**Output**:
- `src/hikuweb/services/schema_translator.py`
- `tests/test_schema_translator.py`
- All tests passing

```text
You are continuing to build hikuweb. Services layer structure from Prompt 7 exists.

TASK: Create JSON Schema to Pydantic model translator - PRIMITIVE TYPES ONLY

## TDD WORKFLOW (Follow this exact order):

STEP 1: Write ALL tests first (they will fail - this is expected)
STEP 2: Run tests to confirm they fail: uv run pytest tests/test_schema_translator.py -v
STEP 3: Implement the code to make tests pass
STEP 4: Run tests again to confirm they pass
STEP 5: Refactor if needed (keep tests green)
STEP 6: Run ruff check and format

We use pydantic.create_model() to dynamically create Pydantic models from JSON Schema.

## TEST SPECIFICATIONS:

1. Create tests/test_schema_translator.py with tests for primitive types:
   - Translates {"type": "string"} to str field
   - Translates {"type": "integer"} to int field
   - Translates {"type": "number"} to float field
   - Translates {"type": "boolean"} to bool field
   - Handles required fields (no default, field is required)
   - Handles optional fields (default None)
   - Handles default values from schema
   - Generated model can validate data
   - Generated model rejects invalid data types
   - Empty schema creates empty model

## IMPLEMENTATION:

2. Create src/hikuweb/services/schema_translator.py:
   - Function: json_schema_to_pydantic(schema: dict, model_name: str = "DynamicModel") -> type[BaseModel]
   - Helper: _map_primitive_type(prop: dict) -> type
   - Type mapping:
     - "string" -> str
     - "integer" -> int
     - "number" -> float
     - "boolean" -> bool
     - unknown -> Any
   - Handle "required" array from schema to determine required vs optional fields
   - Handle "default" in property definitions

3. For now, DO NOT handle:
   - Arrays (type: "array") - next prompt
   - Nested objects (type: "object" with properties) - prompt after
   - $ref, anyOf, oneOf, allOf - out of MVP scope

## VERIFICATION:

4. Run tests: uv run pytest tests/test_schema_translator.py -v
5. Run linter: uv run ruff check src/hikuweb/services/schema_translator.py tests/test_schema_translator.py
6. Format code: uv run ruff format src/hikuweb/services/schema_translator.py tests/test_schema_translator.py
7. ALL tests must pass before moving to Prompt 9

Remember: ABOUTME comments, type annotations. Use pydantic.create_model().
```

---

## PROMPT 9: Schema Translation - Arrays

**Goal**: Extend schema translator to handle array types

**Prerequisites**: Prompt 8 completed

**Builds on**: Prompt 8 (primitive translation works)

**Output**:
- Updated `src/hikuweb/services/schema_translator.py`
- Updated `tests/test_schema_translator.py`
- All tests passing

```text
You are continuing to build hikuweb. Schema translator with primitives from Prompt 8 exists.

TASK: Extend JSON Schema to Pydantic translator to handle ARRAYS

## TDD WORKFLOW (Follow this exact order):

STEP 1: Write NEW tests first for arrays (they will fail - this is expected)
STEP 2: Run tests to confirm new tests fail: uv run pytest tests/test_schema_translator.py -v
STEP 3: Update the implementation to make new tests pass
STEP 4: Run ALL tests again to confirm they pass (including previous tests)
STEP 5: Refactor if needed (keep tests green)
STEP 6: Run ruff check and format

## TEST SPECIFICATIONS:

1. Add tests to tests/test_schema_translator.py for arrays:
   - Translates {"type": "array", "items": {"type": "string"}} to list[str]
   - Translates {"type": "array", "items": {"type": "integer"}} to list[int]
   - Translates {"type": "array", "items": {"type": "number"}} to list[float]
   - Translates {"type": "array", "items": {"type": "boolean"}} to list[bool]
   - Array without items specification defaults to list[Any]
   - Required array field works correctly
   - Optional array field defaults to None (not empty list)
   - Generated model validates array data correctly
   - Generated model rejects non-array data for array fields

## IMPLEMENTATION:

2. Update src/hikuweb/services/schema_translator.py:
   - Update _map_primitive_type() to handle "array" type
   - When type is "array", look at "items" to determine inner type
   - Use typing.List or list[] for the type annotation
   - Import List from typing if needed

3. DO NOT handle nested objects yet (arrays of objects) - next prompt.

## VERIFICATION:

4. Run ALL tests: uv run pytest tests/test_schema_translator.py -v
5. Run linter: uv run ruff check src/hikuweb/services/schema_translator.py tests/test_schema_translator.py
6. Format code: uv run ruff format src/hikuweb/services/schema_translator.py tests/test_schema_translator.py
7. ALL tests must pass (including previous primitive tests) before moving to Prompt 10

Remember: ABOUTME comments, type annotations. Build incrementally on existing code.
```

---

## PROMPT 10: Schema Translation - Nested Objects

**Goal**: Extend schema translator to handle nested objects

**Prerequisites**: Prompt 9 completed

**Builds on**: Prompt 9 (arrays work)

**Output**:
- Updated `src/hikuweb/services/schema_translator.py`
- Updated `tests/test_schema_translator.py`
- All tests passing

```text
You are continuing to build hikuweb. Schema translator with primitives and arrays from Prompts 8-9 exists.

TASK: Extend JSON Schema to Pydantic translator to handle NESTED OBJECTS

## TDD WORKFLOW (Follow this exact order):

STEP 1: Write NEW tests first for nested objects (they will fail - this is expected)
STEP 2: Run tests to confirm new tests fail: uv run pytest tests/test_schema_translator.py -v
STEP 3: Update the implementation to make new tests pass
STEP 4: Run ALL tests again to confirm they pass (including previous tests)
STEP 5: Refactor if needed (keep tests green)
STEP 6: Run ruff check and format

## TEST SPECIFICATIONS:

1. Add tests to tests/test_schema_translator.py for nested objects:
   - Translates nested object property to nested Pydantic model
   - Handles deeply nested objects (2+ levels)
   - Handles arrays of objects: {"type": "array", "items": {"type": "object", "properties": {...}}}
   - Required nested object field works correctly
   - Optional nested object field defaults to None
   - Generated model validates nested data correctly
   - Generated model rejects invalid nested data

   Example schema to test:
   {
     "type": "object",
     "properties": {
       "name": {"type": "string"},
       "address": {
         "type": "object",
         "properties": {
           "street": {"type": "string"},
           "city": {"type": "string"}
         },
         "required": ["street"]
       },
       "tags": {
         "type": "array",
         "items": {
           "type": "object",
           "properties": {
             "name": {"type": "string"},
             "value": {"type": "integer"}
           }
         }
       }
     },
     "required": ["name"]
   }

## IMPLEMENTATION:

2. Update src/hikuweb/services/schema_translator.py:
   - Handle "object" type by recursively calling json_schema_to_pydantic()
   - Generate unique model names for nested objects (e.g., "ParentModel_fieldname")
   - Handle arrays of objects by combining array and object logic

## VERIFICATION:

3. Run ALL tests: uv run pytest tests/test_schema_translator.py -v
4. Run linter: uv run ruff check src/hikuweb/services/schema_translator.py tests/test_schema_translator.py
5. Format code: uv run ruff format src/hikuweb/services/schema_translator.py tests/test_schema_translator.py
6. ALL tests must pass (including previous tests) before moving to Prompt 11

Remember: ABOUTME comments, type annotations. Recursive model creation is the key pattern here.
```

---

## PROMPT 11: robots.txt Service

**Goal**: Create service to fetch, parse, and check robots.txt

**Prerequisites**: Prompt 10 completed

**Builds on**: Prompt 3 (config for cache TTL)

**Output**:
- `src/hikuweb/services/robots.py`
- `tests/test_robots.py`
- All tests passing

```text
You are continuing to build hikuweb. Config module from Prompt 3 exists.

TASK: Create robots.txt service with fetching, parsing, and caching

## TDD WORKFLOW (Follow this exact order):

STEP 1: Write ALL tests first (they will fail - this is expected)
STEP 2: Run tests to confirm they fail: uv run pytest tests/test_robots.py -v
STEP 3: Implement the code to make tests pass
STEP 4: Run tests again to confirm they pass
STEP 5: Refactor if needed (keep tests green)
STEP 6: Run ruff check and format

## TEST SPECIFICATIONS:

1. Create tests/test_robots.py with tests for:
   - parse_robots_txt() correctly parses User-agent and Disallow rules
   - parse_robots_txt() handles multiple User-agent sections
   - parse_robots_txt() handles wildcard User-agent (*)
   - is_path_allowed() returns True for allowed paths
   - is_path_allowed() returns False for disallowed paths
   - is_path_allowed() handles wildcard patterns in Disallow
   - is_path_allowed() defaults to True if no matching rules
   - RobotsChecker caches results with TTL
   - RobotsChecker refreshes cache after TTL expires
   - RobotsChecker handles missing robots.txt (assume all allowed)
   - RobotsChecker handles network errors gracefully (assume all allowed)
   - check_url() extracts domain and path correctly

## IMPLEMENTATION:

2. Create src/hikuweb/services/robots.py:
   - Class: RobotsChecker
     - __init__(self, cache_ttl_seconds: int = 3600)
     - _cache: dict[str, tuple[dict, float]] (domain -> (rules, timestamp))
     - async fetch_robots_txt(domain: str) -> Optional[str]
     - parse_robots_txt(content: str) -> dict (user_agent -> list of disallowed paths)
     - is_path_allowed(rules: dict, path: str, user_agent: str = "*") -> bool
     - async check_url(url: str) -> tuple[bool, Optional[str]] (allowed, reason)
     - _is_cache_valid(domain: str) -> bool
   - Use httpx for async HTTP requests
   - Cache robots.txt content in memory with TTL
   - Our user agent: "hikuweb/0.1"

3. For testing HTTP calls, use unittest.mock to mock httpx responses.

## VERIFICATION:

4. Run tests: uv run pytest tests/test_robots.py -v
5. Run linter: uv run ruff check src/hikuweb/services/robots.py tests/test_robots.py
6. Format code: uv run ruff format src/hikuweb/services/robots.py tests/test_robots.py
7. ALL tests must pass before moving to Prompt 12

Remember: ABOUTME comments, type annotations. Handle edge cases gracefully.
```

---

## PROMPT 12: Rate Limiter Service

**Goal**: Create per-domain rate limiter

**Prerequisites**: Prompt 11 completed

**Builds on**: Prompt 3 (config for rate limit settings)

**Output**:
- `src/hikuweb/services/rate_limiter.py`
- `tests/test_rate_limiter.py`
- All tests passing

```text
You are continuing to build hikuweb. Config module from Prompt 3 exists.

TASK: Create per-domain rate limiter service

## TDD WORKFLOW (Follow this exact order):

STEP 1: Write ALL tests first (they will fail - this is expected)
STEP 2: Run tests to confirm they fail: uv run pytest tests/test_rate_limiter.py -v
STEP 3: Implement the code to make tests pass
STEP 4: Run tests again to confirm they pass
STEP 5: Refactor if needed (keep tests green)
STEP 6: Run ruff check and format

## TEST SPECIFICATIONS:

1. Create tests/test_rate_limiter.py with tests for:
   - RateLimiter allows first request to a domain
   - RateLimiter blocks rapid successive requests to same domain
   - RateLimiter allows requests after waiting for rate limit period
   - RateLimiter tracks different domains independently
   - RateLimiter.acquire() returns True if allowed, False if blocked
   - RateLimiter.wait_time() returns seconds until next allowed request
   - RateLimiter handles domain extraction from URLs correctly
   - RateLimiter cleans up old entries to prevent memory leaks

## IMPLEMENTATION:

2. Create src/hikuweb/services/rate_limiter.py:
   - Class: DomainRateLimiter
     - __init__(self, requests_per_second: float = 1.0)
     - _last_request: dict[str, float] (domain -> timestamp)
     - _lock: threading.Lock (for thread safety)
     - extract_domain(url: str) -> str
     - acquire(url: str) -> bool (True if request allowed)
     - wait_time(url: str) -> float (seconds until next request allowed)
     - cleanup(max_age_seconds: float = 3600) -> int (remove old entries, return count)
   - Use simple token bucket algorithm: one request per (1/requests_per_second) seconds per domain
   - Thread-safe with lock

## VERIFICATION:

3. Run tests: uv run pytest tests/test_rate_limiter.py -v
4. Run linter: uv run ruff check src/hikuweb/services/rate_limiter.py tests/test_rate_limiter.py
5. Format code: uv run ruff format src/hikuweb/services/rate_limiter.py tests/test_rate_limiter.py
6. ALL tests must pass before moving to Prompt 13

Remember: ABOUTME comments, type annotations. Thread safety is important.
```

---

## PROMPT 13: FastAPI App + Health Endpoint

**Goal**: Create FastAPI application skeleton with health endpoint

**Prerequisites**: Prompt 12 completed

**Builds on**: Prompt 3 (config), Prompt 4 (database connection)

**Output**:
- `src/hikuweb/main.py`
- `src/hikuweb/api/routes.py`
- `tests/test_api_health.py`
- All tests passing

```text
You are continuing to build hikuweb. Config and database modules from Prompts 3-6 exist.

TASK: Create FastAPI application skeleton with health endpoint

## TDD WORKFLOW (Follow this exact order):

STEP 1: Write ALL tests first (they will fail - this is expected)
STEP 2: Run tests to confirm they fail: uv run pytest tests/test_api_health.py -v
STEP 3: Implement the code to make tests pass
STEP 4: Run tests again to confirm they pass
STEP 5: Refactor if needed (keep tests green)
STEP 6: Run ruff check and format

## TEST SPECIFICATIONS:

1. Create tests/test_api_health.py with tests for:
   - GET /health returns 200 status
   - GET /health returns {"status": "healthy", "version": "0.1.0"}
   - Health endpoint is accessible without authentication

## IMPLEMENTATION:

2. Create src/hikuweb/api/routes.py:
   - Create APIRouter instance
   - Define GET /health endpoint
   - Return HealthResponse model with status and version

3. Create src/hikuweb/main.py:
   - Create FastAPI app instance with title, description, version
   - Include router from routes.py
   - Add startup event to initialize database tables (create if not exist)
   - Add CORS middleware (allow all origins for now - MVP)
   - Create lifespan context manager for startup/shutdown

4. Update tests/conftest.py:
   - Add fixture for FastAPI TestClient
   - Use httpx AsyncClient for async tests if needed

## VERIFICATION:

5. Run tests: uv run pytest tests/test_api_health.py -v
6. Run linter: uv run ruff check src/hikuweb/main.py src/hikuweb/api/ tests/test_api_health.py
7. Format code: uv run ruff format src/hikuweb/main.py src/hikuweb/api/ tests/test_api_health.py
8. ALL tests must pass before moving to Prompt 14

9. Manual verification - app runs:
   - uv run uvicorn hikuweb.main:app --reload
   - Check http://localhost:8000/health
   - Check http://localhost:8000/docs (OpenAPI)

Remember: ABOUTME comments, type annotations. Use Pydantic models for request/response.
```

---

## PROMPT 14: Authentication Dependency

**Goal**: Create API key authentication as FastAPI dependency

**Prerequisites**: Prompt 13 completed

**Builds on**: Prompt 7 (API key service), Prompt 13 (FastAPI app)

**Output**:
- `src/hikuweb/api/dependencies.py`
- `tests/test_api_auth.py`
- All tests passing

```text
You are continuing to build hikuweb. API key service from Prompt 7 and FastAPI app from Prompt 13 exist.

TASK: Create API key authentication as FastAPI dependency

## TDD WORKFLOW (Follow this exact order):

STEP 1: Write ALL tests first (they will fail - this is expected)
STEP 2: Run tests to confirm they fail: uv run pytest tests/test_api_auth.py -v
STEP 3: Implement the code to make tests pass
STEP 4: Run tests again to confirm they pass
STEP 5: Refactor if needed (keep tests green)
STEP 6: Run ruff check and format

## TEST SPECIFICATIONS:

1. Create tests/test_api_auth.py with tests for:
   - Request without X-API-Key header returns 401
   - Request with invalid API key returns 401
   - Request with inactive API key returns 401
   - Request with valid API key succeeds
   - Auth dependency injects api_key_record into route handlers
   - Error response includes appropriate error message

## IMPLEMENTATION:

2. Create src/hikuweb/api/dependencies.py:
   - get_db() dependency: yields database connection
   - get_api_key() dependency:
     - Reads X-API-Key header
     - Validates against database using api_key_service
     - Returns api key record dict if valid
     - Raises HTTPException(401) if invalid
   - Define security scheme for OpenAPI docs (APIKeyHeader)

3. Create a simple protected test endpoint in routes.py:
   - GET /auth-test that requires authentication
   - Returns {"authenticated": true, "key_name": "<name from record>"}
   - This is just for testing auth - can be removed later or kept for debugging

4. Update tests/conftest.py:
   - Add fixture to create test API key in database
   - Add fixture for authenticated TestClient (with X-API-Key header)

## VERIFICATION:

5. Run tests: uv run pytest tests/test_api_auth.py -v
6. Run linter: uv run ruff check src/hikuweb/api/dependencies.py tests/test_api_auth.py
7. Format code: uv run ruff format src/hikuweb/api/dependencies.py tests/test_api_auth.py
8. ALL tests must pass before moving to Prompt 15

Remember: ABOUTME comments, type annotations. Use FastAPI's Depends() for dependency injection.
```

---

## PROMPT 15: Extract Endpoint

**Goal**: Create POST /extract endpoint with all services wired together

**Prerequisites**: Prompt 14 completed

**Builds on**: All previous prompts (schema translator, robots, rate limiter, auth)

**Output**:
- Updated `src/hikuweb/api/routes.py`
- `src/hikuweb/services/extraction.py`
- `tests/test_api_extract.py`
- All tests passing

```text
You are continuing to build hikuweb. All services from Prompts 7-12 and FastAPI app from Prompts 13-14 exist.

TASK: Create POST /extract endpoint with all services wired together

## TDD WORKFLOW (Follow this exact order):

STEP 1: Write ALL tests first (they will fail - this is expected)
STEP 2: Run tests to confirm they fail: uv run pytest tests/test_api_extract.py -v
STEP 3: Implement the code to make tests pass
STEP 4: Run tests again to confirm they pass
STEP 5: Refactor if needed (keep tests green)
STEP 6: Run ruff check and format

## TEST SPECIFICATIONS:

1. Create tests/test_api_extract.py with tests for:
   - POST /extract without auth returns 401
   - POST /extract with missing url returns 422 validation error
   - POST /extract with missing schema returns 422 validation error
   - POST /extract with invalid JSON schema returns 400
   - POST /extract with robots.txt blocked URL returns 403
   - POST /extract with rate limited domain returns 429
   - POST /extract with valid request returns extracted data
   - Response includes extraction metadata (cached, duration_ms)
   - Extraction is logged to database
   - Use mocked hikugen for these tests (don't hit real LLM)

## IMPLEMENTATION:

2. Create src/hikuweb/services/extraction.py:
   - Class: ExtractionService
     - __init__(self, openrouter_api_key: str, db_path: str)
     - Creates HikuExtractor instance internally
     - async extract(url: str, schema: dict) -> dict
       - Converts JSON schema to Pydantic model using schema_translator
       - Calls hikugen's extract() method
       - Returns extracted data as dict
   - Handle hikugen exceptions and convert to appropriate errors

3. Update src/hikuweb/api/routes.py:
   - Add POST /extract endpoint
   - Request model: ExtractRequest(url: str, schema: dict, cache_key: Optional[str])
   - Response model: ExtractResponse(data: dict, cached: bool, duration_ms: int)
   - Wire together:
     - Auth dependency (get API key)
     - Robots checker (verify URL allowed)
     - Rate limiter (check/acquire)
     - Schema translator (convert schema)
     - Extraction service (call hikugen)
     - Logging (record to database)

4. Add dependencies to dependencies.py:
   - get_robots_checker() -> RobotsChecker (singleton)
   - get_rate_limiter() -> DomainRateLimiter (singleton)
   - get_extraction_service() -> ExtractionService (singleton)

## VERIFICATION:

5. Run tests: uv run pytest tests/test_api_extract.py -v
6. Run linter: uv run ruff check src/hikuweb/services/extraction.py src/hikuweb/api/ tests/test_api_extract.py
7. Format code: uv run ruff format src/hikuweb/services/extraction.py src/hikuweb/api/ tests/test_api_extract.py
8. ALL tests must pass before moving to Prompt 16

Remember: ABOUTME comments, type annotations. This is the main endpoint - test thoroughly!
```

---

## PROMPT 16: Usage Endpoint

**Goal**: Create GET /usage endpoint for usage statistics

**Prerequisites**: Prompt 15 completed

**Builds on**: Prompt 6 (extraction_logs), Prompt 14 (auth)

**Output**:
- Updated `src/hikuweb/api/routes.py`
- `tests/test_api_usage.py`
- All tests passing

```text
You are continuing to build hikuweb. Database and auth from previous prompts exist.

TASK: Create GET /usage endpoint for usage statistics

## TDD WORKFLOW (Follow this exact order):

STEP 1: Write ALL tests first (they will fail - this is expected)
STEP 2: Run tests to confirm they fail: uv run pytest tests/test_api_usage.py -v
STEP 3: Implement the code to make tests pass
STEP 4: Run tests again to confirm they pass
STEP 5: Refactor if needed (keep tests green)
STEP 6: Run ruff check and format

## TEST SPECIFICATIONS:

1. Create tests/test_api_usage.py with tests for:
   - GET /usage without auth returns 401
   - GET /usage with auth returns usage stats
   - Response includes total_extractions count
   - Response includes success_count
   - Response includes error_count  
   - Response includes average_duration_ms
   - Response includes recent_extractions list (last 10)
   - Stats are scoped to the authenticated API key only

## IMPLEMENTATION:

2. Update src/hikuweb/api/routes.py:
   - Add GET /usage endpoint
   - Response model: UsageResponse
     - total_extractions: int
     - success_count: int
     - error_count: int
     - blocked_count: int
     - average_duration_ms: Optional[float]
     - recent_extractions: list[ExtractionLogSummary]
   - ExtractionLogSummary model:
     - url: str
     - status: str
     - created_at: str
     - duration_ms: int
   - Query extraction_logs table filtered by api_key_id

## VERIFICATION:

3. Run tests: uv run pytest tests/test_api_usage.py -v
4. Run linter: uv run ruff check src/hikuweb/api/routes.py tests/test_api_usage.py
5. Format code: uv run ruff format src/hikuweb/api/routes.py tests/test_api_usage.py
6. ALL tests must pass before moving to Prompt 17

Remember: ABOUTME comments, type annotations. Keep response models clean.
```

---

## PROMPT 17: hikugen Integration & E2E Tests

**Goal**: Wire up real hikugen, create integration tests, polish

**Prerequisites**: Prompt 16 completed

**Builds on**: All previous prompts

**Output**:
- `tests/test_integration.py`
- Any necessary fixes
- All tests passing
- Working end-to-end flow

```text
You are continuing to build hikuweb. All components from Prompts 1-16 exist.

TASK: Complete hikugen integration and create end-to-end tests

This is the final prompt. Make sure everything works together.

## TDD WORKFLOW (Follow this exact order):

STEP 1: Write integration tests first (they will fail - this is expected)
STEP 2: Run tests to confirm they fail: uv run pytest tests/test_integration.py -v
STEP 3: Fix any integration issues to make tests pass
STEP 4: Run ALL tests to confirm everything works together
STEP 5: Polish and refactor as needed
STEP 6: Run ruff check and format on entire codebase

## TEST SPECIFICATIONS:

1. Create tests/test_integration.py with end-to-end tests:
   - Full extraction flow: auth -> robots check -> rate limit -> extract -> log
   - Test with a real (simple) website that won't change often
     - Consider using httpbin.org or a static test page
     - Or create a simple test HTML fixture
   - Verify extracted data matches expected schema
   - Verify extraction is logged correctly
   - Verify usage stats update after extraction
   - Test error cases end-to-end (blocked URL, rate limit, invalid schema)
   
   NOTE: These tests may need OPENROUTER_API_KEY to run.
   Mark them with @pytest.mark.integration and skip if env var not set.

## IMPLEMENTATION:

2. Review and fix any integration issues:
   - Ensure hikugen is properly imported and works
   - Ensure database connections are handled correctly (no leaks)
   - Ensure async/sync boundaries are handled correctly
   - Ensure error messages are user-friendly

3. Polish:
   - Add proper error handling for all edge cases
   - Ensure OpenAPI docs are complete and accurate
   - Add response examples to route docstrings
   - Verify all ABOUTME comments are in place

## VERIFICATION:

4. Run ALL tests: uv run pytest -v
5. Run integration tests specifically: uv run pytest tests/test_integration.py -v
6. Run linter: uv run ruff check src/ tests/
7. Format code: uv run ruff format src/ tests/

8. Manual testing:
   - Start server: uv run uvicorn hikuweb.main:app --reload
   - Create an API key manually (via Python REPL or add a script)
   - Test /extract endpoint with real request
   - Check /usage endpoint

9. Final checklist:
   - [ ] All tests pass
   - [ ] No linting errors (uv run ruff check src/ tests/)
   - [ ] Code is formatted (uv run ruff format src/ tests/)
   - [ ] OpenAPI docs work (http://localhost:8000/docs)
   - [ ] Health endpoint works
   - [ ] Auth works
   - [ ] Extract endpoint works
   - [ ] Usage endpoint works

Remember: This is MVP completion. Document any known limitations or future improvements.
```

---

## Appendix: Environment Variables

```bash
# Required
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Optional (with defaults)
DATABASE_PATH=hikuweb.db
RATE_LIMIT_REQUESTS_PER_SECOND=1.0
ROBOTS_CACHE_TTL_SECONDS=3600
```

---

## Appendix: API Reference (Target State)

### GET /health
No authentication required.

**Response 200:**
```json
{
  "status": "healthy",
  "version": "0.1.0"
}
```

### POST /extract
Requires `X-API-Key` header.

**Request:**
```json
{
  "url": "https://example.com/page",
  "schema": {
    "type": "object",
    "properties": {
      "title": {"type": "string"},
      "price": {"type": "number"}
    },
    "required": ["title"]
  },
  "cache_key": "optional-custom-key"
}
```

**Response 200:**
```json
{
  "data": {
    "title": "Example Product",
    "price": 29.99
  },
  "cached": false,
  "duration_ms": 1234
}
```

**Error Responses:**
- 401: Invalid or missing API key
- 403: URL blocked by robots.txt
- 422: Validation error (missing/invalid fields)
- 429: Rate limit exceeded
- 500: Extraction failed

### GET /usage
Requires `X-API-Key` header.

**Response 200:**
```json
{
  "total_extractions": 150,
  "success_count": 142,
  "error_count": 5,
  "blocked_count": 3,
  "average_duration_ms": 2150.5,
  "recent_extractions": [
    {
      "url": "https://example.com/page",
      "status": "success",
      "created_at": "2024-01-15T10:30:00Z",
      "duration_ms": 1850
    }
  ]
}
```

---

## Notes for Implementation

1. **TDD is mandatory**: Write tests before implementation for each prompt.

2. **Incremental commits**: Commit after each prompt is complete and all tests pass.

3. **No orphaned code**: Every piece of code must be tested and integrated before moving on.

4. **Error handling**: Convert hikugen exceptions to appropriate HTTP errors with user-friendly messages.

5. **Thread safety**: SQLite needs care with concurrent access. Consider connection pooling or write locking.

6. **Async considerations**: FastAPI is async, but hikugen is sync. Use `run_in_executor` if needed.

7. **Testing hikugen**: Mock hikugen in unit tests. Only use real hikugen in integration tests.
