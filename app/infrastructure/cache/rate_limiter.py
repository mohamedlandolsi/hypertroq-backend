"""
Redis-based rate limiter for API endpoints.

Provides distributed rate limiting using Redis for scalability
across multiple application instances.
"""

import logging
from datetime import datetime, timezone
from typing import Callable, Optional

from fastapi import HTTPException, Request, status

from app.infrastructure.cache.redis_client import redis_client

logger = logging.getLogger(__name__)


class RedisRateLimiter:
    """
    Redis-based rate limiter for distributed rate limiting.
    
    Uses Redis counters with expiration to track request counts
    per client within a time window.
    """

    @staticmethod
    async def check_rate_limit(
        request: Request,
        max_requests: int,
        window_seconds: int,
        identifier: str = "ip",
    ) -> None:
        """
        Check if request exceeds rate limit.
        
        Args:
            request: FastAPI request object
            max_requests: Maximum number of requests allowed in window
            window_seconds: Time window in seconds
            identifier: How to identify clients ('ip' or 'user')
            
        Raises:
            HTTPException 429: If rate limit exceeded
            
        Note:
            Uses Redis INCR with EXPIRE for atomic operations.
            Falls back to allowing request if Redis unavailable.
        """
        if not redis_client.redis:
            logger.warning("Redis not connected, skipping rate limit check")
            return

        # Determine client identifier
        if identifier == "ip":
            client_id = request.client.host if request.client else "unknown"
        elif identifier == "user":
            # Try to extract user from token
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                try:
                    from app.core.security import decode_token
                    token = auth_header.split(" ")[1]
                    payload = decode_token(token)
                    client_id = payload.get("user_id") or payload.get("sub") or "unknown"
                except Exception:
                    client_id = request.client.host if request.client else "unknown"
            else:
                client_id = request.client.host if request.client else "unknown"
        else:
            client_id = request.client.host if request.client else "unknown"

        # Create rate limit key
        endpoint = request.url.path
        key = f"rate_limit:{endpoint}:{client_id}"

        try:
            # Get current count
            current_count = await redis_client.redis.get(key)
            
            if current_count is None:
                # First request in window
                await redis_client.redis.setex(key, window_seconds, 1)
                remaining = max_requests - 1
            else:
                current_count = int(current_count)
                
                if current_count >= max_requests:
                    # Rate limit exceeded
                    ttl = await redis_client.redis.ttl(key)
                    logger.warning(
                        f"Rate limit exceeded for {client_id} on {endpoint}: "
                        f"{current_count}/{max_requests} requests"
                    )
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail=f"Rate limit exceeded. Maximum {max_requests} requests per {window_seconds} seconds.",
                        headers={
                            "Retry-After": str(ttl if ttl > 0 else window_seconds),
                            "X-RateLimit-Limit": str(max_requests),
                            "X-RateLimit-Remaining": "0",
                            "X-RateLimit-Reset": str(
                                int(datetime.now(timezone.utc).timestamp()) + (ttl if ttl > 0 else window_seconds)
                            ),
                        },
                    )
                
                # Increment counter
                await redis_client.redis.incr(key)
                remaining = max_requests - current_count - 1

            # Add rate limit headers to response (handled by middleware)
            request.state.rate_limit_headers = {
                "X-RateLimit-Limit": str(max_requests),
                "X-RateLimit-Remaining": str(remaining),
                "X-RateLimit-Reset": str(
                    int(datetime.now(timezone.utc).timestamp()) + window_seconds
                ),
            }

        except HTTPException:
            raise
        except Exception as e:
            # Log error but don't block request if Redis fails
            logger.error(f"Rate limit check failed: {str(e)}")
            # Allow request to proceed


def rate_limit_dependency(
    max_requests: int = 10,
    window_seconds: int = 60,
    identifier: str = "ip",
) -> Callable:
    """
    Create a FastAPI dependency for rate limiting.
    
    Args:
        max_requests: Maximum requests allowed in window
        window_seconds: Time window in seconds
        identifier: Client identifier ('ip' or 'user')
        
    Returns:
        Async dependency function
        
    Example:
        @router.post("/login", dependencies=[Depends(rate_limit_dependency(5, 60))])
        async def login(...):
            ...
    """
    async def dependency(request: Request) -> None:
        await RedisRateLimiter.check_rate_limit(
            request, max_requests, window_seconds, identifier
        )
    
    return dependency


# Pre-configured rate limiters for common use cases
auth_rate_limit = rate_limit_dependency(max_requests=10, window_seconds=60, identifier="ip")
strict_auth_rate_limit = rate_limit_dependency(max_requests=5, window_seconds=60, identifier="ip")
register_rate_limit = rate_limit_dependency(max_requests=3, window_seconds=300, identifier="ip")
