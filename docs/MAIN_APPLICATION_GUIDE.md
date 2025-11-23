# Main Application Guide

## Overview

The HypertroQ Backend API is built with FastAPI and implements a production-ready architecture with comprehensive middleware, health checks, error handling, and observability features.

## Application Metadata

```python
Title: "HypertroQ API"
Description: "Science-based hypertrophy training platform"
Version: "1.0.0"
Documentation: /docs (Swagger UI), /redoc (ReDoc)
```

## Middleware Stack

Middleware is applied in the following order (first added is outermost):

1. **CORS Middleware** - Cross-Origin Resource Sharing configuration
2. **ErrorHandlingMiddleware** - Global error catching and consistent responses
3. **RequestIDMiddleware** - Unique request tracking with X-Request-ID header
4. **TimingMiddleware** - Performance monitoring with X-Process-Time header
5. **LoggingMiddleware** - Request/response logging with detailed context

### Request ID Tracking

Every request gets a unique identifier that's:
- Generated automatically or preserved from client-provided `X-Request-ID` header
- Stored in `request.state.request_id` for use in handlers
- Added to response headers as `X-Request-ID`
- Included in error responses for debugging

**Example Usage in Handlers:**
```python
@router.get("/example")
async def example_endpoint(request: Request):
    request_id = request.state.request_id
    logger.info(f"Processing request {request_id}")
    return {"data": "example"}
```

### Performance Timing

The `TimingMiddleware` adds an `X-Process-Time` header to all responses:
```
X-Process-Time: 45.23ms
```

This helps identify slow endpoints and monitor API performance.

## Health Check Endpoints

### Basic Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "service": "hypertroq-backend",
  "version": "1.0.0"
}
```

### Database Health Check
```http
GET /health/db
```

Tests database connectivity by executing a simple query.

**Success Response (200):**
```json
{
  "status": "healthy",
  "service": "database",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Failure Response (503):**
```json
{
  "status": "unhealthy",
  "service": "database",
  "error": "Connection timeout",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Redis Health Check
```http
GET /health/redis
```

Tests Redis connectivity by executing a PING command.

**Success Response (200):**
```json
{
  "status": "healthy",
  "service": "redis",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Failure Response (503):**
```json
{
  "status": "unhealthy",
  "service": "redis",
  "error": "Connection refused",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Lifecycle Management

The application uses a `lifespan` context manager to handle startup and shutdown events:

### Startup Events

1. **Database Connection** - Tests database connectivity and establishes connection pool
2. **Redis Connection** - Connects to Redis cache server
3. **Sentry Initialization** (optional) - Enables error tracking if `SENTRY_DSN` is configured

**Startup Logs:**
```
Starting HypertroQ Backend API...
✓ Database connection established
✓ Redis connection established
✓ Sentry error tracking initialized
🚀 Application startup complete
```

### Shutdown Events

1. **Redis Disconnect** - Closes Redis connections gracefully
2. **Database Cleanup** - Disposes of database connection pools

**Shutdown Logs:**
```
Shutting down HypertroQ Backend API...
✓ Redis connection closed
✓ Database connections closed
👋 Application shutdown complete
```

## Exception Handlers

The application provides specialized handlers for different error types:

### HTTP Exceptions

**Trigger:** Raised `HTTPException` from FastAPI
**Status Code:** Matches exception status code
**Response Format:**
```json
{
  "error": {
    "code": "HTTP_ERROR",
    "message": "Not Found",
    "status_code": 404,
    "timestamp": "2024-01-15T10:30:00Z",
    "request_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

### Request Validation Errors

**Trigger:** Invalid request data (Pydantic validation)
**Status Code:** 422 Unprocessable Entity
**Response Format:**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": [
      {
        "loc": ["body", "email"],
        "msg": "value is not a valid email address",
        "type": "value_error.email"
      }
    ],
    "timestamp": "2024-01-15T10:30:00Z",
    "request_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

### Pydantic Validation Errors

**Trigger:** Data model validation errors
**Status Code:** 422 Unprocessable Entity
**Response Format:**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Data validation failed",
    "details": [...],
    "timestamp": "2024-01-15T10:30:00Z",
    "request_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

### Database Errors

**Trigger:** SQLAlchemy exceptions
**Status Code:** 500 Internal Server Error
**Response Format:**
```json
{
  "error": {
    "code": "DATABASE_ERROR",
    "message": "A database error occurred. Please try again later.",
    "timestamp": "2024-01-15T10:30:00Z",
    "request_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

**Note:** Database errors are logged with full stack trace but client receives generic message for security.

### General Exceptions

**Trigger:** Any unhandled exception
**Status Code:** 500 Internal Server Error
**Response Format:**
```json
{
  "error": {
    "code": "INTERNAL_SERVER_ERROR",
    "message": "An unexpected error occurred. Please try again later.",
    "timestamp": "2024-01-15T10:30:00Z",
    "request_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

**Note:** Automatically sent to Sentry if configured.

## Observability

### Sentry Integration

Error tracking is automatically enabled if `SENTRY_DSN` is configured in environment:

```bash
SENTRY_DSN=https://...@sentry.io/...
ENVIRONMENT=production  # or development, staging
```

**Features:**
- Automatic exception capture and reporting
- 10% transaction sampling for performance monitoring
- Environment-based error grouping
- Request context included with errors

### Response Headers

Every response includes observability headers:

```http
X-Request-ID: 550e8400-e29b-41d4-a716-446655440000
X-Process-Time: 45.23ms
```

### Logging

All requests are logged with detailed context:

```
2024-01-15 10:30:00 - app.middleware.logging - INFO - GET /api/v1/programs 200 45.23ms
```

## Root Endpoint

```http
GET /
```

**Response:**
```json
{
  "name": "HypertroQ API",
  "version": "1.0.0",
  "status": "operational",
  "message": "Welcome to HypertroQ - Science-based hypertrophy training platform",
  "documentation": {
    "interactive": "/docs",
    "redoc": "/redoc",
    "openapi": "/openapi.json"
  },
  "health_checks": {
    "status": "/health",
    "database": "/health/db",
    "cache": "/health/redis"
  }
}
```

## Running the Application

### Development Mode

```powershell
# Using commands.ps1
.\commands.ps1 dev

# Or directly with uvicorn
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode

```powershell
# Using gunicorn with uvicorn workers
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile -
```

## Environment Variables

Required configuration:

```bash
# Application
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO
RELOAD=true  # Development only

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/hypertroq
DIRECT_URL=postgresql://user:pass@localhost/hypertroq  # For migrations

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-secret-key
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS
BACKEND_CORS_ORIGINS=["http://localhost:3000","https://hypertroq.com"]

# Optional: Error Tracking
SENTRY_DSN=https://...@sentry.io/...
ENVIRONMENT=production
```

## Monitoring Checklist

For production deployments, monitor:

- [ ] Health check endpoints return 200 OK
- [ ] Database health check succeeds
- [ ] Redis health check succeeds
- [ ] Response times are acceptable (check X-Process-Time)
- [ ] Error rate is low (monitor Sentry)
- [ ] Request IDs are unique and properly tracked
- [ ] CORS is properly configured for frontend domain
- [ ] All middleware is active and functioning

## Troubleshooting

### Application Won't Start

**Check logs for:**
- Database connection errors
- Redis connection errors
- Missing environment variables
- Port already in use

**Solutions:**
```powershell
# Test database connection
poetry run python -c "from app.infrastructure.database.connection import DatabaseManager; import asyncio; asyncio.run(DatabaseManager().test_connection())"

# Test Redis connection
redis-cli ping

# Check port availability
netstat -ano | findstr :8000
```

### Health Checks Failing

**Database health check fails:**
- Verify `DATABASE_URL` is correct
- Check database is running and accessible
- Verify credentials and permissions
- Check firewall rules

**Redis health check fails:**
- Verify `REDIS_URL` is correct
- Check Redis is running: `redis-cli ping`
- Verify network connectivity
- Check Redis authentication if required

### High Response Times

**Check X-Process-Time header:**
- Times > 1000ms indicate slow endpoints
- Database queries may need optimization
- Consider adding caching with Redis
- Review middleware overhead

### CORS Errors

**Symptoms:** Browser shows CORS errors in console

**Solutions:**
- Verify frontend URL in `BACKEND_CORS_ORIGINS`
- Check CORS middleware is first in stack
- Ensure credentials are properly configured
- Test with simple curl request first

## Best Practices

1. **Always check health endpoints** before deploying
2. **Monitor X-Process-Time** to identify slow endpoints
3. **Use request IDs** for debugging and log correlation
4. **Enable Sentry** in production for error tracking
5. **Keep middleware order** - CORS must be first
6. **Handle all exceptions** at appropriate levels
7. **Use structured logging** with context
8. **Test graceful shutdown** to avoid data loss
9. **Configure proper timeouts** for long-running operations
10. **Monitor database connection pool** usage

## Security Considerations

- All errors return generic messages to clients (detailed logs server-side)
- Request IDs help track issues without exposing internals
- Database errors don't leak schema information
- CORS is explicitly configured (not wildcard)
- Sentry integration respects privacy (no PII in errors)
- Exception handlers prevent information disclosure

## Performance Optimization

1. **Use async/await** throughout the application
2. **Connection pooling** for database (SQLAlchemy)
3. **Redis caching** for frequently accessed data
4. **Middleware ordering** optimized for performance
5. **Lazy loading** for optional features (Sentry)
6. **Efficient logging** with appropriate levels
7. **Health checks** are lightweight and cached
