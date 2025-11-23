"""
Main FastAPI application module.

Production-ready FastAPI application with comprehensive middleware,
health checks, error handling, and observability.
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.error_handlers import register_exception_handlers
from app.infrastructure.cache import redis_client
from app.infrastructure.database.connection import DatabaseManager
from app.presentation.api.v1 import api_router
from app.presentation.middleware import (
    ErrorHandlingMiddleware,
    LoggingMiddleware,
    RequestIDMiddleware,
    TimingMiddleware,
    setup_cors,
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle manager for the application.
    
    Handles startup and shutdown events for:
    - Database connections
    - Redis cache connections
    - Sentry integration (if configured)
    """
    # Startup
    logger.info("Starting HypertroQ Backend API...")
    
    # Initialize database
    try:
        db_manager = DatabaseManager()
        await db_manager.test_connection()
        logger.info("✓ Database connection established")
    except Exception as e:
        logger.error(f"✗ Database connection failed: {e}")
        raise
    
    # Initialize Redis
    try:
        await redis_client.connect()
        logger.info("✓ Redis connection established")
    except Exception as e:
        logger.error(f"✗ Redis connection failed: {e}")
        raise
    
    # Initialize Sentry (if configured)
    if hasattr(settings, 'SENTRY_DSN') and settings.SENTRY_DSN:
        try:
            import sentry_sdk
            sentry_sdk.init(
                dsn=settings.SENTRY_DSN,
                environment=getattr(settings, 'ENVIRONMENT', 'production'),
                traces_sample_rate=0.1,  # 10% of transactions for performance monitoring
            )
            logger.info("✓ Sentry error tracking initialized")
        except Exception as e:
            logger.warning(f"Sentry initialization failed: {e}")
    
    logger.info("🚀 Application startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down HypertroQ Backend API...")
    
    try:
        await redis_client.disconnect()
        logger.info("✓ Redis connection closed")
    except Exception as e:
        logger.error(f"Error closing Redis connection: {e}")
    
    try:
        await db_manager.dispose()
        logger.info("✓ Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database connections: {e}")
    
    logger.info("👋 Application shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="HypertroQ API",
    description="Science-based hypertrophy training platform - Progressive overload tracking and AI-powered workout optimization",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
    contact={
        "name": "HypertroQ Support",
        "url": "https://hypertroq.com",
        "email": "support@hypertroq.com",
    },
    license_info={
        "name": "Proprietary",
    },
)

# Register exception handlers
register_exception_handlers(app)

# Add middleware (order matters - first added is outermost)
setup_cors(app)  # CORS must be first
app.add_middleware(ErrorHandlingMiddleware)  # Catch all errors
app.add_middleware(RequestIDMiddleware)  # Track requests
app.add_middleware(TimingMiddleware)  # Performance monitoring
app.add_middleware(LoggingMiddleware)  # Log all requests

# Include API router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


# ============================================================================
# Root Endpoint
# ============================================================================

@app.get("/", tags=["root"])
async def root() -> dict[str, Any]:
    """
    Root endpoint returning API information.
    
    Returns:
        API metadata including version, documentation links, and status
    """
    return {
        "name": "HypertroQ API",
        "version": "1.0.0",
        "status": "operational",
        "message": "Welcome to HypertroQ - Science-based hypertrophy training platform",
        "documentation": {
            "interactive": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json",
        },
        "health_checks": {
            "status": "/health",
            "database": "/health/db",
            "cache": "/health/redis",
        },
    }


# ============================================================================
# Health Check Endpoints
# ============================================================================

@app.get("/health", tags=["health"])
async def health_check() -> dict[str, Any]:
    """
    Basic health check endpoint.
    
    Returns:
        System status and timestamp
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "hypertroq-backend",
        "version": "1.0.0",
    }


@app.get("/health/db", tags=["health"])
async def health_check_database() -> dict[str, Any]:
    """
    Database health check endpoint.
    
    Tests database connectivity by executing a simple query.
    
    Returns:
        Database connection status
    """
    try:
        db_manager = DatabaseManager()
        await db_manager.test_connection()
        return {
            "status": "healthy",
            "service": "database",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "service": "database",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )


@app.get("/health/redis", tags=["health"])
async def health_check_redis() -> dict[str, Any]:
    """
    Redis health check endpoint.
    
    Tests Redis connectivity by executing a PING command.
    
    Returns:
        Redis connection status
    """
    try:
        await redis_client.ping()
        return {
            "status": "healthy",
            "service": "redis",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "service": "redis",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )


# ============================================================================
# Application Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True,
    )
