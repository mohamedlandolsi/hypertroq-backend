"""
Exercise management API endpoints.

Provides CRUD operations for exercises with:
- Multi-tenant authorization (global vs organization exercises)
- Subscription tier enforcement (Pro required for custom exercises)
- Full-text search and filtering
- Image upload support
- Rate limiting on create/update/delete operations
"""

import logging
from typing import Annotated, List
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Request,
    Response,
    status,
)

from app.core.dependencies import (
    DatabaseDep,
    CurrentUserDep,
    rate_limit,
)
from app.domain.entities.user import User
from app.domain.value_objects.equipment import Equipment
from app.domain.value_objects.muscle_groups import MuscleGroup
from app.infrastructure.cache.redis_client import RedisClient
from app.repositories.exercise_repository import ExerciseRepository
from app.schemas.exercise import (
    ExerciseCreate,
    ExerciseFilter,
    ExerciseListResponse,
    ExerciseResponse,
    ExerciseSummaryResponse,
    ExerciseUpdate,
)
from app.services.exercise_service import ExerciseService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/exercises", tags=["Exercises"])


# ==================== Dependency Injection ====================


def get_exercise_repository(db: DatabaseDep) -> ExerciseRepository:
    """Get exercise repository dependency."""
    return ExerciseRepository(db)


def get_exercise_service(
    repository: Annotated[ExerciseRepository, Depends(get_exercise_repository)],
) -> ExerciseService:
    """
    Get exercise service dependency.
    
    Note: Redis client is optional. Service will work without caching if unavailable.
    """
    # TODO: Inject Redis client when available
    # redis_client = RedisClient() if settings.REDIS_ENABLED else None
    return ExerciseService(repository=repository, redis_client=None)


# ==================== Public Endpoints ====================


@router.get(
    "/muscles/groups",
    response_model=List[dict],
    summary="Get all muscle groups",
    description="Returns a list of all available muscle groups with their display names and categories.",
    status_code=status.HTTP_200_OK,
)
async def get_muscle_groups() -> List[dict]:
    """
    Get all available muscle groups.
    
    Returns comprehensive list of 18 muscle groups used in exercise targeting.
    No authentication required - public reference data.
    
    Returns:
        List of muscle groups with:
        - value: Enum value (e.g., "CHEST")
        - display_name: Human-readable name (e.g., "Chest")
        - category: Muscle category (e.g., "Upper Body - Push")
        
    Example response:
        ```json
        [
            {
                "value": "CHEST",
                "display_name": "Chest",
                "category": "Upper Body - Push"
            },
            {
                "value": "LATS",
                "display_name": "Lats",
                "category": "Upper Body - Pull"
            },
            ...
        ]
        ```
    """
    return [
        {
            "value": muscle.value,
            "display_name": muscle.display_name,
            "category": muscle.category,
        }
        for muscle in MuscleGroup
    ]


@router.get(
    "/equipment/types",
    response_model=List[dict],
    summary="Get all equipment types",
    description="Returns a list of all available equipment types with their properties.",
    status_code=status.HTTP_200_OK,
)
async def get_equipment_types() -> List[dict]:
    """
    Get all available equipment types.
    
    Returns comprehensive list of equipment types used in exercises.
    No authentication required - public reference data.
    
    Returns:
        List of equipment types with:
        - value: Enum value (e.g., "BARBELL")
        - display_name: Human-readable name (e.g., "Barbell")
        - is_free_weight: Whether it's a free weight
        - is_fixed_path: Whether it uses a fixed movement path
        
    Example response:
        ```json
        [
            {
                "value": "BARBELL",
                "display_name": "Barbell",
                "is_free_weight": true,
                "is_fixed_path": false
            },
            {
                "value": "MACHINE",
                "display_name": "Machine",
                "is_free_weight": false,
                "is_fixed_path": true
            },
            ...
        ]
        ```
    """
    return [
        {
            "value": equipment.value,
            "display_name": equipment.display_name,
            "is_free_weight": equipment.is_free_weight,
            "is_fixed_path": equipment.is_fixed_path,
        }
        for equipment in Equipment
    ]


# ==================== Exercise CRUD Endpoints ====================


@router.get(
    "",
    response_model=ExerciseListResponse,
    summary="List exercises",
    description="Get paginated list of exercises with optional filtering by equipment, muscle group, and search query.",
    status_code=status.HTTP_200_OK,
)
async def list_exercises(
    request: Request,
    current_user: CurrentUserDep,
    exercise_service: Annotated[ExerciseService, Depends(get_exercise_service)],
    search: str | None = Query(
        None,
        description="Search query for exercise name or description (full-text search)",
        min_length=2,
        max_length=100,
    ),
    equipment: Equipment | None = Query(
        None,
        description="Filter by equipment type (e.g., BARBELL, DUMBBELL)",
    ),
    muscle_group: MuscleGroup | None = Query(
        None,
        description="Filter by primary muscle group (e.g., CHEST, LATS)",
    ),
    is_global: bool | None = Query(
        None,
        description="Filter by scope: true for global exercises, false for organization-specific, null for both",
    ),
    page: int = Query(
        1,
        ge=1,
        description="Page number (1-indexed)",
    ),
    limit: int = Query(
        20,
        ge=1,
        le=100,
        description="Number of items per page (max 100)",
    ),
) -> ExerciseListResponse:
    """
    List exercises with filtering and pagination.
    
    Returns global exercises and exercises from the user's organization.
    Results are ordered by global status first, then by name.
    
    **Filtering:**
    - `search`: Full-text search on exercise name and description
    - `equipment`: Filter by specific equipment type
    - `muscle_group`: Filter exercises targeting specific muscle group
    - `is_global`: Filter by scope (global vs organization-specific)
    
    **Pagination:**
    - `page`: Current page number (1-indexed)
    - `limit`: Items per page (1-100, default 20)
    
    **Response includes:**
    - Paginated exercise list with full details
    - Total count of matching exercises
    - Pagination metadata (page, total_pages, has_next, has_previous)
    
    **Authorization:**
    - Authenticated users see global + their organization's exercises
    - Results respect multi-tenant boundaries
    """
    # Calculate skip for pagination
    skip = (page - 1) * limit
    
    # Create filters
    filters = ExerciseFilter(
        search=search,
        equipment=equipment,
        muscle_group=muscle_group,
        is_global=is_global,
        skip=skip,
        limit=limit,
    )
    
    # Get exercises
    result = await exercise_service.list_exercises(filters=filters, user=current_user)
    
    logger.info(
        f"User {current_user.id} listed exercises: "
        f"page={page}, limit={limit}, total={result.total}, filters={filters}"
    )
    
    return result


@router.get(
    "/search",
    response_model=List[ExerciseSummaryResponse],
    summary="Search exercises",
    description="Full-text search for exercises with lightweight response format.",
    status_code=status.HTTP_200_OK,
)
async def search_exercises(
    request: Request,
    current_user: CurrentUserDep,
    exercise_service: Annotated[ExerciseService, Depends(get_exercise_service)],
    q: str = Query(
        ...,
        description="Search query string",
        min_length=2,
        max_length=100,
    ),
    limit: int = Query(
        20,
        ge=1,
        le=50,
        description="Maximum number of results (max 50)",
    ),
) -> List[ExerciseSummaryResponse]:
    """
    Full-text search for exercises.
    
    Uses PostgreSQL full-text search with relevance ranking.
    Returns lightweight response for autocomplete/search results.
    
    **Search behavior:**
    - Searches exercise name and description
    - Results ranked by relevance (ts_rank)
    - Includes global + organization exercises
    
    **Response format:**
    - Lightweight summary (id, name, equipment, primary_muscles)
    - Optimized for search dropdowns and autocomplete
    
    **Use cases:**
    - Exercise search/autocomplete in UI
    - Quick lookup by name
    - Finding exercises by description keywords
    """
    results = await exercise_service.search_exercises(
        query=q,
        user=current_user,
        limit=limit,
    )
    
    logger.debug(
        f"User {current_user.id} searched exercises: "
        f"query='{q}', results={len(results)}"
    )
    
    return results


@router.get(
    "/{exercise_id}",
    response_model=ExerciseResponse,
    summary="Get exercise by ID",
    description="Get detailed information about a specific exercise.",
    status_code=status.HTTP_200_OK,
    responses={
        404: {
            "description": "Exercise not found or not accessible",
            "content": {
                "application/json": {
                    "example": {"detail": "Exercise not found or you don't have access to it"}
                }
            },
        },
    },
)
async def get_exercise(
    exercise_id: UUID,
    current_user: CurrentUserDep,
    exercise_service: Annotated[ExerciseService, Depends(get_exercise_service)],
) -> ExerciseResponse:
    """
    Get exercise by ID.
    
    Returns full exercise details including:
    - Basic info (name, description, equipment)
    - Muscle contributions with percentages
    - Primary and secondary muscle lists
    - Computed fields (is_compound, total_contribution)
    - Metadata (created_at, updated_at, creator, scope)
    
    **Authorization:**
    - Users can access global exercises
    - Users can access their organization's exercises
    - 404 returned if exercise not found or not accessible
    
    **Caching:**
    - Global exercises cached for 1 hour (if Redis available)
    - Organization exercises fetched from database
    """
    return await exercise_service.get_exercise_by_id(
        exercise_id=exercise_id,
        user=current_user,
    )


@router.post(
    "",
    response_model=ExerciseResponse,
    summary="Create exercise",
    description="Create a new custom exercise. Requires Pro subscription or admin role.",
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {
            "description": "Exercise created successfully",
        },
        403: {
            "description": "Insufficient permissions (Pro subscription required)",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Pro subscription required to create custom exercises. "
                                  "Upgrade your plan to access this feature."
                    }
                }
            },
        },
        409: {
            "description": "Exercise name already exists",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Exercise with name 'Barbell Bench Press' already exists in your organization"
                    }
                }
            },
        },
        422: {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Total muscle contribution must be >= 1.0"
                    }
                }
            },
        },
    },
)
@rate_limit(max_requests=10, window_seconds=60, identifier="user")
async def create_exercise(
    request: Request,
    exercise_data: ExerciseCreate,
    current_user: CurrentUserDep,  # Changed from VerifiedUserDep for development
    exercise_service: Annotated[ExerciseService, Depends(get_exercise_service)],
) -> ExerciseResponse:
    """
    Create a new exercise.
    
    **Subscription Requirements:**
    - Pro tier required for custom exercises
    - Admin users can create global exercises (no subscription check)
    - Free tier users receive upgrade prompt
    
    **Validation:**
    - Name: 3-100 characters, unique within scope
    - Muscle contributions: Total >= 1.0, at least one PRIMARY (1.0)
    - Equipment: Valid equipment type
    - Image: Optional, validated file type and size (if provided)
    
    **Scope:**
    - Admin users create global exercises (accessible to all)
    - Regular users create organization exercises
    - Global exercises: no organization_id
    - Org exercises: linked to user's organization
    
    **Image Upload (TODO):**
    - Supported formats: JPEG, PNG, WebP
    - Max size: 5MB
    - Stored in Cloud Storage
    - Returns public URL in response
    
    **Rate Limiting:**
    - 10 requests per minute per user
    - Prevents abuse of exercise creation
    
    **Business Rules:**
    - Names must be unique within scope (global or organization)
    - At least one muscle must have PRIMARY (1.0) contribution
    - Sum of muscle contributions must be >= 1.0
    """
    result = await exercise_service.create_exercise(
        exercise_data=exercise_data,
        user=current_user,
    )
    
    logger.info(
        f"Exercise '{result.name}' created by user {current_user.id} "
        f"(global={result.is_global}, id={result.id})"
    )
    
    return result


@router.put(
    "/{exercise_id}",
    response_model=ExerciseResponse,
    summary="Update exercise",
    description="Update an existing exercise. Requires ownership or admin role.",
    status_code=status.HTTP_200_OK,
    responses={
        403: {
            "description": "Insufficient permissions",
            "content": {
                "application/json": {
                    "example": {"detail": "You don't have permission to update this exercise"}
                }
            },
        },
        404: {
            "description": "Exercise not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Exercise not found or you don't have access to it"}
                }
            },
        },
        409: {
            "description": "Name conflict",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Exercise with name 'New Name' already exists globally"
                    }
                }
            },
        },
    },
)
@rate_limit(max_requests=20, window_seconds=60, identifier="user")
async def update_exercise(
    request: Request,
    exercise_id: UUID,
    exercise_data: ExerciseUpdate,
    current_user: CurrentUserDep,
    exercise_service: Annotated[ExerciseService, Depends(get_exercise_service)],
) -> ExerciseResponse:
    """
    Update an existing exercise.
    
    **Authorization:**
    - Creator can update their own exercises
    - Admins can update any exercise (including global)
    - Non-admins cannot update global exercises
    - 403 if insufficient permissions
    
    **Partial Updates:**
    - All fields optional
    - Only provided fields are updated
    - Null values ignored (use empty string to clear)
    
    **Name Changes:**
    - If name changed, checks for duplicates within scope
    - Must be unique in organization (or globally for global exercises)
    - Excludes current exercise from duplicate check
    
    **Muscle Contributions:**
    - If updated, must still meet validation rules
    - Total >= 1.0, at least one PRIMARY muscle
    
    **Cache Invalidation:**
    - Updates invalidate cached exercise (if Redis enabled)
    - Global exercises also invalidate list cache
    
    **Rate Limiting:**
    - 20 requests per minute per user
    """
    result = await exercise_service.update_exercise(
        exercise_id=exercise_id,
        exercise_data=exercise_data,
        user=current_user,
    )
    
    logger.info(
        f"Exercise {exercise_id} updated by user {current_user.id}"
    )
    
    return result


@router.delete(
    "/{exercise_id}",
    summary="Delete exercise",
    description="Delete an exercise. Requires ownership or admin role.",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        204: {
            "description": "Exercise deleted successfully",
        },
        403: {
            "description": "Insufficient permissions",
            "content": {
                "application/json": {
                    "example": {"detail": "You don't have permission to delete this exercise"}
                }
            },
        },
        404: {
            "description": "Exercise not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Exercise not found or you don't have access to it"}
                }
            },
        },
        409: {
            "description": "Exercise in use",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Cannot delete exercise that is used in programs. "
                                  "Remove it from all programs first."
                    }
                }
            },
        },
    },
)
@rate_limit(max_requests=10, window_seconds=60, identifier="user")
async def delete_exercise(
    request: Request,
    exercise_id: UUID,
    current_user: CurrentUserDep,
    exercise_service: Annotated[ExerciseService, Depends(get_exercise_service)],
) -> Response:
    """
    Delete an exercise.
    
    **Authorization:**
    - Creator can delete their own exercises
    - Admins can delete any exercise (including global)
    - Non-admins cannot delete global exercises
    - 403 if insufficient permissions
    
    **Safety Checks (TODO):**
    - Checks if exercise is used in any programs
    - Prevents deletion if exercise is in use
    - Returns 409 with helpful message
    - Suggests removing from programs first
    
    **Soft Delete:**
    - Removes exercise from database
    - Future: May implement soft delete with deleted_at timestamp
    
    **Image Cleanup (TODO):**
    - Deletes associated image from Cloud Storage
    - Frees up storage space
    
    **Cache Invalidation:**
    - Removes exercise from cache (if Redis enabled)
    - Invalidates global exercise lists if global
    
    **Rate Limiting:**
    - 10 requests per minute per user
    - Prevents accidental bulk deletions
    
    **Response:**
    - 204 No Content on success
    - No response body
    """
    await exercise_service.delete_exercise(
        exercise_id=exercise_id,
        user=current_user,
    )
    
    logger.info(
        f"Exercise {exercise_id} deleted by user {current_user.id}"
    )
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ==================== Admin Endpoints ====================


@router.get(
    "/stats/overview",
    response_model=dict,
    summary="Get exercise statistics",
    description="Get overview statistics about exercises (global and organization-specific).",
    status_code=status.HTTP_200_OK,
)
async def get_exercise_stats(
    current_user: CurrentUserDep,
    repository: Annotated[ExerciseRepository, Depends(get_exercise_repository)],
) -> dict:
    """
    Get exercise statistics.
    
    Returns:
    - Total exercises accessible to user
    - Count of global exercises
    - Count of organization exercises
    - Breakdown by equipment type
    - Breakdown by primary muscle group
    
    **Use cases:**
    - Dashboard statistics
    - Analytics and insights
    - Exercise library overview
    
    Example response:
        ```json
        {
            "total": 150,
            "global": 120,
            "organization": 30,
            "by_equipment": {
                "BARBELL": 45,
                "DUMBBELL": 38,
                "CABLE": 25,
                ...
            },
            "by_muscle": {
                "CHEST": 20,
                "LATS": 18,
                "QUADS": 15,
                ...
            }
        }
        ```
    """
    # TODO: Implement statistics aggregation
    # This would require additional repository methods for efficient counting
    
    org_count = await repository.count_by_organization(current_user.organization_id)
    
    return {
        "total": org_count,
        "global": 0,  # TODO: Count global exercises
        "organization": org_count,
        "by_equipment": {},  # TODO: Aggregate by equipment
        "by_muscle": {},  # TODO: Aggregate by muscle
    }

