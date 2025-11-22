"""Organization repository interface."""
from abc import abstractmethod
from uuid import UUID
from typing import List

from app.domain.interfaces.repository import IRepository
from app.domain.entities.organization import Organization


class IOrganizationRepository(IRepository[Organization]):
    """Interface for organization repository."""

    @abstractmethod
    async def get_by_lemonsqueezy_customer_id(self, customer_id: str) -> Organization | None:
        """Get organization by LemonSqueezy customer ID."""
        pass

    @abstractmethod
    async def get_by_lemonsqueezy_subscription_id(self, subscription_id: str) -> Organization | None:
        """Get organization by LemonSqueezy subscription ID."""
        pass

    @abstractmethod
    async def get_with_users(self, id: UUID) -> Organization | None:
        """Get organization with all its users."""
        pass

    @abstractmethod
    async def get_all_with_active_subscriptions(self) -> List[Organization]:
        """Get all organizations with active subscriptions."""
        pass
