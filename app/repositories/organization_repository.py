"""
Organization repository for data access operations.

Implements the repository pattern for Organization entity operations.
"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.organization import OrganizationModel


class OrganizationRepository:
    """
    Repository for Organization data access operations.
    
    Handles all database interactions for organizations without business logic.
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize repository with database session.
        
        Args:
            session: SQLAlchemy async session for database operations
        """
        self._session = session

    async def create(self, org_data: dict) -> OrganizationModel:
        """
        Create a new organization in the database.
        
        Args:
            org_data: Dictionary containing organization fields:
                - name (str): Organization name
                - subscription_tier (str, optional): Subscription tier
                - subscription_status (str, optional): Subscription status
                - lemonsqueezy_customer_id (str, optional): LemonSqueezy customer ID
                - lemonsqueezy_subscription_id (str, optional): LemonSqueezy subscription ID
        
        Returns:
            OrganizationModel: Created organization instance
            
        Raises:
            IntegrityError: If constraints are violated
            SQLAlchemyError: For other database errors
        """
        try:
            organization = OrganizationModel(**org_data)
            self._session.add(organization)
            await self._session.commit()
            await self._session.refresh(organization)
            return organization
        except IntegrityError as e:
            await self._session.rollback()
            raise IntegrityError(
                "Organization creation failed: constraint violation",
                params=None,
                orig=e.orig,
            ) from e
        except SQLAlchemyError as e:
            await self._session.rollback()
            raise SQLAlchemyError(
                f"Database error during organization creation: {str(e)}"
            ) from e

    async def get_by_id(self, org_id: UUID) -> Optional[OrganizationModel]:
        """
        Retrieve organization by ID.
        
        Args:
            org_id: UUID of the organization to retrieve
            
        Returns:
            OrganizationModel if found, None otherwise
            
        Raises:
            SQLAlchemyError: For database errors
        """
        try:
            result = await self._session.execute(
                select(OrganizationModel).where(OrganizationModel.id == org_id)
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            raise SQLAlchemyError(
                f"Database error during organization retrieval: {str(e)}"
            ) from e

    async def get_by_name(self, name: str) -> Optional[OrganizationModel]:
        """
        Retrieve organization by name.
        
        Args:
            name: Organization name to search for
            
        Returns:
            OrganizationModel if found, None otherwise
            
        Raises:
            SQLAlchemyError: For database errors
        """
        try:
            result = await self._session.execute(
                select(OrganizationModel).where(OrganizationModel.name == name)
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            raise SQLAlchemyError(
                f"Database error during organization lookup: {str(e)}"
            ) from e

    async def update(
        self, org_id: UUID, org_data: dict
    ) -> Optional[OrganizationModel]:
        """
        Update an existing organization.
        
        Args:
            org_id: UUID of the organization to update
            org_data: Dictionary of fields to update
        
        Returns:
            Updated OrganizationModel if found, None if organization doesn't exist
            
        Raises:
            IntegrityError: If update violates constraints
            SQLAlchemyError: For other database errors
        """
        try:
            org = await self.get_by_id(org_id)
            if not org:
                return None

            if org_data:
                stmt = (
                    update(OrganizationModel)
                    .where(OrganizationModel.id == org_id)
                    .values(**org_data)
                    .execution_options(synchronize_session="fetch")
                )
                await self._session.execute(stmt)
                await self._session.commit()
                await self._session.refresh(org)
            
            return org
        except IntegrityError as e:
            await self._session.rollback()
            raise IntegrityError(
                "Organization update failed: constraint violation",
                params=None,
                orig=e.orig,
            ) from e
        except SQLAlchemyError as e:
            await self._session.rollback()
            raise SQLAlchemyError(
                f"Database error during organization update: {str(e)}"
            ) from e

    async def delete(self, org_id: UUID) -> bool:
        """
        Delete an organization by ID.
        
        Args:
            org_id: UUID of the organization to delete
            
        Returns:
            True if organization was deleted, False if not found
            
        Raises:
            SQLAlchemyError: For database errors
        """
        try:
            stmt = delete(OrganizationModel).where(OrganizationModel.id == org_id)
            result = await self._session.execute(stmt)
            await self._session.commit()
            return result.rowcount > 0
        except SQLAlchemyError as e:
            await self._session.rollback()
            raise SQLAlchemyError(
                f"Database error during organization deletion: {str(e)}"
            ) from e
