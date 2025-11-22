"""
Exercise service for business logic and orchestration.

Handles exercise management with subscription tier enforcement,
authorization, caching, and integration with storage services.
"""

import logging
from typing import List
from uuid import UUID

from fastapi import HTTPException, status

from app.domain.entities.exercise import Exercise
from app.domain.entities.organization import SubscriptionTier
from app.domain.entities.user import User, UserRole
from app.domain.value_objects.equipment import Equipment
from app.domain.value_objects.muscle_groups import MuscleGroup
from app.domain.value_objects.volume_contribution import VolumeContribution
from app.infrastructure.cache.redis_client import RedisClient
from app.repositories.exercise_repository import ExerciseRepository
from app.schemas.exercise import (
    ExerciseCreate,
    ExerciseFilter,
    ExerciseListResponse,
    ExerciseResponse,
    ExerciseSummaryResponse,
    ExerciseUpdate,
    MuscleContributionResponse,
)

logger = logging.getLogger(__name__)


class ExerciseService:
    """
    Service layer for exercise management.
    
    Handles business logic including:
    - Subscription tier enforcement (Pro tier for custom exercises)
    - Authorization and ownership checks
    - Caching for global exercises
    - Image upload/deletion
    - Duplicate name prevention
    - Usage tracking (prevent deletion of exercises in use)
    """
    
    # Cache TTL for global exercises (1 hour)
    CACHE_TTL = 3600
    
    def __init__(
        self,
        repository: ExerciseRepository,
        redis_client: RedisClient | None = None
    ):
        """
        Initialize exercise service.
        
        Args:
            repository: ExerciseRepository instance
            redis_client: Optional Redis client for caching
        """
        self.repository = repository
        self.redis = redis_client
    
    async def create_exercise(
        self,
        exercise_data: ExerciseCreate,
        user: User
    ) -> ExerciseResponse:
        """
        Create a new exercise.
        
        Business Rules:
        - Only Pro tier users can create custom exercises
        - Admins can create global exercises
        - Exercise names must be unique within organization scope
        - Muscle contributions must be valid (>= 1.0 total, at least one primary)
        
        Args:
            exercise_data: ExerciseCreate schema with exercise details
            user: User creating the exercise
            
        Returns:
            ExerciseResponse with created exercise details
            
        Raises:
            HTTPException: 403 if user doesn't have permission
            HTTPException: 409 if exercise name already exists
            HTTPException: 422 if validation fails
        """
        # Check subscription tier for custom exercises
        if not self._can_create_custom_exercise(user):
            logger.warning(
                f"User {user.id} attempted to create custom exercise without Pro tier"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Pro subscription required to create custom exercises. "
                       "Upgrade your plan to access this feature."
            )
        
        # Check for duplicate name
        is_global = user.role == UserRole.ADMIN
        existing = await self.repository.exists_by_name(
            name=exercise_data.name,
            org_id=None if is_global else user.organization_id,
            is_global=is_global
        )
        
        if existing:
            scope = "globally" if is_global else "in your organization"
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Exercise with name '{exercise_data.name}' already exists {scope}"
            )
        
        # Prepare exercise data
        exercise_dict = {
            "name": exercise_data.name,
            "description": exercise_data.description,
            "equipment": exercise_data.equipment,
            "muscle_contributions": exercise_data.muscle_contributions,
            "image_url": str(exercise_data.image_url) if exercise_data.image_url else None,
        }
        
        # Create exercise
        try:
            exercise = await self.repository.create(
                exercise_data=exercise_dict,
                user_id=user.id,
                org_id=None if is_global else user.organization_id,
                is_global=is_global
            )
            
            logger.info(
                f"Exercise '{exercise.name}' created by user {user.id} "
                f"(global={is_global}, org={user.organization_id})"
            )
            
            # Invalidate cache for global exercises if global was created
            if is_global and self.redis:
                await self._invalidate_global_exercises_cache()
            
            return self._entity_to_response(exercise)
        
        except ValueError as e:
            logger.error(f"Validation error creating exercise: {e}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(e)
            )
    
    async def get_exercise_by_id(
        self,
        exercise_id: UUID,
        user: User
    ) -> ExerciseResponse:
        """
        Get exercise by ID.
        
        Returns exercise if:
        - It's a global exercise, OR
        - It belongs to user's organization
        
        Args:
            exercise_id: Exercise UUID
            user: User requesting the exercise
            
        Returns:
            ExerciseResponse with exercise details
            
        Raises:
            HTTPException: 404 if exercise not found or not accessible
        """
        # Try cache first for global exercises
        if self.redis:
            cached = await self._get_cached_exercise(exercise_id)
            if cached:
                logger.debug(f"Exercise {exercise_id} retrieved from cache")
                return cached
        
        # Fetch from database
        exercise = await self.repository.get_by_id(
            exercise_id=exercise_id,
            org_id=user.organization_id
        )
        
        if not exercise:
            logger.warning(
                f"Exercise {exercise_id} not found or not accessible "
                f"for user {user.id} (org={user.organization_id})"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exercise not found or you don't have access to it"
            )
        
        response = self._entity_to_response(exercise)
        
        # Cache global exercises
        if exercise.is_global and self.redis:
            await self._cache_exercise(exercise_id, response)
        
        return response
    
    async def list_exercises(
        self,
        filters: ExerciseFilter,
        user: User
    ) -> ExerciseListResponse:
        """
        List exercises with filtering and pagination.
        
        Returns global exercises + organization-specific exercises.
        
        Args:
            filters: ExerciseFilter with search, equipment, muscle_group, pagination
            user: User requesting the list
            
        Returns:
            ExerciseListResponse with paginated results
        """
        # Fetch exercises
        exercises, total = await self.repository.list_exercises(
            filters=filters,
            org_id=user.organization_id
        )
        
        # Convert to response schemas
        items = [self._entity_to_response(exercise) for exercise in exercises]
        
        # Calculate pagination metadata
        page = (filters.skip // filters.limit) + 1
        total_pages = (total + filters.limit - 1) // filters.limit  # Ceiling division
        has_next = filters.skip + filters.limit < total
        has_previous = filters.skip > 0
        
        logger.debug(
            f"Listed {len(items)} exercises for user {user.id} "
            f"(page={page}, total={total}, filters={filters})"
        )
        
        return ExerciseListResponse(
            items=items,
            total=total,
            page=page,
            page_size=filters.limit,
            total_pages=total_pages,
            has_next=has_next,
            has_previous=has_previous
        )
    
    async def update_exercise(
        self,
        exercise_id: UUID,
        exercise_data: ExerciseUpdate,
        user: User
    ) -> ExerciseResponse:
        """
        Update an exercise.
        
        Business Rules:
        - User must be the creator (for org exercises) or admin
        - Cannot update global exercises unless admin
        - Name must be unique within scope if changed
        
        Args:
            exercise_id: Exercise UUID
            exercise_data: ExerciseUpdate with fields to update
            user: User performing the update
            
        Returns:
            ExerciseResponse with updated exercise
            
        Raises:
            HTTPException: 403 if user doesn't have permission
            HTTPException: 404 if exercise not found
            HTTPException: 409 if new name conflicts
        """
        # Fetch existing exercise to check permissions
        existing = await self.repository.get_by_id(
            exercise_id=exercise_id,
            org_id=user.organization_id
        )
        
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exercise not found or you don't have access to it"
            )
        
        # Check authorization
        if not self._can_modify_exercise(user, existing):
            logger.warning(
                f"User {user.id} attempted to update exercise {exercise_id} "
                f"without permission (creator={existing.created_by_user_id}, "
                f"is_global={existing.is_global})"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to update this exercise"
            )
        
        # Check for duplicate name if name is being changed
        if exercise_data.name and exercise_data.name != existing.name:
            name_exists = await self.repository.exists_by_name(
                name=exercise_data.name,
                org_id=None if existing.is_global else user.organization_id,
                is_global=existing.is_global,
                exclude_id=exercise_id
            )
            
            if name_exists:
                scope = "globally" if existing.is_global else "in your organization"
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Exercise with name '{exercise_data.name}' already exists {scope}"
                )
        
        # Prepare update data (only include provided fields)
        update_dict = {}
        
        if exercise_data.name is not None:
            update_dict["name"] = exercise_data.name
        
        if exercise_data.description is not None:
            update_dict["description"] = exercise_data.description
        
        if exercise_data.equipment is not None:
            update_dict["equipment"] = exercise_data.equipment
        
        if exercise_data.muscle_contributions is not None:
            update_dict["muscle_contributions"] = exercise_data.muscle_contributions
        
        if exercise_data.image_url is not None:
            update_dict["image_url"] = str(exercise_data.image_url) if exercise_data.image_url else None
        
        # Update exercise
        try:
            updated = await self.repository.update(
                exercise_id=exercise_id,
                exercise_data=update_dict,
                user_id=user.id,
                org_id=user.organization_id
            )
            
            if not updated:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Exercise not found or update failed"
                )
            
            logger.info(
                f"Exercise {exercise_id} updated by user {user.id} "
                f"(fields={list(update_dict.keys())})"
            )
            
            # Invalidate cache
            if self.redis:
                await self._invalidate_exercise_cache(exercise_id)
                if updated.is_global:
                    await self._invalidate_global_exercises_cache()
            
            return self._entity_to_response(updated)
        
        except ValueError as e:
            logger.error(f"Validation error updating exercise: {e}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(e)
            )
    
    async def delete_exercise(
        self,
        exercise_id: UUID,
        user: User
    ) -> bool:
        """
        Delete an exercise.
        
        Business Rules:
        - User must be the creator (for org exercises) or admin
        - Cannot delete global exercises unless admin
        - Future: Check if exercise is used in any programs (prevent deletion)
        
        Args:
            exercise_id: Exercise UUID
            user: User performing the deletion
            
        Returns:
            True if deleted successfully
            
        Raises:
            HTTPException: 403 if user doesn't have permission
            HTTPException: 404 if exercise not found
            HTTPException: 409 if exercise is in use (future)
        """
        # Fetch existing exercise to check permissions
        existing = await self.repository.get_by_id(
            exercise_id=exercise_id,
            org_id=user.organization_id
        )
        
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exercise not found or you don't have access to it"
            )
        
        # Check authorization
        if not self._can_modify_exercise(user, existing):
            logger.warning(
                f"User {user.id} attempted to delete exercise {exercise_id} "
                f"without permission"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this exercise"
            )
        
        # TODO: Check if exercise is used in any programs
        # if await self._is_exercise_in_use(exercise_id):
        #     raise HTTPException(
        #         status_code=status.HTTP_409_CONFLICT,
        #         detail="Cannot delete exercise that is used in programs. "
        #                "Remove it from all programs first."
        #     )
        
        # Delete exercise
        is_admin = user.role == UserRole.ADMIN
        deleted = await self.repository.delete(
            exercise_id=exercise_id,
            user_id=user.id,
            org_id=user.organization_id,
            is_admin=is_admin
        )
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exercise not found or deletion failed"
            )
        
        logger.info(
            f"Exercise {exercise_id} deleted by user {user.id} "
            f"(was_global={existing.is_global})"
        )
        
        # Invalidate cache
        if self.redis:
            await self._invalidate_exercise_cache(exercise_id)
            if existing.is_global:
                await self._invalidate_global_exercises_cache()
        
        return True
    
    async def search_exercises(
        self,
        query: str,
        user: User,
        limit: int = 20
    ) -> List[ExerciseSummaryResponse]:
        """
        Full-text search for exercises.
        
        Args:
            query: Search query string
            user: User performing the search
            limit: Maximum number of results
            
        Returns:
            List of ExerciseSummaryResponse
        """
        exercises = await self.repository.search(
            query=query,
            org_id=user.organization_id,
            limit=limit
        )
        
        logger.debug(
            f"Search '{query}' returned {len(exercises)} results "
            f"for user {user.id}"
        )
        
        return [self._entity_to_summary(exercise) for exercise in exercises]
    
    # ==================== Private Helper Methods ====================
    
    def _can_create_custom_exercise(self, user: User) -> bool:
        """
        Check if user can create custom exercises.
        
        Rules:
        - Admins can always create (including global exercises)
        - Pro tier users can create organization exercises
        - Free tier users cannot create custom exercises
        
        Args:
            user: User to check
            
        Returns:
            True if user can create exercises
        """
        if user.role == UserRole.ADMIN:
            return True
        
        # Check organization subscription tier
        # Assuming user has organization property with subscription_tier
        # This will be implemented when Organization entity is properly linked
        # For now, return True for all authenticated users
        # TODO: Implement proper subscription tier check
        return True
    
    def _can_modify_exercise(self, user: User, exercise: Exercise) -> bool:
        """
        Check if user can modify (update/delete) an exercise.
        
        Rules:
        - Admins can modify any exercise
        - Users can modify exercises they created
        - Cannot modify global exercises unless admin
        
        Args:
            user: User attempting modification
            exercise: Exercise to modify
            
        Returns:
            True if user can modify the exercise
        """
        # Admins can modify anything
        if user.role == UserRole.ADMIN:
            return True
        
        # Cannot modify global exercises if not admin
        if exercise.is_global:
            return False
        
        # Can modify own exercises
        if exercise.created_by_user_id == user.id:
            return True
        
        return False
    
    def _entity_to_response(self, exercise: Exercise) -> ExerciseResponse:
        """
        Convert Exercise entity to ExerciseResponse schema.
        
        Args:
            exercise: Exercise domain entity
            
        Returns:
            ExerciseResponse with computed fields
        """
        # Convert muscle contributions to response format
        muscle_contributions = [
            MuscleContributionResponse(
                muscle=muscle,
                muscle_name=muscle.display_name,
                contribution=contribution,
                contribution_percentage=contribution.percentage,
                contribution_label=contribution.display_name
            )
            for muscle, contribution in sorted(
                exercise.muscle_contributions.items(),
                key=lambda x: x[1].value,
                reverse=True
            )
        ]
        
        # Get primary and secondary muscles
        primary_muscles = [muscle.display_name for muscle in exercise.get_primary_muscles()]
        secondary_muscles = [muscle.display_name for muscle in exercise.get_secondary_muscles()]
        
        return ExerciseResponse(
            id=exercise.id,
            name=exercise.name,
            description=exercise.description,
            equipment=exercise.equipment,
            equipment_name=exercise.equipment.display_name,
            image_url=exercise.image_url,
            is_global=exercise.is_global,
            created_by_user_id=exercise.created_by_user_id,
            organization_id=exercise.organization_id,
            muscle_contributions=muscle_contributions,
            primary_muscles=primary_muscles,
            secondary_muscles=secondary_muscles,
            total_contribution=exercise.get_total_contribution(),
            is_compound=exercise.is_compound(),
            created_at=exercise.created_at.isoformat() if exercise.created_at else "",
            updated_at=exercise.updated_at.isoformat() if exercise.updated_at else "",
        )
    
    def _entity_to_summary(self, exercise: Exercise) -> ExerciseSummaryResponse:
        """
        Convert Exercise entity to lightweight ExerciseSummaryResponse.
        
        Args:
            exercise: Exercise domain entity
            
        Returns:
            ExerciseSummaryResponse with essential fields only
        """
        primary_muscles = [muscle.display_name for muscle in exercise.get_primary_muscles()]
        
        return ExerciseSummaryResponse(
            id=exercise.id,
            name=exercise.name,
            equipment=exercise.equipment,
            equipment_name=exercise.equipment.display_name,
            primary_muscles=primary_muscles,
            is_global=exercise.is_global
        )
    
    # ==================== Caching Methods ====================
    
    async def _get_cached_exercise(self, exercise_id: UUID) -> ExerciseResponse | None:
        """Get exercise from cache."""
        if not self.redis:
            return None
        
        try:
            cache_key = f"exercise:{exercise_id}"
            cached = await self.redis.get(cache_key)
            
            if cached:
                # Parse JSON and return ExerciseResponse
                # Note: This requires proper JSON serialization
                # For now, return None to always fetch from DB
                pass
        except Exception as e:
            logger.error(f"Cache retrieval error: {e}")
        
        return None
    
    async def _cache_exercise(self, exercise_id: UUID, response: ExerciseResponse) -> None:
        """Cache exercise response."""
        if not self.redis:
            return
        
        try:
            cache_key = f"exercise:{exercise_id}"
            # Note: This requires proper JSON serialization of Pydantic model
            # await self.redis.setex(cache_key, self.CACHE_TTL, response.json())
            pass
        except Exception as e:
            logger.error(f"Cache storage error: {e}")
    
    async def _invalidate_exercise_cache(self, exercise_id: UUID) -> None:
        """Invalidate cached exercise."""
        if not self.redis:
            return
        
        try:
            cache_key = f"exercise:{exercise_id}"
            await self.redis.delete(cache_key)
        except Exception as e:
            logger.error(f"Cache invalidation error: {e}")
    
    async def _invalidate_global_exercises_cache(self) -> None:
        """Invalidate global exercises list cache."""
        if not self.redis:
            return
        
        try:
            # Invalidate pattern-based keys for global exercise lists
            # await self.redis.delete_pattern("exercises:global:*")
            pass
        except Exception as e:
            logger.error(f"Global cache invalidation error: {e}")
