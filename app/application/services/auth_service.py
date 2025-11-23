"""Authentication service."""
import logging
from uuid import UUID
from fastapi import HTTPException, status

from app.domain.entities.user import User
from app.application.dtos.auth_dto import TokenDTO, LoginDTO
from app.application.services.user_service import UserService
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_token_type,
    generate_secure_token,
    hash_password,
)

logger = logging.getLogger(__name__)


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

    async def request_password_reset(self, email: str) -> None:
        """
        Request password reset for user.
        
        Note: Always succeeds to prevent email enumeration.
        In production, this would send an email with a reset token.
        """
        try:
            # Get user by email
            user = await self.user_service.get_user_by_email(email)
            
            if user:
                # Generate reset token
                reset_token = generate_secure_token(32)
                
                # In production: 
                # 1. Store token in database/cache with expiration (e.g., 1 hour)
                # 2. Send email with reset link containing token
                # For now, just log it
                logger.info(f"Password reset requested for {email}. Token: {reset_token}")
                
                # TODO: Implement email sending via Celery task
                # await send_password_reset_email(user.email, reset_token)
        except Exception as e:
            # Log error but don't expose it to prevent enumeration
            logger.error(f"Error in password reset request: {str(e)}")
            pass

    async def confirm_password_reset(self, token: str, new_password: str) -> None:
        """
        Confirm password reset with token and set new password.
        
        Args:
            token: Password reset token
            new_password: New password to set
            
        Raises:
            HTTPException: If token is invalid or expired
        """
        # In production: Verify token from database/cache
        # For now, we'll decode it as a JWT (temporary implementation)
        try:
            # TODO: Implement proper token verification from database/cache
            # For now, raise an error as tokens aren't stored yet
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired reset token"
            )
            
            # Future implementation:
            # 1. Verify token exists in cache/database
            # 2. Check if token hasn't expired
            # 3. Get user_id from token
            # 4. Update user password
            # 5. Invalidate the token
            # 6. Optionally invalidate all existing tokens
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error confirming password reset: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired reset token"
            )

    async def verify_email(self, token: str) -> bool:
        """
        Verify user email with verification token.
        
        Args:
            token: Email verification token
            
        Returns:
            True if verification successful
            
        Raises:
            HTTPException: If token is invalid or expired
        """
        try:
            # In production: Verify token from database/cache
            # For now, decode as JWT to get user_id
            payload = decode_token(token)
            user_id_str = payload.get("user_id") or payload.get("sub")
            
            if not user_id_str:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid verification token"
                )
            
            user_id = UUID(user_id_str)
            
            # Update user verification status
            await self.user_service.verify_user_email(user_id)
            
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error verifying email: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired verification token"
            )
