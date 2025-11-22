"""
Exercise repository for database operations.

Handles CRUD operations for exercises with proper authorization,
filtering, pagination, and full-text search capabilities.
"""

from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import Select, and_, func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.exercise import Exercise
from app.domain.value_objects.equipment import Equipment
from app.domain.value_objects.muscle_groups import MuscleGroup
from app.domain.value_objects.volume_contribution import VolumeContribution
from app.models.exercise import ExerciseModel
from app.schemas.exercise import ExerciseFilter


class ExerciseRepository:
    """
    Repository for Exercise entity database operations.
    
    Handles persistence, retrieval, and querying of exercises with support for:
    - Global (admin-created) and organization-specific exercises
    - Full-text search on name and description
    - Filtering by equipment, muscle groups, and scope
    - Pagination and sorting
    - Authorization checks for updates and deletes
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.
        
        Args:
            session: Async SQLAlchemy session
        """
        self.session = session
    
    async def create(
        self,
        exercise_data: dict,
        user_id: UUID,
        org_id: UUID | None = None,
        is_global: bool = False
    ) -> Exercise:
        """
        Create a new exercise.
        
        Args:
            exercise_data: Exercise attributes (name, description, equipment, muscle_contributions, image_url)
            user_id: ID of user creating the exercise
            org_id: Organization ID (None for global exercises)
            is_global: True if creating global exercise (admin only)
            
        Returns:
            Exercise: Created exercise entity
            
        Raises:
            ValueError: If validation fails
            
        Examples:
            >>> muscle_contributions = {
            ...     MuscleGroup.CHEST: VolumeContribution.PRIMARY,
            ...     MuscleGroup.TRICEPS: VolumeContribution.HIGH
            ... }
            >>> exercise = await repo.create({
            ...     "name": "Bench Press",
            ...     "equipment": Equipment.BARBELL,
            ...     "muscle_contributions": muscle_contributions
            ... }, user_id, org_id)
        """
        # Convert muscle contributions to dict for JSONB storage
        muscle_contributions_dict = {
            muscle.value: contribution.value
            for muscle, contribution in exercise_data["muscle_contributions"].items()
        }
        
        # Create Exercise entity for validation
        exercise_entity = Exercise(
            name=exercise_data["name"],
            description=exercise_data.get("description", ""),
            equipment=exercise_data["equipment"],
            muscle_contributions=exercise_data["muscle_contributions"],
            image_url=exercise_data.get("image_url"),
            is_global=is_global,
            created_by_user_id=None if is_global else user_id,
            organization_id=None if is_global else org_id,
        )
        
        # Create database model
        model = ExerciseModel(
            id=exercise_entity.id,
            name=exercise_entity.name,
            description=exercise_entity.description,
            equipment=exercise_entity.equipment.value,
            image_url=exercise_entity.image_url,
            is_global=is_global,
            created_by_user_id=None if is_global else user_id,
            organization_id=None if is_global else org_id,
            muscle_contributions=muscle_contributions_dict,
            created_at=exercise_entity.created_at,
            updated_at=exercise_entity.updated_at,
        )
        
        self.session.add(model)
        await self.session.flush()
        
        return exercise_entity
    
    async def get_by_id(
        self,
        exercise_id: UUID,
        org_id: UUID | None = None
    ) -> Exercise | None:
        """
        Get exercise by ID.
        
        Returns exercise if:
        - It's a global exercise, OR
        - It belongs to the specified organization
        
        Args:
            exercise_id: Exercise UUID
            org_id: Organization ID (None to only fetch global exercises)
            
        Returns:
            Exercise entity if found and accessible, None otherwise
        """
        query = select(ExerciseModel).where(ExerciseModel.id == exercise_id)
        
        # Add authorization filter: global OR belongs to org
        if org_id is not None:
            query = query.where(
                or_(
                    ExerciseModel.is_global == True,
                    ExerciseModel.organization_id == org_id
                )
            )
        else:
            # Only global exercises if no org_id provided
            query = query.where(ExerciseModel.is_global == True)
        
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        
        if model is None:
            return None
        
        return self._model_to_entity(model)
    
    async def get_by_name(
        self,
        name: str,
        org_id: UUID | None = None,
        is_global: bool = False
    ) -> Exercise | None:
        """
        Get exercise by name within organization or global scope.
        
        Args:
            name: Exercise name
            org_id: Organization ID (for non-global exercises)
            is_global: True to search global exercises
            
        Returns:
            Exercise entity if found, None otherwise
        """
        query = select(ExerciseModel).where(
            func.lower(ExerciseModel.name) == name.lower()
        )
        
        if is_global:
            query = query.where(ExerciseModel.is_global == True)
        else:
            query = query.where(
                and_(
                    ExerciseModel.organization_id == org_id,
                    ExerciseModel.is_global == False
                )
            )
        
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        
        if model is None:
            return None
        
        return self._model_to_entity(model)
    
    async def list_exercises(
        self,
        filters: ExerciseFilter,
        org_id: UUID | None = None
    ) -> Tuple[List[Exercise], int]:
        """
        List exercises with filtering and pagination.
        
        Returns global exercises + organization-specific exercises.
        Supports filtering by equipment, muscle groups, search term.
        
        Args:
            filters: ExerciseFilter with search, equipment, muscle_group, is_global, skip, limit
            org_id: Organization ID to include org-specific exercises (None for global only)
            
        Returns:
            Tuple of (list of exercises, total count)
            
        Examples:
            >>> filters = ExerciseFilter(
            ...     search="press",
            ...     equipment=Equipment.BARBELL,
            ...     muscle_group=MuscleGroup.CHEST,
            ...     skip=0,
            ...     limit=20
            ... )
            >>> exercises, total = await repo.list_exercises(filters, org_id)
        """
        # Build base query with authorization
        query = self._build_base_query(org_id, filters.is_global)
        
        # Apply filters
        query = self._apply_filters(query, filters)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0
        
        # Apply ordering (global first, then by name)
        query = query.order_by(
            ExerciseModel.is_global.desc(),
            ExerciseModel.name.asc()
        )
        
        # Apply pagination
        query = query.offset(filters.skip).limit(filters.limit)
        
        # Execute query
        result = await self.session.execute(query)
        models = result.scalars().all()
        
        # Convert to entities
        exercises = [self._model_to_entity(model) for model in models]
        
        return exercises, total
    
    async def update(
        self,
        exercise_id: UUID,
        exercise_data: dict,
        user_id: UUID,
        org_id: UUID | None = None
    ) -> Exercise | None:
        """
        Update an exercise.
        
        Only allows updates if:
        - User created the exercise (non-global), OR
        - User is admin updating a global exercise
        
        Args:
            exercise_id: Exercise UUID
            exercise_data: Fields to update (name, description, equipment, muscle_contributions, image_url)
            user_id: ID of user performing update
            org_id: Organization ID for authorization
            
        Returns:
            Updated Exercise entity if found and authorized, None otherwise
            
        Raises:
            ValueError: If validation fails
        """
        # Fetch existing exercise
        query = select(ExerciseModel).where(ExerciseModel.id == exercise_id)
        
        # Authorization: must be creator or global exercise (admin check done in service)
        if org_id is not None:
            query = query.where(
                or_(
                    ExerciseModel.is_global == True,
                    and_(
                        ExerciseModel.organization_id == org_id,
                        ExerciseModel.created_by_user_id == user_id
                    )
                )
            )
        else:
            query = query.where(ExerciseModel.is_global == True)
        
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        
        if model is None:
            return None
        
        # Update fields
        if "name" in exercise_data:
            model.name = exercise_data["name"]
        
        if "description" in exercise_data:
            model.description = exercise_data["description"]
        
        if "equipment" in exercise_data:
            model.equipment = exercise_data["equipment"].value
        
        if "image_url" in exercise_data:
            model.image_url = exercise_data["image_url"]
        
        if "muscle_contributions" in exercise_data:
            # Convert to dict for JSONB
            model.muscle_contributions = {
                muscle.value: contribution.value
                for muscle, contribution in exercise_data["muscle_contributions"].items()
            }
        
        await self.session.flush()
        
        return self._model_to_entity(model)
    
    async def delete(
        self,
        exercise_id: UUID,
        user_id: UUID,
        org_id: UUID | None = None,
        is_admin: bool = False
    ) -> bool:
        """
        Delete an exercise (soft delete).
        
        Only allows deletion if:
        - User created the exercise (non-global), OR
        - User is admin deleting any exercise
        
        Args:
            exercise_id: Exercise UUID
            user_id: ID of user performing deletion
            org_id: Organization ID for authorization
            is_admin: True if user is admin (can delete global exercises)
            
        Returns:
            True if deleted, False if not found or not authorized
        """
        query = select(ExerciseModel).where(ExerciseModel.id == exercise_id)
        
        # Authorization
        if is_admin:
            # Admin can delete anything in their org or global
            if org_id is not None:
                query = query.where(
                    or_(
                        ExerciseModel.is_global == True,
                        ExerciseModel.organization_id == org_id
                    )
                )
        else:
            # Non-admin can only delete own exercises
            query = query.where(
                and_(
                    ExerciseModel.created_by_user_id == user_id,
                    ExerciseModel.organization_id == org_id,
                    ExerciseModel.is_global == False
                )
            )
        
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        
        if model is None:
            return False
        
        # Perform soft delete
        await self.session.delete(model)
        await self.session.flush()
        
        return True
    
    async def search(
        self,
        query: str,
        org_id: UUID | None = None,
        limit: int = 20
    ) -> List[Exercise]:
        """
        Full-text search on exercise name and description.
        
        Uses PostgreSQL's full-text search with GIN index.
        Returns global + organization-specific exercises.
        
        Args:
            query: Search query string
            org_id: Organization ID to include org exercises
            limit: Maximum number of results (default 20)
            
        Returns:
            List of matching exercises, ordered by relevance
            
        Examples:
            >>> exercises = await repo.search("bench press", org_id, limit=10)
        """
        # Build base query
        base_query = self._build_base_query(org_id, is_global_filter=None)
        
        # Add full-text search using PostgreSQL's tsvector
        search_query = base_query.where(
            text(
                "to_tsvector('english', name || ' ' || COALESCE(description, '')) "
                "@@ plainto_tsquery('english', :search_term)"
            ).bindparams(search_term=query)
        )
        
        # Order by relevance (rank) and limit
        search_query = search_query.order_by(
            text(
                "ts_rank(to_tsvector('english', name || ' ' || COALESCE(description, '')), "
                "plainto_tsquery('english', :search_term)) DESC"
            ).bindparams(search_term=query)
        ).limit(limit)
        
        result = await self.session.execute(search_query)
        models = result.scalars().all()
        
        return [self._model_to_entity(model) for model in models]
    
    async def exists_by_name(
        self,
        name: str,
        org_id: UUID | None = None,
        is_global: bool = False,
        exclude_id: UUID | None = None
    ) -> bool:
        """
        Check if exercise with given name exists.
        
        Args:
            name: Exercise name to check
            org_id: Organization ID (for non-global exercises)
            is_global: True to check global exercises
            exclude_id: Exercise ID to exclude from check (for updates)
            
        Returns:
            True if exercise with name exists, False otherwise
        """
        query = select(func.count()).select_from(ExerciseModel).where(
            func.lower(ExerciseModel.name) == name.lower()
        )
        
        if is_global:
            query = query.where(ExerciseModel.is_global == True)
        else:
            query = query.where(
                and_(
                    ExerciseModel.organization_id == org_id,
                    ExerciseModel.is_global == False
                )
            )
        
        if exclude_id is not None:
            query = query.where(ExerciseModel.id != exclude_id)
        
        result = await self.session.execute(query)
        count = result.scalar() or 0
        
        return count > 0
    
    async def count_by_organization(self, org_id: UUID) -> int:
        """
        Count exercises for an organization (including global).
        
        Args:
            org_id: Organization ID
            
        Returns:
            Total number of accessible exercises
        """
        query = select(func.count()).select_from(ExerciseModel).where(
            or_(
                ExerciseModel.is_global == True,
                ExerciseModel.organization_id == org_id
            )
        )
        
        result = await self.session.execute(query)
        return result.scalar() or 0
    
    # ==================== Private Helper Methods ====================
    
    def _build_base_query(
        self,
        org_id: UUID | None,
        is_global_filter: bool | None
    ) -> Select:
        """
        Build base query with authorization filters.
        
        Args:
            org_id: Organization ID (None for global only)
            is_global_filter: Filter by global status (None = both)
            
        Returns:
            SQLAlchemy select query
        """
        query = select(ExerciseModel)
        
        # Authorization: global OR belongs to org
        if org_id is not None:
            auth_conditions = [ExerciseModel.is_global == True]
            
            # Add org-specific condition
            if is_global_filter is None or not is_global_filter:
                auth_conditions.append(ExerciseModel.organization_id == org_id)
            
            query = query.where(or_(*auth_conditions))
        else:
            # Only global if no org_id
            query = query.where(ExerciseModel.is_global == True)
        
        # Apply is_global filter if specified
        if is_global_filter is not None:
            query = query.where(ExerciseModel.is_global == is_global_filter)
        
        return query
    
    def _apply_filters(self, query: Select, filters: ExerciseFilter) -> Select:
        """
        Apply filtering conditions to query.
        
        Args:
            query: Base SQLAlchemy query
            filters: ExerciseFilter with search, equipment, muscle_group
            
        Returns:
            Filtered query
        """
        # Equipment filter
        if filters.equipment is not None:
            query = query.where(ExerciseModel.equipment == filters.equipment.value)
        
        # Muscle group filter (JSONB query)
        if filters.muscle_group is not None:
            query = query.where(
                ExerciseModel.muscle_contributions.has_key(filters.muscle_group.value)
            )
        
        # Search filter (simple ILIKE for name/description)
        if filters.search:
            search_term = f"%{filters.search}%"
            query = query.where(
                or_(
                    ExerciseModel.name.ilike(search_term),
                    ExerciseModel.description.ilike(search_term)
                )
            )
        
        return query
    
    def _model_to_entity(self, model: ExerciseModel) -> Exercise:
        """
        Convert database model to domain entity.
        
        Args:
            model: SQLAlchemy ExerciseModel
            
        Returns:
            Exercise domain entity
        """
        # Convert JSONB muscle_contributions back to enums
        muscle_contributions = {
            MuscleGroup(muscle): VolumeContribution.from_float(contribution)
            for muscle, contribution in model.muscle_contributions.items()
        }
        
        return Exercise(
            id=model.id,
            name=model.name,
            description=model.description,
            equipment=Equipment(model.equipment),
            muscle_contributions=muscle_contributions,
            image_url=model.image_url,
            is_global=model.is_global,
            created_by_user_id=model.created_by_user_id,
            organization_id=model.organization_id,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
