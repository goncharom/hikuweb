# ABOUTME: API route definitions for hikuweb.
# ABOUTME: Defines health, extract, and usage endpoints.
# ruff: noqa: B008

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from hikuweb.api.dependencies import get_api_key

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
