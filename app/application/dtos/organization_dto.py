"""Organization DTOs (Data Transfer Objects)."""
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field
from app.domain.entities.organization import SubscriptionTier, SubscriptionStatus


class OrganizationCreateDTO(BaseModel):
    """DTO for creating a new organization."""
    name: str = Field(..., min_length=1, max_length=255)


class OrganizationUpdateDTO(BaseModel):
    """DTO for updating organization information."""
    name: str | None = Field(None, min_length=1, max_length=255)


class OrganizationSubscriptionUpdateDTO(BaseModel):
    """DTO for updating organization subscription."""
    subscription_tier: SubscriptionTier
    subscription_status: SubscriptionStatus
    lemonsqueezy_customer_id: str | None = None
    lemonsqueezy_subscription_id: str | None = None


class OrganizationResponseDTO(BaseModel):
    """DTO for organization response."""
    id: UUID
    name: str
    subscription_tier: SubscriptionTier
    subscription_status: SubscriptionStatus
    lemonsqueezy_customer_id: str | None
    lemonsqueezy_subscription_id: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OrganizationWithStatsDTO(OrganizationResponseDTO):
    """DTO for organization with statistics."""
    user_count: int
    can_create_custom_exercises: bool
    can_create_programs: bool
    has_unlimited_ai_queries: bool
