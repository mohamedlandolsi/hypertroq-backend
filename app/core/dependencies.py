"""Dependency injection for FastAPI routes."""
from typing import AsyncGenerator, Annotated, Any
from uuid import UUID
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import decode_token, verify_token_type


# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/login"
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


async def get_token_payload(token: Annotated[str, Depends(oauth2_scheme)]) -> TokenPayload:
    """Get token payload with user and organization context."""
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


async def get_current_active_user(
    current_user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> Any:
    """Get current active user from database."""
    from app.infrastructure.repositories.user_repository import UserRepository
    
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(current_user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    return user


# Type aliases for dependency injection
DatabaseDep = Annotated[AsyncSession, Depends(get_db)]
TokenPayloadDep = Annotated[TokenPayload, Depends(get_token_payload)]
CurrentUserIdDep = Annotated[UUID, Depends(get_current_user_id)]
CurrentOrganizationIdDep = Annotated[UUID, Depends(get_current_organization_id)]
AdminRoleDep = Annotated[TokenPayload, Depends(require_admin_role)]
CurrentActiveUserDep = Annotated[Any, Depends(get_current_active_user)]

# Backward compatibility
CurrentUserDep = CurrentUserIdDep
