"""
Authentication Pydantic schemas for request/response validation.

Includes comprehensive validation for email format, password strength,
and field length constraints.
"""

import re
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


# ==================== Request Schemas ====================


class UserRegister(BaseModel):
    """
    User registration request schema.
    
    Validates email format, password strength, and field lengths.
    Creates a new user account and associated organization.
    """

    email: EmailStr = Field(
        ...,
        description="User's email address (must be unique)",
        examples=["john.doe@example.com"],
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password (min 8 chars, must include uppercase, lowercase, digit, special char)",
        examples=["<your_secure_password>"],
    )
    full_name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="User's full name",
        examples=["John Doe"],
    )
    organization_name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Name of the organization to create",
        examples=["Acme Fitness"],
    )

    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "email": "john.doe@example.com",
                "password": "<your_secure_password>",
                "full_name": "John Doe",
                "organization_name": "Acme Fitness",
            }
        },
    )

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """
        Validate password meets security requirements.
        
        Requirements:
        - At least 8 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        - At least one special character
        """
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")

        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")

        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")

        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")

        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain at least one special character")

        return v

    @field_validator("full_name", "organization_name")
    @classmethod
    def validate_name_fields(cls, v: str) -> str:
        """Validate name fields are not empty or just whitespace."""
        if not v or not v.strip():
            raise ValueError("Field cannot be empty or contain only whitespace")
        return v.strip()


class UserLogin(BaseModel):
    """
    User login request schema.
    
    Authenticates user and returns access/refresh tokens.
    """

    email: EmailStr = Field(
        ...,
        description="User's email address",
        examples=["john.doe@example.com"],
    )
    password: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="User's password",
        examples=["<your_password>"],
    )

    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "email": "john.doe@example.com",
                "password": "<your_password>",
            }
        },
    )


class TokenRefresh(BaseModel):
    """
    Token refresh request schema.
    
    Exchanges a valid refresh token for a new access token.
    """

    refresh_token: str = Field(
        ...,
        min_length=1,
        description="Valid JWT refresh token",
        examples=["<your_refresh_token>"],
    )

    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "refresh_token": "<your_refresh_token>",
            }
        },
    )


class PasswordReset(BaseModel):
    """
    Password reset request schema.
    
    Initiates password reset process by sending email with reset token.
    """

    email: EmailStr = Field(
        ...,
        description="Email address of account to reset password for",
        examples=["john.doe@example.com"],
    )

    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "email": "john.doe@example.com",
            }
        },
    )


class PasswordResetConfirm(BaseModel):
    """
    Password reset confirmation schema.
    
    Completes password reset using token from email and new password.
    """

    token: str = Field(
        ...,
        min_length=1,
        description="Password reset token from email",
        examples=["<reset_token_from_email>"],
    )
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="New password (min 8 chars, must include uppercase, lowercase, digit, special char)",
        examples=["<your_new_password>"],
    )

    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "token": "<reset_token_from_email>",
                "new_password": "<your_new_password>",
            }
        },
    )

    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """
        Validate password meets security requirements.
        
        Requirements:
        - At least 8 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        - At least one special character
        """
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")

        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")

        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")

        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")

        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain at least one special character")

        return v


# ==================== Response Schemas ====================


class TokenResponse(BaseModel):
    """
    JWT token response schema.
    
    Returned after successful login or token refresh.
    """

    access_token: str = Field(
        ...,
        description="JWT access token for API authentication (short-lived)",
        examples=["<jwt_access_token>"],
    )
    refresh_token: str = Field(
        ...,
        description="JWT refresh token for obtaining new access tokens (long-lived)",
        examples=["<jwt_refresh_token>"],
    )
    token_type: Literal["bearer"] = Field(
        default="bearer",
        description="Token type for Authorization header",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "<jwt_access_token>",
                "refresh_token": "<jwt_refresh_token>",
                "token_type": "bearer",
            }
        }
    )


class UserResponse(BaseModel):
    """
    User information response schema.
    
    Returns safe user data (excludes sensitive fields like password).
    """

    id: UUID = Field(
        ...,
        description="Unique user identifier",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    email: str = Field(
        ...,
        description="User's email address",
        examples=["john.doe@example.com"],
    )
    full_name: str = Field(
        ...,
        description="User's full name",
        examples=["John Doe"],
    )
    role: str = Field(
        ...,
        description="User's role in organization (admin, coach, member)",
        examples=["admin"],
    )
    organization_id: UUID = Field(
        ...,
        description="ID of organization user belongs to",
        examples=["660e8400-e29b-41d4-a716-446655440000"],
    )
    is_verified: bool = Field(
        ...,
        description="Whether user's email has been verified",
        examples=[True],
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "john.doe@example.com",
                "full_name": "John Doe",
                "role": "admin",
                "organization_id": "660e8400-e29b-41d4-a716-446655440000",
                "is_verified": True,
            }
        },
    )


class MessageResponse(BaseModel):
    """
    Generic message response schema.
    
    Used for simple success/info messages (e.g., password reset email sent).
    """

    message: str = Field(
        ...,
        description="Response message",
        examples=["Password reset email sent successfully"],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Operation completed successfully",
            }
        }
    )
