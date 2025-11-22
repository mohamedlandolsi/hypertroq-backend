"""
Example usage of authentication dependencies.

This file demonstrates how to use the authentication dependencies
in FastAPI route handlers.
"""

from typing import Annotated
from fastapi import APIRouter, Depends
from app.core.dependencies import (
    CurrentUserDep,
    CurrentActiveUserDep,
    VerifiedUserDep,
    AdminUserDep,
    CurrentOrganizationDep,
    DatabaseDep,
    rate_limit,
)

router = APIRouter()


# ==================== Basic Authentication ====================


@router.get("/profile")
async def get_profile(current_user: CurrentUserDep):
    """
    Get user profile.
    
    Requires: Valid JWT token
    Returns: User information
    """
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role,
    }


# ==================== Active User Required ====================


@router.put("/profile")
async def update_profile(
    current_user: CurrentActiveUserDep,
    db: DatabaseDep,
):
    """
    Update user profile.
    
    Requires: Active user account
    """
    # User is guaranteed to be active
    return {"message": "Profile updated"}


# ==================== Verified Email Required ====================


@router.post("/programs")
async def create_program(
    verified_user: VerifiedUserDep,
    db: DatabaseDep,
):
    """
    Create a new training program.
    
    Requires: Verified email address
    """
    # User is guaranteed to be active and email verified
    return {"message": "Program created"}


# ==================== Admin Only ====================


@router.get("/admin/users")
async def list_all_users(
    admin: AdminUserDep,
    db: DatabaseDep,
):
    """
    List all users (admin only).
    
    Requires: ADMIN role
    """
    # User is guaranteed to be an active admin
    return {"users": []}


# ==================== Organization Context ====================


@router.get("/organization/members")
async def get_organization_members(
    current_user: CurrentUserDep,
    organization: CurrentOrganizationDep,
    db: DatabaseDep,
):
    """
    Get all members in user's organization.
    
    Returns: Organization and its members
    """
    return {
        "organization_id": str(organization.id),
        "organization_name": organization.name,
        "subscription_tier": organization.subscription_tier,
    }


# ==================== Rate Limited Endpoints ====================


@router.post("/auth/login")
@rate_limit(max_requests=5, window_seconds=60, identifier="ip")
async def login_with_rate_limit(email: str, password: str):
    """
    Login endpoint with rate limiting.
    
    Rate limit: 5 requests per minute per IP
    """
    # Login logic here
    return {"access_token": "...", "token_type": "bearer"}


@router.post("/auth/register")
@rate_limit(max_requests=3, window_seconds=300, identifier="ip")
async def register_with_rate_limit(email: str, password: str):
    """
    Registration endpoint with rate limiting.
    
    Rate limit: 3 requests per 5 minutes per IP
    """
    # Registration logic here
    return {"message": "Registration successful"}


# ==================== Multiple Dependencies ====================


@router.post("/admin/organizations/{org_id}/upgrade")
async def upgrade_organization(
    org_id: str,
    admin: AdminUserDep,
    db: DatabaseDep,
):
    """
    Upgrade organization subscription (admin only).
    
    Requires: ADMIN role + active account
    """
    # Admin can upgrade any organization
    return {"message": "Organization upgraded"}


@router.get("/verified/features")
async def get_verified_features(
    verified_user: VerifiedUserDep,
    organization: CurrentOrganizationDep,
):
    """
    Get features available to verified users.
    
    Requires: Verified email + active account
    """
    return {
        "user_verified": verified_user.is_verified,
        "org_tier": organization.subscription_tier,
    }
