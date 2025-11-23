"""Workout Exercise Value Object.

Represents an exercise within a workout session, including sets and ordering.
"""

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class WorkoutExercise(BaseModel):
    """Value object for an exercise within a workout session.
    
    Represents a specific exercise that is part of a workout, including
    the number of sets to perform and its position in the workout.
    
    Attributes:
        exercise_id: Reference to the exercise entity
        sets: Number of sets to perform (1-10)
        order_in_session: Position of exercise in workout (1-indexed)
        notes: Optional notes for this specific exercise instance
    
    Examples:
        >>> exercise = WorkoutExercise(
        ...     exercise_id=UUID("..."),
        ...     sets=4,
        ...     order_in_session=1,
        ...     notes="Focus on slow negatives"
        ... )
    """
    
    exercise_id: UUID = Field(description="Reference to exercise entity")
    sets: int = Field(ge=1, le=10, description="Number of sets to perform")
    order_in_session: int = Field(ge=1, description="Position in workout (1-indexed)")
    notes: str | None = Field(default=None, max_length=500, description="Optional exercise notes")
    
    @field_validator("notes")
    @classmethod
    def validate_notes(cls, v: str | None) -> str | None:
        """Validate and clean notes field.
        
        Args:
            v: Notes string or None
            
        Returns:
            str | None: Cleaned notes or None
        """
        if v is not None:
            v = v.strip()
            if not v:
                return None
        return v
    
    @field_validator("order_in_session")
    @classmethod
    def validate_order(cls, v: int) -> int:
        """Validate order_in_session is positive.
        
        Args:
            v: Order value
            
        Returns:
            int: Validated order
            
        Raises:
            ValueError: If order is not positive
        """
        if v < 1:
            raise ValueError("order_in_session must be at least 1")
        return v
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization.
        
        Returns:
            dict: Dictionary representation suitable for JSONB storage
        """
        return {
            "exercise_id": str(self.exercise_id),
            "sets": self.sets,
            "order_in_session": self.order_in_session,
            "notes": self.notes,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorkoutExercise":
        """Create instance from dictionary.
        
        Args:
            data: Dictionary with exercise data
            
        Returns:
            WorkoutExercise: New instance
        """
        return cls(
            exercise_id=UUID(data["exercise_id"]) if isinstance(data["exercise_id"], str) else data["exercise_id"],
            sets=data["sets"],
            order_in_session=data["order_in_session"],
            notes=data.get("notes"),
        )
    
    def __str__(self) -> str:
        """String representation."""
        notes_str = f" ({self.notes})" if self.notes else ""
        return f"Exercise {self.exercise_id}: {self.sets} sets{notes_str}"
    
    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return (
            f"WorkoutExercise(exercise_id={self.exercise_id}, sets={self.sets}, "
            f"order={self.order_in_session})"
        )
    
    class Config:
        """Pydantic model configuration."""
        frozen = True  # Make immutable (value object)
