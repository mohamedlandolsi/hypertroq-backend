"""
Authentication service for user registration, login, and token management.

Implements business logic for authentication flows including:
- User registration with organization creation
- Login with credential verification
- Token generation and refresh
- Email verification
- Password reset functionality

All security-sensitive operations are logged for audit purposes.
Token storage uses Redis for distributed systems support.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_secure_token,
    get_password_hash,
    verify_password,
    verify_token_type,
    verify_token_subject,
)
from app.infrastructure.cache.redis_client import redis_client
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import TokenResponse, UserResponse

# Configure logging for security events
logger = logging.getLogger(__name__)


class AuthenticationError(HTTPException):
    """Custom exception for authentication failures."""

    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class RegistrationError(HTTPException):
    """Custom exception for registration failures."""

    def __init__(self, detail: str = "Registration failed"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )


class TokenError(HTTPException):
    """Custom exception for token-related errors."""

    def __init__(self, detail: str = "Invalid or expired token"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class AuthService:
    """
    Authentication service handling user registration, login, and token management.
    
    This service coordinates between user and organization repositories to
    implement authentication workflows while maintaining business logic
    separation from data access.
    
    Token storage uses Redis for scalability across multiple instances.
    Falls back to in-memory storage if Redis is unavailable.
    """

    # In-memory fallback storage (used only if Redis unavailable)
    _verification_tokens: dict[str, dict] = {}
    _reset_tokens: dict[str, dict] = {}

    def __init__(
        self,
        user_repository: UserRepository,
        organization_repository: OrganizationRepository,
    ) -> None:
        """
        Initialize authentication service with required repositories.
        
        Args:
            user_repository: Repository for user data access
            organization_repository: Repository for organization data access
        """
        self._user_repo = user_repository
        self._org_repo = organization_repository

    async def _store_verification_token(
        self, token: str, user_id: UUID, email: str, expires_hours: int = 24
    ) -> None:
        """Store verification token in Redis or memory."""
        token_data = {
            "user_id": str(user_id),
            "email": email,
            "expires_at": (
                datetime.now(timezone.utc) + timedelta(hours=expires_hours)
            ).isoformat(),
        }
        
        if redis_client.redis:
            try:
                # Store in Redis with expiration
                await redis_client.redis.setex(
                    f"verification_token:{token}",
                    expires_hours * 3600,
                    str(token_data),
                )
            except Exception as e:
                logger.warning(f"Failed to store token in Redis: {e}. Using memory fallback.")
                self._verification_tokens[token] = {
                    "user_id": user_id,
                    "email": email,
                    "expires_at": datetime.now(timezone.utc) + timedelta(hours=expires_hours),
                }
        else:
            # Fallback to in-memory
            self._verification_tokens[token] = {
                "user_id": user_id,
                "email": email,
                "expires_at": datetime.now(timezone.utc) + timedelta(hours=expires_hours),
            }

    async def _get_verification_token(self, token: str) -> Optional[dict]:
        """Get verification token from Redis or memory."""
        if redis_client.redis:
            try:
                token_data = await redis_client.redis.get(f"verification_token:{token}")
                if token_data:
                    import ast
                    return ast.literal_eval(token_data)
            except Exception as e:
                logger.warning(f"Failed to get token from Redis: {e}. Checking memory fallback.")
        
        return self._verification_tokens.get(token)

    async def _delete_verification_token(self, token: str) -> None:
        """Delete verification token from Redis or memory."""
        if redis_client.redis:
            try:
                await redis_client.redis.delete(f"verification_token:{token}")
            except Exception as e:
                logger.warning(f"Failed to delete token from Redis: {e}")
        
        self._verification_tokens.pop(token, None)

    async def _store_reset_token(
        self, token: str, user_id: UUID, email: str, expires_hours: int = 1
    ) -> None:
        """Store password reset token in Redis or memory."""
        token_data = {
            "user_id": str(user_id),
            "email": email,
            "expires_at": (
                datetime.now(timezone.utc) + timedelta(hours=expires_hours)
            ).isoformat(),
        }
        
        if redis_client.redis:
            try:
                await redis_client.redis.setex(
                    f"reset_token:{token}",
                    expires_hours * 3600,
                    str(token_data),
                )
            except Exception as e:
                logger.warning(f"Failed to store reset token in Redis: {e}. Using memory fallback.")
                self._reset_tokens[token] = {
                    "user_id": user_id,
                    "email": email,
                    "expires_at": datetime.now(timezone.utc) + timedelta(hours=expires_hours),
                }
        else:
            self._reset_tokens[token] = {
                "user_id": user_id,
                "email": email,
                "expires_at": datetime.now(timezone.utc) + timedelta(hours=expires_hours),
            }

    async def _get_reset_token(self, token: str) -> Optional[dict]:
        """Get password reset token from Redis or memory."""
        if redis_client.redis:
            try:
                token_data = await redis_client.redis.get(f"reset_token:{token}")
                if token_data:
                    import ast
                    return ast.literal_eval(token_data)
            except Exception as e:
                logger.warning(f"Failed to get reset token from Redis: {e}. Checking memory fallback.")
        
        return self._reset_tokens.get(token)

    async def _delete_reset_token(self, token: str) -> None:
        """Delete password reset token from Redis or memory."""
        if redis_client.redis:
            try:
                await redis_client.redis.delete(f"reset_token:{token}")
            except Exception as e:
                logger.warning(f"Failed to delete reset token from Redis: {e}")
        
        self._reset_tokens.pop(token, None)

    async def register(
        self,
        email: str,
        password: str,
        full_name: str,
        organization_name: str,
    ) -> TokenResponse:
        """
        Register a new user with a new organization.
        
        Process:
        1. Validate email is not already registered
        2. Hash password securely
        3. Create new organization
        4. Create user as admin of organization
        5. Generate access and refresh tokens
        6. Send verification email (stub for now)
        
        Args:
            email: User's email address (will be validated by schema)
            password: Plain text password (will be hashed)
            full_name: User's full name
            organization_name: Name for new organization
            
        Returns:
            TokenResponse containing access_token, refresh_token, and token_type
            
        Raises:
            RegistrationError: If email already exists or registration fails
            
        Security:
            - Logs registration attempts for audit
            - Uses bcrypt for password hashing
            - Generates secure random tokens
        """
        logger.info(f"Registration attempt for email: {email}")

        try:
            # Check if email already exists
            if await self._user_repo.exists_by_email(email):
                logger.warning(f"Registration failed: Email already exists - {email}")
                raise RegistrationError(
                    detail="An account with this email already exists"
                )

            # Hash password
            hashed_password = get_password_hash(password)

            # Create organization
            org_data = {
                "name": organization_name,
                "subscription_tier": "FREE",
                "subscription_status": "ACTIVE",
            }
            organization = await self._org_repo.create(org_data)
            logger.info(
                f"Organization created: {organization.id} - {organization.name}"
            )

            # Create user as admin
            user_data = {
                "email": email,
                "hashed_password": hashed_password,
                "full_name": full_name,
                "organization_id": organization.id,
                "role": "ADMIN",
                "is_active": True,
                "is_verified": False,
            }
            user = await self._user_repo.create(user_data)
            logger.info(f"User created: {user.id} - {user.email}")

            # Generate verification token
            verification_token = generate_secure_token()
            await self._store_verification_token(
                token=verification_token,
                user_id=user.id,
                email=email,
                expires_hours=24,
            )
            logger.info(f"Verification token generated for user: {user.id}")

            # TODO: Send verification email
            # await self._send_verification_email(email, verification_token)
            logger.info(f"Verification email stub called for: {email}")

            # Generate tokens
            token_data = {
                "user_id": str(user.id),
                "organization_id": str(organization.id),
                "role": user.role,
            }
            access_token = create_access_token(subject=token_data)
            refresh_token = create_refresh_token(subject=token_data)

            logger.info(f"Registration successful for user: {user.id}")
            return TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="bearer",
            )

        except IntegrityError as e:
            logger.error(f"Database integrity error during registration: {str(e)}")
            raise RegistrationError(
                detail="Registration failed due to data conflict"
            ) from e
        except SQLAlchemyError as e:
            logger.error(f"Database error during registration: {str(e)}")
            raise RegistrationError(
                detail="Registration failed due to database error"
            ) from e
        except RegistrationError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during registration: {str(e)}")
            raise RegistrationError(detail="Registration failed") from e

    async def login(self, email: str, password: str) -> TokenResponse:
        """
        Authenticate user and generate tokens.
        
        Process:
        1. Verify user exists
        2. Verify password
        3. Check if user is active
        4. Generate access and refresh tokens
        
        Args:
            email: User's email address
            password: Plain text password
            
        Returns:
            TokenResponse containing access_token, refresh_token, and token_type
            
        Raises:
            AuthenticationError: If credentials are invalid or account is inactive
            
        Security:
            - Logs all login attempts
            - Uses constant-time password comparison
            - Returns generic error message to prevent user enumeration
        """
        logger.info(f"Login attempt for email: {email}")

        try:
            # Get user by email
            user = await self._user_repo.get_by_email(email)
            if not user:
                logger.warning(f"Login failed: User not found - {email}")
                raise AuthenticationError(detail="Invalid email or password")

            # Verify password
            if not verify_password(password, user.hashed_password):
                logger.warning(f"Login failed: Invalid password - {email}")
                raise AuthenticationError(detail="Invalid email or password")

            # Check if user is active
            if not user.is_active:
                logger.warning(f"Login failed: Account inactive - {email}")
                raise AuthenticationError(
                    detail="Your account has been deactivated. Please contact support."
                )

            # Generate tokens
            token_data = {
                "user_id": str(user.id),
                "organization_id": str(user.organization_id),
                "role": user.role,
            }
            access_token = create_access_token(subject=token_data)
            refresh_token = create_refresh_token(subject=token_data)

            logger.info(f"Login successful for user: {user.id}")
            return TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="bearer",
            )

        except AuthenticationError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during login: {str(e)}")
            raise AuthenticationError(detail="Login failed") from e

    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        """
        Generate new access token using refresh token.
        
        Process:
        1. Decode and validate refresh token
        2. Verify token type is 'refresh'
        3. Extract user information
        4. Generate new access token
        
        Args:
            refresh_token: Valid JWT refresh token
            
        Returns:
            TokenResponse with new access_token (refresh_token unchanged)
            
        Raises:
            TokenError: If refresh token is invalid or expired
            
        Security:
            - Validates token signature
            - Checks token type
            - Logs token refresh events
        """
        logger.info("Token refresh attempt")

        try:
            # Decode and validate token
            payload = decode_token(refresh_token)

            # Verify token type
            verify_token_type(payload, "refresh")

            # Extract user information
            user_id = verify_token_subject(payload)
            organization_id = payload.get("organization_id")
            role = payload.get("role")

            # Verify user still exists and is active
            user = await self._user_repo.get_by_id(UUID(user_id))
            if not user:
                logger.warning(f"Token refresh failed: User not found - {user_id}")
                raise TokenError(detail="User not found")

            if not user.is_active:
                logger.warning(f"Token refresh failed: User inactive - {user_id}")
                raise TokenError(detail="Account is inactive")

            # Generate new access token
            token_data = {
                "user_id": str(user_id),
                "organization_id": str(organization_id or user.organization_id),
                "role": role or user.role,
            }
            new_access_token = create_access_token(subject=token_data)

            logger.info(f"Token refresh successful for user: {user_id}")
            return TokenResponse(
                access_token=new_access_token,
                refresh_token=refresh_token,
                token_type="bearer",
            )

        except (TokenError, HTTPException):
            raise
        except Exception as e:
            logger.error(f"Unexpected error during token refresh: {str(e)}")
            raise TokenError(detail="Token refresh failed") from e

    async def verify_email(self, token: str) -> bool:
        """
        Verify user email using verification token.
        
        Process:
        1. Validate token exists and hasn't expired
        2. Get user from token
        3. Update user.is_verified to True
        4. Invalidate token
        
        Args:
            token: Email verification token from email link
            
        Returns:
            True if verification successful
            
        Raises:
            TokenError: If token is invalid or expired
            HTTPException: If user not found or update fails
            
        Security:
            - Tokens expire after 24 hours
            - Single-use tokens (invalidated after use)
            - Logs verification attempts
        """
        logger.info("Email verification attempt")

        try:
            # Check if token exists
            token_data = await self._get_verification_token(token)
            if not token_data:
                logger.warning("Email verification failed: Invalid token")
                raise TokenError(detail="Invalid verification token")

            # Check if token has expired
            expires_at_str = token_data.get("expires_at")
            if isinstance(expires_at_str, str):
                expires_at = datetime.fromisoformat(expires_at_str)
            else:
                expires_at = expires_at_str
                
            if datetime.now(timezone.utc) > expires_at:
                logger.warning("Email verification failed: Token expired")
                await self._delete_verification_token(token)
                raise TokenError(detail="Verification token has expired")

            # Get user
            user_id_str = token_data.get("user_id")
            if isinstance(user_id_str, str):
                user_id = UUID(user_id_str)
            else:
                user_id = user_id_str
            user = await self._user_repo.get_by_id(user_id)
            if not user:
                logger.error(f"Email verification failed: User not found - {user_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found",
                )

            # Update user verification status
            updated_user = await self._user_repo.update(
                user_id, {"is_verified": True}
            )
            if not updated_user:
                logger.error(
                    f"Email verification failed: Update failed - {user_id}"
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to verify email",
                )

            # Invalidate token
            await self._delete_verification_token(token)

            logger.info(f"Email verification successful for user: {user_id}")
            return True

        except (TokenError, HTTPException):
            raise
        except Exception as e:
            logger.error(f"Unexpected error during email verification: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Email verification failed",
            ) from e

    async def request_password_reset(self, email: str) -> bool:
        """
        Initiate password reset process.
        
        Process:
        1. Check if user exists (silent fail for security)
        2. Generate reset token
        3. Store token with expiration
        4. Send password reset email (stub for now)
        
        Args:
            email: Email address of account to reset
            
        Returns:
            Always returns True (silent fail to prevent user enumeration)
            
        Security:
            - Always returns success even if email not found
            - Tokens expire after 1 hour
            - Logs reset requests for audit
            - Single-use tokens
        """
        logger.info(f"Password reset requested for email: {email}")

        try:
            # Check if user exists (but don't reveal if they don't)
            user = await self._user_repo.get_by_email(email)
            if not user:
                logger.info(
                    f"Password reset requested for non-existent email: {email}"
                )
                # Return True anyway to prevent user enumeration
                return True

            # Generate reset token
            reset_token = generate_secure_token()
            await self._store_reset_token(
                token=reset_token,
                user_id=user.id,
                email=email,
                expires_hours=1,
            )
            logger.info(f"Password reset token generated for user: {user.id}")

            # TODO: Send password reset email
            # await self._send_password_reset_email(email, reset_token)
            logger.info(f"Password reset email stub called for: {email}")

            return True

        except Exception as e:
            logger.error(f"Error during password reset request: {str(e)}")
            # Still return True to prevent information leakage
            return True

    async def reset_password(self, token: str, new_password: str) -> bool:
        """
        Complete password reset process.
        
        Process:
        1. Validate reset token
        2. Check token hasn't expired
        3. Hash new password
        4. Update user password
        5. Invalidate token
        
        Args:
            token: Password reset token from email
            new_password: New plain text password (will be hashed)
            
        Returns:
            True if password reset successful
            
        Raises:
            TokenError: If token is invalid or expired
            HTTPException: If user not found or update fails
            
        Security:
            - Tokens expire after 1 hour
            - Single-use tokens (invalidated after use)
            - Password is hashed before storage
            - Logs password reset events
        """
        logger.info("Password reset attempt")

        try:
            # Check if token exists
            token_data = await self._get_reset_token(token)
            if not token_data:
                logger.warning("Password reset failed: Invalid token")
                raise TokenError(detail="Invalid or expired reset token")

            # Check if token has expired
            expires_at_str = token_data.get("expires_at")
            if isinstance(expires_at_str, str):
                expires_at = datetime.fromisoformat(expires_at_str)
            else:
                expires_at = expires_at_str
                
            if datetime.now(timezone.utc) > expires_at:
                logger.warning("Password reset failed: Token expired")
                await self._delete_reset_token(token)
                raise TokenError(detail="Reset token has expired")

            # Get user
            user_id_str = token_data.get("user_id")
            if isinstance(user_id_str, str):
                user_id = UUID(user_id_str)
            else:
                user_id = user_id_str
            user = await self._user_repo.get_by_id(user_id)
            if not user:
                logger.error(f"Password reset failed: User not found - {user_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found",
                )

            # Hash new password
            hashed_password = get_password_hash(new_password)

            # Update user password
            updated_user = await self._user_repo.update(
                user_id, {"hashed_password": hashed_password}
            )
            if not updated_user:
                logger.error(f"Password reset failed: Update failed - {user_id}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to reset password",
                )

            # Invalidate token
            await self._delete_reset_token(token)

            logger.info(f"Password reset successful for user: {user_id}")
            return True

        except (TokenError, HTTPException):
            raise
        except Exception as e:
            logger.error(f"Unexpected error during password reset: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Password reset failed",
            ) from e

    async def get_current_user(self, user_id: UUID) -> Optional[UserResponse]:
        """
        Get current user information.
        
        Args:
            user_id: UUID of the user
            
        Returns:
            UserResponse with safe user data
            
        Raises:
            HTTPException: If user not found
        """
        user = await self._user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        return UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            organization_id=user.organization_id,
            is_verified=user.is_verified,
        )
