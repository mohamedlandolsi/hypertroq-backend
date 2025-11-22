"""Organization repository implementation."""
from uuid import UUID
from typing import List
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.organization import Organization, SubscriptionStatus
from app.domain.interfaces.organization_repository import IOrganizationRepository
from app.models.organization import OrganizationModel


class OrganizationRepository(IOrganizationRepository):
    """SQLAlchemy implementation of organization repository."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with database session."""
        self.session = session

    def _to_entity(self, model: OrganizationModel) -> Organization:
        """Convert database model to domain entity."""
        return Organization(
            id=model.id,
            name=model.name,
            subscription_tier=model.subscription_tier,
            subscription_status=model.subscription_status,
            lemonsqueezy_customer_id=model.lemonsqueezy_customer_id,
            lemonsqueezy_subscription_id=model.lemonsqueezy_subscription_id,
        )

    def _to_model(self, entity: Organization) -> OrganizationModel:
        """Convert domain entity to database model."""
        return OrganizationModel(
            id=entity.id,
            name=entity.name,
            subscription_tier=entity.subscription_tier,
            subscription_status=entity.subscription_status,
            lemonsqueezy_customer_id=entity.lemonsqueezy_customer_id,
            lemonsqueezy_subscription_id=entity.lemonsqueezy_subscription_id,
        )

    async def get_by_id(self, id: UUID) -> Organization | None:
        """Get organization by ID."""
        result = await self.session.execute(
            select(OrganizationModel).where(OrganizationModel.id == id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_lemonsqueezy_customer_id(self, customer_id: str) -> Organization | None:
        """Get organization by LemonSqueezy customer ID."""
        result = await self.session.execute(
            select(OrganizationModel).where(
                OrganizationModel.lemonsqueezy_customer_id == customer_id
            )
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_lemonsqueezy_subscription_id(self, subscription_id: str) -> Organization | None:
        """Get organization by LemonSqueezy subscription ID."""
        result = await self.session.execute(
            select(OrganizationModel).where(
                OrganizationModel.lemonsqueezy_subscription_id == subscription_id
            )
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_with_users(self, id: UUID) -> Organization | None:
        """Get organization with all its users eagerly loaded."""
        result = await self.session.execute(
            select(OrganizationModel)
            .options(selectinload(OrganizationModel.users))
            .where(OrganizationModel.id == id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_all_with_active_subscriptions(self) -> List[Organization]:
        """Get all organizations with active subscriptions."""
        result = await self.session.execute(
            select(OrganizationModel).where(
                OrganizationModel.subscription_status == SubscriptionStatus.ACTIVE
            )
        )
        models = result.scalars().all()
        return [self._to_entity(model) for model in models]

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Organization]:
        """Get all organizations with pagination."""
        result = await self.session.execute(
            select(OrganizationModel).offset(skip).limit(limit)
        )
        models = result.scalars().all()
        return [self._to_entity(model) for model in models]

    async def create(self, entity: Organization) -> Organization:
        """Create new organization."""
        model = self._to_model(entity)
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return self._to_entity(model)

    async def update(self, entity: Organization) -> Organization:
        """Update existing organization."""
        result = await self.session.execute(
            select(OrganizationModel).where(OrganizationModel.id == entity.id)
        )
        model = result.scalar_one_or_none()
        
        if model:
            model.name = entity.name
            model.subscription_tier = entity.subscription_tier
            model.subscription_status = entity.subscription_status
            model.lemonsqueezy_customer_id = entity.lemonsqueezy_customer_id
            model.lemonsqueezy_subscription_id = entity.lemonsqueezy_subscription_id
            
            await self.session.commit()
            await self.session.refresh(model)
            return self._to_entity(model)
        
        raise ValueError(f"Organization with id {entity.id} not found")

    async def delete(self, id: UUID) -> bool:
        """Delete organization by ID (cascades to users)."""
        result = await self.session.execute(
            select(OrganizationModel).where(OrganizationModel.id == id)
        )
        model = result.scalar_one_or_none()
        
        if model:
            await self.session.delete(model)
            await self.session.commit()
            return True
        
        return False
