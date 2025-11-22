"""User service for business logic."""
from uuid import UUID
from fastapi import HTTPException, status

from app.domain.entities.user import User, UserRole
from app.domain.interfaces.user_repository import IUserRepository
from app.application.dtos.user_dto import UserCreateDTO, UserUpdateDTO, UserResponseDTO
from app.core.security import get_password_hash, verify_password


class UserService:
    """Service for user-related business logic."""

    def __init__(self, user_repository: IUserRepository) -> None:
        """Initialize user service with repository."""
        self.user_repository = user_repository

    async def create_user(self, user_data: UserCreateDTO, role: UserRole = UserRole.USER) -> UserResponseDTO:
        """Create a new user.
        
        Args:
            user_data: User creation data including email, password, full_name, and organization_id
            role: User role (default: USER)
            
        Returns:
            UserResponseDTO with created user information
            
        Raises:
            HTTPException: If email is already registered
        """
        # Check if user already exists
        existing_user = await self.user_repository.get_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Create user entity
        hashed_password = get_password_hash(user_data.password)
        user = User(
            email=user_data.email,
            hashed_password=hashed_password,
            full_name=user_data.full_name,
            organization_id=user_data.organization_id,
            role=role,
        )

        # Save to repository
        created_user = await self.user_repository.create(user)

        return UserResponseDTO(
            id=created_user.id,
            email=created_user.email,
            full_name=created_user.full_name,
            organization_id=created_user.organization_id,
            role=created_user.role,
            is_active=created_user.is_active,
            is_verified=created_user.is_verified,
            profile_image_url=created_user.profile_image_url,
            created_at=created_user.created_at,
            updated_at=created_user.updated_at,
        )

    async def get_user(self, user_id: UUID) -> UserResponseDTO:
        """Get user by ID."""
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        return UserResponseDTO(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            organization_id=user.organization_id,
            role=user.role,
            is_active=user.is_active,
            is_verified=user.is_verified,
            profile_image_url=user.profile_image_url,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

    async def get_users_by_organization(
        self,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> list[UserResponseDTO]:
        """Get all users in an organization."""
        users = await self.user_repository.get_by_organization(organization_id, skip, limit)
        return [
            UserResponseDTO(
                id=user.id,
                email=user.email,
                full_name=user.full_name,
                organization_id=user.organization_id,
                role=user.role,
                is_active=user.is_active,
                is_verified=user.is_verified,
                profile_image_url=user.profile_image_url,
                created_at=user.created_at,
                updated_at=user.updated_at,
            )
            for user in users
        ]

    async def update_user(self, user_id: UUID, user_data: UserUpdateDTO) -> UserResponseDTO:
        """Update user information."""
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Update user entity
        if user_data.email or user_data.full_name or user_data.profile_image_url is not None:
            user.update_profile(
                email=user_data.email,
                full_name=user_data.full_name,
                profile_image_url=user_data.profile_image_url
            )
        
        if user_data.password:
            hashed_password = get_password_hash(user_data.password)
            user.update_password(hashed_password)

        # Save changes
        updated_user = await self.user_repository.update(user)

        return UserResponseDTO(
            id=updated_user.id,
            email=updated_user.email,
            full_name=updated_user.full_name,
            organization_id=updated_user.organization_id,
            role=updated_user.role,
            is_active=updated_user.is_active,
            is_verified=updated_user.is_verified,
            profile_image_url=updated_user.profile_image_url,
            created_at=updated_user.created_at,
            updated_at=updated_user.updated_at,
        )

    async def delete_user(self, user_id: UUID) -> bool:
        """Delete user by ID."""
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        return await self.user_repository.delete(user_id)

    async def authenticate_user(self, email: str, password: str) -> User | None:
        """Authenticate user by email and password."""
        user = await self.user_repository.get_by_email(email)
        if not user:
            return None
        
        if not verify_password(password, user.hashed_password):
            return None
        
        return user

    async def verify_user_email(self, user_id: UUID) -> UserResponseDTO:
        """Mark user's email as verified."""
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        user.verify_email()
        updated_user = await self.user_repository.update(user)

        return UserResponseDTO(
            id=updated_user.id,
            email=updated_user.email,
            full_name=updated_user.full_name,
            organization_id=updated_user.organization_id,
            role=updated_user.role,
            is_active=updated_user.is_active,
            is_verified=updated_user.is_verified,
            profile_image_url=updated_user.profile_image_url,
            created_at=updated_user.created_at,
            updated_at=updated_user.updated_at,
        )
