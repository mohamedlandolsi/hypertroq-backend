"""Training Program Entity.

Represents a complete training program with sessions, schedule, and volume tracking.
"""

from datetime import date, datetime, timedelta
from typing import Any
from uuid import UUID

from pydantic import BaseModel

from app.domain.entities.base import Entity
from app.domain.entities.training_split import TrainingSplitType
from app.domain.entities.training_structure import (
    CyclicStructure,
    StructureType,
    WeeklyStructure,
)
from app.domain.entities.workout_session import WorkoutSession
from app.domain.value_objects.muscle_groups import MuscleGroup


class ScheduledSession(BaseModel):
    """Value object representing a scheduled workout session.
    
    Links a workout session to a specific date in the program schedule.
    
    Attributes:
        session_id: Reference to WorkoutSession
        session_name: Name of the session for display
        scheduled_date: Date when session should be performed
        day_of_week: Day abbreviation (MON, TUE, etc.) for weekly, or None for cyclic
        cycle_day: Day number in cycle for cyclic structure, or None for weekly
    """
    
    session_id: UUID
    session_name: str
    scheduled_date: date
    day_of_week: str | None = None
    cycle_day: int | None = None
    
    class Config:
        """Pydantic model configuration."""
        frozen = True


class TrainingProgram(Entity):
    """Training program entity representing a complete hypertrophy program.
    
    A training program combines a split type (how muscles are divided),
    a structure (when workouts occur), and workout sessions (what exercises to do).
    
    Programs can be:
    - Templates: Admin-created, available to all (is_template=True)
    - User Programs: Created by users or cloned from templates (is_template=False)
    
    Business Rules:
        - Templates must not have organization_id or created_by_user_id
        - User programs must have organization_id
        - Number of sessions should align with split type and structure
        - Total weekly volume per muscle should be 10-25 sets for hypertrophy
        - Program duration should be reasonable (typically 4-12 weeks)
        - Sessions must have unique day_numbers and order_in_program
    
    Examples:
        >>> program = TrainingProgram(
        ...     name="Upper/Lower 4-Day Split",
        ...     split_type=TrainingSplitType.UPPER_LOWER,
        ...     structure_type=StructureType.WEEKLY,
        ...     structure_config=WeeklyStructure(
        ...         days_per_week=4,
        ...         selected_days=["MON", "TUE", "THU", "FRI"]
        ...     ),
        ...     sessions=[...],
        ...     is_template=True
        ... )
    """
    
    def __init__(
        self,
        name: str,
        split_type: TrainingSplitType,
        structure_type: StructureType,
        structure_config: WeeklyStructure | CyclicStructure,
        sessions: list[WorkoutSession],
        description: str = "",
        is_template: bool = False,
        created_by_user_id: UUID | None = None,
        organization_id: UUID | None = None,
        duration_weeks: int | None = None,
        id: UUID | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ):
        """Initialize TrainingProgram entity.
        
        Args:
            name: Program name (e.g., "Upper/Lower 4-Day Split")
            split_type: Type of training split
            structure_type: Weekly or cyclic structure
            structure_config: Configuration for schedule structure
            sessions: List of workout sessions in program
            description: Program description and notes
            is_template: True for admin templates, False for user programs
            created_by_user_id: User who created program (None for templates)
            organization_id: Organization owning program (None for templates)
            duration_weeks: Recommended program duration in weeks
            id: Unique identifier (auto-generated if None)
            created_at: Creation timestamp
            updated_at: Last update timestamp
            
        Raises:
            ValueError: If validation fails
        """
        super().__init__(id)
        
        if created_at:
            self._created_at = created_at
        if updated_at:
            self._updated_at = updated_at
        
        self._name = name.strip()
        self._description = description.strip()
        self._split_type = split_type
        self._structure_type = structure_type
        self._structure_config = structure_config
        self._sessions = sessions
        self._is_template = is_template
        self._created_by_user_id = created_by_user_id
        self._organization_id = organization_id
        self._duration_weeks = duration_weeks
        
        # Validate on initialization
        self._validate_program()
    
    # ==================== Properties ====================
    
    @property
    def name(self) -> str:
        """Program name."""
        return self._name
    
    @property
    def description(self) -> str:
        """Program description."""
        return self._description
    
    @property
    def split_type(self) -> TrainingSplitType:
        """Type of training split."""
        return self._split_type
    
    @property
    def structure_type(self) -> StructureType:
        """Structure type (weekly or cyclic)."""
        return self._structure_type
    
    @property
    def structure_config(self) -> WeeklyStructure | CyclicStructure:
        """Structure configuration."""
        return self._structure_config
    
    @property
    def sessions(self) -> list[WorkoutSession]:
        """List of workout sessions (copy to maintain immutability)."""
        return self._sessions.copy()
    
    @property
    def is_template(self) -> bool:
        """True if admin template, False if user program."""
        return self._is_template
    
    @property
    def created_by_user_id(self) -> UUID | None:
        """User who created program (None for templates)."""
        return self._created_by_user_id
    
    @property
    def organization_id(self) -> UUID | None:
        """Organization owning program (None for templates)."""
        return self._organization_id
    
    @property
    def duration_weeks(self) -> int | None:
        """Recommended program duration in weeks."""
        return self._duration_weeks
    
    @property
    def session_count(self) -> int:
        """Number of sessions in program."""
        return len(self._sessions)
    
    # ==================== Business Logic Methods ====================
    
    def generate_schedule(
        self,
        start_date: date,
        weeks: int | None = None
    ) -> list[ScheduledSession]:
        """Generate a training schedule with specific dates.
        
        Creates a schedule by mapping workout sessions to calendar dates
        based on the program's structure type and configuration.
        
        Args:
            start_date: Starting date for the schedule
            weeks: Number of weeks to generate (uses duration_weeks if not provided)
            
        Returns:
            list[ScheduledSession]: Scheduled sessions with dates
            
        Examples:
            >>> program.generate_schedule(date(2025, 1, 6), weeks=4)
            [
                ScheduledSession(
                    session_id=UUID("..."),
                    session_name="Upper Body A",
                    scheduled_date=date(2025, 1, 6),
                    day_of_week="MON"
                ),
                ...
            ]
            
        Raises:
            ValueError: If sessions don't align with structure
        """
        if weeks is None:
            weeks = self._duration_weeks or 4
        
        scheduled_sessions: list[ScheduledSession] = []
        
        if self._structure_type == StructureType.WEEKLY:
            scheduled_sessions = self._generate_weekly_schedule(start_date, weeks)
        elif self._structure_type == StructureType.CYCLIC:
            scheduled_sessions = self._generate_cyclic_schedule(start_date, weeks)
        
        return scheduled_sessions
    
    def _generate_weekly_schedule(self, start_date: date, weeks: int) -> list[ScheduledSession]:
        """Generate schedule for weekly structure.
        
        Args:
            start_date: Starting date
            weeks: Number of weeks
            
        Returns:
            list[ScheduledSession]: Scheduled sessions
        """
        if not isinstance(self._structure_config, WeeklyStructure):
            raise ValueError("Structure config must be WeeklyStructure for weekly programs")
        
        # Generate base schedule from structure
        base_schedule = self._structure_config.generate_schedule(start_date, weeks)
        
        # Map sessions to days
        # Sessions are cycled through the training days
        session_cycle = sorted(self._sessions, key=lambda s: s.order_in_program)
        scheduled_sessions: list[ScheduledSession] = []
        
        for idx, (schedule_date, day_abbr) in enumerate(base_schedule):
            # Cycle through sessions
            session = session_cycle[idx % len(session_cycle)]
            
            scheduled_sessions.append(
                ScheduledSession(
                    session_id=session.id,
                    session_name=session.name,
                    scheduled_date=schedule_date,
                    day_of_week=day_abbr,
                    cycle_day=None,
                )
            )
        
        return scheduled_sessions
    
    def _generate_cyclic_schedule(self, start_date: date, weeks: int) -> list[ScheduledSession]:
        """Generate schedule for cyclic structure.
        
        Args:
            start_date: Starting date
            weeks: Number of weeks
            
        Returns:
            list[ScheduledSession]: Scheduled sessions
        """
        if not isinstance(self._structure_config, CyclicStructure):
            raise ValueError("Structure config must be CyclicStructure for cyclic programs")
        
        # Generate base schedule from structure
        base_schedule = self._structure_config.generate_schedule(start_date, weeks)
        
        # Map sessions to training days
        session_cycle = sorted(self._sessions, key=lambda s: s.order_in_program)
        scheduled_sessions: list[ScheduledSession] = []
        
        training_day_count = 0
        for schedule_date, cycle_day, is_training in base_schedule:
            if is_training:
                # Cycle through sessions
                session = session_cycle[training_day_count % len(session_cycle)]
                
                scheduled_sessions.append(
                    ScheduledSession(
                        session_id=session.id,
                        session_name=session.name,
                        scheduled_date=schedule_date,
                        day_of_week=None,
                        cycle_day=cycle_day,
                    )
                )
                
                training_day_count += 1
        
        return scheduled_sessions
    
    def clone_from_template(
        self,
        user_id: UUID,
        organization_id: UUID,
        new_name: str | None = None,
    ) -> "TrainingProgram":
        """Clone this program for a user (typically from a template).
        
        Creates a new program instance with the same structure and sessions,
        but owned by the specified user and organization.
        
        Args:
            user_id: ID of user creating the clone
            organization_id: ID of user's organization
            new_name: Optional custom name (defaults to "My {template_name}")
            
        Returns:
            TrainingProgram: New program instance
            
        Examples:
            >>> template = get_template("Upper/Lower Split")
            >>> my_program = template.clone_from_template(
            ...     user_id=user.id,
            ...     organization_id=user.organization_id,
            ...     new_name="My Custom Upper/Lower"
            ... )
        """
        # Clone sessions (create new instances with new IDs)
        cloned_sessions = []
        for session in self._sessions:
            cloned_session = WorkoutSession(
                program_id=None,  # Will be set when program is created
                name=session.name,
                day_number=session.day_number,
                order_in_program=session.order_in_program,
                exercises=session.exercises,  # Exercises are value objects, safe to reuse
            )
            cloned_sessions.append(cloned_session)
        
        # Create cloned program
        clone_name = new_name or f"My {self._name}"
        
        cloned_program = TrainingProgram(
            name=clone_name,
            description=self._description,
            split_type=self._split_type,
            structure_type=self._structure_type,
            structure_config=self._structure_config,
            sessions=cloned_sessions,
            is_template=False,
            created_by_user_id=user_id,
            organization_id=organization_id,
            duration_weeks=self._duration_weeks,
        )
        
        # Update session program_ids
        for session in cloned_sessions:
            session._program_id = cloned_program.id
        
        return cloned_program
    
    def validate_program(self) -> bool:
        """Validate program meets all business rules.
        
        Returns:
            bool: True if valid
            
        Raises:
            ValueError: If validation fails
        """
        self._validate_program()
        return True
    
    def get_total_weekly_volume(
        self,
        exercise_contributions: dict[UUID, dict[MuscleGroup, float]]
    ) -> dict[MuscleGroup, float]:
        """Calculate total weekly volume per muscle group.
        
        Sums volume across all sessions and divides by program cycle length
        to get average weekly volume.
        
        Args:
            exercise_contributions: Mapping of exercise_id to muscle contributions
                Example: {
                    UUID("bench-press"): {MuscleGroup.CHEST: 1.0, MuscleGroup.TRICEPS: 0.75}
                }
        
        Returns:
            dict[MuscleGroup, float]: Average weekly volume per muscle
            
        Examples:
            >>> volume = program.get_total_weekly_volume(contributions)
            >>> volume[MuscleGroup.CHEST]
            16.0  # Sets per week
        """
        # Calculate total volume across all sessions
        total_volume: dict[MuscleGroup, float] = {}
        
        for session in self._sessions:
            session_volume = session.calculate_muscle_volume(exercise_contributions)
            for muscle, volume in session_volume.items():
                total_volume[muscle] = total_volume.get(muscle, 0.0) + volume
        
        # Adjust for cycle length if needed
        if self._structure_type == StructureType.WEEKLY:
            # Volume is already per week cycle
            return total_volume
        elif self._structure_type == StructureType.CYCLIC:
            # Convert to weekly volume
            if isinstance(self._structure_config, CyclicStructure):
                cycle_length = self._structure_config.cycle_length
                weeks_per_cycle = cycle_length / 7.0
                
                weekly_volume = {
                    muscle: volume / weeks_per_cycle
                    for muscle, volume in total_volume.items()
                }
                return weekly_volume
        
        return total_volume
    
    def get_session_by_day(self, day_number: int) -> WorkoutSession | None:
        """Get session by day number.
        
        Args:
            day_number: Day number to find
            
        Returns:
            WorkoutSession | None: Session if found, else None
        """
        for session in self._sessions:
            if session.day_number == day_number:
                return session
        return None
    
    def get_sessions_ordered(self) -> list[WorkoutSession]:
        """Get sessions sorted by order_in_program.
        
        Returns:
            list[WorkoutSession]: Ordered sessions
        """
        return sorted(self._sessions, key=lambda s: s.order_in_program)
    
    def get_volume_warnings(
        self,
        exercise_contributions: dict[UUID, dict[MuscleGroup, float]]
    ) -> list[str]:
        """Get warnings about volume being too low or too high.
        
        Args:
            exercise_contributions: Exercise muscle contributions
            
        Returns:
            list[str]: Warning messages
        """
        warnings: list[str] = []
        weekly_volume = self.get_total_weekly_volume(exercise_contributions)
        
        for muscle, volume in weekly_volume.items():
            if volume < 10:
                warnings.append(
                    f"{muscle.display_name}: {volume:.1f} sets/week (minimum 10 recommended for hypertrophy)"
                )
            elif volume > 25:
                warnings.append(
                    f"{muscle.display_name}: {volume:.1f} sets/week (may exceed recovery capacity, max 25 recommended)"
                )
        
        return warnings
    
    # ==================== Update Methods ====================
    
    def update_details(
        self,
        name: str | None = None,
        description: str | None = None,
        duration_weeks: int | None = None,
    ) -> None:
        """Update program details.
        
        Args:
            name: New program name
            description: New description
            duration_weeks: New duration
            
        Raises:
            ValueError: If validation fails
        """
        if name is not None:
            self._name = name.strip()
            if not self._name:
                raise ValueError("Program name cannot be empty")
        
        if description is not None:
            self._description = description.strip()
        
        if duration_weeks is not None:
            if duration_weeks < 1:
                raise ValueError("duration_weeks must be at least 1")
            if duration_weeks > 52:
                raise ValueError("duration_weeks should not exceed 52 (1 year)")
            self._duration_weeks = duration_weeks
        
        self._updated_at = datetime.utcnow()
    
    def update_sessions(self, sessions: list[WorkoutSession]) -> None:
        """Update program sessions.
        
        Args:
            sessions: New list of sessions
            
        Raises:
            ValueError: If validation fails
        """
        self._sessions = sessions
        self._validate_program()
        self._updated_at = datetime.utcnow()
    
    def add_session(self, session: WorkoutSession) -> None:
        """Add a session to the program.
        
        Args:
            session: Session to add
            
        Raises:
            ValueError: If validation fails
        """
        self._sessions.append(session)
        self._validate_program()
        self._updated_at = datetime.utcnow()
    
    def remove_session(self, session_id: UUID) -> None:
        """Remove a session from the program.
        
        Args:
            session_id: ID of session to remove
            
        Raises:
            ValueError: If session not found or would leave program with no sessions
        """
        if len(self._sessions) <= 1:
            raise ValueError("Cannot remove last session from program")
        
        original_count = len(self._sessions)
        self._sessions = [s for s in self._sessions if s.id != session_id]
        
        if len(self._sessions) == original_count:
            raise ValueError(f"Session {session_id} not found in program")
        
        self._validate_program()
        self._updated_at = datetime.utcnow()
    
    # ==================== Validation ====================
    
    def _validate_program(self) -> None:
        """Validate program meets all business rules.
        
        Rules:
            1. Name must not be empty
            2. Must have at least one session
            3. Session day_numbers must be unique
            4. Session order_in_program must be unique and sequential
            5. Structure config must match structure type
            6. Templates must not have organization_id or created_by_user_id
            7. User programs must have organization_id
            8. Duration weeks must be reasonable
            9. Number of sessions should align with structure frequency
            
        Raises:
            ValueError: If validation fails
        """
        # Validate name
        if not self._name:
            raise ValueError("Program name cannot be empty")
        
        # Validate sessions exist
        if not self._sessions:
            raise ValueError("Program must have at least one session")
        
        # Validate session day numbers are unique
        day_numbers = [s.day_number for s in self._sessions]
        if len(day_numbers) != len(set(day_numbers)):
            raise ValueError("Session day_numbers must be unique")
        
        # Validate session ordering
        orders = [s.order_in_program for s in self._sessions]
        if len(orders) != len(set(orders)):
            raise ValueError("Session order_in_program values must be unique")
        
        # Validate structure config matches structure type
        if self._structure_type == StructureType.WEEKLY:
            if not isinstance(self._structure_config, WeeklyStructure):
                raise ValueError("Structure config must be WeeklyStructure for WEEKLY type")
        elif self._structure_type == StructureType.CYCLIC:
            if not isinstance(self._structure_config, CyclicStructure):
                raise ValueError("Structure config must be CyclicStructure for CYCLIC type")
        
        # Validate template constraints
        if self._is_template:
            if self._organization_id is not None:
                raise ValueError("Template programs cannot have organization_id")
            if self._created_by_user_id is not None:
                raise ValueError("Template programs cannot have created_by_user_id")
        else:
            if self._organization_id is None:
                raise ValueError("User programs must have organization_id")
        
        # Validate duration weeks
        if self._duration_weeks is not None:
            if self._duration_weeks < 1:
                raise ValueError("duration_weeks must be at least 1")
            if self._duration_weeks > 52:
                raise ValueError("duration_weeks should not exceed 52 weeks")
        
        # Validate session count aligns with structure
        self._validate_session_structure_alignment()
    
    def _validate_session_structure_alignment(self) -> None:
        """Validate that session count aligns with structure.
        
        Raises:
            ValueError: If sessions don't align with structure
        """
        session_count = len(self._sessions)
        
        if self._structure_type == StructureType.WEEKLY:
            if isinstance(self._structure_config, WeeklyStructure):
                days_per_week = self._structure_config.days_per_week
                # Sessions should be a factor or multiple of days per week
                if session_count > days_per_week * 2:
                    import warnings
                    warnings.warn(
                        f"Program has {session_count} sessions but only {days_per_week} "
                        "training days per week. Sessions will cycle.",
                        UserWarning
                    )
        
        elif self._structure_type == StructureType.CYCLIC:
            if isinstance(self._structure_config, CyclicStructure):
                days_on = self._structure_config.days_on
                if session_count > days_on * 2:
                    import warnings
                    warnings.warn(
                        f"Program has {session_count} sessions but only {days_on} "
                        "consecutive training days. Sessions will cycle.",
                        UserWarning
                    )
    
    # ==================== Equality & Representation ====================
    
    def __str__(self) -> str:
        """String representation."""
        template_str = " (Template)" if self._is_template else ""
        return (
            f"{self._name}{template_str} - {self._split_type} "
            f"({len(self._sessions)} sessions, {self._structure_type})"
        )
    
    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return (
            f"TrainingProgram(id={self.id}, name='{self._name}', "
            f"split={self._split_type.name}, sessions={len(self._sessions)}, "
            f"is_template={self._is_template})"
        )
