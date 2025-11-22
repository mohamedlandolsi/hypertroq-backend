"""SQLAlchemy Organization model."""
from typing import List
from sqlalchemy import String, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import BaseModel
from app.domain.entities.organization import SubscriptionTier, SubscriptionStatus


class OrganizationModel(BaseModel):
    """SQLAlchemy Organization model mapping to organizations table."""

    __tablename__ = "organizations"

    # Basic Information
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Organization name"
    )

    # Subscription Information
    subscription_tier: Mapped[str] = mapped_column(
        SQLEnum(SubscriptionTier, name="subscription_tier"),
        default=SubscriptionTier.FREE,
        nullable=False,
        doc="Subscription tier (FREE or PRO)"
    )

    subscription_status: Mapped[str] = mapped_column(
        SQLEnum(SubscriptionStatus, name="subscription_status"),
        default=SubscriptionStatus.ACTIVE,
        nullable=False,
        doc="Current subscription status (ACTIVE, CANCELED, or EXPIRED)"
    )

    # LemonSqueezy Integration
    lemonsqueezy_customer_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
        index=True,
        doc="LemonSqueezy customer ID"
    )

    lemonsqueezy_subscription_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
        index=True,
        doc="LemonSqueezy subscription ID"
    )

    # Relationships
    users: Mapped[List["UserModel"]] = relationship(
        "UserModel",
        back_populates="organization",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Organization(id={self.id}, name={self.name}, tier={self.subscription_tier})>"
