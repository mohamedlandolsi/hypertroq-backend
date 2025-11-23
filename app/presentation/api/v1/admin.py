"""
Admin API routes for system management and analytics.

All endpoints require admin role and include:
- Dashboard statistics
- User management
- Global exercise management
- Program template management
- Analytics and reporting
- Audit logging
"""

import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.core.dependencies import (
    AdminUserDep,
    DatabaseDep,
    rate_limit,
)
from app.domain.entities.user import User
from app.infrastructure.repositories.organization_repository import OrganizationRepository
from app.repositories.exercise_repository import ExerciseRepository
from app.repositories.program_repository import ProgramRepository
from app.repositories.user_repository import UserRepository
from app.schemas.admin import (
    AdminDashboardStats,
    SubscriptionAnalytics,
    UpdateUserRoleRequest,
    UsageAnalytics,
    UserActionResponse,
    UserFilter,
    UserListResponse,
)
from app.schemas.exercise import (
    ExerciseCreate,
    ExerciseFilter,
    ExerciseListResponse,
    ExerciseResponse,
    ExerciseUpdate,
)
from app.schemas.training_program import (
    ProgramCreate,
    ProgramFilter,
    ProgramListResponse,
    ProgramResponse,
    ProgramUpdate,
)
from app.services.admin_service import AdminService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["Admin"])


# ==================== Dependency Injection ====================


def get_admin_service(
    db: DatabaseDep,
) -> AdminService:
    """
    Get admin service with all required repositories.
    
    Args:
        db: Database session
        
    Returns:
        AdminService instance
    """
    user_repo = UserRepository(db)
    org_repo = OrganizationRepository(db)
    exercise_repo = ExerciseRepository(db)
    program_repo = ProgramRepository(db)
    
    return AdminService(
        session=db,
        user_repo=user_repo,
        org_repo=org_repo,
        exercise_repo=exercise_repo,
        program_repo=program_repo,
    )


AdminServiceDep = Annotated[AdminService, Depends(get_admin_service)]


# ==================== Dashboard ====================


@router.get(
    "/dashboard",
    response_model=AdminDashboardStats,
    summary="Get admin dashboard statistics",
    description="""
    Get comprehensive dashboard statistics for system monitoring.
    
    **Requires:** Admin role
    
    **Returns:**
    - **User metrics:** Total, active (30 days), verified, suspended
    - **Organization metrics:** Total, active organizations
    - **Subscription stats:** Free/Pro breakdown, MRR, active/cancelled/expired
    - **Content stats:** Exercises (global/custom), programs (templates/custom)
    - **System health:** Database, Redis status, response time, error rate, uptime
    
    **Use cases:**
    - Monitor system health and performance
    - Track user growth and engagement
    - Monitor subscription revenue (MRR)
    - Identify system issues early
    
    **Audit:** This action is logged for security monitoring.
    """,
    responses={
        200: {
            "description": "Dashboard statistics",
            "content": {
                "application/json": {
                    "example": {
                        "total_users": 500,
                        "active_users": 320,
                        "verified_users": 450,
                        "suspended_users": 5,
                        "total_organizations": 195,
                        "active_organizations": 180,
                        "subscription_stats": {
                            "free_tier_count": 150,
                            "pro_tier_count": 45,
                            "total_active": 45,
                            "monthly_recurring_revenue": 1350.00
                        },
                        "content_stats": {
                            "total_exercises": 250,
                            "global_exercises": 200,
                            "total_programs": 120,
                            "program_templates": 15
                        },
                        "system_health": {
                            "database_status": "healthy",
                            "redis_status": "healthy",
                            "avg_response_time_ms": 45.2
                        }
                    }
                }
            }
        },
        403: {"description": "Not an admin user"}
    }
)
async def get_dashboard(
    admin_service: AdminServiceDep,
    admin_user: AdminUserDep,
) -> AdminDashboardStats:
    """
    Get comprehensive dashboard statistics.
    
    Requires admin role. Action is logged for audit.
    """
    try:
        logger.info(f"Admin {admin_user.email} accessing dashboard")
        return await admin_service.get_dashboard_stats(admin_user)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching dashboard stats: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve dashboard statistics"
        )


# ==================== User Management ====================


@router.get(
    "/users",
    response_model=UserListResponse,
    summary="List users with admin details",
    description="""
    List all users with filtering, pagination, and admin-only fields.
    
    **Requires:** Admin role
    
    **Filters:**
    - `search`: Search in email and full name
    - `role`: Filter by role (USER, ADMIN)
    - `is_active`: Filter by active status
    - `is_verified`: Filter by email verification status
    - `subscription_tier`: Filter by organization subscription tier (FREE, PRO)
    
    **Admin-only fields:**
    - Login count
    - Programs created
    - Custom exercises created
    - Last login timestamp
    - Organization details
    
    **Use cases:**
    - Find users by email or name
    - Identify suspended or unverified accounts
    - Monitor user activity and content creation
    - Export user lists for analysis
    """,
    responses={
        200: {
            "description": "Paginated user list with admin details",
            "content": {
                "application/json": {
                    "example": {
                        "items": [
                            {
                                "id": "uuid",
                                "email": "user@example.com",
                                "role": "USER",
                                "is_active": True,
                                "is_verified": True,
                                "organization_name": "Gym XYZ",
                                "subscription_tier": "PRO",
                                "programs_created": 3,
                                "exercises_created": 5
                            }
                        ],
                        "total": 500,
                        "page": 1,
                        "has_more": True
                    }
                }
            }
        },
        403: {"description": "Not an admin user"}
    }
)
async def list_users(
    admin_service: AdminServiceDep,
    admin_user: AdminUserDep,
    search: str | None = Query(None, description="Search in email and name", max_length=100),
    role: str | None = Query(None, description="Filter by role (USER, ADMIN)"),
    is_active: bool | None = Query(None, description="Filter by active status"),
    is_verified: bool | None = Query(None, description="Filter by verified status"),
    subscription_tier: str | None = Query(None, description="Filter by subscription tier (FREE, PRO)"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
) -> UserListResponse:
    """
    List users with admin details and filtering.
    
    Requires admin role. Returns extended user information.
    """
    try:
        filters = UserFilter(
            search=search,
            role=role,
            is_active=is_active,
            is_verified=is_verified,
            subscription_tier=subscription_tier,
            skip=skip,
            limit=limit,
        )
        
        logger.info(
            f"Admin {admin_user.email} listing users with filters: "
            f"search={search}, role={role}, active={is_active}"
        )
        
        return await admin_service.list_users(filters, admin_user)
    
    except ValueError as e:
        logger.warning(f"Invalid filter values: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing users: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users"
        )


@router.put(
    "/users/{user_id}/role",
    response_model=dict,
    summary="Update user role",
    description="""
    Update a user's role (USER ↔ ADMIN).
    
    **Requires:** Admin role
    
    **Restrictions:**
    - Cannot change your own role
    - Only USER and ADMIN roles supported
    
    **Use cases:**
    - Promote user to admin
    - Demote admin to regular user
    - Grant system access to trusted users
    
    **Audit:** This critical action is logged with old/new roles.
    
    **Rate limiting:** 10 role changes per hour per admin.
    """,
    responses={
        200: {
            "description": "Role updated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "message": "User role updated successfully",
                        "user_id": "uuid",
                        "new_role": "ADMIN"
                    }
                }
            }
        },
        400: {"description": "Invalid role value"},
        403: {"description": "Cannot change own role or not admin"},
        404: {"description": "User not found"},
        429: {"description": "Rate limit exceeded"}
    }
)
@rate_limit(max_requests=10, window_seconds=3600, identifier="user")
async def update_user_role(
    request: Request,
    user_id: UUID,
    role_update: UpdateUserRoleRequest,
    admin_service: AdminServiceDep,
    admin_user: AdminUserDep,
) -> dict:
    """
    Update user role (USER ↔ ADMIN).
    
    Requires admin role. Cannot change own role.
    Rate limited to 10 changes per hour.
    """
    try:
        logger.info(
            f"Admin {admin_user.email} updating user {user_id} role to {role_update.role}"
        )
        
        updated_user = await admin_service.update_user_role(
            user_id,
            role_update,
            admin_user
        )
        
        return {
            "message": "User role updated successfully",
            "user_id": str(updated_user.id),
            "new_role": updated_user.role
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user role: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user role"
        )


@router.post(
    "/users/{user_id}/suspend",
    response_model=UserActionResponse,
    summary="Suspend user account",
    description="""
    Suspend a user account (set is_active to False).
    
    **Requires:** Admin role
    
    **Effects:**
    - User cannot log in
    - Existing sessions remain valid until expiry
    - User data is preserved
    - Can be reversed (unsuspend via database)
    
    **Restrictions:**
    - Cannot suspend your own account
    - Cannot suspend already suspended accounts
    
    **Use cases:**
    - Temporarily disable accounts for violations
    - Lock accounts pending investigation
    - Respond to security incidents
    
    **Audit:** Action logged with reason and admin details.
    
    **Rate limiting:** 20 suspensions per hour per admin.
    """,
    responses={
        200: {
            "description": "User suspended successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "User suspended successfully",
                        "user_id": "uuid",
                        "action": "suspend",
                        "performed_by": "admin-uuid"
                    }
                }
            }
        },
        400: {"description": "User already suspended"},
        403: {"description": "Cannot suspend own account or not admin"},
        404: {"description": "User not found"},
        429: {"description": "Rate limit exceeded"}
    }
)
@rate_limit(max_requests=20, window_seconds=3600, identifier="user")
async def suspend_user(
    request: Request,
    user_id: UUID,
    admin_service: AdminServiceDep,
    admin_user: AdminUserDep,
    reason: str | None = Query(None, description="Reason for suspension", max_length=500),
) -> UserActionResponse:
    """
    Suspend user account.
    
    Requires admin role. Cannot suspend self.
    Rate limited to 20 suspensions per hour.
    """
    try:
        logger.warning(
            f"Admin {admin_user.email} suspending user {user_id}. Reason: {reason}"
        )
        
        return await admin_service.suspend_user(user_id, admin_user, reason)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error suspending user: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to suspend user"
        )


@router.delete(
    "/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Permanently delete user",
    description="""
    Permanently delete a user account and associated data.
    
    **Requires:** Admin role
    
    **⚠️ WARNING - DESTRUCTIVE OPERATION:**
    - User account is permanently deleted
    - Cannot be undone
    - May orphan organization if last member
    - Cascade effects on user data
    
    **Restrictions:**
    - Cannot delete your own account
    - Check for organization impact before deletion
    
    **Use cases:**
    - GDPR deletion requests
    - Remove spam/fake accounts
    - Clean up test accounts
    
    **Audit:** Critical action logged with full details.
    
    **Rate limiting:** 5 deletions per hour per admin.
    """,
    responses={
        204: {"description": "User permanently deleted"},
        403: {"description": "Cannot delete own account or not admin"},
        404: {"description": "User not found"},
        429: {"description": "Rate limit exceeded"}
    }
)
@rate_limit(max_requests=5, window_seconds=3600, identifier="user")
async def delete_user(
    request: Request,
    user_id: UUID,
    admin_service: AdminServiceDep,
    admin_user: AdminUserDep,
) -> None:
    """
    Permanently delete user account.
    
    **DESTRUCTIVE:** Cannot be undone.
    Requires admin role. Cannot delete self.
    Rate limited to 5 deletions per hour.
    """
    try:
        logger.critical(
            f"Admin {admin_user.email} deleting user {user_id} - PERMANENT"
        )
        
        await admin_service.delete_user(user_id, admin_user)
        
        logger.critical(f"User {user_id} permanently deleted")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user"
        )


# ==================== Exercise Management ====================


@router.get(
    "/exercises",
    response_model=ExerciseListResponse,
    summary="Get all exercises (admin view)",
    description="""
    Get all exercises including global and organization-specific.
    
    **Requires:** Admin role
    
    **Filters:**
    - `search`: Full-text search in name and description
    - `equipment`: Filter by equipment type
    - `muscle_group`: Filter by primary muscle group
    - `is_global`: Show only global (None) or org-specific (not None)
    
    **Admin view includes:**
    - All global exercises (organization_id = NULL)
    - All organization exercises (for monitoring)
    - Creator information
    - Usage statistics
    
    **Use cases:**
    - Review all exercises in system
    - Identify duplicate exercises
    - Monitor custom exercise creation
    - Quality control on global library
    """,
    responses={
        200: {"description": "List of all exercises"},
        403: {"description": "Not an admin user"}
    }
)
async def list_all_exercises(
    admin_service: AdminServiceDep,
    admin_user: AdminUserDep,
    search: str | None = Query(None, description="Search term", max_length=100),
    equipment: str | None = Query(None, description="Filter by equipment"),
    muscle_group: str | None = Query(None, description="Filter by muscle group"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
) -> ExerciseListResponse:
    """
    Get all exercises with admin access.
    
    Requires admin role. Returns global and org exercises.
    """
    try:
        logger.info(f"Admin {admin_user.email} listing all exercises")
        
        filters = ExerciseFilter(
            search=search,
            equipment=equipment,
            muscle_group=muscle_group,
            skip=skip,
            limit=limit,
        )
        
        # Use exercise repository directly for admin view
        # This would need to be exposed via admin service for proper access
        # For now, return via service method
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Admin exercise listing not yet fully implemented. Use service method."
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing exercises: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve exercises"
        )


@router.post(
    "/exercises",
    response_model=ExerciseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create global exercise",
    description="""
    Create a new global exercise visible to all users.
    
    **Requires:** Admin role
    
    **Global exercises:**
    - Visible to all users in exercise library
    - No organization_id (NULL in database)
    - Part of official exercise database
    - Should be high-quality, well-documented
    
    **Requirements:**
    - Unique name (case-insensitive check)
    - Valid equipment type
    - At least one primary muscle
    - Proper muscle volume contributions (sum to reasonable values)
    
    **Use cases:**
    - Build official exercise library
    - Add new popular exercises
    - Standardize exercise database
    - Ensure quality control
    
    **Audit:** Creation logged with exercise details.
    
    **Rate limiting:** 20 creations per hour per admin.
    """,
    responses={
        201: {
            "description": "Global exercise created",
            "content": {
                "application/json": {
                    "example": {
                        "id": "uuid",
                        "name": "Barbell Bench Press",
                        "equipment": "BARBELL",
                        "primary_muscles": ["CHEST"],
                        "is_global": True
                    }
                }
            }
        },
        400: {"description": "Invalid exercise data"},
        403: {"description": "Not an admin user"},
        429: {"description": "Rate limit exceeded"}
    }
)
@rate_limit(max_requests=20, window_seconds=3600, identifier="user")
async def create_global_exercise(
    request: Request,
    exercise_data: ExerciseCreate,
    admin_service: AdminServiceDep,
    admin_user: AdminUserDep,
) -> ExerciseResponse:
    """
    Create global exercise visible to all users.
    
    Requires admin role.
    Rate limited to 20 creations per hour.
    """
    try:
        logger.info(
            f"Admin {admin_user.email} creating global exercise: {exercise_data.name}"
        )
        
        exercise = await admin_service.create_global_exercise(
            exercise_data,
            admin_user
        )
        
        # Convert to response (would need proper DTO conversion)
        return ExerciseResponse(
            id=exercise.id,
            name=exercise.name,
            description=exercise.description,
            equipment=exercise.equipment.value,
            primary_muscles=[m.value for m in exercise.primary_muscles],
            secondary_muscles=[m.value for m in exercise.secondary_muscles],
            volume_contribution=exercise.volume_contribution.to_dict(),
            instructions=exercise.instructions,
            tips=exercise.tips,
            image_url=exercise.image_url,
            video_url=exercise.video_url,
            is_custom=False,  # Global exercise
            created_at=exercise.created_at,
            updated_at=exercise.updated_at,
        )
    
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Exercise validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating global exercise: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create global exercise"
        )


@router.put(
    "/exercises/{exercise_id}",
    response_model=ExerciseResponse,
    summary="Update global exercise",
    description="""
    Update an existing global exercise.
    
    **Requires:** Admin role
    
    **Restrictions:**
    - Can only update global exercises (organization_id = NULL)
    - Cannot change organization exercises
    - Name must remain unique
    
    **Use cases:**
    - Fix typos in exercise names
    - Update muscle contributions
    - Add instructions or tips
    - Update media URLs
    
    **Audit:** Update logged with changes made.
    
    **Rate limiting:** 30 updates per hour per admin.
    """,
    responses={
        200: {"description": "Global exercise updated"},
        400: {"description": "Invalid update data"},
        403: {"description": "Not admin or not a global exercise"},
        404: {"description": "Exercise not found"},
        429: {"description": "Rate limit exceeded"}
    }
)
@rate_limit(max_requests=30, window_seconds=3600, identifier="user")
async def update_global_exercise(
    request: Request,
    exercise_id: UUID,
    exercise_data: ExerciseUpdate,
    admin_service: AdminServiceDep,
    admin_user: AdminUserDep,
) -> ExerciseResponse:
    """
    Update global exercise.
    
    Requires admin role. Only updates global exercises.
    Rate limited to 30 updates per hour.
    """
    try:
        logger.info(
            f"Admin {admin_user.email} updating global exercise {exercise_id}"
        )
        
        exercise = await admin_service.update_global_exercise(
            exercise_id,
            exercise_data,
            admin_user
        )
        
        # Convert to response
        return ExerciseResponse(
            id=exercise.id,
            name=exercise.name,
            description=exercise.description,
            equipment=exercise.equipment.value,
            primary_muscles=[m.value for m in exercise.primary_muscles],
            secondary_muscles=[m.value for m in exercise.secondary_muscles],
            volume_contribution=exercise.volume_contribution.to_dict(),
            instructions=exercise.instructions,
            tips=exercise.tips,
            image_url=exercise.image_url,
            video_url=exercise.video_url,
            is_custom=False,
            created_at=exercise.created_at,
            updated_at=exercise.updated_at,
        )
    
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Exercise update validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating global exercise: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update global exercise"
        )


@router.delete(
    "/exercises/{exercise_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete global exercise",
    description="""
    Delete a global exercise from the system.
    
    **Requires:** Admin role
    
    **⚠️ WARNING:**
    - May affect existing programs using this exercise
    - Exercise will be removed from workout sessions
    - Consider deprecating instead of deleting
    
    **Restrictions:**
    - Can only delete global exercises
    - Cannot delete organization exercises
    
    **Use cases:**
    - Remove duplicate exercises
    - Clean up poorly documented exercises
    - Remove exercises with incorrect data
    
    **Best practice:** Check usage before deletion.
    
    **Audit:** Deletion logged with exercise details.
    
    **Rate limiting:** 10 deletions per hour per admin.
    """,
    responses={
        204: {"description": "Global exercise deleted"},
        403: {"description": "Not admin or not a global exercise"},
        404: {"description": "Exercise not found"},
        429: {"description": "Rate limit exceeded"}
    }
)
@rate_limit(max_requests=10, window_seconds=3600, identifier="user")
async def delete_global_exercise(
    request: Request,
    exercise_id: UUID,
    admin_service: AdminServiceDep,
    admin_user: AdminUserDep,
) -> None:
    """
    Delete global exercise.
    
    **WARNING:** May affect existing programs.
    Requires admin role. Only deletes global exercises.
    Rate limited to 10 deletions per hour.
    """
    try:
        logger.warning(
            f"Admin {admin_user.email} deleting global exercise {exercise_id}"
        )
        
        await admin_service.delete_global_exercise(exercise_id, admin_user)
        
        logger.warning(f"Global exercise {exercise_id} deleted")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting global exercise: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete global exercise"
        )


# ==================== Program Template Management ====================


@router.get(
    "/programs/templates",
    response_model=ProgramListResponse,
    summary="Get all program templates",
    description="""
    Get all program templates (admin view).
    
    **Requires:** Admin role
    
    **Admin view includes:**
    - All templates regardless of creator
    - Clone statistics
    - Usage metrics
    - Template quality indicators
    
    **Filters:**
    - `search`: Search in name and description
    - `split_type`: Filter by split type
    - `structure_type`: Filter by structure (WEEKLY, CYCLIC)
    
    **Use cases:**
    - Review all available templates
    - Monitor template usage
    - Identify popular templates
    - Quality control on template library
    """,
    responses={
        200: {"description": "List of all templates"},
        403: {"description": "Not an admin user"}
    }
)
async def list_program_templates(
    admin_service: AdminServiceDep,
    admin_user: AdminUserDep,
    search: str | None = Query(None, description="Search term", max_length=100),
    split_type: str | None = Query(None, description="Filter by split type"),
    structure_type: str | None = Query(None, description="Filter by structure"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
) -> ProgramListResponse:
    """
    Get all program templates.
    
    Requires admin role. Returns all templates with stats.
    """
    try:
        logger.info(f"Admin {admin_user.email} listing program templates")
        
        # Would use program repository with admin access
        # For now, raise not implemented
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Admin template listing not yet fully implemented. Use service method."
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing templates: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve templates"
        )


@router.post(
    "/programs/templates",
    response_model=ProgramResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create program template",
    description="""
    Create a new program template available to all users.
    
    **Requires:** Admin role
    
    **Template characteristics:**
    - is_template = True
    - organization_id = NULL (global)
    - Visible in template library for all users
    - Can be cloned by any Pro user
    
    **Requirements:**
    - Well-documented with clear name and description
    - Complete session and exercise configuration
    - Balanced volume distribution
    - Follows hypertrophy best practices
    
    **Use cases:**
    - Build official program library
    - Add proven program templates
    - Provide ready-to-use programs
    - Guide users to effective training
    
    **Audit:** Creation logged with program details.
    
    **Rate limiting:** 10 creations per hour per admin.
    """,
    responses={
        201: {
            "description": "Template created",
            "content": {
                "application/json": {
                    "example": {
                        "id": "uuid",
                        "name": "Upper/Lower 4-Day Split",
                        "is_template": True,
                        "sessions": []
                    }
                }
            }
        },
        400: {"description": "Invalid program data"},
        403: {"description": "Not an admin user"},
        429: {"description": "Rate limit exceeded"}
    }
)
@rate_limit(max_requests=10, window_seconds=3600, identifier="user")
async def create_program_template(
    request: Request,
    program_data: ProgramCreate,
    admin_service: AdminServiceDep,
    admin_user: AdminUserDep,
) -> ProgramResponse:
    """
    Create program template visible to all users.
    
    Requires admin role.
    Rate limited to 10 creations per hour.
    """
    try:
        logger.info(
            f"Admin {admin_user.email} creating program template: {program_data.name}"
        )
        
        program = await admin_service.create_program_template(
            program_data,
            admin_user
        )
        
        # Convert to response (simplified - would need proper conversion)
        return ProgramResponse(
            id=program.id,
            name=program.name,
            description=program.description,
            split_type=program.split_type.value,
            structure_type=program.structure_type.value,
            structure_config=program.structure_config.to_dict(),
            is_template=True,
            duration_weeks=program.duration_weeks,
            sessions=[],  # Would include session details
            stats=None,  # Would calculate stats
            created_at=program.created_at,
            updated_at=program.updated_at,
        )
    
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Template validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating template: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create program template"
        )


@router.put(
    "/programs/templates/{template_id}",
    response_model=ProgramResponse,
    summary="Update program template",
    description="""
    Update an existing program template.
    
    **Requires:** Admin role
    
    **What you can update:**
    - Template name and description
    - Duration in weeks
    - Note: Structure changes require creating new template
    
    **Restrictions:**
    - Can only update templates (is_template = True)
    - Cannot update user programs
    - Changes affect future clones only
    
    **Use cases:**
    - Fix typos in template names
    - Update descriptions
    - Adjust program duration
    - Improve template quality
    
    **Audit:** Update logged with changes.
    
    **Rate limiting:** 30 updates per hour per admin.
    """,
    responses={
        200: {"description": "Template updated"},
        400: {"description": "Invalid update data"},
        403: {"description": "Not admin or not a template"},
        404: {"description": "Template not found"},
        429: {"description": "Rate limit exceeded"}
    }
)
@rate_limit(max_requests=30, window_seconds=3600, identifier="user")
async def update_program_template(
    request: Request,
    template_id: UUID,
    program_data: ProgramUpdate,
    admin_service: AdminServiceDep,
    admin_user: AdminUserDep,
) -> ProgramResponse:
    """
    Update program template.
    
    Requires admin role. Only updates templates.
    Rate limited to 30 updates per hour.
    """
    try:
        logger.info(
            f"Admin {admin_user.email} updating template {template_id}"
        )
        
        program = await admin_service.update_program_template(
            template_id,
            program_data,
            admin_user
        )
        
        # Convert to response
        return ProgramResponse(
            id=program.id,
            name=program.name,
            description=program.description,
            split_type=program.split_type.value,
            structure_type=program.structure_type.value,
            structure_config=program.structure_config.to_dict(),
            is_template=True,
            duration_weeks=program.duration_weeks,
            sessions=[],
            stats=None,
            created_at=program.created_at,
            updated_at=program.updated_at,
        )
    
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Template update validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating template: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update program template"
        )


@router.delete(
    "/programs/templates/{template_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete program template",
    description="""
    Delete a program template from the library.
    
    **Requires:** Admin role
    
    **Effects:**
    - Template removed from library
    - Users cannot clone it anymore
    - Existing cloned programs are NOT affected
    - Cascade deletes all sessions
    
    **Restrictions:**
    - Can only delete templates (is_template = True)
    - Cannot delete user programs
    
    **Use cases:**
    - Remove outdated templates
    - Clean up duplicate templates
    - Remove poor quality templates
    - Reorganize template library
    
    **Audit:** Deletion logged with template details.
    
    **Rate limiting:** 5 deletions per hour per admin.
    """,
    responses={
        204: {"description": "Template deleted"},
        403: {"description": "Not admin or not a template"},
        404: {"description": "Template not found"},
        429: {"description": "Rate limit exceeded"}
    }
)
@rate_limit(max_requests=5, window_seconds=3600, identifier="user")
async def delete_program_template(
    request: Request,
    template_id: UUID,
    admin_service: AdminServiceDep,
    admin_user: AdminUserDep,
) -> None:
    """
    Delete program template.
    
    Requires admin role. Only deletes templates.
    Cloned programs are not affected.
    Rate limited to 5 deletions per hour.
    """
    try:
        logger.warning(
            f"Admin {admin_user.email} deleting template {template_id}"
        )
        
        await admin_service.delete_program_template(template_id, admin_user)
        
        logger.warning(f"Template {template_id} deleted")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting template: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete program template"
        )


# ==================== Analytics ====================


@router.get(
    "/analytics/subscriptions",
    response_model=SubscriptionAnalytics,
    summary="Get subscription analytics",
    description="""
    Get detailed subscription analytics and revenue metrics.
    
    **Requires:** Admin role
    
    **Metrics included:**
    - **Current state:** Total, active, cancelled, expired subscribers
    - **Revenue:** MRR (Monthly Recurring Revenue), ARPU (Average Revenue Per User)
    - **Growth:** New subscriptions, cancellations this month
    - **Churn:** Monthly churn rate percentage
    - **Tier distribution:** Free vs Pro percentages
    - **Historical data:** 12-month revenue and subscriber growth trends
    
    **Use cases:**
    - Monitor business health and revenue
    - Track subscription growth trends
    - Identify churn issues
    - Forecast future revenue
    - Make pricing decisions
    
    **Refresh rate:** Generated in real-time on each request.
    """,
    responses={
        200: {
            "description": "Subscription analytics",
            "content": {
                "application/json": {
                    "example": {
                        "total_subscribers": 45,
                        "active_subscribers": 43,
                        "monthly_recurring_revenue": 1350.00,
                        "average_revenue_per_user": 31.40,
                        "churn_rate_percent": 2.3,
                        "monthly_revenue_history": []
                    }
                }
            }
        },
        403: {"description": "Not an admin user"}
    }
)
async def get_subscription_analytics(
    admin_service: AdminServiceDep,
    admin_user: AdminUserDep,
) -> SubscriptionAnalytics:
    """
    Get subscription analytics and revenue metrics.
    
    Requires admin role. Real-time data.
    """
    try:
        logger.info(f"Admin {admin_user.email} fetching subscription analytics")
        return await admin_service.get_subscription_analytics(admin_user)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching subscription analytics: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve subscription analytics"
        )


@router.get(
    "/analytics/usage",
    response_model=UsageAnalytics,
    summary="Get usage analytics",
    description="""
    Get system usage analytics and engagement metrics.
    
    **Requires:** Admin role
    
    **Metrics included:**
    - **User engagement:** DAU, WAU, MAU (Daily/Weekly/Monthly Active Users)
    - **Content creation:** Exercises and programs created this week/month
    - **Feature adoption:** Users with custom content, cloned templates
    - **Activity trends:** Avg programs per user, avg exercises per program
    - **Popular content:** Most used exercises, most cloned templates
    
    **Use cases:**
    - Monitor user engagement
    - Track feature adoption
    - Identify popular content
    - Understand user behavior
    - Guide product development
    
    **Refresh rate:** Generated in real-time on each request.
    """,
    responses={
        200: {
            "description": "Usage analytics",
            "content": {
                "application/json": {
                    "example": {
                        "daily_active_users": 120,
                        "weekly_active_users": 280,
                        "monthly_active_users": 320,
                        "users_with_custom_programs": 78,
                        "avg_programs_per_user": 2.4
                    }
                }
            }
        },
        403: {"description": "Not an admin user"}
    }
)
async def get_usage_analytics(
    admin_service: AdminServiceDep,
    admin_user: AdminUserDep,
) -> UsageAnalytics:
    """
    Get usage analytics and engagement metrics.
    
    Requires admin role. Real-time data.
    """
    try:
        logger.info(f"Admin {admin_user.email} fetching usage analytics")
        return await admin_service.get_usage_analytics(admin_user)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching usage analytics: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve usage analytics"
        )
