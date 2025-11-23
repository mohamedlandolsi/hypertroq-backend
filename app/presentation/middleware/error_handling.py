"""
Global error handling middleware.

Catches unhandled exceptions and returns consistent error responses.
"""

import logging
from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to catch and handle unhandled exceptions.
    
    Logs errors and returns consistent JSON error responses.
    """
    
    async def dispatch(
        self, 
        request: Request, 
        call_next: Callable
    ) -> Response:
        """
        Process request and catch unhandled exceptions.
        
        Args:
            request: Incoming request
            call_next: Next middleware/handler
            
        Returns:
            Response or error response
        """
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            # Log the error with full context
            logger.error(
                f"Unhandled exception in {request.method} {request.url.path}",
                exc_info=exc,
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "client": request.client.host if request.client else None,
                }
            )
            
            # Return generic error response
            return JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "code": "INTERNAL_SERVER_ERROR",
                        "message": "An unexpected error occurred. Please try again later.",
                    }
                }
            )
