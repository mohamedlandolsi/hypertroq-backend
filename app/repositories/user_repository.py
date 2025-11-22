"""
User repository for data access operations.

Implements the repository pattern for User entity operations.
Handles all database interactions for users without business logic.
"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import UserModel


class UserRepository:
    """
    Repository for User data access operations.
    
    Follows repository pattern - only handles data persistence,
    no business logic. All methods are async for non-blocking I/O.
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize repository with database session.
        
        Args:
            session: SQLAlchemy async session for database operations
        """
        self._session = session

    async def create(self, user_data: dict) -> UserModel:
        """
        Create a new user in the database.
        
        Args:
            user_data: Dictionary containing user fields:
                - email (str): User email address
                - hashed_password (str): Bcrypt hashed password
                - full_name (str): User's full name
                - organization_id (UUID): Organization ID
                - role (str, optional): User role (default: USER)
                - is_active (bool, optional): Active status (default: True)
                - is_verified (bool, optional): Verification status (default: False)
                - profile_image_url (str, optional): Profile image URL
        
        Returns:
            UserModel: Created user instance
            
        Raises:
            IntegrityError: If email already exists or foreign key constraint fails
            SQLAlchemyError: For other database errors
        """
        try:
            user = UserModel(**user_data)
            self._session.add(user)
            await self._session.commit()
            await self._session.refresh(user)
            return user
        except IntegrityError as e:
            await self._session.rollback()
            raise IntegrityError(
                "User creation failed: email may already exist or invalid organization_id",
                params=None,
                orig=e.orig,
            ) from e
        except SQLAlchemyError as e:
            await self._session.rollback()
            raise SQLAlchemyError(f"Database error during user creation: {str(e)}") from e

    async def get_by_id(self, user_id: UUID) -> Optional[UserModel]:
        """
        Retrieve user by ID.
        
        Args:
            user_id: UUID of the user to retrieve
            
        Returns:
            UserModel if found, None otherwise
            
        Raises:
            SQLAlchemyError: For database errors
        """
        try:
            result = await self._session.execute(
                select(UserModel).where(UserModel.id == user_id)
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            raise SQLAlchemyError(f"Database error during user retrieval: {str(e)}") from e

    async def get_by_email(self, email: str) -> Optional[UserModel]:
        """
        Retrieve user by email address.
        
        Args:
            email: Email address to search for
            
        Returns:
            UserModel if found, None otherwise
            
        Raises:
            SQLAlchemyError: For database errors
        """
        try:
            result = await self._session.execute(
                select(UserModel).where(UserModel.email == email)
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            raise SQLAlchemyError(f"Database error during email lookup: {str(e)}") from e

    async def update(self, user_id: UUID, user_data: dict) -> Optional[UserModel]:
        """
        Update an existing user.
        
        Args:
            user_id: UUID of the user to update
            user_data: Dictionary of fields to update (only provided fields are updated)
                Allowed fields:
                - email (str)
                - hashed_password (str)
                - full_name (str)
                - role (str)
                - is_active (bool)
                - is_verified (bool)
                - profile_image_url (str)
                - organization_id (UUID)
        
        Returns:
            Updated UserModel if found, None if user doesn't exist
            
        Raises:
            IntegrityError: If email update violates unique constraint
            SQLAlchemyError: For other database errors
        """
        try:
            # First check if user exists
            user = await self.get_by_id(user_id)
            if not user:
                return None

            # Update only provided fields
            if user_data:
                stmt = (
                    update(UserModel)
                    .where(UserModel.id == user_id)
                    .values(**user_data)
                    .execution_options(synchronize_session="fetch")
                )
                await self._session.execute(stmt)
                await self._session.commit()
                
                # Refresh to get updated data
                await self._session.refresh(user)
            
            return user
        except IntegrityError as e:
            await self._session.rollback()
            raise IntegrityError(
                "User update failed: email may already exist",
                params=None,
                orig=e.orig,
            ) from e
        except SQLAlchemyError as e:
            await self._session.rollback()
            raise SQLAlchemyError(f"Database error during user update: {str(e)}") from e

    async def delete(self, user_id: UUID) -> bool:
        """
        Delete a user by ID.
        
        Args:
            user_id: UUID of the user to delete
            
        Returns:
            True if user was deleted, False if user not found
            
        Raises:
            SQLAlchemyError: For database errors
        """
        try:
            stmt = delete(UserModel).where(UserModel.id == user_id)
            result = await self._session.execute(stmt)
            await self._session.commit()
            
            # Check if any rows were affected
            return result.rowcount > 0
        except SQLAlchemyError as e:
            await self._session.rollback()
            raise SQLAlchemyError(f"Database error during user deletion: {str(e)}") from e

    async def list_by_organization(
        self,
        org_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[UserModel]:
        """
        List all users in an organization with pagination.
        
        Args:
            org_id: UUID of the organization
            skip: Number of records to skip (offset for pagination)
            limit: Maximum number of records to return
            
        Returns:
            List of UserModel instances (may be empty)
            
        Raises:
            SQLAlchemyError: For database errors
        """
        try:
            result = await self._session.execute(
                select(UserModel)
                .where(UserModel.organization_id == org_id)
                .order_by(UserModel.created_at.desc())
                .offset(skip)
                .limit(limit)
            )
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            raise SQLAlchemyError(
                f"Database error during organization users retrieval: {str(e)}"
            ) from e

    async def exists_by_email(self, email: str) -> bool:
        """
        Check if a user with the given email exists.
        
        More efficient than get_by_email when only existence check is needed.
        
        Args:
            email: Email address to check
            
        Returns:
            True if user exists, False otherwise
            
        Raises:
            SQLAlchemyError: For database errors
        """
        try:
            result = await self._session.execute(
                select(UserModel.id).where(UserModel.email == email).limit(1)
            )
            return result.scalar_one_or_none() is not None
        except SQLAlchemyError as e:
            raise SQLAlchemyError(
                f"Database error during email existence check: {str(e)}"
            ) from e

    async def count_by_organization(self, org_id: UUID) -> int:
        """
        Count total users in an organization.
        
        Useful for pagination metadata.
        
        Args:
            org_id: UUID of the organization
            
        Returns:
            Total count of users in organization
            
        Raises:
            SQLAlchemyError: For database errors
        """
        try:
            from sqlalchemy import func
            
            result = await self._session.execute(
                select(func.count(UserModel.id)).where(
                    UserModel.organization_id == org_id
                )
            )
            return result.scalar_one()
        except SQLAlchemyError as e:
            raise SQLAlchemyError(
                f"Database error during user count: {str(e)}"
            ) from e

    async def get_active_users(
        self,
        org_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[UserModel]:
        """
        List active users in an organization.
        
        Args:
            org_id: UUID of the organization
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of active UserModel instances
            
        Raises:
            SQLAlchemyError: For database errors
        """
        try:
            result = await self._session.execute(
                select(UserModel)
                .where(
                    UserModel.organization_id == org_id,
                    UserModel.is_active == True,
                )
                .order_by(UserModel.created_at.desc())
                .offset(skip)
                .limit(limit)
            )
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            raise SQLAlchemyError(
                f"Database error during active users retrieval: {str(e)}"
            ) from e
