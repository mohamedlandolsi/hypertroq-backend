"""
Tests for authentication dependencies.

Tests the authentication dependency chain including:
- Token validation
- User retrieval
- Active user checks
- Verified user checks
- Admin role checks
- Organization retrieval
"""

import pytest
from datetime import timedelta
from uuid import uuid4
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import (
    get_current_user,
    get_current_active_user,
    require_verified_user,
    require_admin,
    get_current_organization,
)
from app.core.security import create_access_token
from app.repositories.user_repository import UserRepository
from app.repositories.organization_repository import OrganizationRepository


@pytest.fixture
async def test_organization(db_session: AsyncSession):
    """Create test organization."""
    org_repo = OrganizationRepository(db_session)
    org_data = {
        "name": "Test Organization",
        "subscription_tier": "FREE",
        "subscription_status": "ACTIVE",
    }
    org = await org_repo.create(org_data)
    return org


@pytest.fixture
async def test_user(db_session: AsyncSession, test_organization):
    """Create test user."""
    user_repo = UserRepository(db_session)
    user_data = {
        "email": "test@example.com",
        "hashed_password": "$2b$12$test_hashed_password",
        "full_name": "Test User",
        "organization_id": test_organization.id,
        "role": "USER",
        "is_active": True,
        "is_verified": True,
    }
    user = await user_repo.create(user_data)
    return user


@pytest.fixture
async def admin_user(db_session: AsyncSession, test_organization):
    """Create admin user."""
    user_repo = UserRepository(db_session)
    user_data = {
        "email": "admin@example.com",
        "hashed_password": "$2b$12$test_hashed_password",
        "full_name": "Admin User",
        "organization_id": test_organization.id,
        "role": "ADMIN",
        "is_active": True,
        "is_verified": True,
    }
    user = await user_repo.create(user_data)
    return user


@pytest.fixture
async def inactive_user(db_session: AsyncSession, test_organization):
    """Create inactive user."""
    user_repo = UserRepository(db_session)
    user_data = {
        "email": "inactive@example.com",
        "hashed_password": "$2b$12$test_hashed_password",
        "full_name": "Inactive User",
        "organization_id": test_organization.id,
        "role": "USER",
        "is_active": False,
        "is_verified": True,
    }
    user = await user_repo.create(user_data)
    return user


@pytest.fixture
async def unverified_user(db_session: AsyncSession, test_organization):
    """Create unverified user."""
    user_repo = UserRepository(db_session)
    user_data = {
        "email": "unverified@example.com",
        "hashed_password": "$2b$12$test_hashed_password",
        "full_name": "Unverified User",
        "organization_id": test_organization.id,
        "role": "USER",
        "is_active": True,
        "is_verified": False,
    }
    user = await user_repo.create(user_data)
    return user


def create_token_for_user(user, organization):
    """Helper to create access token for user."""
    token_data = {
        "user_id": str(user.id),
        "organization_id": str(organization.id),
        "role": user.role,
    }
    return create_access_token(subject=token_data)


# ==================== Test get_current_user ====================


@pytest.mark.asyncio
async def test_get_current_user_success(db_session, test_user, test_organization):
    """Test successful user retrieval."""
    token = create_token_for_user(test_user, test_organization)
    
    user = await get_current_user(token=token, db=db_session)
    
    assert user is not None
    assert user.id == test_user.id
    assert user.email == test_user.email


@pytest.mark.asyncio
async def test_get_current_user_invalid_token(db_session):
    """Test with invalid token."""
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(token="invalid_token", db=db_session)
    
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_expired_token(db_session, test_user, test_organization):
    """Test with expired token."""
    token_data = {
        "user_id": str(test_user.id),
        "organization_id": str(test_organization.id),
        "role": test_user.role,
    }
    # Create token that expires immediately
    expired_token = create_access_token(
        subject=token_data,
        expires_delta=timedelta(seconds=-1)
    )
    
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(token=expired_token, db=db_session)
    
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_nonexistent_user(db_session, test_organization):
    """Test with token for non-existent user."""
    fake_user_id = uuid4()
    token_data = {
        "user_id": str(fake_user_id),
        "organization_id": str(test_organization.id),
        "role": "USER",
    }
    token = create_access_token(subject=token_data)
    
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(token=token, db=db_session)
    
    assert exc_info.value.status_code == 401
    assert "User not found" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_current_user_inactive_account(db_session, inactive_user, test_organization):
    """Test with inactive user account."""
    token = create_token_for_user(inactive_user, test_organization)
    
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(token=token, db=db_session)
    
    assert exc_info.value.status_code == 403
    assert "deactivated" in exc_info.value.detail.lower()


# ==================== Test get_current_active_user ====================


@pytest.mark.asyncio
async def test_get_current_active_user_success(db_session, test_user, test_organization):
    """Test active user retrieval."""
    token = create_token_for_user(test_user, test_organization)
    current_user = await get_current_user(token=token, db=db_session)
    
    active_user = await get_current_active_user(current_user=current_user)
    
    assert active_user is not None
    assert active_user.is_active is True


# ==================== Test require_verified_user ====================


@pytest.mark.asyncio
async def test_require_verified_user_success(db_session, test_user, test_organization):
    """Test verified user access."""
    token = create_token_for_user(test_user, test_organization)
    current_user = await get_current_user(token=token, db=db_session)
    
    verified_user = await require_verified_user(current_user=current_user)
    
    assert verified_user is not None
    assert verified_user.is_verified is True


@pytest.mark.asyncio
async def test_require_verified_user_unverified(db_session, unverified_user, test_organization):
    """Test unverified user rejection."""
    token = create_token_for_user(unverified_user, test_organization)
    current_user = await get_current_user(token=token, db=db_session)
    
    with pytest.raises(HTTPException) as exc_info:
        await require_verified_user(current_user=current_user)
    
    assert exc_info.value.status_code == 403
    assert "verification" in exc_info.value.detail.lower()


# ==================== Test require_admin ====================


@pytest.mark.asyncio
async def test_require_admin_success(db_session, admin_user, test_organization):
    """Test admin user access."""
    token = create_token_for_user(admin_user, test_organization)
    current_user = await get_current_user(token=token, db=db_session)
    
    admin = await require_admin(current_user=current_user)
    
    assert admin is not None
    assert admin.role == "ADMIN"


@pytest.mark.asyncio
async def test_require_admin_non_admin(db_session, test_user, test_organization):
    """Test non-admin user rejection."""
    token = create_token_for_user(test_user, test_organization)
    current_user = await get_current_user(token=token, db=db_session)
    
    with pytest.raises(HTTPException) as exc_info:
        await require_admin(current_user=current_user)
    
    assert exc_info.value.status_code == 403
    assert "admin" in exc_info.value.detail.lower()


# ==================== Test get_current_organization ====================


@pytest.mark.asyncio
async def test_get_current_organization_success(db_session, test_user, test_organization):
    """Test organization retrieval."""
    token = create_token_for_user(test_user, test_organization)
    current_user = await get_current_user(token=token, db=db_session)
    
    organization = await get_current_organization(
        current_user=current_user,
        db=db_session
    )
    
    assert organization is not None
    assert organization.id == test_organization.id
    assert organization.name == test_organization.name


@pytest.mark.asyncio
async def test_get_current_organization_not_found(db_session, test_user):
    """Test with non-existent organization."""
    # Manually set invalid organization_id
    test_user.organization_id = uuid4()
    
    with pytest.raises(HTTPException) as exc_info:
        await get_current_organization(current_user=test_user, db=db_session)
    
    assert exc_info.value.status_code == 404
    assert "Organization not found" in exc_info.value.detail
