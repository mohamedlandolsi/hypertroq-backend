"""Workout Session Entity.

Represents a single workout session within a training program, containing
exercises and their volume contributions.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from app.domain.entities.base import Entity
from app.domain.entities.workout_exercise import WorkoutExercise
from app.domain.value_objects.muscle_groups import MuscleGroup


class WorkoutSession(Entity):
    """Workout session entity representing a single training session.
    
    A workout session is part of a training program and contains a list of
    exercises with their sets. It calculates total volume distributed across
    muscle groups based on exercise contributions.
    
    Business Rules:
        - Session must belong to a program
        - Session must have a unique name within the program
        - Exercises must be ordered (order_in_session)
        - Total sets should be reasonable (typically 10-25 per session)
        - Volume per muscle should not exceed 10 sets in a single session
    
    Attributes:
        program_id: Reference to the parent training program
        name: Session name (e.g., "Upper Body A", "Push Day 1")
        day_number: Day number in program sequence (1-indexed)
        order_in_program: Order of this session in the program
        exercises: List of exercises in this session
        
    Examples:
        >>> session = WorkoutSession(
        ...     program_id=UUID("..."),
        ...     name="Upper Body A",
        ...     day_number=1,
        ...     order_in_program=1,
        ...     exercises=[
        ...         WorkoutExercise(exercise_id=UUID("..."), sets=4, order_in_session=1),
        ...         WorkoutExercise(exercise_id=UUID("..."), sets=3, order_in_session=2),
        ...     ]
        ... )
        >>> session.calculate_total_sets()
        7
    """
    
    def __init__(
        self,
        program_id: UUID,
        name: str,
        day_number: int,
        order_in_program: int,
        exercises: list[WorkoutExercise],
        id: UUID | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ):
        """Initialize WorkoutSession entity.
        
        Args:
            program_id: Reference to parent training program
            name: Session name (e.g., "Upper Body A")
            day_number: Day number in program sequence (1-indexed)
            order_in_program: Order of this session in program
            exercises: List of exercises in session
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
        
        self._program_id = program_id
        self._name = name.strip()
        self._day_number = day_number
        self._order_in_program = order_in_program
        self._exercises = exercises
        
        # Validate on initialization
        self._validate_session()
    
    # ==================== Properties ====================
    
    @property
    def program_id(self) -> UUID:
        """Parent training program ID."""
        return self._program_id
    
    @property
    def name(self) -> str:
        """Session name."""
        return self._name
    
    @property
    def day_number(self) -> int:
        """Day number in program sequence (1-indexed)."""
        return self._day_number
    
    @property
    def order_in_program(self) -> int:
        """Order of this session in the program."""
        return self._order_in_program
    
    @property
    def exercises(self) -> list[WorkoutExercise]:
        """List of exercises in session (copy to maintain immutability)."""
        return self._exercises.copy()
    
    @property
    def total_sets(self) -> int:
        """Calculate total number of sets in session."""
        return self.calculate_total_sets()
    
    @property
    def muscle_volume(self) -> dict[MuscleGroup, float]:
        """Calculate volume distribution across muscle groups."""
        return self.calculate_muscle_volume({})
    
    # ==================== Business Logic Methods ====================
    
    def calculate_total_sets(self) -> int:
        """Calculate total number of sets across all exercises.
        
        Returns:
            int: Sum of sets from all exercises
            
        Examples:
            >>> session.calculate_total_sets()
            15  # 4 + 3 + 4 + 4
        """
        return sum(exercise.sets for exercise in self._exercises)
    
    def calculate_muscle_volume(
        self,
        exercise_contributions: dict[UUID, dict[MuscleGroup, float]]
    ) -> dict[MuscleGroup, float]:
        """Calculate volume contribution to each muscle group.
        
        This method requires exercise contribution data to calculate accurate
        muscle-specific volume. Each exercise contributes fractionally to
        different muscle groups based on its muscle_contributions mapping.
        
        Args:
            exercise_contributions: Mapping of exercise_id to muscle contributions
                Example: {
                    UUID("bench-press"): {MuscleGroup.CHEST: 1.0, MuscleGroup.TRICEPS: 0.75},
                    UUID("rows"): {MuscleGroup.LATS: 1.0, MuscleGroup.ELBOW_FLEXORS: 0.5}
                }
        
        Returns:
            dict[MuscleGroup, float]: Mapping of muscle groups to total volume (sets)
            
        Examples:
            >>> contributions = {
            ...     bench_press_id: {MuscleGroup.CHEST: 1.0, MuscleGroup.TRICEPS: 0.75},
            ...     rows_id: {MuscleGroup.LATS: 1.0, MuscleGroup.ELBOW_FLEXORS: 0.5}
            ... }
            >>> session.calculate_muscle_volume(contributions)
            {
                MuscleGroup.CHEST: 4.0,      # 4 sets bench press × 1.0
                MuscleGroup.TRICEPS: 3.0,    # 4 sets bench press × 0.75
                MuscleGroup.LATS: 3.0,       # 3 sets rows × 1.0
                MuscleGroup.ELBOW_FLEXORS: 1.5  # 3 sets rows × 0.5
            }
        """
        muscle_volume: dict[MuscleGroup, float] = {}
        
        for workout_exercise in self._exercises:
            # Get muscle contributions for this exercise
            contributions = exercise_contributions.get(workout_exercise.exercise_id, {})
            
            # Calculate volume contribution to each muscle
            for muscle, contribution in contributions.items():
                volume = workout_exercise.sets * contribution
                muscle_volume[muscle] = muscle_volume.get(muscle, 0.0) + volume
        
        return muscle_volume
    
    def get_exercises_ordered(self) -> list[WorkoutExercise]:
        """Get exercises sorted by order_in_session.
        
        Returns:
            list[WorkoutExercise]: Exercises in workout order
        """
        return sorted(self._exercises, key=lambda e: e.order_in_session)
    
    def get_exercise_count(self) -> int:
        """Get number of exercises in session.
        
        Returns:
            int: Number of exercises
        """
        return len(self._exercises)
    
    def has_exercise(self, exercise_id: UUID) -> bool:
        """Check if session includes a specific exercise.
        
        Args:
            exercise_id: Exercise ID to check
            
        Returns:
            bool: True if exercise is in session
        """
        return any(e.exercise_id == exercise_id for e in self._exercises)
    
    def get_exercise_by_id(self, exercise_id: UUID) -> WorkoutExercise | None:
        """Get exercise instance by exercise_id.
        
        Args:
            exercise_id: Exercise ID to find
            
        Returns:
            WorkoutExercise | None: Exercise if found, else None
        """
        for exercise in self._exercises:
            if exercise.exercise_id == exercise_id:
                return exercise
        return None
    
    def validate_session(self) -> bool:
        """Validate session meets business rules.
        
        Returns:
            bool: True if valid
            
        Raises:
            ValueError: If validation fails
        """
        self._validate_session()
        return True
    
    # ==================== Update Methods ====================
    
    def update_details(
        self,
        name: str | None = None,
        day_number: int | None = None,
        order_in_program: int | None = None,
    ) -> None:
        """Update session details.
        
        Args:
            name: New session name
            day_number: New day number
            order_in_program: New order in program
            
        Raises:
            ValueError: If validation fails
        """
        if name is not None:
            self._name = name.strip()
            if not self._name:
                raise ValueError("Session name cannot be empty")
        
        if day_number is not None:
            if day_number < 1:
                raise ValueError("day_number must be at least 1")
            self._day_number = day_number
        
        if order_in_program is not None:
            if order_in_program < 1:
                raise ValueError("order_in_program must be at least 1")
            self._order_in_program = order_in_program
        
        self._updated_at = datetime.utcnow()
    
    def update_exercises(self, exercises: list[WorkoutExercise]) -> None:
        """Update session exercises.
        
        Args:
            exercises: New list of exercises
            
        Raises:
            ValueError: If validation fails
        """
        self._exercises = exercises
        self._validate_session()
        self._updated_at = datetime.utcnow()
    
    def add_exercise(self, exercise: WorkoutExercise) -> None:
        """Add an exercise to the session.
        
        Args:
            exercise: Exercise to add
            
        Raises:
            ValueError: If validation fails or exercise already exists
        """
        if self.has_exercise(exercise.exercise_id):
            raise ValueError(f"Exercise {exercise.exercise_id} already exists in session")
        
        self._exercises.append(exercise)
        self._validate_session()
        self._updated_at = datetime.utcnow()
    
    def remove_exercise(self, exercise_id: UUID) -> None:
        """Remove an exercise from the session.
        
        Args:
            exercise_id: ID of exercise to remove
            
        Raises:
            ValueError: If exercise not found
        """
        original_count = len(self._exercises)
        self._exercises = [e for e in self._exercises if e.exercise_id != exercise_id]
        
        if len(self._exercises) == original_count:
            raise ValueError(f"Exercise {exercise_id} not found in session")
        
        self._validate_session()
        self._updated_at = datetime.utcnow()
    
    def reorder_exercises(self, exercise_order: list[UUID]) -> None:
        """Reorder exercises based on list of exercise IDs.
        
        Args:
            exercise_order: List of exercise IDs in desired order
            
        Raises:
            ValueError: If exercise_order doesn't match current exercises
        """
        if len(exercise_order) != len(self._exercises):
            raise ValueError("exercise_order must contain all exercises")
        
        # Verify all exercises are present
        current_ids = {e.exercise_id for e in self._exercises}
        new_ids = set(exercise_order)
        if current_ids != new_ids:
            raise ValueError("exercise_order must contain exactly the same exercises")
        
        # Create new ordered list
        exercise_map = {e.exercise_id: e for e in self._exercises}
        new_exercises = []
        
        for order, exercise_id in enumerate(exercise_order, start=1):
            exercise = exercise_map[exercise_id]
            # Create new instance with updated order
            new_exercise = WorkoutExercise(
                exercise_id=exercise.exercise_id,
                sets=exercise.sets,
                order_in_session=order,
                notes=exercise.notes,
            )
            new_exercises.append(new_exercise)
        
        self._exercises = new_exercises
        self._updated_at = datetime.utcnow()
    
    # ==================== Validation ====================
    
    def _validate_session(self) -> None:
        """Validate session meets business rules.
        
        Rules:
            1. Name must not be empty
            2. day_number must be positive
            3. order_in_program must be positive
            4. Exercises can be empty (added later via editor)
            5. If exercises exist, order_in_session must be unique
            6. Total sets should be reasonable (warn if > 30)
            7. No duplicate exercises
            
        Raises:
            ValueError: If validation fails
        """
        # Validate name
        if not self._name:
            raise ValueError("Session name cannot be empty")
        
        # Validate day_number
        if self._day_number < 1:
            raise ValueError("day_number must be at least 1")
        
        # Validate order_in_program
        if self._order_in_program < 1:
            raise ValueError("order_in_program must be at least 1")
        
        # Exercises can be empty - they can be added later via the editor
        # Only validate if exercises exist
        if self._exercises:
            # Validate exercise ordering
            orders = [e.order_in_session for e in self._exercises]
            if len(orders) != len(set(orders)):
                raise ValueError("Exercise order_in_session values must be unique")
            
            # Validate no duplicate exercises
            exercise_ids = [e.exercise_id for e in self._exercises]
            if len(exercise_ids) != len(set(exercise_ids)):
                raise ValueError("Session cannot contain duplicate exercises")
        
        # Warn about excessive total sets
        total_sets = self.calculate_total_sets()
        if total_sets > 30:
            # This is a warning, not an error - some advanced programs may exceed this
            import warnings
            warnings.warn(
                f"Session has {total_sets} total sets, which is quite high. "
                "Consider splitting into multiple sessions.",
                UserWarning
            )
    
    # ==================== Equality & Representation ====================
    
    def __str__(self) -> str:
        """String representation."""
        return (
            f"{self._name} (Day {self._day_number}) - "
            f"{len(self._exercises)} exercises, {self.total_sets} sets"
        )
    
    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return (
            f"WorkoutSession(id={self.id}, name='{self._name}', "
            f"day={self._day_number}, exercises={len(self._exercises)})"
        )
