"""Organization service for business logic."""
from uuid import UUID
from fastapi import HTTPException, status

from app.domain.entities.organization import Organization, SubscriptionTier, SubscriptionStatus
from app.domain.interfaces.organization_repository import IOrganizationRepository
from app.application.dtos.organization_dto import (
    OrganizationCreateDTO,
    OrganizationUpdateDTO,
    OrganizationSubscriptionUpdateDTO,
    OrganizationResponseDTO,
    OrganizationWithStatsDTO,
)


class OrganizationService:
    """Service for organization-related business logic."""

    def __init__(self, organization_repository: IOrganizationRepository) -> None:
        """Initialize organization service with repository."""
        self.organization_repository = organization_repository

    async def create_organization(self, org_data: OrganizationCreateDTO) -> OrganizationResponseDTO:
        """Create a new organization with FREE tier."""
        organization = Organization(
            name=org_data.name,
            subscription_tier=SubscriptionTier.FREE,
            subscription_status=SubscriptionStatus.ACTIVE,
        )

        created_org = await self.organization_repository.create(organization)

        return OrganizationResponseDTO(
            id=created_org.id,
            name=created_org.name,
            subscription_tier=created_org.subscription_tier,
            subscription_status=created_org.subscription_status,
            lemonsqueezy_customer_id=created_org.lemonsqueezy_customer_id,
            lemonsqueezy_subscription_id=created_org.lemonsqueezy_subscription_id,
            created_at=created_org.created_at,
            updated_at=created_org.updated_at,
        )

    async def get_organization(self, org_id: UUID) -> OrganizationResponseDTO:
        """Get organization by ID."""
        org = await self.organization_repository.get_by_id(org_id)
        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )

        return OrganizationResponseDTO(
            id=org.id,
            name=org.name,
            subscription_tier=org.subscription_tier,
            subscription_status=org.subscription_status,
            lemonsqueezy_customer_id=org.lemonsqueezy_customer_id,
            lemonsqueezy_subscription_id=org.lemonsqueezy_subscription_id,
            created_at=org.created_at,
            updated_at=org.updated_at,
        )

    async def update_organization(
        self,
        org_id: UUID,
        org_data: OrganizationUpdateDTO
    ) -> OrganizationResponseDTO:
        """Update organization information."""
        org = await self.organization_repository.get_by_id(org_id)
        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )

        if org_data.name:
            org.update_name(org_data.name)

        updated_org = await self.organization_repository.update(org)

        return OrganizationResponseDTO(
            id=updated_org.id,
            name=updated_org.name,
            subscription_tier=updated_org.subscription_tier,
            subscription_status=updated_org.subscription_status,
            lemonsqueezy_customer_id=updated_org.lemonsqueezy_customer_id,
            lemonsqueezy_subscription_id=updated_org.lemonsqueezy_subscription_id,
            created_at=updated_org.created_at,
            updated_at=updated_org.updated_at,
        )

    async def upgrade_to_pro(
        self,
        org_id: UUID,
        lemonsqueezy_customer_id: str,
        lemonsqueezy_subscription_id: str
    ) -> OrganizationResponseDTO:
        """Upgrade organization to PRO tier."""
        org = await self.organization_repository.get_by_id(org_id)
        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )

        org.upgrade_to_pro(lemonsqueezy_customer_id, lemonsqueezy_subscription_id)
        updated_org = await self.organization_repository.update(org)

        return OrganizationResponseDTO(
            id=updated_org.id,
            name=updated_org.name,
            subscription_tier=updated_org.subscription_tier,
            subscription_status=updated_org.subscription_status,
            lemonsqueezy_customer_id=updated_org.lemonsqueezy_customer_id,
            lemonsqueezy_subscription_id=updated_org.lemonsqueezy_subscription_id,
            created_at=updated_org.created_at,
            updated_at=updated_org.updated_at,
        )

    async def downgrade_to_free(self, org_id: UUID) -> OrganizationResponseDTO:
        """Downgrade organization to FREE tier."""
        org = await self.organization_repository.get_by_id(org_id)
        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )

        org.downgrade_to_free()
        updated_org = await self.organization_repository.update(org)

        return OrganizationResponseDTO(
            id=updated_org.id,
            name=updated_org.name,
            subscription_tier=updated_org.subscription_tier,
            subscription_status=updated_org.subscription_status,
            lemonsqueezy_customer_id=updated_org.lemonsqueezy_customer_id,
            lemonsqueezy_subscription_id=updated_org.lemonsqueezy_subscription_id,
            created_at=updated_org.created_at,
            updated_at=updated_org.updated_at,
        )

    async def cancel_subscription(self, org_id: UUID) -> OrganizationResponseDTO:
        """Cancel organization subscription."""
        org = await self.organization_repository.get_by_id(org_id)
        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )

        org.cancel_subscription()
        updated_org = await self.organization_repository.update(org)

        return OrganizationResponseDTO(
            id=updated_org.id,
            name=updated_org.name,
            subscription_tier=updated_org.subscription_tier,
            subscription_status=updated_org.subscription_status,
            lemonsqueezy_customer_id=updated_org.lemonsqueezy_customer_id,
            lemonsqueezy_subscription_id=updated_org.lemonsqueezy_subscription_id,
            created_at=updated_org.created_at,
            updated_at=updated_org.updated_at,
        )

    async def get_by_lemonsqueezy_subscription_id(
        self,
        subscription_id: str
    ) -> OrganizationResponseDTO:
        """Get organization by LemonSqueezy subscription ID."""
        org = await self.organization_repository.get_by_lemonsqueezy_subscription_id(subscription_id)
        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )

        return OrganizationResponseDTO(
            id=org.id,
            name=org.name,
            subscription_tier=org.subscription_tier,
            subscription_status=org.subscription_status,
            lemonsqueezy_customer_id=org.lemonsqueezy_customer_id,
            lemonsqueezy_subscription_id=org.lemonsqueezy_subscription_id,
            created_at=org.created_at,
            updated_at=org.updated_at,
        )

    async def check_feature_access(self, org_id: UUID, feature: str) -> bool:
        """Check if organization has access to a specific feature.
        
        Args:
            org_id: Organization ID
            feature: Feature name ('custom_exercises', 'programs', 'unlimited_ai')
            
        Returns:
            True if organization has access to the feature
            
        Raises:
            HTTPException: If organization not found or feature is invalid
        """
        org = await self.organization_repository.get_by_id(org_id)
        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )

        if feature == "custom_exercises":
            return org.can_create_custom_exercises()
        elif feature == "programs":
            return org.can_create_programs()
        elif feature == "unlimited_ai":
            return org.has_unlimited_ai_queries()
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid feature: {feature}"
            )

    async def require_pro_feature(self, org_id: UUID, feature_name: str) -> None:
        """Require organization to have PRO access for a feature.
        
        Raises:
            HTTPException: If organization doesn't have access to the feature
        """
        has_access = await self.check_feature_access(org_id, feature_name)
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This feature ({feature_name}) requires a PRO subscription"
            )
