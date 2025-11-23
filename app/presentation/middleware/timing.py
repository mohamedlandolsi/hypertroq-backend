"""
Timing middleware for tracking request processing time.

Adds X-Process-Time header to all responses showing request duration.
"""

import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class TimingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to track request processing time.
    
    Adds X-Process-Time header with milliseconds taken to process request.
    """
    
    async def dispatch(
        self, 
        request: Request, 
        call_next: Callable
    ) -> Response:
        """
        Process request and add timing header.
        
        Args:
            request: Incoming request
            call_next: Next middleware/handler
            
        Returns:
            Response with X-Process-Time header
        """
        start_time = time.time()
        
        response = await call_next(request)
        
        process_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        response.headers["X-Process-Time"] = f"{process_time:.2f}ms"
        
        return response
