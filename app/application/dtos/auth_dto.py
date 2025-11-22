"""Authentication DTOs."""
from pydantic import BaseModel


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
