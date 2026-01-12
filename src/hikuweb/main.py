# ABOUTME: FastAPI application entry point for hikuweb.
# ABOUTME: Configures app, middleware, and lifespan events.

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from hikuweb.api.routes import router
from hikuweb.config import get_settings
from hikuweb.db.api_keys import create_api_keys_table
from hikuweb.db.connection import get_db_connection
from hikuweb.db.extraction_logs import create_extraction_logs_table


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager.

    Handles startup and shutdown events:
    - Startup: Initialize database tables
    - Shutdown: Cleanup resources

    Args:
        app: FastAPI application instance.

    Yields:
        None during application runtime.
    """
    # Startup: initialize database tables
    settings = get_settings()
    with get_db_connection(settings.database_path) as conn:
        create_api_keys_table(conn)
        create_extraction_logs_table(conn)

    yield

    # Shutdown: cleanup (currently nothing to clean up)


app = FastAPI(
    title="hikuweb",
    description="REST API service for AI-powered web scraping with hikugen",
    version="0.1.0",
    lifespan=lifespan,
)

# Add CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for MVP
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Include API routes
app.include_router(router)
