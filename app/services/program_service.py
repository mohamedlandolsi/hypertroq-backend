"""
Training Program Service.

Business logic for training program operations including creation, cloning,
updates, volume calculations, and validation.
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status

from app.domain.entities.organization import SubscriptionTier
from app.domain.entities.training_program import TrainingProgram
from app.domain.entities.training_split import TrainingSplitType
from app.domain.entities.training_structure import (
    CyclicStructure,
    StructureType,
    WeeklyStructure,
)
from app.domain.entities.user import User
from app.domain.entities.workout_exercise import WorkoutExercise
from app.domain.entities.workout_session import WorkoutSession
from app.domain.value_objects.muscle_groups import MuscleGroup
from app.repositories.exercise_repository import ExerciseRepository
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.program_repository import ProgramRepository
from app.schemas.training_program import (
    MuscleVolumeResponse,
    ProgramCreate,
    ProgramFilter,
    ProgramListItemResponse,
    ProgramListResponse,
    ProgramResponse,
    ProgramStatsResponse,
    ProgramUpdate,
    SessionCreate,
    SessionResponse,
    SessionUpdate,
    WorkoutExerciseResponse,
)

logger = logging.getLogger(__name__)


class ProgramService:
    """Service for training program business logic.
    
    Handles program CRUD operations, validation, volume calculations,
    and subscription checks.
    """
    
    def __init__(
        self,
        program_repository: ProgramRepository,
        exercise_repository: ExerciseRepository,
        organization_repository: OrganizationRepository,
    ):
        """Initialize service with repositories.
        
        Args:
            program_repository: Program data access
            exercise_repository: Exercise data access
            organization_repository: Organization data access
        """
        self.program_repo = program_repository
        self.exercise_repo = exercise_repository
        self.org_repo = organization_repository
    
    # ==================== Program CRUD ====================
    
    async def create_program(
        self,
        program_data: ProgramCreate,
        user: User,
    ) -> ProgramResponse:
        """Create a new training program.
        
        Validates structure configuration, checks subscription tier,
        creates program, and calculates initial statistics.
        
        Args:
            program_data: Program creation data
            user: User creating the program
            
        Returns:
            ProgramResponse: Created program with stats
            
        Raises:
            HTTPException: If validation fails or insufficient permissions
            
        Examples:
            >>> program = await service.create_program(program_data, user)
        """
        logger.info(f"Creating program '{program_data.name}' for user {user.id}")
        
        # Check subscription tier
        await self._check_program_creation_permission(user)
        
        # Validate structure config matches type
        structure_config = self._parse_structure_config(
            program_data.structure_type,
            program_data.structure_config,
        )
        
        # Validate exercises exist
        await self._validate_session_exercises(program_data.sessions, user)
        
        # Create workout sessions
        sessions = []
        for session_data in program_data.sessions:
            exercises = [
                WorkoutExercise(
                    exercise_id=ex.exercise_id,
                    sets=ex.sets,
                    order_in_session=ex.order_in_session,
                    notes=ex.notes,
                )
                for ex in session_data.exercises
            ]
            
            session = WorkoutSession(
                program_id=None,  # Will be set after program creation
                name=session_data.name,
                day_number=session_data.day_number,
                order_in_program=session_data.order_in_program,
                exercises=exercises,
            )
            sessions.append(session)
        
        # Create program entity
        program = TrainingProgram(
            name=program_data.name,
            description=program_data.description,
            split_type=program_data.split_type,
            structure_type=program_data.structure_type,
            structure_config=structure_config,
            sessions=sessions,
            is_template=False,
            created_by_user_id=user.id,
            organization_id=user.organization_id,
            duration_weeks=program_data.duration_weeks,
        )
        
        # Update session program IDs
        for session in sessions:
            session._program_id = program.id
        
        # Persist to database
        created_program = await self.program_repo.create_program(program)
        
        # Calculate stats
        stats = await self._calculate_program_stats(created_program, user)
        
        # Check volume warnings
        volume_warnings = await self._get_volume_warnings(created_program, user)
        if volume_warnings:
            logger.warning(
                f"Program {created_program.id} has volume warnings: {volume_warnings}"
            )
        
        logger.info(f"Successfully created program {created_program.id}")
        
        return await self._program_to_response(created_program, stats)
    
    async def clone_from_template(
        self,
        template_id: UUID,
        user: User,
        new_name: Optional[str] = None,
    ) -> ProgramResponse:
        """Clone a template program for the user.
        
        Args:
            template_id: ID of template to clone
            user: User cloning the program
            new_name: Optional custom name for clone
            
        Returns:
            ProgramResponse: Cloned program with stats
            
        Raises:
            HTTPException: If template not found or user lacks permission
            
        Examples:
            >>> program = await service.clone_from_template(template_id, user)
        """
        logger.info(f"Cloning template {template_id} for user {user.id}")
        
        # Check subscription tier
        await self._check_program_creation_permission(user)
        
        # Clone template
        cloned_program = await self.program_repo.clone_template(
            template_id=template_id,
            user_id=user.id,
            org_id=user.organization_id,
            new_name=new_name,
        )
        
        if cloned_program is None:
            logger.error(f"Template {template_id} not found or not a template")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found",
            )
        
        # Calculate stats
        stats = await self._calculate_program_stats(cloned_program, user)
        
        logger.info(f"Successfully cloned program {cloned_program.id}")
        
        return await self._program_to_response(cloned_program, stats)
    
    async def get_program(
        self,
        program_id: UUID,
        user: User,
    ) -> ProgramResponse:
        """Get program by ID with stats.
        
        Args:
            program_id: Program ID to retrieve
            user: User requesting the program
            
        Returns:
            ProgramResponse: Program with stats
            
        Raises:
            HTTPException: If not found or unauthorized
        """
        program = await self.program_repo.get_by_id(
            program_id,
            org_id=user.organization_id,
        )
        
        if program is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Program not found",
            )
        
        stats = await self._calculate_program_stats(program, user)
        
        return await self._program_to_response(program, stats)
    
    async def update_program(
        self,
        program_id: UUID,
        program_data: ProgramUpdate,
        user: User,
    ) -> ProgramResponse:
        """Update program details.
        
        Args:
            program_id: Program ID to update
            program_data: Update data
            user: User updating the program
            
        Returns:
            ProgramResponse: Updated program with stats
            
        Raises:
            HTTPException: If not found, unauthorized, or validation fails
        """
        logger.info(f"Updating program {program_id} by user {user.id}")
        
        # Get and verify ownership
        program = await self.program_repo.get_by_id(
            program_id,
            org_id=user.organization_id,
        )
        
        if program is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Program not found",
            )
        
        await self._verify_program_ownership(program, user)
        
        # Prepare update data
        update_data = {}
        if program_data.name is not None:
            update_data["name"] = program_data.name
        if program_data.description is not None:
            update_data["description"] = program_data.description
        if program_data.duration_weeks is not None:
            update_data["duration_weeks"] = program_data.duration_weeks
        
        if not update_data:
            # No changes, return current program
            stats = await self._calculate_program_stats(program, user)
            return await self._program_to_response(program, stats)
        
        # Update program
        updated_program = await self.program_repo.update_program(
            program_id,
            update_data,
        )
        
        if updated_program is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Program not found",
            )
        
        # Recalculate stats
        stats = await self._calculate_program_stats(updated_program, user)
        
        logger.info(f"Successfully updated program {program_id}")
        
        return await self._program_to_response(updated_program, stats)
    
    async def delete_program(
        self,
        program_id: UUID,
        user: User,
    ) -> bool:
        """Delete a program.
        
        Args:
            program_id: Program ID to delete
            user: User deleting the program
            
        Returns:
            bool: True if deleted
            
        Raises:
            HTTPException: If not found or unauthorized
        """
        logger.info(f"Deleting program {program_id} by user {user.id}")
        
        # Get and verify ownership
        program = await self.program_repo.get_by_id(
            program_id,
            org_id=user.organization_id,
        )
        
        if program is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Program not found",
            )
        
        await self._verify_program_ownership(program, user)
        
        # Delete program (cascades to sessions)
        deleted = await self.program_repo.delete_program(program_id)
        
        if deleted:
            logger.info(f"Successfully deleted program {program_id}")
        
        return deleted
    
    async def list_programs(
        self,
        filters: ProgramFilter,
        user: User,
    ) -> ProgramListResponse:
        """List programs with filtering and pagination.
        
        Returns templates plus user's organization programs.
        
        Args:
            filters: Filter and pagination parameters
            user: User requesting the list
            
        Returns:
            ProgramListResponse: Paginated program list
        """
        programs, total = await self.program_repo.list_programs(
            filters,
            org_id=user.organization_id,
        )
        
        # Convert to list items
        items = [
            ProgramListItemResponse(
                id=program.id,
                name=program.name,
                description=program.description,
                split_type=program.split_type.value,
                structure_type=program.structure_type.value,
                is_template=program.is_template,
                duration_weeks=program.duration_weeks,
                session_count=len(program.sessions),
                created_at=program.created_at,
            )
            for program in programs
        ]
        
        # Calculate pagination
        page = (filters.skip // filters.limit) + 1
        has_more = (filters.skip + filters.limit) < total
        
        return ProgramListResponse(
            items=items,
            total=total,
            page=page,
            page_size=filters.limit,
            has_more=has_more,
        )
    
    # ==================== Session CRUD ====================
    
    async def add_session(
        self,
        program_id: UUID,
        session_data: SessionCreate,
        user: User,
    ) -> SessionResponse:
        """Add a new session to a program.
        
        Args:
            program_id: Program ID to add session to
            session_data: Session creation data
            user: User adding the session
            
        Returns:
            SessionResponse: Created session
            
        Raises:
            HTTPException: If program not found, unauthorized, or validation fails
        """
        logger.info(f"Adding session to program {program_id} by user {user.id}")
        
        # Get and verify program ownership
        program = await self.program_repo.get_by_id(
            program_id,
            org_id=user.organization_id,
        )
        
        if program is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Program not found",
            )
        
        await self._verify_program_ownership(program, user)
        
        # Validate exercises exist
        await self._validate_session_exercises([session_data], user)
        
        # Create workout exercises
        exercises = [
            WorkoutExercise(
                exercise_id=ex.exercise_id,
                sets=ex.sets,
                order_in_session=ex.order_in_session,
                notes=ex.notes,
            )
            for ex in session_data.exercises
        ]
        
        # Create session entity
        session = WorkoutSession(
            program_id=program_id,
            name=session_data.name,
            day_number=session_data.day_number,
            order_in_program=session_data.order_in_program,
            exercises=exercises,
        )
        
        # Persist to database
        created_session = await self.program_repo.create_session(session)
        
        logger.info(f"Successfully added session {created_session.id}")
        
        return await self._session_to_response(created_session, user)
    
    async def update_session(
        self,
        session_id: UUID,
        session_data: SessionUpdate,
        user: User,
    ) -> SessionResponse:
        """Update a workout session.
        
        Args:
            session_id: Session ID to update
            session_data: Update data
            user: User updating the session
            
        Returns:
            SessionResponse: Updated session
            
        Raises:
            HTTPException: If not found, unauthorized, or validation fails
        """
        logger.info(f"Updating session {session_id} by user {user.id}")
        
        # Get session
        session = await self.program_repo.get_session_by_id(session_id)
        
        if session is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found",
            )
        
        # Verify program ownership
        program = await self.program_repo.get_by_id(
            session.program_id,
            org_id=user.organization_id,
        )
        
        if program is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Program not found",
            )
        
        await self._verify_program_ownership(program, user)
        
        # Prepare update data
        update_data = {}
        if session_data.name is not None:
            update_data["name"] = session_data.name
        if session_data.day_number is not None:
            update_data["day_number"] = session_data.day_number
        if session_data.order_in_program is not None:
            update_data["order_in_program"] = session_data.order_in_program
        if session_data.exercises is not None:
            # Validate exercises
            await self._validate_session_exercises([session_data], user)
            
            # Convert to dict format for JSONB
            exercises_data = [
                {
                    "exercise_id": str(ex.exercise_id),
                    "sets": ex.sets,
                    "order_in_session": ex.order_in_session,
                    "notes": ex.notes,
                }
                for ex in session_data.exercises
            ]
            update_data["exercises"] = exercises_data
            
            # Recalculate total sets
            update_data["total_sets"] = sum(ex.sets for ex in session_data.exercises)
        
        if not update_data:
            # No changes, return current session
            return await self._session_to_response(session, user)
        
        # Update session
        updated_session = await self.program_repo.update_session(
            session_id,
            update_data,
        )
        
        if updated_session is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found",
            )
        
        logger.info(f"Successfully updated session {session_id}")
        
        return await self._session_to_response(updated_session, user)
    
    async def delete_session(
        self,
        session_id: UUID,
        user: User,
    ) -> bool:
        """Delete a workout session.
        
        Args:
            session_id: Session ID to delete
            user: User deleting the session
            
        Returns:
            bool: True if deleted
            
        Raises:
            HTTPException: If not found or unauthorized
        """
        logger.info(f"Deleting session {session_id} by user {user.id}")
        
        # Get session
        session = await self.program_repo.get_session_by_id(session_id)
        
        if session is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found",
            )
        
        # Verify program ownership
        program = await self.program_repo.get_by_id(
            session.program_id,
            org_id=user.organization_id,
        )
        
        if program is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Program not found",
            )
        
        await self._verify_program_ownership(program, user)
        
        # Delete session
        deleted = await self.program_repo.delete_session(session_id)
        
        if deleted:
            logger.info(f"Successfully deleted session {session_id}")
        
        return deleted
    
    # ==================== Statistics ====================
    
    async def get_program_stats(
        self,
        program_id: UUID,
        user: User,
    ) -> ProgramStatsResponse:
        """Calculate program statistics including volume per muscle.
        
        Args:
            program_id: Program ID
            user: User requesting stats
            
        Returns:
            ProgramStatsResponse: Program statistics
            
        Raises:
            HTTPException: If not found or unauthorized
        """
        program = await self.program_repo.get_by_id(
            program_id,
            org_id=user.organization_id,
        )
        
        if program is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Program not found",
            )
        
        return await self._calculate_program_stats(program, user)
    
    # ==================== Helper Methods ====================
    
    async def _check_program_creation_permission(self, user: User) -> None:
        """Check if user has permission to create programs.
        
        Requires Pro tier or admin role.
        
        Args:
            user: User to check
            
        Raises:
            HTTPException: If user lacks permission
        """
        # Get organization to check subscription
        org = await self.org_repo.get_by_id(user.organization_id)
        
        if org is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Organization not found",
            )
        
        # Allow admins and Pro tier
        if not user.is_admin and org.subscription_tier != SubscriptionTier.PRO:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Pro subscription required to create custom programs",
            )
    
    async def _verify_program_ownership(
        self,
        program: TrainingProgram,
        user: User,
    ) -> None:
        """Verify user owns or has access to program.
        
        Args:
            program: Program to check
            user: User to verify
            
        Raises:
            HTTPException: If user doesn't own program
        """
        # Templates can't be modified
        if program.is_template:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot modify template programs",
            )
        
        # Check organization ownership
        if program.organization_id != user.organization_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to modify this program",
            )
    
    def _parse_structure_config(
        self,
        structure_type: StructureType,
        structure_config: dict,
    ) -> WeeklyStructure | CyclicStructure:
        """Parse and validate structure configuration.
        
        Args:
            structure_type: Type of structure
            structure_config: Configuration dict
            
        Returns:
            WeeklyStructure | CyclicStructure: Parsed configuration
            
        Raises:
            HTTPException: If validation fails
        """
        try:
            if structure_type == StructureType.WEEKLY:
                return WeeklyStructure(**structure_config.model_dump())
            else:
                return CyclicStructure(**structure_config.model_dump())
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid structure configuration: {str(e)}",
            )
    
    async def _validate_session_exercises(
        self,
        sessions: list[SessionCreate | SessionUpdate],
        user: User,
    ) -> None:
        """Validate that all exercises exist and are accessible.
        
        Args:
            sessions: Sessions containing exercises to validate
            user: User for authorization
            
        Raises:
            HTTPException: If any exercise is invalid
        """
        # Collect all exercise IDs
        exercise_ids = set()
        for session in sessions:
            if hasattr(session, 'exercises') and session.exercises:
                exercise_ids.update(ex.exercise_id for ex in session.exercises)
        
        if not exercise_ids:
            return
        
        # Validate exercises exist and are accessible
        for exercise_id in exercise_ids:
            exercise = await self.exercise_repo.get_by_id(
                exercise_id,
                org_id=user.organization_id,
            )
            
            if exercise is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Exercise {exercise_id} not found or not accessible",
                )
    
    async def _calculate_program_stats(
        self,
        program: TrainingProgram,
        user: User,
    ) -> ProgramStatsResponse:
        """Calculate comprehensive program statistics.
        
        Args:
            program: Program to calculate stats for
            user: User for exercise data access
            
        Returns:
            ProgramStatsResponse: Calculated statistics
        """
        # Get all exercises with contributions
        exercise_contributions = await self._get_exercise_contributions(program, user)
        
        # Calculate weekly volume
        weekly_volume = program.get_total_weekly_volume(exercise_contributions)
        
        # Convert to response format
        volume_responses = []
        for muscle, sets_per_week in weekly_volume.items():
            status = self._get_volume_status(sets_per_week)
            volume_responses.append(
                MuscleVolumeResponse(
                    muscle=muscle.value,
                    muscle_name=muscle.display_name,
                    sets_per_week=sets_per_week,
                    status=status,
                )
            )
        
        # Calculate totals
        total_sessions = len(program.sessions)
        total_sets = sum(session.total_sets for session in program.sessions)
        avg_sets_per_session = total_sets / total_sessions if total_sessions > 0 else 0
        
        # Calculate training frequency
        if program.structure_type == StructureType.WEEKLY:
            training_frequency = program.structure_config.days_per_week
        else:
            training_frequency = program.structure_config.weekly_frequency
        
        return ProgramStatsResponse(
            total_sessions=total_sessions,
            total_sets=total_sets,
            avg_sets_per_session=round(avg_sets_per_session, 1),
            weekly_volume=volume_responses,
            training_frequency=round(training_frequency, 1),
        )
    
    async def _get_exercise_contributions(
        self,
        program: TrainingProgram,
        user: User,
    ) -> dict[UUID, dict[MuscleGroup, float]]:
        """Get muscle contributions for all exercises in program.
        
        Args:
            program: Program containing exercises
            user: User for authorization
            
        Returns:
            dict: Mapping of exercise_id to muscle contributions
        """
        # Collect all exercise IDs
        exercise_ids = set()
        for session in program.sessions:
            exercise_ids.update(ex.exercise_id for ex in session.exercises)
        
        # Fetch exercises
        contributions = {}
        for exercise_id in exercise_ids:
            exercise = await self.exercise_repo.get_by_id(
                exercise_id,
                org_id=user.organization_id,
            )
            
            if exercise:
                # Convert MuscleGroup enum to contribution values
                contributions[exercise_id] = {
                    muscle: contribution.value
                    for muscle, contribution in exercise.muscle_contributions.items()
                }
        
        return contributions
    
    async def _get_volume_warnings(
        self,
        program: TrainingProgram,
        user: User,
    ) -> list[str]:
        """Get volume warnings for the program.
        
        Args:
            program: Program to check
            user: User for exercise data access
            
        Returns:
            list[str]: Warning messages
        """
        exercise_contributions = await self._get_exercise_contributions(program, user)
        return program.get_volume_warnings(exercise_contributions)
    
    def _get_volume_status(self, sets_per_week: float) -> str:
        """Determine volume status based on sets per week.
        
        Args:
            sets_per_week: Weekly volume for muscle
            
        Returns:
            str: Status (low/optimal/high/excessive)
        """
        if sets_per_week < 10:
            return "low"
        elif sets_per_week <= 20:
            return "optimal"
        elif sets_per_week <= 25:
            return "high"
        else:
            return "excessive"
    
    async def _program_to_response(
        self,
        program: TrainingProgram,
        stats: ProgramStatsResponse,
    ) -> ProgramResponse:
        """Convert program entity to response DTO.
        
        Args:
            program: Program entity
            stats: Calculated statistics
            
        Returns:
            ProgramResponse: Response DTO
        """
        # Convert sessions
        session_responses = []
        for session in program.sessions:
            session_responses.append(
                SessionResponse(
                    id=session.id,
                    program_id=session.program_id,
                    name=session.name,
                    day_number=session.day_number,
                    order_in_program=session.order_in_program,
                    exercises=[
                        WorkoutExerciseResponse(
                            exercise_id=ex.exercise_id,
                            exercise_name=None,  # Could be populated if needed
                            sets=ex.sets,
                            order_in_session=ex.order_in_session,
                            notes=ex.notes,
                        )
                        for ex in session.exercises
                    ],
                    total_sets=session.total_sets,
                    exercise_count=len(session.exercises),
                    created_at=session.created_at,
                    updated_at=session.updated_at,
                )
            )
        
        return ProgramResponse(
            id=program.id,
            name=program.name,
            description=program.description,
            split_type=program.split_type.value,
            structure_type=program.structure_type.value,
            structure_config=program.structure_config.model_dump(),
            is_template=program.is_template,
            created_by_user_id=program.created_by_user_id,
            organization_id=program.organization_id,
            duration_weeks=program.duration_weeks,
            sessions=session_responses,
            stats=stats,
            created_at=program.created_at,
            updated_at=program.updated_at,
        )
    
    async def _session_to_response(
        self,
        session: WorkoutSession,
        user: User,
    ) -> SessionResponse:
        """Convert session entity to response DTO.
        
        Args:
            session: Session entity
            user: User for exercise name lookup
            
        Returns:
            SessionResponse: Response DTO
        """
        # Get exercise names
        exercises = []
        for ex in session.exercises:
            exercise = await self.exercise_repo.get_by_id(
                ex.exercise_id,
                org_id=user.organization_id,
            )
            
            exercises.append(
                WorkoutExerciseResponse(
                    exercise_id=ex.exercise_id,
                    exercise_name=exercise.name if exercise else None,
                    sets=ex.sets,
                    order_in_session=ex.order_in_session,
                    notes=ex.notes,
                )
            )
        
        return SessionResponse(
            id=session.id,
            program_id=session.program_id,
            name=session.name,
            day_number=session.day_number,
            order_in_program=session.order_in_program,
            exercises=exercises,
            total_sets=session.total_sets,
            exercise_count=len(session.exercises),
            created_at=session.created_at,
            updated_at=session.updated_at,
        )
