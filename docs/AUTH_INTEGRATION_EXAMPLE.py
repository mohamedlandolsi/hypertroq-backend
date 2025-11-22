"""
Example integration of authentication routes into FastAPI application.

This demonstrates how to:
1. Initialize Redis connection
2. Register authentication routes
3. Add rate limit headers middleware
4. Handle Redis lifecycle
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.auth import router as auth_router
from app.infrastructure.cache.redis_client import redis_client
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Handles startup and shutdown events:
    - Connects to Redis on startup
    - Disconnects from Redis on shutdown
    """
    # Startup
    print("🚀 Starting application...")
    
    # Connect to Redis
    try:
        await redis_client.connect()
        print("✅ Connected to Redis")
    except Exception as e:
        print(f"⚠️  Redis connection failed: {e}")
        print("   Application will use in-memory fallback for rate limiting")
    
    yield
    
    # Shutdown
    print("👋 Shutting down application...")
    
    # Disconnect from Redis
    try:
        await redis_client.disconnect()
        print("✅ Disconnected from Redis")
    except Exception as e:
        print(f"⚠️  Redis disconnect failed: {e}")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="HypertroQ Backend API for hypertrophy training management",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_rate_limit_headers(request: Request, call_next):
    """
    Middleware to add rate limit headers to responses.
    
    The rate limiter stores headers in request.state.rate_limit_headers,
    and this middleware adds them to the response.
    """
    response = await call_next(request)
    
    # Add rate limit headers if set by rate limiter
    if hasattr(request.state, "rate_limit_headers"):
        for header, value in request.state.rate_limit_headers.items():
            response.headers[header] = value
    
    return response


@app.exception_handler(429)
async def rate_limit_handler(request: Request, exc):
    """Custom handler for rate limit exceeded errors."""
    return JSONResponse(
        status_code=429,
        content={
            "detail": str(exc.detail),
            "type": "rate_limit_exceeded",
        },
        headers=exc.headers if hasattr(exc, "headers") else {},
    )


# Register authentication routes
app.include_router(auth_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "HypertroQ Backend API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Checks status of critical services:
    - API: Always healthy if responding
    - Redis: Connected or using fallback
    """
    redis_status = "connected" if redis_client.redis else "fallback"
    
    return {
        "status": "healthy",
        "services": {
            "api": "healthy",
            "redis": redis_status,
        },
    }


# Example: Protected endpoint using authentication
from app.core.dependencies import CurrentUserDep, VerifiedUserDep


@app.get("/api/v1/profile")
async def get_profile(current_user: CurrentUserDep):
    """
    Example protected endpoint.
    
    Requires valid JWT token in Authorization header.
    """
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role,
    }


@app.get("/api/v1/verified-only")
async def verified_only(verified_user: VerifiedUserDep):
    """
    Example endpoint requiring verified email.
    
    Requires valid JWT token + verified email.
    """
    return {
        "message": "You have access to this verified-only feature!",
        "user_id": str(verified_user.id),
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
    )
