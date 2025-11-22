"""
Authentication API routes.

Provides endpoints for user authentication, registration,
token management, email verification, and password reset.

All authentication endpoints include rate limiting to prevent
brute force attacks and abuse.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, status

from app.core.dependencies import (
    CurrentUserDep,
    DatabaseDep,
)
from app.infrastructure.cache.rate_limiter import (
    auth_rate_limit,
    register_rate_limit,
    strict_auth_rate_limit,
)
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    MessageResponse,
    PasswordReset,
    PasswordResetConfirm,
    TokenRefresh,
    TokenResponse,
    UserLogin,
    UserRegister,
    UserResponse,
)
from app.services.auth_service import AuthService

# Configure logging
logger = logging.getLogger(__name__)

# Create router with prefix and tags
router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
    responses={
        429: {
            "description": "Too Many Requests - Rate limit exceeded",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Rate limit exceeded. Maximum 10 requests per 60 seconds."
                    }
                }
            },
        },
    },
)


def get_auth_service(db: DatabaseDep) -> AuthService:
    """
    Create AuthService instance with repositories.
    
    Args:
        db: Database session from dependency injection
        
    Returns:
        Configured AuthService instance
    """
    user_repo = UserRepository(db)
    org_repo = OrganizationRepository(db)
    return AuthService(user_repo, org_repo)


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(register_rate_limit)],
    summary="Register new user",
    description="""
    Register a new user account with organization.
    
    This endpoint:
    - Validates email format and password strength
    - Creates a new organization for the user
    - Creates user as admin of the organization
    - Generates JWT access and refresh tokens
    - Sends email verification (if configured)
    
    **Rate Limit:** 3 requests per 5 minutes per IP
    
    **Password Requirements:**
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    """,
    responses={
        201: {
            "description": "User successfully registered",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "token_type": "bearer",
                    }
                }
            },
        },
        400: {
            "description": "Bad Request - Email already exists or invalid data",
            "content": {
                "application/json": {
                    "example": {"detail": "An account with this email already exists"}
                }
            },
        },
        422: {
            "description": "Validation Error - Invalid input format",
        },
    },
)
async def register(
    user_data: UserRegister,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    """
    Register a new user with organization.
    
    Creates both user account and organization, then returns JWT tokens.
    """
    try:
        logger.info(f"Registration request received for email: {user_data.email}")
        
        token_response = await auth_service.register(
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.full_name,
            organization_name=user_data.organization_name,
        )
        
        logger.info(f"Registration successful for email: {user_data.email}")
        return token_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed. Please try again later.",
        )


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(auth_rate_limit)],
    summary="Login user",
    description="""
    Authenticate user and receive JWT tokens.
    
    This endpoint:
    - Validates user credentials
    - Checks if account is active
    - Generates new JWT access and refresh tokens
    
    **Rate Limit:** 10 requests per minute per IP
    
    The access token should be included in the Authorization header
    for subsequent API requests:
    ```
    Authorization: Bearer <access_token>
    ```
    """,
    responses={
        200: {
            "description": "Login successful",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "token_type": "bearer",
                    }
                }
            },
        },
        401: {
            "description": "Unauthorized - Invalid credentials",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid email or password"}
                }
            },
        },
        403: {
            "description": "Forbidden - Account inactive",
            "content": {
                "application/json": {
                    "example": {"detail": "Your account has been deactivated. Please contact support."}
                }
            },
        },
    },
)
async def login(
    credentials: UserLogin,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    """
    Login with email and password.
    
    Returns JWT access and refresh tokens for authentication.
    """
    try:
        logger.info(f"Login request received for email: {credentials.email}")
        
        token_response = await auth_service.login(
            email=credentials.email,
            password=credentials.password,
        )
        
        logger.info(f"Login successful for email: {credentials.email}")
        return token_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed. Please try again later.",
        )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(auth_rate_limit)],
    summary="Refresh access token",
    description="""
    Get a new access token using a valid refresh token.
    
    This endpoint:
    - Validates the refresh token
    - Verifies user still exists and is active
    - Generates a new access token
    - Returns the same refresh token
    
    **Rate Limit:** 10 requests per minute per IP
    
    Use this endpoint when the access token expires to get a new one
    without requiring the user to login again.
    """,
    responses={
        200: {
            "description": "Token refreshed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "token_type": "bearer",
                    }
                }
            },
        },
        401: {
            "description": "Unauthorized - Invalid or expired refresh token",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid or expired token"}
                }
            },
        },
    },
)
async def refresh_token(
    token_data: TokenRefresh,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    """
    Refresh access token using refresh token.
    
    Validates refresh token and returns new access token.
    """
    try:
        logger.info("Token refresh request received")
        
        token_response = await auth_service.refresh_token(
            refresh_token=token_data.refresh_token
        )
        
        logger.info("Token refresh successful")
        return token_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed. Please try again later.",
        )


@router.post(
    "/verify-email/{token}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify email address",
    description="""
    Verify user's email address using verification token.
    
    This endpoint:
    - Validates the verification token
    - Checks token hasn't expired (24 hour window)
    - Updates user's is_verified status to True
    - Invalidates the token (single-use)
    
    The verification token is sent to the user's email after registration.
    """,
    responses={
        200: {
            "description": "Email verified successfully",
            "content": {
                "application/json": {
                    "example": {"message": "Email verified successfully"}
                }
            },
        },
        401: {
            "description": "Unauthorized - Invalid or expired token",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid or expired verification token"}
                }
            },
        },
        404: {
            "description": "Not Found - User not found",
        },
    },
)
async def verify_email(
    token: Annotated[str, Path(description="Email verification token from email")],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> MessageResponse:
    """
    Verify user's email address.
    
    Uses token from verification email to mark email as verified.
    """
    try:
        logger.info(f"Email verification request received")
        
        success = await auth_service.verify_email(token=token)
        
        if success:
            logger.info("Email verification successful")
            return MessageResponse(message="Email verified successfully")
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email verification failed",
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Email verification failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email verification failed. Please try again later.",
        )


@router.post(
    "/password-reset/request",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(strict_auth_rate_limit)],
    summary="Request password reset",
    description="""
    Initiate password reset process.
    
    This endpoint:
    - Generates a secure reset token
    - Sends password reset email (if user exists)
    - Always returns success (prevents user enumeration)
    
    **Rate Limit:** 5 requests per minute per IP
    
    If the email exists in the system, a password reset link will be
    sent to that address. The link expires after 1 hour.
    
    For security, this endpoint always returns success even if the
    email doesn't exist in the system.
    """,
    responses={
        200: {
            "description": "Reset email sent (or would be sent if user exists)",
            "content": {
                "application/json": {
                    "example": {
                        "message": "If an account exists with this email, a password reset link has been sent."
                    }
                }
            },
        },
    },
)
async def request_password_reset(
    reset_data: PasswordReset,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> MessageResponse:
    """
    Request password reset email.
    
    Sends reset link to email if account exists (always returns success).
    """
    try:
        logger.info(f"Password reset request for email: {reset_data.email}")
        
        await auth_service.request_password_reset(email=reset_data.email)
        
        # Always return success to prevent user enumeration
        return MessageResponse(
            message="If an account exists with this email, a password reset link has been sent."
        )
        
    except Exception as e:
        logger.error(f"Password reset request failed: {str(e)}")
        # Still return success to prevent user enumeration
        return MessageResponse(
            message="If an account exists with this email, a password reset link has been sent."
        )


@router.post(
    "/password-reset/confirm",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(auth_rate_limit)],
    summary="Confirm password reset",
    description="""
    Complete password reset process with token and new password.
    
    This endpoint:
    - Validates the reset token
    - Checks token hasn't expired (1 hour window)
    - Validates new password strength
    - Updates user's password
    - Invalidates the token (single-use)
    
    **Rate Limit:** 10 requests per minute per IP
    
    **Password Requirements:**
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    """,
    responses={
        200: {
            "description": "Password reset successfully",
            "content": {
                "application/json": {
                    "example": {"message": "Password reset successfully"}
                }
            },
        },
        401: {
            "description": "Unauthorized - Invalid or expired token",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid or expired reset token"}
                }
            },
        },
        404: {
            "description": "Not Found - User not found",
        },
    },
)
async def confirm_password_reset(
    reset_data: PasswordResetConfirm,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> MessageResponse:
    """
    Reset password using token and new password.
    
    Validates token and updates user's password.
    """
    try:
        logger.info("Password reset confirmation request received")
        
        success = await auth_service.reset_password(
            token=reset_data.token,
            new_password=reset_data.new_password,
        )
        
        if success:
            logger.info("Password reset successful")
            return MessageResponse(message="Password reset successfully")
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password reset failed",
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password reset confirmation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset failed. Please try again later.",
        )


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current user",
    description="""
    Get information about the currently authenticated user.
    
    This endpoint:
    - Requires valid JWT access token
    - Returns user information (excluding sensitive data)
    
    **Authentication Required:** Yes
    
    Include your access token in the Authorization header:
    ```
    Authorization: Bearer <access_token>
    ```
    """,
    responses={
        200: {
            "description": "Current user information",
            "content": {
                "application/json": {
                    "example": {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "email": "john.doe@example.com",
                        "full_name": "John Doe",
                        "role": "ADMIN",
                        "organization_id": "660e8400-e29b-41d4-a716-446655440000",
                        "is_verified": True,
                    }
                }
            },
        },
        401: {
            "description": "Unauthorized - Invalid or missing token",
            "content": {
                "application/json": {
                    "example": {"detail": "Could not validate credentials"}
                }
            },
        },
    },
)
async def get_current_user(
    current_user: CurrentUserDep,
) -> UserResponse:
    """
    Get current authenticated user information.
    
    Returns user data excluding sensitive information.
    """
    try:
        return UserResponse(
            id=current_user.id,
            email=current_user.email,
            full_name=current_user.full_name,
            role=current_user.role,
            organization_id=current_user.organization_id,
            is_verified=current_user.is_verified,
        )
        
    except Exception as e:
        logger.error(f"Failed to get current user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user information",
        )
