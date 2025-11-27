"""Dependency injection for FastAPI routes."""
import logging
from datetime import datetime, timedelta, timezone
from functools import wraps
from typing import Annotated, Any, AsyncGenerator, Callable, Optional
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import decode_token, verify_token_type

# Configure logging
logger = logging.getLogger(__name__)


# HTTPBearer scheme for token authentication (simpler Swagger UI)
http_bearer = HTTPBearer(
    scheme_name="Bearer",
    description="Enter your JWT access token"
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session dependency.
    
    Import is inside the function to avoid circular imports.
    """
    from app.infrastructure.database import get_db as database_get_db
    
    async for session in database_get_db():
        yield session


class TokenPayload:
    """Token payload with user and organization context."""
    def __init__(self, user_id: str, organization_id: str, role: str):
        self.user_id = UUID(user_id)
        self.organization_id = UUID(organization_id)
        self.role = role


async def get_token_payload(credentials: Annotated[HTTPAuthorizationCredentials, Depends(http_bearer)]) -> TokenPayload:
    """Get token payload with user and organization context."""
    token = credentials.credentials
    payload = decode_token(token)
    verify_token_type(payload, "access")
    
    user_id = payload.get("user_id") or payload.get("sub")
    organization_id = payload.get("organization_id")
    role = payload.get("role", "USER")
    
    if not user_id or not organization_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing user or organization context",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return TokenPayload(user_id, organization_id, role)


async def get_current_user_id(token_payload: Annotated[TokenPayload, Depends(get_token_payload)]) -> UUID:
    """Get current user ID from token."""
    return token_payload.user_id


async def get_current_organization_id(token_payload: Annotated[TokenPayload, Depends(get_token_payload)]) -> UUID:
    """Get current organization ID from token."""
    return token_payload.organization_id


async def require_admin_role(token_payload: Annotated[TokenPayload, Depends(get_token_payload)]) -> TokenPayload:
    """Require user to have ADMIN role."""
    if token_payload.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return token_payload


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(http_bearer)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Any:
    """
    Get current user from JWT token.
    
    Process:
    1. Decode and validate JWT token
    2. Verify token type is 'access'
    3. Extract user ID from token payload
    4. Retrieve user from database
    5. Verify user is active
    
    Args:
        token: JWT access token from Authorization header
        db: Database session
        
    Returns:
        User model instance
        
    Raises:
        HTTPException 401: If token is invalid, expired, or user not found
        HTTPException 403: If user account is inactive
        
    Security:
        - Validates token signature
        - Checks token type and expiration
        - Verifies user still exists in database
    """
    from app.infrastructure.repositories.user_repository import UserRepository

    try:
        # Extract token from credentials
        token = credentials.credentials
        
        # Decode and validate token
        payload = decode_token(token)
        
        # Verify token type
        verify_token_type(payload, "access")
        
        # Extract user ID
        user_id_str = payload.get("user_id") or payload.get("sub")
        if not user_id_str:
            logger.warning("Token validation failed: missing user_id")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user identifier",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user_id = UUID(user_id_str)
        
        # Get user from database
        user_repo = UserRepository(db)
        user = await user_repo.get_by_id(user_id)
        
        if not user:
            logger.warning(f"Token validation failed: user not found - {user_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check if user is active
        if not user.is_active:
            logger.warning(f"Access denied: inactive user - {user_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your account has been deactivated. Please contact support.",
            )
        
        return user
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Token validation error: Invalid UUID - {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Unexpected error in get_current_user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_active_user(
    current_user: Annotated[Any, Depends(get_current_user)]
) -> Any:
    """
    Get current active user (already verified by get_current_user).
    
    This dependency is kept for backward compatibility and semantic clarity.
    The get_current_user dependency already checks if user is active.
    
    Args:
        current_user: User from get_current_user dependency
        
    Returns:
        User model instance
        
    Raises:
        HTTPException 403: If user is not active
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been deactivated. Please contact support.",
        )
    return current_user


async def require_verified_user(
    current_user: Annotated[Any, Depends(get_current_active_user)]
) -> Any:
    """
    Require user to have verified email.
    
    Use this dependency for endpoints that require email verification
    (e.g., creating programs, accessing pro features).
    
    Args:
        current_user: User from get_current_active_user dependency
        
    Returns:
        User model instance with verified email
        
    Raises:
        HTTPException 403: If user email is not verified
        
    Example:
        @router.post("/programs")
        async def create_program(
            user: Annotated[User, Depends(require_verified_user)]
        ):
            # User is guaranteed to be active and verified
            ...
    """
    if not current_user.is_verified:
        logger.info(f"Access denied: unverified user - {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verification required. Please verify your email to access this feature.",
        )
    return current_user


async def require_admin(
    current_user: Annotated[Any, Depends(get_current_active_user)]
) -> Any:
    """
    Require user to have ADMIN role.
    
    Use this dependency for admin-only endpoints
    (e.g., managing organizations, viewing all users).
    
    Args:
        current_user: User from get_current_active_user dependency
        
    Returns:
        User model instance with ADMIN role
        
    Raises:
        HTTPException 403: If user is not an admin
        
    Example:
        @router.get("/admin/users")
        async def list_all_users(
            admin: Annotated[User, Depends(require_admin)]
        ):
            # User is guaranteed to be an active admin
            ...
    """
    if current_user.role != "ADMIN":
        logger.warning(
            f"Admin access denied: user {current_user.id} has role {current_user.role}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator privileges required to access this resource.",
        )
    return current_user


async def get_current_organization(
    current_user: Annotated[Any, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Any:
    """
    Get organization for current user.
    
    Retrieves the organization that the current user belongs to.
    Useful for endpoints that need organization context.
    
    Args:
        current_user: User from get_current_user dependency
        db: Database session
        
    Returns:
        Organization model instance
        
    Raises:
        HTTPException 404: If organization not found
        
    Example:
        @router.get("/organization/settings")
        async def get_org_settings(
            org: Annotated[Organization, Depends(get_current_organization)]
        ):
            return org.settings
    """
    from app.infrastructure.repositories.organization_repository import OrganizationRepository

    try:
        org_repo = OrganizationRepository(db)
        organization = await org_repo.get_by_id(current_user.organization_id)
        
        if not organization:
            logger.error(
                f"Organization not found for user {current_user.id}: {current_user.organization_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found",
            )
        
        return organization
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving organization: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve organization",
        )


# ==================== Rate Limiting ====================

# In-memory rate limiting (production: use Redis)
_rate_limit_storage: dict[str, list[datetime]] = {}


def rate_limit(
    max_requests: int = 5,
    window_seconds: int = 60,
    identifier: str = "ip"
) -> Callable:
    """
    Rate limiting decorator for FastAPI endpoints.
    
    Limits the number of requests from a client within a time window.
    
    Args:
        max_requests: Maximum number of requests allowed in window
        window_seconds: Time window in seconds
        identifier: How to identify clients ('ip' or 'user')
        
    Returns:
        Decorator function
        
    Example:
        @router.post("/auth/login")
        @rate_limit(max_requests=5, window_seconds=60)
        async def login(...):
            ...
            
    Note:
        In production, use Redis for distributed rate limiting.
        Current implementation uses in-memory storage.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request from args/kwargs
            request: Optional[Request] = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            if not request:
                request = kwargs.get("request")
            
            if not request:
                # If no request found, skip rate limiting
                logger.warning("Rate limit decorator: Request object not found")
                return await func(*args, **kwargs)
            
            # Determine identifier
            if identifier == "ip":
                client_id = request.client.host if request.client else "unknown"
            elif identifier == "user":
                # Try to get user from token
                auth_header = request.headers.get("Authorization")
                if auth_header and auth_header.startswith("Bearer "):
                    token = auth_header.split(" ")[1]
                    try:
                        payload = decode_token(token)
                        client_id = payload.get("user_id") or payload.get("sub") or "unknown"
                    except Exception:
                        client_id = request.client.host if request.client else "unknown"
                else:
                    client_id = request.client.host if request.client else "unknown"
            else:
                client_id = "unknown"
            
            # Create storage key
            key = f"{func.__name__}:{client_id}"
            
            # Get current time
            now = datetime.now(timezone.utc)
            window_start = now - timedelta(seconds=window_seconds)
            
            # Initialize or clean up old requests
            if key not in _rate_limit_storage:
                _rate_limit_storage[key] = []
            
            # Remove requests outside the window
            _rate_limit_storage[key] = [
                req_time for req_time in _rate_limit_storage[key]
                if req_time > window_start
            ]
            
            # Check rate limit
            if len(_rate_limit_storage[key]) >= max_requests:
                logger.warning(
                    f"Rate limit exceeded for {client_id} on {func.__name__}"
                )
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded. Maximum {max_requests} requests per {window_seconds} seconds.",
                    headers={
                        "Retry-After": str(window_seconds),
                        "X-RateLimit-Limit": str(max_requests),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(int((window_start + timedelta(seconds=window_seconds)).timestamp())),
                    }
                )
            
            # Add current request
            _rate_limit_storage[key].append(now)
            
            # Execute function
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


# ==================== Type Aliases ====================

# Database dependency
DatabaseDep = Annotated[AsyncSession, Depends(get_db)]

# Token-based dependencies (lightweight, no DB query)
TokenPayloadDep = Annotated[TokenPayload, Depends(get_token_payload)]
CurrentUserIdDep = Annotated[UUID, Depends(get_current_user_id)]
CurrentOrganizationIdDep = Annotated[UUID, Depends(get_current_organization_id)]

# User dependencies (with DB query)
CurrentUserDep = Annotated[Any, Depends(get_current_user)]
CurrentActiveUserDep = Annotated[Any, Depends(get_current_active_user)]
VerifiedUserDep = Annotated[Any, Depends(require_verified_user)]
AdminUserDep = Annotated[Any, Depends(require_admin)]

# Organization dependency
CurrentOrganizationDep = Annotated[Any, Depends(get_current_organization)]

# Role-based token dependency (lightweight)
AdminRoleDep = Annotated[TokenPayload, Depends(require_admin_role)]

