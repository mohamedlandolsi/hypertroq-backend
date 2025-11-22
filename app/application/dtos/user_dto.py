"""User DTOs (Data Transfer Objects)."""
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr


class UserCreateDTO(BaseModel):
    """DTO for creating a new user."""
    email: EmailStr
    password: str
    full_name: str | None = None


class UserUpdateDTO(BaseModel):
    """DTO for updating user information."""
    email: EmailStr | None = None
    full_name: str | None = None
    password: str | None = None


class UserResponseDTO(BaseModel):
    """DTO for user response."""
    id: UUID
    email: str
    full_name: str | None
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
