"""Authentication service."""
from fastapi import HTTPException, status

from app.domain.entities.user import User
from app.application.dtos.auth_dto import TokenDTO, LoginDTO
from app.application.services.user_service import UserService
from app.core.security import create_access_token, create_refresh_token, decode_token, verify_token_type


class AuthService:
    """Service for authentication logic."""

    def __init__(self, user_service: UserService) -> None:
        """Initialize auth service."""
        self.user_service = user_service

    async def login(self, login_data: LoginDTO) -> TokenDTO:
        """Authenticate user and return tokens with organization context."""
        user = await self.user_service.authenticate_user(
            login_data.email,
            login_data.password
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )

        # Create tokens with organization context
        token_data = {
            "user_id": str(user.id),
            "organization_id": str(user.organization_id),
            "role": user.role.value,
        }
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        return TokenDTO(
            access_token=access_token,
            refresh_token=refresh_token,
        )

    async def refresh_token(self, refresh_token: str) -> TokenDTO:
        """Refresh access token using refresh token."""
        payload = decode_token(refresh_token)
        verify_token_type(payload, "refresh")
        
        user_id = payload.get("user_id")
        organization_id = payload.get("organization_id")
        role = payload.get("role")
        
        if not user_id or not organization_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )

        # Create new tokens with same context
        token_data = {
            "user_id": user_id,
            "organization_id": organization_id,
            "role": role,
        }
        access_token = create_access_token(token_data)
        new_refresh_token = create_refresh_token(token_data)

        return TokenDTO(
            access_token=access_token,
            refresh_token=new_refresh_token,
        )
