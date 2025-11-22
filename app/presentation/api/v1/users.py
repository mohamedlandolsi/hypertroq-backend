"""User routes."""
from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends

from app.application.dtos.user_dto import UserResponseDTO, UserUpdateDTO
from app.application.services.user_service import UserService
from app.infrastructure.repositories.user_repository import UserRepository
from app.core.dependencies import DatabaseDep, CurrentUserDep

router = APIRouter(prefix="/users", tags=["Users"])


def get_user_service(db: DatabaseDep) -> UserService:
    """Get user service dependency."""
    user_repo = UserRepository(db)
    return UserService(user_repo)


@router.get("/me", response_model=UserResponseDTO)
async def get_current_user(
    current_user_id: CurrentUserDep,
    user_service: Annotated[UserService, Depends(get_user_service)]
) -> UserResponseDTO:
    """Get current authenticated user."""
    return await user_service.get_user(UUID(current_user_id))


@router.get("/{user_id}", response_model=UserResponseDTO)
async def get_user(
    user_id: UUID,
    user_service: Annotated[UserService, Depends(get_user_service)],
    current_user_id: CurrentUserDep,
) -> UserResponseDTO:
    """Get user by ID."""
    return await user_service.get_user(user_id)


@router.put("/me", response_model=UserResponseDTO)
async def update_current_user(
    user_data: UserUpdateDTO,
    current_user_id: CurrentUserDep,
    user_service: Annotated[UserService, Depends(get_user_service)]
) -> UserResponseDTO:
    """Update current user information."""
    return await user_service.update_user(UUID(current_user_id), user_data)


@router.delete("/me")
async def delete_current_user(
    current_user_id: CurrentUserDep,
    user_service: Annotated[UserService, Depends(get_user_service)]
) -> dict[str, str]:
    """Delete current user account."""
    await user_service.delete_user(UUID(current_user_id))
    return {"message": "User deleted successfully"}
