"""Authentication DTOs."""
from pydantic import BaseModel, EmailStr, Field


class TokenDTO(BaseModel):
    """DTO for authentication tokens."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefreshDTO(BaseModel):
    """DTO for refreshing tokens."""
    refresh_token: str


class LoginDTO(BaseModel):
    """DTO for user login."""
    email: str
    password: str


class PasswordResetRequestDTO(BaseModel):
    """DTO for requesting password reset."""
    email: EmailStr


class PasswordResetConfirmDTO(BaseModel):
    """DTO for confirming password reset."""
    token: str
    new_password: str = Field(..., min_length=8)


class EmailVerificationDTO(BaseModel):
    """DTO for email verification response."""
    message: str
    email_verified: bool
