"""User repository implementation."""
from uuid import UUID
from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.user import User
from app.domain.interfaces.user_repository import IUserRepository
from app.models.user import UserModel


class UserRepository(IUserRepository):
    """SQLAlchemy implementation of user repository."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with database session."""
        self.session = session

    def _to_entity(self, model: UserModel) -> User:
        """Convert database model to domain entity."""
        return User(
            id=model.id,
            email=model.email,
            hashed_password=model.hashed_password,
            full_name=model.full_name,
            is_active=model.is_active,
            is_superuser=model.is_superuser,
        )

    def _to_model(self, entity: User) -> UserModel:
        """Convert domain entity to database model."""
        return UserModel(
            id=entity.id,
            email=entity.email,
            hashed_password=entity.hashed_password,
            full_name=entity.full_name,
            is_active=entity.is_active,
            is_superuser=entity.is_superuser,
        )

    async def get_by_id(self, id: UUID) -> User | None:
        """Get user by ID."""
        result = await self.session.execute(
            select(UserModel).where(UserModel.id == id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_email(self, email: str) -> User | None:
        """Get user by email."""
        result = await self.session.execute(
            select(UserModel).where(UserModel.email == email)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def exists_by_email(self, email: str) -> bool:
        """Check if user exists by email."""
        result = await self.session.execute(
            select(UserModel.id).where(UserModel.email == email)
        )
        return result.scalar_one_or_none() is not None

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all users with pagination."""
        result = await self.session.execute(
            select(UserModel).offset(skip).limit(limit)
        )
        models = result.scalars().all()
        return [self._to_entity(model) for model in models]

    async def create(self, entity: User) -> User:
        """Create new user."""
        model = self._to_model(entity)
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return self._to_entity(model)

    async def update(self, entity: User) -> User:
        """Update existing user."""
        result = await self.session.execute(
            select(UserModel).where(UserModel.id == entity.id)
        )
        model = result.scalar_one_or_none()
        
        if model:
            model.email = entity.email
            model.hashed_password = entity.hashed_password
            model.full_name = entity.full_name
            model.is_active = entity.is_active
            model.is_superuser = entity.is_superuser
            
            await self.session.commit()
            await self.session.refresh(model)
            return self._to_entity(model)
        
        raise ValueError(f"User with id {entity.id} not found")

    async def delete(self, id: UUID) -> bool:
        """Delete user by ID."""
        result = await self.session.execute(
            select(UserModel).where(UserModel.id == id)
        )
        model = result.scalar_one_or_none()
        
        if model:
            await self.session.delete(model)
            await self.session.commit()
            return True
        
        return False
