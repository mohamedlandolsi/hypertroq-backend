"""
User profile routes.

Endpoints for user profile management, organization details,
activity stats, and account operations.
"""

import logging
from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse

from app.application.dtos.organization_dto import OrganizationWithStatsDTO
from app.application.dtos.user_dto import (
    MessageResponseDTO,
    PasswordChangeDTO,
    UserActivityStatsDTO,
    UserProfileUpdateDTO,
    UserResponseDTO,
    UserWithOrganizationDTO,
)
from app.application.services.organization_service import OrganizationService
from app.application.services.user_service import UserService
from app.core.config import settings
from app.core.dependencies import CurrentUserDep, DatabaseDep
from app.core.storage import storage_client
from app.infrastructure.repositories.organization_repository import (
    OrganizationRepository,
)
from app.infrastructure.repositories.user_repository import UserRepository

router = APIRouter(prefix="/users", tags=["User Profile"])
logger = logging.getLogger(__name__)

# Allowed image types and maximum file size
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB


# ============================================================================
# Dependency Injection
# ============================================================================


def get_user_service(db: DatabaseDep) -> UserService:
    """Get user service dependency."""
    user_repo = UserRepository(db)
    return UserService(user_repo)


def get_organization_service(db: DatabaseDep) -> OrganizationService:
    """Get organization service dependency."""
    org_repo = OrganizationRepository(db)
    user_repo = UserRepository(db)
    return OrganizationService(org_repo, user_repo)


# ============================================================================
# Profile Endpoints
# ============================================================================


@router.get(
    "/me",
    response_model=UserWithOrganizationDTO,
    summary="Get current user profile",
    description="Retrieve the authenticated user's profile with organization and subscription details",
)
async def get_current_user_profile(
    current_user: CurrentUserDep,
    user_service: Annotated[UserService, Depends(get_user_service)],
    org_service: Annotated[OrganizationService, Depends(get_organization_service)],
) -> UserWithOrganizationDTO:
    """
    Get current user profile with organization details.
    
    Returns:
        User profile including:
        - Basic user information
        - Organization details
        - Subscription tier and status
        - Profile image URL
    """
    user = await user_service.get_user(current_user.id)
    organization = await org_service.get_organization(user.organization_id)
    
    return UserWithOrganizationDTO(
        **user.model_dump(),
        organization=organization.model_dump()
    )


@router.put(
    "/me",
    response_model=UserResponseDTO,
    summary="Update user profile",
    description="Update user profile information (name only, use separate endpoint for image)",
)
async def update_user_profile(
    profile_data: UserProfileUpdateDTO,
    current_user: CurrentUserDep,
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> UserResponseDTO:
    """
    Update user profile information.
    
    Allows updating:
    - Full name
    
    Note: Use PUT /users/me/image to update profile image
    """
    # Create update DTO with only name
    from app.application.dtos.user_dto import UserUpdateDTO
    
    update_data = UserUpdateDTO(
        full_name=profile_data.full_name,
    )
    
    return await user_service.update_user(current_user.id, update_data)


@router.put(
    "/me/image",
    response_model=UserResponseDTO,
    summary="Upload profile image",
    description="Upload a new profile image with automatic optimization (JPEG, PNG, or WebP, max 5MB)",
)
async def upload_profile_image(
    image: UploadFile = File(...),
    current_user: CurrentUserDep = None,
    user_service: Annotated[UserService, Depends(get_user_service)] = None,
) -> UserResponseDTO:
    """
    Upload user profile image with automatic optimization.
    
    Accepts:
    - JPEG, PNG, or WebP format
    - Maximum file size: 5 MB
    
    Automatically optimizes image:
    - Resizes to max 800x800 (maintains aspect ratio)
    - Compresses to 85% quality JPEG
    - Reduces file size for faster loading
    
    Returns:
        Updated user profile with new image URL
        
    Raises:
        400: Invalid file format or size
        500: Upload failed
    """
    from app.core.image_utils import optimize_profile_image, ImageProcessingError
    
    # Validate file type
    if image.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed types: {', '.join(ALLOWED_IMAGE_TYPES)}",
        )
    
    # Read file content
    image_content = await image.read()
    
    # Validate file size
    if len(image_content) > MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size: {MAX_IMAGE_SIZE // (1024 * 1024)} MB",
        )
    
    try:
        # Optimize image (resize to 800x800 and compress)
        optimized_image, metadata = optimize_profile_image(image_content)
        
        logger.info(
            f"Image optimized for user {current_user_id}: "
            f"{metadata['original_size_kb']:.1f}KB -> {metadata['final_size_kb']:.1f}KB "
            f"({metadata['reduction_percent']:.1f}% reduction)"
        )
        
    except ImageProcessingError as e:
        logger.error(f"Image processing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Image processing failed: {str(e)}",
        )
    
    try:
        # Upload optimized image to cloud storage
        file_path = f"users/{current_user_id}/profile.jpg"  # Always save as JPEG
        image_url = await storage_client.upload_file(
            file_content=optimized_image,
            bucket_name="hypertroq-user-uploads",
            file_path=file_path,
            content_type="image/jpeg",
            make_public=True,
        )
        
        if not image_url:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload image",
            )
        
        # Update user profile with image URL
        from app.application.dtos.user_dto import UserUpdateDTO
        
        update_data = UserUpdateDTO(profile_image_url=image_url)
        return await user_service.update_user(current_user.id, update_data)
        
    except Exception as e:
        logger.error(f"Failed to upload profile image: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload image",
        )


@router.put(
    "/me/password",
    response_model=MessageResponseDTO,
    summary="Change password",
    description="Change user password (requires current password)",
)
async def change_password(
    password_data: PasswordChangeDTO,
    current_user: CurrentUserDep,
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> MessageResponseDTO:
    """
    Change user password.
    
    Requires:
    - Current password for verification
    - New password (minimum 8 characters)
    
    Returns:
        Success message
        
    Raises:
        400: Current password is incorrect
        404: User not found
        
    Note:
        Sends confirmation email to user's email address
    """
    from app.infrastructure.email.service import EmailService
    
    # Change password
    await user_service.change_password(current_user.id, password_data)
    
    # Send confirmation email
    user_dto = await user_service.get_user(current_user.id)
    email_service = EmailService()
    await email_service.send_password_change_email(
        to_email=user_dto.email,
        user_name=user_dto.full_name or user_dto.email,
    )
    
    return MessageResponseDTO(message="Password changed successfully")


# ============================================================================
# Organization Endpoints
# ============================================================================


@router.get(
    "/me/organization",
    response_model=OrganizationWithStatsDTO,
    summary="Get user's organization",
    description="Retrieve organization details including team members and subscription info",
)
async def get_user_organization(
    current_user: CurrentUserDep,
    user_service: Annotated[UserService, Depends(get_user_service)],
    org_service: Annotated[OrganizationService, Depends(get_organization_service)],
) -> OrganizationWithStatsDTO:
    """
    Get user's organization details.
    
    Returns:
        Organization information including:
        - Organization name and ID
        - Subscription tier and status
        - User count
        - Feature availability flags
    """
    user = await user_service.get_user(current_user.id)
    organization = await org_service.get_organization_with_stats(user.organization_id)
    return organization


# ============================================================================
# Activity & Stats Endpoints
# ============================================================================


@router.get(
    "/me/programs",
    response_model=dict,
    summary="Get user's programs",
    description="List all programs created by the user",
)
async def get_user_programs(
    current_user: CurrentUserDep,
    user_service: Annotated[UserService, Depends(get_user_service)],
    db: DatabaseDep,
    skip: int = 0,
    limit: int = 20,
) -> dict:
    """
    Get user's training programs.
    
    Query Parameters:
        skip: Number of records to skip (default: 0)
        limit: Maximum records to return (default: 20, max: 100)
    
    Returns:
        List of user's programs with pagination metadata
        
    Example:
        GET /api/v1/users/me/programs?skip=0&limit=10
        
        Response:
        {
            "data": [
                {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "name": "Upper/Lower 4-Day Split",
                    "description": "Classic upper/lower split",
                    "split_type": "UPPER_LOWER",
                    "structure_type": "WEEKLY",
                    "is_template": false,
                    "duration_weeks": 8,
                    "session_count": 4,
                    "created_at": "2025-11-23T10:00:00Z"
                }
            ],
            "meta": {
                "total": 5,
                "skip": 0,
                "limit": 10,
                "page": 1,
                "has_more": false
            }
        }
    """
    from app.repositories.program_repository import ProgramRepository
    
    # Get current user
    user_dto = await user_service.get_user(current_user.id)
    
    # Create program repository
    program_repo = ProgramRepository(db)
    
    # Get user's programs (non-templates, from their organization)
    programs = await program_repo.get_user_programs(
        org_id=UUID(user_dto.organization_id),
        user_id=current_user.id
    )
    
    # Apply pagination manually (programs are already sorted by created_at desc)
    total = len(programs)
    paginated_programs = programs[skip:skip + limit]
    
    # Convert to response format
    items = [
        {
            "id": str(program.id),
            "name": program.name,
            "description": program.description,
            "split_type": program.split_type.value,
            "structure_type": program.structure_type.value,
            "is_template": program.is_template,
            "duration_weeks": program.duration_weeks,
            "session_count": len(program.sessions),
            "created_at": program.created_at.isoformat(),
        }
        for program in paginated_programs
    ]
    
    # Calculate pagination metadata
    page = (skip // limit) + 1 if limit > 0 else 1
    has_more = (skip + limit) < total
    
    return {
        "data": items,
        "meta": {
            "total": total,
            "skip": skip,
            "limit": limit,
            "page": page,
            "has_more": has_more,
        },
    }


@router.get(
    "/me/activity",
    response_model=UserActivityStatsDTO,
    summary="Get user activity stats",
    description="Retrieve user activity statistics including programs, exercises, and last active date",
)
async def get_user_activity(
    current_user: CurrentUserDep,
    user_service: Annotated[UserService, Depends(get_user_service)],
    db: DatabaseDep,
) -> UserActivityStatsDTO:
    """
    Get user activity statistics.
    
    Returns:
        Activity metrics including:
        - Programs created count (real data)
        - Sessions created count (placeholder: 0)
        - Exercises created count (placeholder: 0)
        - Last active timestamp
        - Account age in days
    """
    from app.repositories.program_repository import ProgramRepository
    
    # Create program repository to get real counts
    program_repo = ProgramRepository(db)
    
    return await user_service.get_user_activity_stats(
        current_user.id,
        program_repository=program_repo
    )


# ============================================================================
# Account Management Endpoints
# ============================================================================


@router.delete(
    "/me",
    response_model=dict,
    summary="Request account deletion",
    description="Request account deletion with 30-day grace period",
)
async def request_account_deletion(
    current_user: CurrentUserDep,
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> dict:
    """
    Request account deletion with 30-day grace period.
    
    This endpoint initiates the account deletion process:
    1. Marks account for deletion (30-day grace period)
    2. Sends confirmation email with cancellation link
    3. Account can be cancelled any time during grace period
    4. After 30 days, account is permanently deleted
    
    Returns:
        Deletion request details including grace period end date
        
    Example Response:
        {
            "requested_at": "2025-12-15T10:00:00Z",
            "deletion_date": "2026-01-14T10:00:00Z",
            "days_remaining": 30,
            "message": "Account deletion requested. You have 30 days to cancel."
        }
    """
    from app.infrastructure.email.service import EmailService
    from datetime import timedelta
    
    # Request deletion (marks for deletion, doesn't actually delete)
    deletion_info = await user_service.delete_user(current_user.id)
    
    # Get user details for email
    user_dto = await user_service.get_user(current_user.id)
    
    # Send deletion confirmation email
    email_service = EmailService()
    deletion_date = datetime.fromisoformat(deletion_info["deletion_date"])
    cancellation_link = f"{settings.FRONTEND_URL}/account/cancel-deletion"
    
    await email_service.send_deletion_request_email(
        to_email=user_dto.email,
        user_name=user_dto.full_name or user_dto.email,
        deletion_date=deletion_date.strftime("%B %d, %Y at %I:%M %p UTC"),
        cancellation_link=cancellation_link,
    )
    
    return deletion_info


@router.post(
    "/me/cancel-deletion",
    response_model=MessageResponseDTO,
    summary="Cancel account deletion",
    description="Cancel pending account deletion request",
)
async def cancel_account_deletion(
    current_user: CurrentUserDep,
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> MessageResponseDTO:
    """
    Cancel pending account deletion request.
    
    This endpoint cancels a previously requested account deletion:
    1. Removes deletion timestamp
    2. Sends cancellation confirmation email
    3. Account remains active
    
    Returns:
        Confirmation message
        
    Raises:
        400: No deletion request pending
        404: User not found
    """
    from app.infrastructure.email.service import EmailService
    
    # Cancel deletion
    await user_service.cancel_deletion(current_user.id)
    
    # Get user details for email
    user_dto = await user_service.get_user(current_user.id)
    
    # Send cancellation confirmation email
    email_service = EmailService()
    await email_service.send_deletion_cancelled_email(
        to_email=user_dto.email,
        user_name=user_dto.full_name or user_dto.email,
    )
    
    return MessageResponseDTO(
        message="Account deletion cancelled. Your account is safe."
    )

