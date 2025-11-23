"""
Error handlers for custom exceptions.

Provides consistent error response format with logging,
request tracking, and environment-specific details.
"""

import logging
import traceback
from datetime import datetime, timezone
from typing import Any

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.core.exceptions import (
    AppException,
    AuthenticationException,
    AuthorizationException,
    BadRequestException,
    ConflictException,
    ErrorCode,
    NotFoundException,
    RateLimitException,
    SubscriptionRequiredException,
    ValidationException,
)

logger = logging.getLogger(__name__)


def get_request_id(request: Request) -> str | None:
    """
    Extract request ID from request state.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Request ID if available, None otherwise
    """
    return getattr(request.state, "request_id", None)


def get_error_response(
    error_code: str,
    message: str,
    status_code: int,
    request: Request,
    details: dict[str, Any] | None = None,
    exception: Exception | None = None,
) -> dict[str, Any]:
    """
    Build consistent error response format.
    
    Args:
        error_code: Machine-readable error code
        message: Human-readable error message
        status_code: HTTP status code
        request: FastAPI request object
        details: Additional error context
        exception: Original exception (for stack trace in development)
        
    Returns:
        Dictionary with error response structure
    """
    error_response = {
        "error": {
            "code": error_code,
            "message": message,
            "status_code": status_code,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_id": get_request_id(request),
            "path": str(request.url.path),
        }
    }
    
    # Add details if provided
    if details:
        error_response["error"]["details"] = details
    
    # Add stack trace in development mode
    if settings.ENVIRONMENT == "development" and exception:
        error_response["error"]["stack_trace"] = traceback.format_exception(
            type(exception), exception, exception.__traceback__
        )
    
    return error_response


def log_error(
    request: Request,
    exception: Exception,
    status_code: int,
    error_code: str,
) -> None:
    """
    Log error with context.
    
    Args:
        request: FastAPI request object
        exception: Exception that occurred
        status_code: HTTP status code
        error_code: Machine-readable error code
    """
    log_data = {
        "error_code": error_code,
        "status_code": status_code,
        "path": request.url.path,
        "method": request.method,
        "request_id": get_request_id(request),
        "client": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
    }
    
    # Log based on severity
    if status_code >= 500:
        logger.error(
            f"{error_code}: {str(exception)}",
            exc_info=exception,
            extra=log_data,
        )
    elif status_code >= 400:
        logger.warning(
            f"{error_code}: {str(exception)}",
            extra=log_data,
        )
    else:
        logger.info(
            f"{error_code}: {str(exception)}",
            extra=log_data,
        )


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """
    Handle custom application exceptions.
    
    Args:
        request: FastAPI request object
        exc: Application exception
        
    Returns:
        JSON response with error details
    """
    log_error(request, exc, exc.status_code, exc.error_code)
    
    response = get_error_response(
        error_code=exc.error_code,
        message=exc.message,
        status_code=exc.status_code,
        request=request,
        details=exc.details,
        exception=exc,
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response,
    )


async def authentication_exception_handler(
    request: Request, exc: AuthenticationException
) -> JSONResponse:
    """
    Handle authentication exceptions (401).
    
    Args:
        request: FastAPI request object
        exc: Authentication exception
        
    Returns:
        JSON response with error details
    """
    log_error(request, exc, 401, exc.error_code)
    
    response = get_error_response(
        error_code=exc.error_code,
        message=exc.message,
        status_code=401,
        request=request,
        details=exc.details,
        exception=exc,
    )
    
    # Add WWW-Authenticate header
    return JSONResponse(
        status_code=401,
        content=response,
        headers={"WWW-Authenticate": "Bearer"},
    )


async def authorization_exception_handler(
    request: Request, exc: AuthorizationException
) -> JSONResponse:
    """
    Handle authorization exceptions (403).
    
    Args:
        request: FastAPI request object
        exc: Authorization exception
        
    Returns:
        JSON response with error details
    """
    log_error(request, exc, 403, exc.error_code)
    
    response = get_error_response(
        error_code=exc.error_code,
        message=exc.message,
        status_code=403,
        request=request,
        details=exc.details,
        exception=exc,
    )
    
    return JSONResponse(
        status_code=403,
        content=response,
    )


async def not_found_exception_handler(
    request: Request, exc: NotFoundException
) -> JSONResponse:
    """
    Handle not found exceptions (404).
    
    Args:
        request: FastAPI request object
        exc: Not found exception
        
    Returns:
        JSON response with error details
    """
    log_error(request, exc, 404, exc.error_code)
    
    response = get_error_response(
        error_code=exc.error_code,
        message=exc.message,
        status_code=404,
        request=request,
        details=exc.details,
        exception=exc,
    )
    
    return JSONResponse(
        status_code=404,
        content=response,
    )


async def validation_exception_handler(
    request: Request, exc: ValidationException
) -> JSONResponse:
    """
    Handle validation exceptions (422).
    
    Args:
        request: FastAPI request object
        exc: Validation exception
        
    Returns:
        JSON response with error details
    """
    log_error(request, exc, 422, exc.error_code)
    
    response = get_error_response(
        error_code=exc.error_code,
        message=exc.message,
        status_code=422,
        request=request,
        details=exc.details,
        exception=exc,
    )
    
    return JSONResponse(
        status_code=422,
        content=response,
    )


async def subscription_required_exception_handler(
    request: Request, exc: SubscriptionRequiredException
) -> JSONResponse:
    """
    Handle subscription required exceptions (402).
    
    Args:
        request: FastAPI request object
        exc: Subscription required exception
        
    Returns:
        JSON response with error details
    """
    log_error(request, exc, 402, exc.error_code)
    
    response = get_error_response(
        error_code=exc.error_code,
        message=exc.message,
        status_code=402,
        request=request,
        details=exc.details,
        exception=exc,
    )
    
    return JSONResponse(
        status_code=402,
        content=response,
    )


async def rate_limit_exception_handler(
    request: Request, exc: RateLimitException
) -> JSONResponse:
    """
    Handle rate limit exceptions (429).
    
    Args:
        request: FastAPI request object
        exc: Rate limit exception
        
    Returns:
        JSON response with error details and Retry-After header
    """
    log_error(request, exc, 429, exc.error_code)
    
    response = get_error_response(
        error_code=exc.error_code,
        message=exc.message,
        status_code=429,
        request=request,
        details=exc.details,
        exception=exc,
    )
    
    # Add Retry-After header if available
    headers = {}
    if exc.details and "retry_after" in exc.details:
        headers["Retry-After"] = str(exc.details["retry_after"])
    
    return JSONResponse(
        status_code=429,
        content=response,
        headers=headers,
    )


async def conflict_exception_handler(
    request: Request, exc: ConflictException
) -> JSONResponse:
    """
    Handle conflict exceptions (409).
    
    Args:
        request: FastAPI request object
        exc: Conflict exception
        
    Returns:
        JSON response with error details
    """
    log_error(request, exc, 409, exc.error_code)
    
    response = get_error_response(
        error_code=exc.error_code,
        message=exc.message,
        status_code=409,
        request=request,
        details=exc.details,
        exception=exc,
    )
    
    return JSONResponse(
        status_code=409,
        content=response,
    )


async def bad_request_exception_handler(
    request: Request, exc: BadRequestException
) -> JSONResponse:
    """
    Handle bad request exceptions (400).
    
    Args:
        request: FastAPI request object
        exc: Bad request exception
        
    Returns:
        JSON response with error details
    """
    log_error(request, exc, 400, exc.error_code)
    
    response = get_error_response(
        error_code=exc.error_code,
        message=exc.message,
        status_code=400,
        request=request,
        details=exc.details,
        exception=exc,
    )
    
    return JSONResponse(
        status_code=400,
        content=response,
    )


async def request_validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    Handle FastAPI request validation errors (422).
    
    Args:
        request: FastAPI request object
        exc: Request validation error
        
    Returns:
        JSON response with validation error details
    """
    log_error(request, exc, 422, ErrorCode.VALIDATION_ERROR)
    
    # Format validation errors
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
        })
    
    response = get_error_response(
        error_code=ErrorCode.VALIDATION_ERROR,
        message="Request validation failed",
        status_code=422,
        request=request,
        details={"errors": errors},
        exception=exc,
    )
    
    return JSONResponse(
        status_code=422,
        content=response,
    )


async def pydantic_validation_exception_handler(
    request: Request, exc: ValidationError
) -> JSONResponse:
    """
    Handle Pydantic validation errors (422).
    
    Args:
        request: FastAPI request object
        exc: Pydantic validation error
        
    Returns:
        JSON response with validation error details
    """
    log_error(request, exc, 422, ErrorCode.VALIDATION_ERROR)
    
    # Format validation errors
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
        })
    
    response = get_error_response(
        error_code=ErrorCode.VALIDATION_ERROR,
        message="Data validation failed",
        status_code=422,
        request=request,
        details={"errors": errors},
        exception=exc,
    )
    
    return JSONResponse(
        status_code=422,
        content=response,
    )


async def database_exception_handler(
    request: Request, exc: SQLAlchemyError
) -> JSONResponse:
    """
    Handle database errors (500).
    
    Args:
        request: FastAPI request object
        exc: SQLAlchemy error
        
    Returns:
        JSON response with error details
    """
    log_error(request, exc, 500, ErrorCode.INTERNAL_SERVER_ERROR)
    
    # Generic message for security (don't expose database details)
    response = get_error_response(
        error_code=ErrorCode.INTERNAL_SERVER_ERROR,
        message="A database error occurred. Please try again later.",
        status_code=500,
        request=request,
        details={},
        exception=exc if settings.ENVIRONMENT == "development" else None,
    )
    
    return JSONResponse(
        status_code=500,
        content=response,
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle all unhandled exceptions (500).
    
    Args:
        request: FastAPI request object
        exc: Exception
        
    Returns:
        JSON response with error details
    """
    log_error(request, exc, 500, ErrorCode.INTERNAL_SERVER_ERROR)
    
    # Send to Sentry if configured
    if hasattr(settings, "SENTRY_DSN") and settings.SENTRY_DSN:
        try:
            import sentry_sdk
            sentry_sdk.capture_exception(exc)
        except Exception:
            pass
    
    # Generic message for security
    response = get_error_response(
        error_code=ErrorCode.INTERNAL_SERVER_ERROR,
        message="An unexpected error occurred. Please try again later.",
        status_code=500,
        request=request,
        details={},
        exception=exc if settings.ENVIRONMENT == "development" else None,
    )
    
    return JSONResponse(
        status_code=500,
        content=response,
    )


def register_exception_handlers(app) -> None:
    """
    Register all exception handlers with FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    # Custom application exceptions
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(AuthenticationException, authentication_exception_handler)
    app.add_exception_handler(AuthorizationException, authorization_exception_handler)
    app.add_exception_handler(NotFoundException, not_found_exception_handler)
    app.add_exception_handler(ValidationException, validation_exception_handler)
    app.add_exception_handler(SubscriptionRequiredException, subscription_required_exception_handler)
    app.add_exception_handler(RateLimitException, rate_limit_exception_handler)
    app.add_exception_handler(ConflictException, conflict_exception_handler)
    app.add_exception_handler(BadRequestException, bad_request_exception_handler)
    
    # FastAPI/Pydantic validation errors
    app.add_exception_handler(RequestValidationError, request_validation_exception_handler)
    app.add_exception_handler(ValidationError, pydantic_validation_exception_handler)
    
    # Database errors
    app.add_exception_handler(SQLAlchemyError, database_exception_handler)
    
    # Catch-all for unhandled exceptions
    app.add_exception_handler(Exception, general_exception_handler)
    
    logger.info("Exception handlers registered successfully")
