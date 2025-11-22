"""Dependency injection for FastAPI routes."""
from typing import AsyncGenerator, Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import decode_token, verify_token_type
from app.infrastructure.database.session import async_session_maker


# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/login"
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session dependency."""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_current_user_id(token: Annotated[str, Depends(oauth2_scheme)]) -> str:
    """Get current user ID from JWT token."""
    payload = decode_token(token)
    verify_token_type(payload, "access")
    
    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user_id


async def get_current_active_user(
    current_user_id: Annotated[str, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> Any:
    """Get current active user from database."""
    # TODO: Implement user repository to fetch user
    # For now, return the user_id
    # Example:
    # user_repo = UserRepository(db)
    # user = await user_repo.get_by_id(current_user_id)
    # if not user or not user.is_active:
    #     raise HTTPException(status_code=400, detail="Inactive user")
    # return user
    return current_user_id


# Type aliases for dependency injection
DatabaseDep = Annotated[AsyncSession, Depends(get_db)]
CurrentUserDep = Annotated[str, Depends(get_current_user_id)]
CurrentActiveUserDep = Annotated[Any, Depends(get_current_active_user)]
