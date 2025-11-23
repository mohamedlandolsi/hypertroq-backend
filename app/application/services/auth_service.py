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
from app.infrastructure.cache.token_storage import token_storage
from app.infrastructure.tasks import (
    send_password_reset_email,
    send_email_verification,
    send_welcome_email,
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
        
        Generates a secure token, stores it in Redis, and sends reset email.
        Always succeeds to prevent email enumeration.
        
        Args:
            email: User email address
        """
        try:
            # Get user by email
            user = await self.user_service.get_user_by_email(email)
            
            if user:
                # Generate and store reset token in Redis
                reset_token = await token_storage.generate_password_reset_token(user.id)
                
                # Send password reset email via Celery
                send_password_reset_email.delay(
                    email=user.email,
                    reset_token=reset_token,
                    user_name=user.full_name
                )
                
                logger.info(f"Password reset email queued for {email}")
        except Exception as e:
            # Log error but don't expose it to prevent enumeration
            logger.error(f"Error in password reset request: {str(e)}")
            pass

    async def confirm_password_reset(self, token: str, new_password: str) -> None:
        """
        Confirm password reset with token and set new password.
        
        Args:
            token: Password reset token from Redis
            new_password: New password to set
            
        Raises:
            HTTPException: If token is invalid or expired
        """
        try:
            # Verify token from Redis
            user_id = await token_storage.verify_password_reset_token(token)
            
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired reset token"
                )
            
            # Get user
            user = await self.user_service.get_user(user_id)
            
            # Update password
            hashed_password = hash_password(new_password)
            await self.user_service.update_user(
                user_id,
                {"hashed_password": hashed_password}
            )
            
            # Invalidate all password reset tokens for this user
            await token_storage.invalidate_all_password_reset_tokens_for_user(user_id)
            
            logger.info(f"Password reset successful for user {user_id}")
            
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
        Verify user email with verification token from Redis.
        
        Args:
            token: Email verification token from Redis
            
        Returns:
            True if verification successful
            
        Raises:
            HTTPException: If token is invalid or expired
        """
        try:
            # Verify token from Redis
            result = await token_storage.verify_email_verification_token(token)
            
            if not result:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired verification token"
                )
            
            user_id, email = result
            
            # Update user verification status
            await self.user_service.verify_user_email(user_id)
            
            # Invalidate the token
            await token_storage.invalidate_email_verification_token(token)
            
            # Send welcome email
            user = await self.user_service.get_user(user_id)
            send_welcome_email.delay(
                email=user.email,
                user_name=user.full_name
            )
            
            logger.info(f"Email verified successfully for user {user_id}")
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error verifying email: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired verification token"
            )
