"""
Training Program API endpoints.

Provides comprehensive program management with:
- Template browsing (admin-created programs)
- Custom program creation (Pro subscription required)
- Program cloning from templates
- Session management with exercises
- Volume statistics and analysis
- Multi-tenant authorization
- Rate limiting on mutation operations
"""

import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.core.dependencies import (
    DatabaseDep,
    CurrentUserDep,
    VerifiedUserDep,
    rate_limit,
)
from app.domain.entities.user import User
from app.repositories.exercise_repository import ExerciseRepository
from app.infrastructure.repositories.organization_repository import OrganizationRepository
from app.repositories.program_repository import ProgramRepository
from app.schemas.training_program import (
    CloneProgramRequest,
    ProgramCreate,
    ProgramFilter,
    ProgramListResponse,
    ProgramResponse,
    ProgramStatsResponse,
    ProgramUpdate,
    SessionCreate,
    SessionResponse,
    SessionUpdate,
)
from app.services.program_service import ProgramService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/programs", tags=["Training Programs"])


# ==================== Dependency Injection ====================


def get_program_repository(db: DatabaseDep) -> ProgramRepository:
    """Get program repository dependency."""
    return ProgramRepository(db)


def get_exercise_repository(db: DatabaseDep) -> ExerciseRepository:
    """Get exercise repository dependency."""
    return ExerciseRepository(db)


def get_organization_repository(db: DatabaseDep) -> OrganizationRepository:
    """Get organization repository dependency."""
    return OrganizationRepository(db)


def get_program_service(
    program_repo: Annotated[ProgramRepository, Depends(get_program_repository)],
    exercise_repo: Annotated[ExerciseRepository, Depends(get_exercise_repository)],
    org_repo: Annotated[OrganizationRepository, Depends(get_organization_repository)],
) -> ProgramService:
    """Get program service dependency with all repositories."""
    return ProgramService(program_repo, exercise_repo, org_repo)


ProgramServiceDep = Annotated[ProgramService, Depends(get_program_service)]


# ==================== Program Endpoints ====================


@router.get(
    "",
    response_model=ProgramListResponse,
    summary="List training programs",
    description="""
    List training programs with filtering and pagination.
    
    **What you can see:**
    - Admin-created templates (visible to all users)
    - Your organization's custom programs
    
    **Filters:**
    - `search`: Search in program name and description (full-text)
    - `split_type`: Filter by split type (UPPER_LOWER, PUSH_PULL_LEGS, etc.)
    - `structure_type`: Filter by structure (WEEKLY, CYCLIC)
    - `is_template`: Filter templates vs user programs
    
    **Pagination:**
    - Uses skip/limit pattern (offset-based)
    - Default: 20 items per page
    - Maximum: 100 items per page
    
    **Response includes:**
    - Basic program info (name, description, split type)
    - Session count and duration
    - Creation/update timestamps
    - Template flag
    """,
    responses={
        200: {
            "description": "List of programs with pagination metadata",
            "content": {
                "application/json": {
                    "example": {
                        "items": [
                            {
                                "id": "123e4567-e89b-12d3-a456-426614174000",
                                "name": "Upper/Lower 4-Day Split",
                                "description": "Classic upper/lower split for intermediate lifters",
                                "split_type": "UPPER_LOWER",
                                "structure_type": "WEEKLY",
                                "is_template": True,
                                "duration_weeks": 8,
                                "session_count": 4,
                                "created_at": "2025-11-23T10:00:00Z",
                                "updated_at": "2025-11-23T10:00:00Z"
                            }
                        ],
                        "total": 25,
                        "page": 1,
                        "page_size": 20,
                        "has_more": True
                    }
                }
            }
        },
        401: {"description": "Not authenticated"}
    }
)
async def list_programs(
    service: ProgramServiceDep,
    current_user: CurrentUserDep,
    search: str | None = Query(None, description="Search term for name/description", max_length=100),
    split_type: str | None = Query(None, description="Filter by split type"),
    structure_type: str | None = Query(None, description="Filter by structure type (WEEKLY, CYCLIC)"),
    is_template: bool | None = Query(None, description="Filter templates (true) vs user programs (false)"),
    skip: int = Query(0, ge=0, description="Number of records to skip for pagination"),
    limit: int = Query(20, ge=1, le=100, description="Maximum records to return"),
) -> ProgramListResponse:
    """
    List training programs with filtering and pagination.
    
    Returns templates plus user's organization programs.
    Supports full-text search and multiple filters.
    """
    try:
        filters = ProgramFilter(
            search=search,
            split_type=split_type,
            structure_type=structure_type,
            is_template=is_template,
            skip=skip,
            limit=limit,
        )
        
        logger.info(
            f"User {current_user.id} listing programs with filters: "
            f"search={search}, split_type={split_type}, is_template={is_template}"
        )
        
        return await service.list_programs(filters, current_user)
    
    except ValueError as e:
        logger.warning(f"Invalid filter values: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid filter values: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error listing programs: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve programs"
        )


@router.get(
    "/{program_id}",
    response_model=ProgramResponse,
    summary="Get training program by ID",
    description="""
    Get a specific training program with complete details.
    
    **Returns:**
    - Complete program information (name, description, split, structure)
    - All workout sessions with exercises and sets
    - Calculated statistics (volume per muscle, frequency, etc.)
    - Creation and update timestamps
    
    **Access control:**
    - Any user can view template programs
    - Users can view their organization's custom programs
    - Programs from other organizations are not accessible
    
    **Use cases:**
    - Preview a template before cloning
    - View your custom program details
    - Check volume distribution across muscle groups
    """,
    responses={
        200: {
            "description": "Program details with sessions and calculated stats",
            "content": {
                "application/json": {
                    "example": {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "name": "Upper/Lower 4-Day Split",
                        "description": "Classic upper/lower split for intermediate lifters",
                        "split_type": "UPPER_LOWER",
                        "structure_type": "WEEKLY",
                        "structure_config": {
                            "days_per_week": 4,
                            "selected_days": ["MON", "TUE", "THU", "FRI"]
                        },
                        "is_template": True,
                        "duration_weeks": 8,
                        "sessions": [
                            {
                                "id": "223e4567-e89b-12d3-a456-426614174001",
                                "name": "Upper Body A",
                                "day_number": 1,
                                "order_in_program": 1,
                                "exercises": [
                                    {
                                        "exercise_id": "323e4567-e89b-12d3-a456-426614174002",
                                        "sets": 3,
                                        "order_in_session": 1,
                                        "notes": "Focus on form"
                                    }
                                ],
                                "total_sets": 15,
                                "exercise_count": 5
                            }
                        ],
                        "stats": {
                            "total_sessions": 4,
                            "total_sets": 60,
                            "avg_sets_per_session": 15.0,
                            "weekly_volume": [
                                {
                                    "muscle": "CHEST",
                                    "muscle_name": "Chest",
                                    "sets_per_week": 16.0,
                                    "status": "optimal"
                                }
                            ],
                            "training_frequency": 4.0
                        },
                        "created_at": "2025-11-23T10:00:00Z",
                        "updated_at": "2025-11-23T10:00:00Z"
                    }
                }
            }
        },
        401: {"description": "Not authenticated"},
        404: {"description": "Program not found or not accessible"}
    }
)
async def get_program(
    program_id: UUID,
    service: ProgramServiceDep,
    current_user: CurrentUserDep,
) -> ProgramResponse:
    """
    Get program by ID with all sessions and calculated statistics.
    
    Accessible to:
    - Any user (for templates)
    - Organization members (for org programs)
    """
    try:
        logger.info(f"User {current_user.id} fetching program {program_id}")
        return await service.get_program(program_id, current_user)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching program {program_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve program"
        )


@router.post(
    "",
    response_model=ProgramResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a custom training program",
    description="""
    Create a custom training program with sessions and exercises.
    
    **Requirements:**
    - **Pro subscription** or admin role
    - Verified email address
    - At least one workout session
    - At least one exercise per session
    - Valid structure configuration matching structure type
    
    **The program:**
    - Belongs to your organization
    - Private to your organization members
    - Fully customizable after creation
    - Can be modified or deleted anytime
    
    **Volume recommendations:**
    - **Optimal:** 10-20 sets/week per muscle (ideal for hypertrophy)
    - **Low:** < 10 sets/week (may be insufficient for growth)
    - **High:** 20-25 sets/week (advanced, near recovery limit)
    - **Excessive:** > 25 sets/week (may exceed recovery capacity)
    
    **Structure types:**
    - **WEEKLY:** Fixed days (Mon, Wed, Fri). Requires `days_per_week` and `selected_days`
    - **CYCLIC:** Repeating pattern (3 on, 1 off). Requires `days_on` and `days_off`
    
    **Rate limiting:** 10 requests per minute per user.
    """,
    responses={
        201: {
            "description": "Program created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "name": "My Custom Program",
                        "description": "Customized for my goals and schedule",
                        "split_type": "UPPER_LOWER",
                        "structure_type": "WEEKLY",
                        "is_template": False,
                        "organization_id": "223e4567-e89b-12d3-a456-426614174001",
                        "sessions": [],
                        "stats": {
                            "total_sessions": 4,
                            "total_sets": 60,
                            "weekly_volume": []
                        }
                    }
                }
            }
        },
        400: {"description": "Invalid program data or validation failed"},
        401: {"description": "Not authenticated"},
        403: {"description": "Pro subscription required or email not verified"},
        429: {"description": "Rate limit exceeded"}
    }
)
@rate_limit(max_requests=10, window_seconds=60, identifier="user")
async def create_program(
    request: Request,
    program_data: ProgramCreate,
    service: ProgramServiceDep,
    current_user: VerifiedUserDep,
) -> ProgramResponse:
    """
    Create a new custom training program.
    
    Requires:
    - Pro subscription or admin role
    - Verified email
    
    Rate limited to 10 requests per minute per user.
    """
    try:
        logger.info(
            f"User {current_user.id} creating program: {program_data.name}, "
            f"split={program_data.split_type}, sessions={len(program_data.sessions)}"
        )
        
        return await service.create_program(program_data, current_user)
    
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Program validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating program: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create program"
        )


@router.post(
    "/{template_id}/clone",
    response_model=ProgramResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Clone a template program",
    description="""
    Clone an admin-created template program to your organization.
    
    **What gets cloned:**
    - Program structure (split type, training structure)
    - All workout sessions with day numbers and ordering
    - All exercises with sets and ordering
    - Exercise notes and configuration
    
    **What's customized:**
    - Program name (default: "My {template_name}" or custom via request)
    - Organization ownership (becomes your org's program)
    - Template flag (set to false - it's your program now)
    - Timestamps (new creation date)
    
    **After cloning:**
    - The program belongs to your organization
    - You can modify sessions, exercises, and settings
    - Changes don't affect the original template
    - You can delete it without affecting the template
    
    **Requirements:**
    - Pro subscription or admin role
    - Verified email address
    
    **Rate limiting:** 20 clones per hour per user.
    """,
    responses={
        201: {
            "description": "Program cloned successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "223e4567-e89b-12d3-a456-426614174001",
                        "name": "My Upper/Lower 4-Day Split",
                        "description": "Classic upper/lower split for intermediate lifters",
                        "split_type": "UPPER_LOWER",
                        "is_template": False,
                        "organization_id": "323e4567-e89b-12d3-a456-426614174002",
                        "sessions": [],
                        "stats": {}
                    }
                }
            }
        },
        400: {"description": "Invalid clone request"},
        401: {"description": "Not authenticated"},
        403: {"description": "Pro subscription required or email not verified"},
        404: {"description": "Template not found"},
        429: {"description": "Rate limit exceeded"}
    }
)
@rate_limit(max_requests=20, window_seconds=3600, identifier="user")
async def clone_template(
    request: Request,
    template_id: UUID,
    clone_request: CloneProgramRequest,
    service: ProgramServiceDep,
    current_user: VerifiedUserDep,
) -> ProgramResponse:
    """
    Clone a template program for the user's organization.
    
    Requires:
    - Pro subscription or admin role
    - Verified email
    
    Rate limited to 20 clones per hour per user.
    """
    try:
        logger.info(
            f"User {current_user.id} cloning template {template_id} "
            f"with name: {clone_request.new_name or 'default'}"
        )
        
        return await service.clone_from_template(
            template_id,
            current_user,
            clone_request.new_name,
        )
    
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Clone validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error cloning template {template_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clone template"
        )


@router.put(
    "/{program_id}",
    response_model=ProgramResponse,
    summary="Update training program",
    description="""
    Update program details (name, description, duration).
    
    **What you can update:**
    - Program name
    - Description text
    - Duration in weeks
    
    **What you cannot update:**
    - Split type (create new program instead)
    - Structure type or configuration (create new program)
    - Template programs (they're read-only - clone first)
    - Other organization's programs
    
    **Requirements:**
    - Must own the program (same organization)
    - Cannot modify template programs
    - Verified email address
    
    **Rate limiting:** 30 updates per minute per user.
    """,
    responses={
        200: {
            "description": "Program updated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "name": "Updated Program Name",
                        "description": "Updated description",
                        "duration_weeks": 12
                    }
                }
            }
        },
        400: {"description": "Invalid update data"},
        401: {"description": "Not authenticated"},
        403: {"description": "Not authorized to modify this program"},
        404: {"description": "Program not found"},
        429: {"description": "Rate limit exceeded"}
    }
)
@rate_limit(max_requests=30, window_seconds=60, identifier="user")
async def update_program(
    request: Request,
    program_id: UUID,
    program_data: ProgramUpdate,
    service: ProgramServiceDep,
    current_user: VerifiedUserDep,
) -> ProgramResponse:
    """
    Update program details (name, description, duration).
    
    Requires program ownership and verified email.
    Rate limited to 30 updates per minute per user.
    """
    try:
        logger.info(
            f"User {current_user.id} updating program {program_id}: "
            f"name={program_data.name}, description={program_data.description}"
        )
        
        return await service.update_program(program_id, program_data, current_user)
    
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Update validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating program {program_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update program"
        )


@router.delete(
    "/{program_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete training program",
    description="""
    Permanently delete a training program and all its sessions.
    
    **This action:**
    - Permanently deletes the program
    - Deletes all associated workout sessions
    - Deletes all exercise configurations
    - Cannot be undone
    
    **Cascade behavior:**
    - All sessions are automatically deleted
    - All exercise entries are removed
    - Foreign key constraints ensure data integrity
    
    **Requirements:**
    - Must own the program (same organization)
    - Cannot delete template programs
    - Verified email address
    
    **Rate limiting:** 10 deletions per hour per user.
    """,
    responses={
        204: {"description": "Program deleted successfully (no content)"},
        401: {"description": "Not authenticated"},
        403: {"description": "Not authorized to delete this program or email not verified"},
        404: {"description": "Program not found"},
        429: {"description": "Rate limit exceeded"}
    }
)
@rate_limit(max_requests=10, window_seconds=3600, identifier="user")
async def delete_program(
    request: Request,
    program_id: UUID,
    service: ProgramServiceDep,
    current_user: VerifiedUserDep,
) -> None:
    """
    Permanently delete a training program.
    
    Requires program ownership and verified email.
    Rate limited to 10 deletions per hour per user.
    """
    try:
        logger.info(f"User {current_user.id} deleting program {program_id}")
        await service.delete_program(program_id, current_user)
        logger.info(f"Program {program_id} deleted successfully")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting program {program_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete program"
        )


@router.get(
    "/{program_id}/stats",
    response_model=ProgramStatsResponse,
    summary="Get program statistics and volume analysis",
    description="""
    Get comprehensive statistics and volume analysis for a training program.
    
    **Returns:**
    - **Total sessions:** Number of workout sessions in program
    - **Total sets:** Sum of all sets across all sessions
    - **Average sets per session:** Mean sets per workout
    - **Weekly volume per muscle:** Sets per week for each muscle group
    - **Volume status:** Classification of volume (low/optimal/high/excessive)
    - **Training frequency:** Workouts per week based on structure
    
    **Volume status guide:**
    - **Low** (< 10 sets/week): May be insufficient for muscle growth (hypertrophy)
    - **Optimal** (10-20 sets/week): Ideal range for hypertrophy in most individuals
    - **High** (20-25 sets/week): Advanced volume, approaching recovery limits
    - **Excessive** (> 25 sets/week): Likely exceeds recovery capacity, risk of overtraining
    
    **Use cases:**
    - Verify volume distribution before starting program
    - Identify under-trained or over-trained muscle groups
    - Compare volume across different programs
    - Plan program modifications based on volume analysis
    
    **Muscle groups tracked:**
    - Upper body: Chest, Lats, Traps/Rhomboids, Front/Side/Rear Delts, Triceps, Elbow Flexors, Forearms
    - Core: Spinal Erectors, Abs, Obliques
    - Lower body: Glutes, Quads, Hamstrings, Adductors, Calves
    """,
    responses={
        200: {
            "description": "Program statistics with volume analysis",
            "content": {
                "application/json": {
                    "example": {
                        "total_sessions": 4,
                        "total_sets": 60,
                        "avg_sets_per_session": 15.0,
                        "weekly_volume": [
                            {
                                "muscle": "CHEST",
                                "muscle_name": "Chest",
                                "sets_per_week": 16.0,
                                "status": "optimal"
                            },
                            {
                                "muscle": "LATS",
                                "muscle_name": "Lats",
                                "sets_per_week": 14.0,
                                "status": "optimal"
                            },
                            {
                                "muscle": "QUADS",
                                "muscle_name": "Quadriceps",
                                "sets_per_week": 8.0,
                                "status": "low"
                            }
                        ],
                        "training_frequency": 4.0
                    }
                }
            }
        },
        401: {"description": "Not authenticated"},
        404: {"description": "Program not found or not accessible"}
    }
)
async def get_program_stats(
    program_id: UUID,
    service: ProgramServiceDep,
    current_user: CurrentUserDep,
) -> ProgramStatsResponse:
    """
    Get comprehensive program statistics including volume per muscle group.
    
    Accessible to any user who can view the program (templates + org programs).
    """
    try:
        logger.info(f"User {current_user.id} fetching stats for program {program_id}")
        return await service.get_program_stats(program_id, current_user)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching stats for program {program_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve program statistics"
        )


# ==================== Session Endpoints ====================


@router.post(
    "/{program_id}/sessions",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add workout session to program",
    description="""
    Add a new workout session to a training program.
    
    **A session contains:**
    - **Name:** Descriptive name (e.g., "Upper Body A", "Leg Day")
    - **Day number:** Position in program sequence (1-7 for weekly, 1-N for cyclic)
    - **Order in program:** Display/execution order (allows custom sequencing)
    - **Exercises:** List of exercises with sets and ordering
    
    **Requirements:**
    - Must own the program (same organization)
    - At least one exercise in the session
    - Valid exercise IDs (must exist in database and be accessible)
    - Unique day number within program (no duplicates)
    - Sets per exercise: 1-10 (validation enforced)
    
    **After creation:**
    - Total sets are automatically calculated
    - Program statistics are updated
    - Volume per muscle is recalculated
    
    **Exercise notes:**
    - Optional notes per exercise (e.g., "Focus on form", "Drop set")
    - Useful for execution guidance and customization
    
    **Rate limiting:** 20 sessions per minute per user.
    """,
    responses={
        201: {
            "description": "Session created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "423e4567-e89b-12d3-a456-426614174003",
                        "program_id": "123e4567-e89b-12d3-a456-426614174000",
                        "name": "Upper Body A",
                        "day_number": 1,
                        "order_in_program": 1,
                        "exercises": [
                            {
                                "exercise_id": "523e4567-e89b-12d3-a456-426614174004",
                                "sets": 3,
                                "order_in_session": 1,
                                "notes": "Focus on controlled negatives"
                            }
                        ],
                        "total_sets": 15,
                        "exercise_count": 5
                    }
                }
            }
        },
        400: {"description": "Invalid session data or validation failed"},
        401: {"description": "Not authenticated"},
        403: {"description": "Not authorized to modify this program or email not verified"},
        404: {"description": "Program not found or exercise IDs invalid"},
        429: {"description": "Rate limit exceeded"}
    }
)
@rate_limit(max_requests=20, window_seconds=60, identifier="user")
async def add_session(
    request: Request,
    program_id: UUID,
    session_data: SessionCreate,
    service: ProgramServiceDep,
    current_user: VerifiedUserDep,
) -> SessionResponse:
    """
    Add a new workout session to a program.
    
    Requires program ownership and verified email.
    Rate limited to 20 sessions per minute per user.
    """
    try:
        logger.info(
            f"User {current_user.id} adding session to program {program_id}: "
            f"name={session_data.name}, exercises={len(session_data.exercises)}"
        )
        
        return await service.add_session(program_id, session_data, current_user)
    
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Session validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error adding session to program {program_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add session"
        )


@router.put(
    "/{program_id}/sessions/{session_id}",
    response_model=SessionResponse,
    summary="Update workout session",
    description="""
    Update a workout session's details and exercises.
    
    **What you can update:**
    - Session name
    - Day number (must be unique within program)
    - Order in program (for custom sequencing)
    - Exercise list (add, remove, reorder)
    - Sets per exercise
    - Exercise notes
    
    **When updating exercises:**
    - Total sets are recalculated automatically
    - Program volume statistics are updated
    - All exercise IDs must exist and be accessible
    - Order is preserved or can be changed
    
    **Requirements:**
    - Must own the program (via session's program)
    - Session must belong to the specified program
    - Verified email address
    - Cannot modify sessions in template programs
    
    **Note:** `program_id` in path is for route consistency but ownership
    is verified through the session -> program relationship.
    
    **Rate limiting:** 30 updates per minute per user.
    """,
    responses={
        200: {
            "description": "Session updated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "423e4567-e89b-12d3-a456-426614174003",
                        "name": "Updated Session Name",
                        "day_number": 2,
                        "exercises": [],
                        "total_sets": 18
                    }
                }
            }
        },
        400: {"description": "Invalid update data or validation failed"},
        401: {"description": "Not authenticated"},
        403: {"description": "Not authorized to modify this session or email not verified"},
        404: {"description": "Session not found or doesn't belong to program"},
        429: {"description": "Rate limit exceeded"}
    }
)
@rate_limit(max_requests=30, window_seconds=60, identifier="user")
async def update_session(
    request: Request,
    program_id: UUID,
    session_id: UUID,
    session_data: SessionUpdate,
    service: ProgramServiceDep,
    current_user: VerifiedUserDep,
) -> SessionResponse:
    """
    Update a workout session's details and exercises.
    
    Requires program ownership (via session) and verified email.
    Rate limited to 30 updates per minute per user.
    
    Note: program_id is used for route consistency but ownership
    is verified through session -> program relationship.
    """
    try:
        logger.info(
            f"User {current_user.id} updating session {session_id} in program {program_id}: "
            f"name={session_data.name}"
        )
        
        return await service.update_session(session_id, session_data, current_user)
    
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Session update validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating session {session_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update session"
        )


@router.delete(
    "/{program_id}/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete workout session",
    description="""
    Permanently delete a workout session from a program.
    
    **This action:**
    - Permanently removes the session
    - Deletes all exercise configurations in the session
    - Updates program statistics (volume, set count)
    - Cannot be undone
    
    **Requirements:**
    - Must own the program (via session's program)
    - Program must have at least 2 sessions (cannot delete last session)
    - Verified email address
    - Cannot delete sessions from template programs
    
    **Validation:**
    - Service prevents deletion of the last session in a program
    - At least one session must remain for program validity
    
    **Note:** `program_id` in path is for route consistency but ownership
    is verified through the session -> program relationship.
    
    **Rate limiting:** 10 deletions per hour per user.
    """,
    responses={
        204: {"description": "Session deleted successfully (no content)"},
        400: {"description": "Cannot delete last session in program"},
        401: {"description": "Not authenticated"},
        403: {"description": "Not authorized to delete this session or email not verified"},
        404: {"description": "Session not found"},
        429: {"description": "Rate limit exceeded"}
    }
)
@rate_limit(max_requests=10, window_seconds=3600, identifier="user")
async def delete_session(
    request: Request,
    program_id: UUID,
    session_id: UUID,
    service: ProgramServiceDep,
    current_user: VerifiedUserDep,
) -> None:
    """
    Permanently delete a workout session.
    
    Requires program ownership (via session) and verified email.
    Rate limited to 10 deletions per hour per user.
    
    Note: program_id is used for route consistency.
    """
    try:
        logger.info(f"User {current_user.id} deleting session {session_id} from program {program_id}")
        await service.delete_session(session_id, current_user)
        logger.info(f"Session {session_id} deleted successfully")
    
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Session deletion validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error deleting session {session_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete session"
        )
