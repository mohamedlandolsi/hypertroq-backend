"""Organization entity."""
from datetime import datetime
from enum import Enum
from uuid import UUID
from app.domain.entities.base import Entity


class SubscriptionTier(str, Enum):
    """Subscription tier enumeration."""
    FREE = "FREE"
    PRO = "PRO"


class SubscriptionStatus(str, Enum):
    """Subscription status enumeration."""
    ACTIVE = "ACTIVE"
    CANCELED = "CANCELED"
    EXPIRED = "EXPIRED"


class Organization(Entity):
    """Organization domain entity."""

    def __init__(
        self,
        name: str,
        subscription_tier: SubscriptionTier = SubscriptionTier.FREE,
        subscription_status: SubscriptionStatus = SubscriptionStatus.ACTIVE,
        lemonsqueezy_customer_id: str | None = None,
        lemonsqueezy_subscription_id: str | None = None,
        id: UUID | None = None,
    ) -> None:
        """Initialize Organization entity.
        
        Args:
            name: Organization name
            subscription_tier: Subscription tier (FREE or PRO)
            subscription_status: Current subscription status
            lemonsqueezy_customer_id: LemonSqueezy customer ID
            lemonsqueezy_subscription_id: LemonSqueezy subscription ID
            id: Optional UUID (generated if not provided)
            
        Raises:
            ValueError: If name is empty
        """
        super().__init__(id)
        
        # Validate name
        if not name or not name.strip():
            raise ValueError("Organization name cannot be empty")
        
        self._name = name.strip()
        self._subscription_tier = subscription_tier
        self._subscription_status = subscription_status
        self._lemonsqueezy_customer_id = lemonsqueezy_customer_id
        self._lemonsqueezy_subscription_id = lemonsqueezy_subscription_id

    @property
    def name(self) -> str:
        """Get organization name."""
        return self._name

    @property
    def subscription_tier(self) -> SubscriptionTier:
        """Get subscription tier."""
        return self._subscription_tier

    @property
    def subscription_status(self) -> SubscriptionStatus:
        """Get subscription status."""
        return self._subscription_status

    @property
    def lemonsqueezy_customer_id(self) -> str | None:
        """Get LemonSqueezy customer ID."""
        return self._lemonsqueezy_customer_id

    @property
    def lemonsqueezy_subscription_id(self) -> str | None:
        """Get LemonSqueezy subscription ID."""
        return self._lemonsqueezy_subscription_id

    def is_pro(self) -> bool:
        """Check if organization has PRO subscription."""
        return self._subscription_tier == SubscriptionTier.PRO

    def is_free(self) -> bool:
        """Check if organization has FREE subscription."""
        return self._subscription_tier == SubscriptionTier.FREE

    def is_subscription_active(self) -> bool:
        """Check if subscription is active."""
        return self._subscription_status == SubscriptionStatus.ACTIVE

    def can_create_custom_exercises(self) -> bool:
        """Check if organization can create custom exercises (PRO feature)."""
        return self.is_pro() and self.is_subscription_active()

    def can_create_programs(self) -> bool:
        """Check if organization can create training programs (PRO feature)."""
        return self.is_pro() and self.is_subscription_active()

    def has_unlimited_ai_queries(self) -> bool:
        """Check if organization has unlimited AI queries (PRO feature)."""
        return self.is_pro() and self.is_subscription_active()

    def update_name(self, name: str) -> None:
        """Update organization name.
        
        Args:
            name: New organization name
            
        Raises:
            ValueError: If name is empty
        """
        if not name or not name.strip():
            raise ValueError("Organization name cannot be empty")
        self._name = name.strip()

    def upgrade_to_pro(
        self,
        lemonsqueezy_customer_id: str,
        lemonsqueezy_subscription_id: str
    ) -> None:
        """Upgrade organization to PRO tier.
        
        Args:
            lemonsqueezy_customer_id: LemonSqueezy customer ID
            lemonsqueezy_subscription_id: LemonSqueezy subscription ID
        """
        self._subscription_tier = SubscriptionTier.PRO
        self._subscription_status = SubscriptionStatus.ACTIVE
        self._lemonsqueezy_customer_id = lemonsqueezy_customer_id
        self._lemonsqueezy_subscription_id = lemonsqueezy_subscription_id

    def downgrade_to_free(self) -> None:
        """Downgrade organization to FREE tier."""
        self._subscription_tier = SubscriptionTier.FREE
        self._subscription_status = SubscriptionStatus.ACTIVE

    def cancel_subscription(self) -> None:
        """Cancel the subscription."""
        self._subscription_status = SubscriptionStatus.CANCELED

    def expire_subscription(self) -> None:
        """Mark subscription as expired."""
        self._subscription_status = SubscriptionStatus.EXPIRED
        # Downgrade to free tier when subscription expires
        self._subscription_tier = SubscriptionTier.FREE

    def reactivate_subscription(self) -> None:
        """Reactivate a canceled or expired subscription."""
        if self._subscription_tier == SubscriptionTier.PRO:
            self._subscription_status = SubscriptionStatus.ACTIVE
