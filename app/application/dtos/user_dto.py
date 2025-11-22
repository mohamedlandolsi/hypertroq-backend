"""User DTOs (Data Transfer Objects)."""
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field
from app.domain.entities.user import UserRole


class UserCreateDTO(BaseModel):
    """DTO for creating a new user."""
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str
    organization_id: UUID


class UserUpdateDTO(BaseModel):
    """DTO for updating user information."""
    email: EmailStr | None = None
    full_name: str | None = None
    password: str | None = Field(None, min_length=8)
    profile_image_url: str | None = None


class UserResponseDTO(BaseModel):
    """DTO for user response."""
    id: UUID
    email: str
    full_name: str
    organization_id: UUID
    role: UserRole
    is_active: bool
    is_verified: bool
    profile_image_url: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
