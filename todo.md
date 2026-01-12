# hikuweb Implementation Progress

> Track progress through the 17-prompt TDD implementation plan

---

## Phase 1: Project Setup

- [ ] **Prompt 1**: Project Initialization
  - [ ] Create pyproject.toml with dependencies
  - [ ] Create folder structure (src/hikuweb, tests)
  - [ ] Create pytest.ini
  - [ ] Run `uv sync` and `uv run pytest`
  - [ ] Commit

- [ ] **Prompt 2**: Tooling Setup
  - [ ] Add ruff configuration to pyproject.toml
  - [ ] Create .pre-commit-config.yaml
  - [ ] Create AGENTS.md
  - [ ] Run `pre-commit install && pre-commit run --all-files`
  - [ ] Commit

---

## Phase 2: Configuration & Database

- [ ] **Prompt 3**: Configuration Management
  - [ ] Write tests/test_config.py (TDD: write tests first!)
  - [ ] Verify tests fail
  - [ ] Create src/hikuweb/config.py
  - [ ] Verify tests pass
  - [ ] Commit

- [ ] **Prompt 4**: Database Connection
  - [ ] Write tests/test_db_connection.py (TDD: write tests first!)
  - [ ] Verify tests fail
  - [ ] Create src/hikuweb/db/connection.py
  - [ ] Update tests/conftest.py with db fixture
  - [ ] Verify tests pass
  - [ ] Commit

- [ ] **Prompt 5**: API Keys Table
  - [ ] Write tests/test_db_api_keys.py (TDD: write tests first!)
  - [ ] Verify tests fail
  - [ ] Create src/hikuweb/db/api_keys.py
  - [ ] Verify tests pass
  - [ ] Commit

- [ ] **Prompt 6**: Extraction Logs Table
  - [ ] Write tests/test_db_extraction_logs.py (TDD: write tests first!)
  - [ ] Verify tests fail
  - [ ] Create src/hikuweb/db/extraction_logs.py
  - [ ] Verify tests pass
  - [ ] Commit

---

## Phase 3: Services

- [ ] **Prompt 7**: API Key Service
  - [ ] Write tests/test_api_key_service.py (TDD: write tests first!)
  - [ ] Verify tests fail
  - [ ] Create src/hikuweb/services/api_key_service.py
  - [ ] Verify tests pass
  - [ ] Commit

- [ ] **Prompt 8**: Schema Translation - Primitives
  - [ ] Write tests/test_schema_translator.py (TDD: write tests first!)
  - [ ] Verify tests fail
  - [ ] Create src/hikuweb/services/schema_translator.py
  - [ ] Verify tests pass
  - [ ] Commit

- [ ] **Prompt 9**: Schema Translation - Arrays
  - [ ] Add array tests to tests/test_schema_translator.py (TDD: write tests first!)
  - [ ] Verify new tests fail
  - [ ] Update src/hikuweb/services/schema_translator.py
  - [ ] Verify ALL tests pass
  - [ ] Commit

- [ ] **Prompt 10**: Schema Translation - Nested Objects
  - [ ] Add nested object tests to tests/test_schema_translator.py (TDD: write tests first!)
  - [ ] Verify new tests fail
  - [ ] Update src/hikuweb/services/schema_translator.py
  - [ ] Verify ALL tests pass
  - [ ] Commit

- [ ] **Prompt 11**: robots.txt Service
  - [ ] Write tests/test_robots.py (TDD: write tests first!)
  - [ ] Verify tests fail
  - [ ] Create src/hikuweb/services/robots.py
  - [ ] Verify tests pass
  - [ ] Commit

- [ ] **Prompt 12**: Rate Limiter Service
  - [ ] Write tests/test_rate_limiter.py (TDD: write tests first!)
  - [ ] Verify tests fail
  - [ ] Create src/hikuweb/services/rate_limiter.py
  - [ ] Verify tests pass
  - [ ] Commit

---

## Phase 4: API Layer

- [ ] **Prompt 13**: FastAPI App + Health Endpoint
  - [ ] Write tests/test_api_health.py (TDD: write tests first!)
  - [ ] Verify tests fail
  - [ ] Create src/hikuweb/main.py
  - [ ] Create src/hikuweb/api/routes.py
  - [ ] Update tests/conftest.py with TestClient fixture
  - [ ] Verify tests pass
  - [ ] Manual test: `uv run uvicorn hikuweb.main:app --reload`
  - [ ] Commit

- [ ] **Prompt 14**: Authentication Dependency
  - [ ] Write tests/test_api_auth.py (TDD: write tests first!)
  - [ ] Verify tests fail
  - [ ] Create src/hikuweb/api/dependencies.py
  - [ ] Add /auth-test endpoint to routes.py
  - [ ] Update tests/conftest.py with auth fixtures
  - [ ] Verify tests pass
  - [ ] Commit

- [ ] **Prompt 15**: Extract Endpoint
  - [ ] Write tests/test_api_extract.py (TDD: write tests first!)
  - [ ] Verify tests fail
  - [ ] Create src/hikuweb/services/extraction.py
  - [ ] Add POST /extract to routes.py
  - [ ] Add singleton dependencies to dependencies.py
  - [ ] Verify tests pass
  - [ ] Commit

- [ ] **Prompt 16**: Usage Endpoint
  - [ ] Write tests/test_api_usage.py (TDD: write tests first!)
  - [ ] Verify tests fail
  - [ ] Add GET /usage to routes.py
  - [ ] Verify tests pass
  - [ ] Commit

---

## Phase 5: Integration & Polish

- [ ] **Prompt 17**: hikugen Integration & E2E Tests
  - [ ] Write tests/test_integration.py (TDD: write tests first!)
  - [ ] Fix any integration issues
  - [ ] Run ALL tests: `uv run pytest -v`
  - [ ] Run linter: `uv run ruff check src/ tests/`
  - [ ] Format code: `uv run ruff format src/ tests/`
  - [ ] Manual testing with real hikugen
  - [ ] Commit

---

## Final Checklist

- [ ] All tests pass (`uv run pytest -v`)
- [ ] No linting errors (`uv run ruff check src/ tests/`)
- [ ] Code is formatted (`uv run ruff format src/ tests/`)
- [ ] OpenAPI docs work (http://localhost:8000/docs)
- [ ] All endpoints work:
  - [ ] GET /health
  - [ ] POST /extract
  - [ ] GET /usage
- [ ] All files have ABOUTME comments
- [ ] README created (if desired)

---

## Notes

- **TDD is MANDATORY**: Always write tests first, verify they fail, then implement
- **Commit after each prompt**: Small, incremental commits
- **Don't skip prompts**: Each builds on the previous one
