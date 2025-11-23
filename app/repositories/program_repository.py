"""
Training Program Repository.

Handles database operations for training programs, sessions, and their relationships.
"""

from typing import Optional
from uuid import UUID

from sqlalchemy import and_, delete, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.entities.training_program import TrainingProgram, ScheduledSession
from app.domain.entities.training_split import TrainingSplitType
from app.domain.entities.training_structure import (
    CyclicStructure,
    StructureType,
    WeeklyStructure,
)
from app.domain.entities.workout_exercise import WorkoutExercise
from app.domain.entities.workout_session import WorkoutSession
from app.models.training_program import TrainingProgramModel
from app.models.workout_session import WorkoutSessionModel
from app.schemas.training_program import ProgramFilter


class ProgramRepository:
    """Repository for training program database operations.
    
    Handles CRUD operations for programs and sessions with proper
    eager loading, authorization, and cascading deletes.
    """
    
    def __init__(self, session: AsyncSession):
        """Initialize repository with database session.
        
        Args:
            session: SQLAlchemy async session
        """
        self.session = session
    
    # ==================== Program Methods ====================
    
    async def create_program(
        self,
        program: TrainingProgram,
    ) -> TrainingProgram:
        """Create a new training program with sessions.
        
        Args:
            program: TrainingProgram entity to create
            
        Returns:
            TrainingProgram: Created program entity
            
        Examples:
            >>> program = TrainingProgram(...)
            >>> created = await repo.create_program(program)
        """
        # Create program model
        program_model = TrainingProgramModel.create_from_entity(program)
        self.session.add(program_model)
        
        # Create session models
        for session in program.sessions:
            session_model = WorkoutSessionModel.create_from_entity(session)
            session_model.program_id = program.id
            self.session.add(session_model)
        
        await self.session.flush()
        await self.session.refresh(program_model, ["sessions"])
        
        return self._model_to_entity(program_model)
    
    async def get_by_id(
        self,
        program_id: UUID,
        org_id: Optional[UUID] = None,
    ) -> Optional[TrainingProgram]:
        """Get program by ID with all sessions and exercises.
        
        Returns templates or user programs belonging to the organization.
        
        Args:
            program_id: Program ID to retrieve
            org_id: Organization ID for authorization (None to skip org check)
            
        Returns:
            TrainingProgram | None: Program entity if found and authorized
            
        Examples:
            >>> program = await repo.get_by_id(program_id, org_id)
        """
        # Build query with eager loading
        query = (
            select(TrainingProgramModel)
            .options(selectinload(TrainingProgramModel.sessions))
            .where(TrainingProgramModel.id == program_id)
        )
        
        # Add authorization filter
        if org_id is not None:
            query = query.where(
                or_(
                    TrainingProgramModel.is_template == True,
                    TrainingProgramModel.organization_id == org_id,
                )
            )
        
        result = await self.session.execute(query)
        program_model = result.scalar_one_or_none()
        
        if program_model is None:
            return None
        
        return self._model_to_entity(program_model)
    
    async def list_programs(
        self,
        filters: ProgramFilter,
        org_id: Optional[UUID] = None,
    ) -> tuple[list[TrainingProgram], int]:
        """List programs with filtering and pagination.
        
        Returns templates plus organization-specific programs.
        
        Args:
            filters: Filter criteria and pagination params
            org_id: Organization ID for authorization
            
        Returns:
            tuple: (list of programs, total count)
            
        Examples:
            >>> programs, total = await repo.list_programs(filters, org_id)
        """
        # Build base query
        query = select(TrainingProgramModel).options(
            selectinload(TrainingProgramModel.sessions)
        )
        
        # Authorization filter
        if org_id is not None:
            query = query.where(
                or_(
                    TrainingProgramModel.is_template == True,
                    TrainingProgramModel.organization_id == org_id,
                )
            )
        
        # Apply filters
        if filters.search:
            search_term = f"%{filters.search.lower()}%"
            query = query.where(
                or_(
                    TrainingProgramModel.name.ilike(search_term),
                    TrainingProgramModel.description.ilike(search_term),
                )
            )
        
        if filters.split_type is not None:
            query = query.where(
                TrainingProgramModel.split_type == filters.split_type.value
            )
        
        if filters.structure_type is not None:
            query = query.where(
                TrainingProgramModel.structure_type == filters.structure_type.value
            )
        
        if filters.is_template is not None:
            query = query.where(
                TrainingProgramModel.is_template == filters.is_template
            )
        
        # Get total count
        count_query = select(TrainingProgramModel.id)
        # Apply same filters to count query
        if org_id is not None:
            count_query = count_query.where(
                or_(
                    TrainingProgramModel.is_template == True,
                    TrainingProgramModel.organization_id == org_id,
                )
            )
        if filters.search:
            search_term = f"%{filters.search.lower()}%"
            count_query = count_query.where(
                or_(
                    TrainingProgramModel.name.ilike(search_term),
                    TrainingProgramModel.description.ilike(search_term),
                )
            )
        if filters.split_type is not None:
            count_query = count_query.where(
                TrainingProgramModel.split_type == filters.split_type.value
            )
        if filters.structure_type is not None:
            count_query = count_query.where(
                TrainingProgramModel.structure_type == filters.structure_type.value
            )
        if filters.is_template is not None:
            count_query = count_query.where(
                TrainingProgramModel.is_template == filters.is_template
            )
        
        count_result = await self.session.execute(count_query)
        total = len(count_result.all())
        
        # Apply ordering
        query = query.order_by(TrainingProgramModel.created_at.desc())
        
        # Apply pagination
        query = query.offset(filters.skip).limit(filters.limit)
        
        # Execute query
        result = await self.session.execute(query)
        program_models = result.scalars().all()
        
        # Convert to entities
        programs = [self._model_to_entity(model) for model in program_models]
        
        return programs, total
    
    async def update_program(
        self,
        program_id: UUID,
        update_data: dict,
    ) -> Optional[TrainingProgram]:
        """Update program details (not sessions).
        
        Args:
            program_id: Program ID to update
            update_data: Dictionary with fields to update
            
        Returns:
            TrainingProgram | None: Updated program entity
            
        Examples:
            >>> updated = await repo.update_program(
            ...     program_id,
            ...     {"name": "New Name", "duration_weeks": 12}
            ... )
        """
        # Get existing program
        program = await self.get_by_id(program_id)
        if program is None:
            return None
        
        # Update fields
        query = (
            update(TrainingProgramModel)
            .where(TrainingProgramModel.id == program_id)
            .values(**update_data)
            .returning(TrainingProgramModel)
        )
        
        result = await self.session.execute(query)
        updated_model = result.scalar_one()
        await self.session.refresh(updated_model, ["sessions"])
        
        return self._model_to_entity(updated_model)
    
    async def delete_program(
        self,
        program_id: UUID,
    ) -> bool:
        """Delete program and cascade to sessions.
        
        Args:
            program_id: Program ID to delete
            
        Returns:
            bool: True if deleted, False if not found
            
        Examples:
            >>> deleted = await repo.delete_program(program_id)
        """
        # Check if exists
        query = select(TrainingProgramModel.id).where(
            TrainingProgramModel.id == program_id
        )
        result = await self.session.execute(query)
        if result.scalar_one_or_none() is None:
            return False
        
        # Delete (will cascade to sessions due to relationship)
        delete_query = delete(TrainingProgramModel).where(
            TrainingProgramModel.id == program_id
        )
        await self.session.execute(delete_query)
        
        return True
    
    # ==================== Session Methods ====================
    
    async def create_session(
        self,
        session: WorkoutSession,
    ) -> WorkoutSession:
        """Create a new workout session.
        
        Args:
            session: WorkoutSession entity to create
            
        Returns:
            WorkoutSession: Created session entity
            
        Examples:
            >>> session = WorkoutSession(program_id=program_id, ...)
            >>> created = await repo.create_session(session)
        """
        session_model = WorkoutSessionModel.create_from_entity(session)
        self.session.add(session_model)
        await self.session.flush()
        await self.session.refresh(session_model)
        
        return self._session_model_to_entity(session_model)
    
    async def get_session_by_id(
        self,
        session_id: UUID,
    ) -> Optional[WorkoutSession]:
        """Get session by ID.
        
        Args:
            session_id: Session ID to retrieve
            
        Returns:
            WorkoutSession | None: Session entity if found
        """
        query = select(WorkoutSessionModel).where(
            WorkoutSessionModel.id == session_id
        )
        result = await self.session.execute(query)
        session_model = result.scalar_one_or_none()
        
        if session_model is None:
            return None
        
        return self._session_model_to_entity(session_model)
    
    async def update_session(
        self,
        session_id: UUID,
        update_data: dict,
    ) -> Optional[WorkoutSession]:
        """Update session details.
        
        Args:
            session_id: Session ID to update
            update_data: Dictionary with fields to update
            
        Returns:
            WorkoutSession | None: Updated session entity
            
        Examples:
            >>> updated = await repo.update_session(
            ...     session_id,
            ...     {"name": "Upper Body A - Modified", "exercises": [...]}
            ... )
        """
        # Get existing session
        session = await self.get_session_by_id(session_id)
        if session is None:
            return None
        
        # Update fields
        query = (
            update(WorkoutSessionModel)
            .where(WorkoutSessionModel.id == session_id)
            .values(**update_data)
            .returning(WorkoutSessionModel)
        )
        
        result = await self.session.execute(query)
        updated_model = result.scalar_one()
        
        return self._session_model_to_entity(updated_model)
    
    async def delete_session(
        self,
        session_id: UUID,
    ) -> bool:
        """Delete a workout session.
        
        Args:
            session_id: Session ID to delete
            
        Returns:
            bool: True if deleted, False if not found
            
        Examples:
            >>> deleted = await repo.delete_session(session_id)
        """
        # Check if exists
        query = select(WorkoutSessionModel.id).where(
            WorkoutSessionModel.id == session_id
        )
        result = await self.session.execute(query)
        if result.scalar_one_or_none() is None:
            return False
        
        # Delete
        delete_query = delete(WorkoutSessionModel).where(
            WorkoutSessionModel.id == session_id
        )
        await self.session.execute(delete_query)
        
        return True
    
    async def reorder_sessions(
        self,
        program_id: UUID,
        session_orders: dict[UUID, int],
    ) -> bool:
        """Reorder sessions within a program.
        
        Updates order_in_program for multiple sessions atomically.
        
        Args:
            program_id: Program ID containing the sessions
            session_orders: Mapping of session_id to new order_in_program
            
        Returns:
            bool: True if successful
            
        Examples:
            >>> success = await repo.reorder_sessions(
            ...     program_id,
            ...     {
            ...         session1_id: 2,
            ...         session2_id: 1,
            ...         session3_id: 3,
            ...     }
            ... )
        """
        # Verify all sessions belong to the program
        query = select(WorkoutSessionModel.id).where(
            and_(
                WorkoutSessionModel.program_id == program_id,
                WorkoutSessionModel.id.in_(session_orders.keys()),
            )
        )
        result = await self.session.execute(query)
        found_sessions = {row[0] for row in result.all()}
        
        if len(found_sessions) != len(session_orders):
            return False
        
        # Update each session's order
        for session_id, new_order in session_orders.items():
            update_query = (
                update(WorkoutSessionModel)
                .where(WorkoutSessionModel.id == session_id)
                .values(order_in_program=new_order)
            )
            await self.session.execute(update_query)
        
        return True
    
    async def get_program_sessions(
        self,
        program_id: UUID,
    ) -> list[WorkoutSession]:
        """Get all sessions for a program, ordered by order_in_program.
        
        Args:
            program_id: Program ID
            
        Returns:
            list[WorkoutSession]: List of session entities
        """
        query = (
            select(WorkoutSessionModel)
            .where(WorkoutSessionModel.program_id == program_id)
            .order_by(WorkoutSessionModel.order_in_program)
        )
        result = await self.session.execute(query)
        session_models = result.scalars().all()
        
        return [self._session_model_to_entity(model) for model in session_models]
    
    # ==================== Cloning Methods ====================
    
    async def clone_template(
        self,
        template_id: UUID,
        user_id: UUID,
        org_id: UUID,
        new_name: Optional[str] = None,
    ) -> Optional[TrainingProgram]:
        """Clone a template program for a user.
        
        Deep copies the program with all sessions and exercises.
        
        Args:
            template_id: ID of template to clone
            user_id: User creating the clone
            org_id: User's organization
            new_name: Optional custom name for clone
            
        Returns:
            TrainingProgram | None: Cloned program entity
            
        Examples:
            >>> cloned = await repo.clone_template(
            ...     template_id,
            ...     user_id,
            ...     org_id,
            ...     "My Custom Program"
            ... )
        """
        # Get template with sessions
        template = await self.get_by_id(template_id)
        if template is None or not template.is_template:
            return None
        
        # Clone using entity method
        cloned_program = template.clone_from_template(
            user_id=user_id,
            organization_id=org_id,
            new_name=new_name,
        )
        
        # Persist to database
        return await self.create_program(cloned_program)
    
    # ==================== Query Helpers ====================
    
    async def get_templates(
        self,
        split_type: Optional[TrainingSplitType] = None,
        structure_type: Optional[StructureType] = None,
    ) -> list[TrainingProgram]:
        """Get all template programs, optionally filtered.
        
        Args:
            split_type: Filter by split type
            structure_type: Filter by structure type
            
        Returns:
            list[TrainingProgram]: List of template programs
        """
        query = (
            select(TrainingProgramModel)
            .options(selectinload(TrainingProgramModel.sessions))
            .where(TrainingProgramModel.is_template == True)
        )
        
        if split_type is not None:
            query = query.where(TrainingProgramModel.split_type == split_type.value)
        
        if structure_type is not None:
            query = query.where(
                TrainingProgramModel.structure_type == structure_type.value
            )
        
        query = query.order_by(TrainingProgramModel.name)
        
        result = await self.session.execute(query)
        program_models = result.scalars().all()
        
        return [self._model_to_entity(model) for model in program_models]
    
    async def get_user_programs(
        self,
        org_id: UUID,
        user_id: Optional[UUID] = None,
    ) -> list[TrainingProgram]:
        """Get programs for an organization, optionally filtered by creator.
        
        Args:
            org_id: Organization ID
            user_id: Optional user ID to filter by creator
            
        Returns:
            list[TrainingProgram]: List of user programs
        """
        query = (
            select(TrainingProgramModel)
            .options(selectinload(TrainingProgramModel.sessions))
            .where(
                and_(
                    TrainingProgramModel.is_template == False,
                    TrainingProgramModel.organization_id == org_id,
                )
            )
        )
        
        if user_id is not None:
            query = query.where(
                TrainingProgramModel.created_by_user_id == user_id
            )
        
        query = query.order_by(TrainingProgramModel.created_at.desc())
        
        result = await self.session.execute(query)
        program_models = result.scalars().all()
        
        return [self._model_to_entity(model) for model in program_models]
    
    async def count_user_programs(
        self,
        org_id: UUID,
        user_id: Optional[UUID] = None,
    ) -> int:
        """Count programs for an organization/user.
        
        Args:
            org_id: Organization ID
            user_id: Optional user ID to filter by creator
            
        Returns:
            int: Number of programs
        """
        query = select(TrainingProgramModel.id).where(
            and_(
                TrainingProgramModel.is_template == False,
                TrainingProgramModel.organization_id == org_id,
            )
        )
        
        if user_id is not None:
            query = query.where(
                TrainingProgramModel.created_by_user_id == user_id
            )
        
        result = await self.session.execute(query)
        return len(result.all())
    
    # ==================== Conversion Methods ====================
    
    def _model_to_entity(
        self,
        model: TrainingProgramModel,
    ) -> TrainingProgram:
        """Convert program model to entity with sessions.
        
        Args:
            model: TrainingProgramModel instance
            
        Returns:
            TrainingProgram: Entity instance
        """
        # Parse structure config
        structure_config: WeeklyStructure | CyclicStructure
        if model.structure_type == StructureType.WEEKLY.value:
            structure_config = WeeklyStructure(**model.structure_config)
        else:
            structure_config = CyclicStructure(**model.structure_config)
        
        # Convert sessions
        sessions = [
            self._session_model_to_entity(session_model)
            for session_model in (model.sessions or [])
        ]
        
        # Create entity
        return TrainingProgram(
            id=model.id,
            name=model.name,
            description=model.description,
            split_type=TrainingSplitType(model.split_type),
            structure_type=StructureType(model.structure_type),
            structure_config=structure_config,
            sessions=sessions,
            is_template=model.is_template,
            created_by_user_id=model.created_by_user_id,
            organization_id=model.organization_id,
            duration_weeks=model.duration_weeks,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
    
    def _session_model_to_entity(
        self,
        model: WorkoutSessionModel,
    ) -> WorkoutSession:
        """Convert session model to entity.
        
        Args:
            model: WorkoutSessionModel instance
            
        Returns:
            WorkoutSession: Entity instance
        """
        # Convert exercises from JSONB
        exercises = [
            WorkoutExercise.from_dict(ex_data)
            for ex_data in model.exercises
        ]
        
        # Create entity
        return WorkoutSession(
            id=model.id,
            program_id=model.program_id,
            name=model.name,
            day_number=model.day_number,
            order_in_program=model.order_in_program,
            exercises=exercises,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
