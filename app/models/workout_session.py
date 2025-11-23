"""
Workout Session SQLAlchemy model for database persistence.

Stores workout sessions with their exercises as JSONB array.
"""

from typing import Any
from uuid import UUID

from sqlalchemy import ForeignKey, Index, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import BaseModel


class WorkoutSessionModel(BaseModel):
    """
    SQLAlchemy model for WorkoutSession entity.
    
    Represents a single workout session within a training program.
    Contains exercises stored as JSONB array for flexibility.
    
    Table Structure:
        - workout_sessions (main table)
        - Indexes: program_id, day_number, order_in_program
        - JSONB storage for exercises array
    
    Database Schema:
        {
            "id": "uuid",
            "program_id": "uuid",
            "name": "Upper Body A",
            "day_number": 1,
            "order_in_program": 1,
            "exercises": [
                {
                    "exercise_id": "uuid",
                    "sets": 4,
                    "order_in_session": 1,
                    "notes": "Focus on form"
                },
                {
                    "exercise_id": "uuid",
                    "sets": 3,
                    "order_in_session": 2,
                    "notes": null
                }
            ],
            "total_sets": 7,
            "created_at": "2025-11-23T...",
            "updated_at": "2025-11-23T..."
        }
    """
    
    __tablename__ = "workout_sessions"
    
    # Foreign Key
    program_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("training_programs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Reference to parent training program"
    )
    
    # Basic Information
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True,
        comment="Session name (e.g., 'Upper Body A', 'Push Day 1')"
    )
    
    day_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
        comment="Day number in program sequence (1-indexed)"
    )
    
    order_in_program: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
        comment="Order of this session in the program"
    )
    
    # Exercises (JSONB array)
    exercises: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        comment="Array of exercises with sets and order"
    )
    
    # Computed field - stored for query performance
    total_sets: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Total number of sets across all exercises (computed)"
    )
    
    # Table Arguments - Indexes and Constraints
    __table_args__ = (
        # Index for finding sessions by program
        Index("ix_workout_sessions_program_id", "program_id"),
        
        # Composite index for program session ordering
        Index(
            "ix_workout_sessions_program_order",
            "program_id",
            "order_in_program"
        ),
        
        # Composite index for program day sequence
        Index(
            "ix_workout_sessions_program_day",
            "program_id",
            "day_number"
        ),
        
        # GIN index for JSONB exercises (enables efficient queries on JSON)
        Index(
            "ix_workout_sessions_exercises",
            "exercises",
            postgresql_using="gin"
        ),
        
        # Index for filtering by total sets
        Index("ix_workout_sessions_total_sets", "total_sets"),
        
        {"comment": "Workout sessions within training programs"}
    )
    
    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return (
            f"<WorkoutSessionModel(id={self.id}, name='{self.name}', "
            f"day={self.day_number}, exercises={len(self.exercises)})>"
        )
    
    @classmethod
    def create_from_entity(cls, session: Any) -> "WorkoutSessionModel":
        """
        Create model instance from WorkoutSession entity.
        
        Args:
            session: WorkoutSession entity instance
            
        Returns:
            WorkoutSessionModel: SQLAlchemy model instance
        """
        # Convert exercises to list of dicts for JSONB storage
        exercises_data = [exercise.to_dict() for exercise in session.exercises]
        
        # Calculate total sets
        total_sets = session.calculate_total_sets()
        
        return cls(
            id=session.id,
            program_id=session.program_id,
            name=session.name,
            day_number=session.day_number,
            order_in_program=session.order_in_program,
            exercises=exercises_data,
            total_sets=total_sets,
            created_at=session.created_at,
            updated_at=session.updated_at,
        )
    
    def update_from_entity(self, session: Any) -> None:
        """
        Update model from WorkoutSession entity.
        
        Args:
            session: WorkoutSession entity instance
        """
        self.program_id = session.program_id
        self.name = session.name
        self.day_number = session.day_number
        self.order_in_program = session.order_in_program
        self.exercises = [exercise.to_dict() for exercise in session.exercises]
        self.total_sets = session.calculate_total_sets()
        self.updated_at = session.updated_at
    
    def to_dict(self) -> dict[str, Any]:
        """
        Convert model to dictionary for API responses.
        
        Returns:
            Dict with all session attributes
        """
        return {
            "id": str(self.id),
            "program_id": str(self.program_id),
            "name": self.name,
            "day_number": self.day_number,
            "order_in_program": self.order_in_program,
            "exercises": self.exercises,
            "total_sets": self.total_sets,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def calculate_muscle_volume(
        self,
        exercise_contributions: dict[str, dict[str, float]]
    ) -> dict[str, float]:
        """
        Calculate volume distribution across muscle groups.
        
        This is a helper method that mirrors the entity's calculation logic.
        
        Args:
            exercise_contributions: Mapping of exercise_id (str) to muscle contributions
                Example: {
                    "exercise-uuid": {"CHEST": 1.0, "TRICEPS": 0.75},
                    "exercise-uuid2": {"LATS": 1.0, "ELBOW_FLEXORS": 0.5}
                }
        
        Returns:
            dict[str, float]: Mapping of muscle group names to total volume
        """
        muscle_volume: dict[str, float] = {}
        
        for exercise_data in self.exercises:
            exercise_id = exercise_data["exercise_id"]
            sets = exercise_data["sets"]
            
            # Get muscle contributions for this exercise
            contributions = exercise_contributions.get(exercise_id, {})
            
            # Calculate volume contribution to each muscle
            for muscle, contribution in contributions.items():
                volume = sets * contribution
                muscle_volume[muscle] = muscle_volume.get(muscle, 0.0) + volume
        
        return muscle_volume
