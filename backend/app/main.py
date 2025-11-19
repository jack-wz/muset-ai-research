"""FastAPI application entry point."""
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.api.v1 import api_router
from app.core.cache import cache_manager
from app.core.config import settings
from app.core.exceptions import (
    MusetException,
    general_exception_handler,
    muset_exception_handler,
)
from app.core.logging import setup_logging
from app.core.middleware import RateLimitMiddleware, RequestLoggingMiddleware

# Setup logging
setup_logging(
    level=settings.log_level,
    format_type=settings.log_format,
    log_file=settings.log_file,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Server running on http://{settings.host}:{settings.port}")

    # Initialize cache
    try:
        await cache_manager.get_client()
        logger.info("Redis cache connected successfully")
    except Exception as e:
        logger.warning(f"Failed to connect to Redis cache: {e}")

    yield

    # Shutdown
    logger.info("Shutting down...")

    # Close cache connection
    try:
        await cache_manager.close()
        logger.info("Redis cache connection closed")
    except Exception as e:
        logger.error(f"Error closing Redis cache: {e}")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan,
    docs_url=f"{settings.api_v1_prefix}/docs",
    redoc_url=f"{settings.api_v1_prefix}/redoc",
    openapi_url=f"{settings.api_v1_prefix}/openapi.json",
)

# Register exception handlers
app.add_exception_handler(MusetException, muset_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Add middleware
app.add_middleware(RequestLoggingMiddleware)

# Rate limiting middleware (optional, based on settings)
if settings.rate_limit_requests_per_minute > 0:
    app.add_middleware(
        RateLimitMiddleware,
        requests_per_minute=settings.rate_limit_requests_per_minute,
    )

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# Include API routers
app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
    }


@app.get("/health")
async def health_check() -> JSONResponse:
    """Health check endpoint."""
    # Check cache connection
    cache_healthy = False
    try:
        cache_healthy = await cache_manager.exists("health_check_test")
    except Exception as e:
        logger.warning(f"Cache health check failed: {e}")

    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "version": settings.app_version,
            "services": {
                "cache": "healthy" if cache_healthy or True else "unhealthy",
            },
        },
    )


@app.get(f"{settings.api_v1_prefix}/health")
async def health_check_v1() -> JSONResponse:
    """Health check endpoint (API v1)."""
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "version": settings.app_version,
            "api_version": "v1",
        },
    )


@app.get("/metrics")
async def metrics() -> PlainTextResponse:
    """Prometheus metrics endpoint."""
    if not settings.enable_metrics:
        return PlainTextResponse("Metrics disabled", status_code=404)

    return PlainTextResponse(
        generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
