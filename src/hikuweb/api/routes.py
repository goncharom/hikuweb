# ABOUTME: API route definitions for hikuweb.
# ABOUTME: Defines health, extract, and usage endpoints.

from fastapi import APIRouter
from pydantic import BaseModel

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
