# ABOUTME: API route definitions for hikuweb.
# ABOUTME: Defines health, extract, and usage endpoints.
# ruff: noqa: B008

import hashlib
import time

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, HttpUrl

from hikuweb.api.dependencies import (
    get_api_key,
    get_db,
    get_extraction_service,
    get_rate_limiter,
    get_robots_checker,
)
from hikuweb.db.connection import DatabaseConnection
from hikuweb.db.extraction_logs import get_logs_by_api_key, get_usage_stats, insert_extraction_log
from hikuweb.services.extraction import ExtractionService
from hikuweb.services.rate_limiter import DomainRateLimiter
from hikuweb.services.robots import RobotsChecker

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model.

    Attributes:
        status: Service health status (always 'healthy' when responding).
        version: Current API version.
    """

    status: str
    version: str


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Health check endpoint.

    Returns service status and version without requiring authentication.
    Useful for monitoring, load balancers, and container orchestration.

    Returns:
        HealthResponse: Current service status and version.

    Example:
        >>> GET /health
        {"status": "healthy", "version": "0.1.0"}
    """
    return HealthResponse(status="healthy", version="0.1.0")


class AuthTestResponse(BaseModel):
    """Auth test endpoint response model.

    Attributes:
        authenticated: Whether authentication succeeded.
        key_name: Name of the authenticated API key.
    """

    authenticated: bool
    key_name: str


@router.get("/auth-test", response_model=AuthTestResponse)
def auth_test(api_key: dict = Depends(get_api_key)) -> AuthTestResponse:
    """Test endpoint for API key authentication.

    Requires valid X-API-Key header. Used for testing authentication dependency.

    Args:
        api_key: API key record injected by get_api_key dependency.

    Returns:
        AuthTestResponse: Authentication status and key name.

    Raises:
        HTTPException: 401 if API key missing, invalid, or inactive.
    """
    return AuthTestResponse(authenticated=True, key_name=api_key["name"])


class ExtractRequest(BaseModel):
    """Request model for POST /extract endpoint.

    Attributes:
        url: Web page URL to extract from (must be valid HTTP/HTTPS URL).
        schema_: JSON Schema definition for extraction structure (aliased as 'schema' in JSON).
    """

    model_config = {"populate_by_name": True}

    url: HttpUrl
    schema_: dict = Field(alias="schema")


class ExtractResponse(BaseModel):
    """Response model for POST /extract endpoint.

    Attributes:
        data: Extracted data matching the provided schema.
        duration_ms: Time taken to perform extraction in milliseconds.
    """

    data: dict
    duration_ms: int


@router.post("/extract", response_model=ExtractResponse)
async def extract(
    request: ExtractRequest,
    api_key: dict = Depends(get_api_key),
    db: DatabaseConnection = Depends(get_db),
    robots_checker: RobotsChecker = Depends(get_robots_checker),
    rate_limiter: DomainRateLimiter = Depends(get_rate_limiter),
    extraction_service: ExtractionService = Depends(get_extraction_service),
) -> ExtractResponse:
    """Extract structured data from URL using JSON schema.

    Requires authentication via X-API-Key header. Performs robots.txt
    compliance checking, rate limiting, and structured extraction using hikugen.

    Args:
        request: Extraction request with URL and JSON schema.
        api_key: API key record injected by authentication dependency.
        db: Database connection for logging.
        robots_checker: Robots.txt compliance checker.
        rate_limiter: Per-domain rate limiter.
        extraction_service: Extraction service wrapper for hikugen.

    Returns:
        ExtractResponse: Extracted data and metadata.

    Raises:
        HTTPException: 400 if schema invalid, 403 if robots blocked, 429 if rate limited, 500 if extraction fails.
    """
    start_time = time.time()
    url_str = str(request.url)
    schema_hash = hashlib.sha256(str(request.schema_).encode()).hexdigest()

    # Validate schema is not empty
    if not request.schema_ or (
        request.schema_.get("type") == "object" and not request.schema_.get("properties")
    ):
        raise HTTPException(status_code=400, detail="Schema must not be empty")

    # Check robots.txt compliance
    allowed, reason = await robots_checker.check_url(url_str)
    if not allowed:
        duration_ms = int((time.time() - start_time) * 1000)
        insert_extraction_log(
            db,
            api_key_id=api_key["id"],
            url=url_str,
            schema_hash=schema_hash,
            status="blocked",
            error_message=reason,
            duration_ms=duration_ms,
        )
        db.commit()
        raise HTTPException(status_code=403, detail=f"Blocked by robots.txt: {reason}")

    # Check rate limit
    if not rate_limiter.acquire(url_str):
        raise HTTPException(status_code=429, detail="Rate limit exceeded for this domain")

    # Perform extraction
    try:
        extracted_data = extraction_service.extract(url_str, request.schema_)
        duration_ms = int((time.time() - start_time) * 1000)

        # Log successful extraction
        insert_extraction_log(
            db,
            api_key_id=api_key["id"],
            url=url_str,
            schema_hash=schema_hash,
            status="success",
            error_message=None,
            duration_ms=duration_ms,
        )
        db.commit()

        return ExtractResponse(data=extracted_data, duration_ms=duration_ms)
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)

        # Log error extraction
        insert_extraction_log(
            db,
            api_key_id=api_key["id"],
            url=url_str,
            schema_hash=schema_hash,
            status="error",
            error_message=str(e),
            duration_ms=duration_ms,
        )
        db.commit()

        raise HTTPException(status_code=500, detail=f"Extraction failed: {e}") from e


class ExtractionLogSummary(BaseModel):
    """Summary of an extraction log entry.

    Attributes:
        url: Web page URL that was extracted.
        status: Extraction status (success, error, blocked).
        created_at: ISO timestamp when extraction was performed.
        duration_ms: Time taken for extraction in milliseconds.
    """

    url: str
    status: str
    created_at: str
    duration_ms: int


class UsageResponse(BaseModel):
    """Response model for GET /usage endpoint.

    Attributes:
        total_extractions: Total number of extraction attempts.
        success_count: Number of successful extractions.
        error_count: Number of failed extractions.
        blocked_count: Number of extractions blocked by robots.txt.
        average_duration_ms: Average extraction duration (nullable if no extractions).
        recent_extractions: List of recent extraction log summaries.
    """

    total_extractions: int
    success_count: int
    error_count: int
    blocked_count: int
    average_duration_ms: float | None
    recent_extractions: list[ExtractionLogSummary]


@router.get("/usage", response_model=UsageResponse)
def get_usage(
    api_key: dict = Depends(get_api_key),
    db: DatabaseConnection = Depends(get_db),
) -> UsageResponse:
    """Get usage statistics for authenticated API key.

    Requires authentication via X-API-Key header. Returns aggregated
    statistics and recent extraction history.

    Args:
        api_key: API key record injected by authentication dependency.
        db: Database connection for querying logs.

    Returns:
        UsageResponse: Usage statistics and recent extractions.

    Raises:
        HTTPException: 401 if API key missing, invalid, or inactive.
    """
    # Get aggregated statistics
    stats = get_usage_stats(db, api_key["id"])

    # Get recent extractions (last 10)
    recent_logs = get_logs_by_api_key(db, api_key["id"], limit=10)

    return UsageResponse(
        total_extractions=stats["total"],
        success_count=stats["success_count"],
        error_count=stats["error_count"],
        blocked_count=stats["blocked_count"],
        average_duration_ms=stats["avg_duration_ms"],
        recent_extractions=[ExtractionLogSummary(**log) for log in recent_logs],
    )
