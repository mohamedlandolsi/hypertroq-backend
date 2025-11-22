"""Tests for user service."""
import pytest
from uuid import uuid4

from app.application.services.user_service import UserService
from app.application.dtos.user_dto import UserCreateDTO
from app.infrastructure.repositories.user_repository import UserRepository


@pytest.mark.asyncio
async def test_create_user(db_session):
    """Test user creation."""
    # Arrange
    user_repo = UserRepository(db_session)
    user_service = UserService(user_repo)
    user_data = UserCreateDTO(
        email="test@example.com",
        password="testpassword123",
        full_name="Test User"
    )
    
    # Act
    created_user = await user_service.create_user(user_data)
    
    # Assert
    assert created_user.email == user_data.email
    assert created_user.full_name == user_data.full_name
    assert created_user.is_active is True


@pytest.mark.asyncio
async def test_get_user(db_session):
    """Test getting user by ID."""
    # Arrange
    user_repo = UserRepository(db_session)
    user_service = UserService(user_repo)
    user_data = UserCreateDTO(
        email="test2@example.com",
        password="testpassword123",
        full_name="Test User 2"
    )
    created_user = await user_service.create_user(user_data)
    
    # Act
    retrieved_user = await user_service.get_user(created_user.id)
    
    # Assert
    assert retrieved_user.id == created_user.id
    assert retrieved_user.email == created_user.email
