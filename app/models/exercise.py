"""
Exercise SQLAlchemy model for database persistence.

Stores resistance training exercises with muscle group targeting and volume contributions.
Supports both global (admin-created) and organization-specific exercises.
"""

from datetime import datetime
from typing import Any, Dict
from uuid import uuid4

from sqlalchemy import Boolean, Index, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import BaseModel


class ExerciseModel(BaseModel):
    """
    SQLAlchemy model for Exercise entity.
    
    Represents resistance training exercises with muscle targeting and volume contributions.
    Exercises can be global (available to all) or organization-specific.
    
    Table Structure:
        - exercises (main table)
        - Indexes: name, is_global, organization_id, full-text search
        - JSONB storage for muscle_contributions (flexible schema)
    
    Database Schema:
        {
            "id": "uuid",
            "name": "Barbell Bench Press",
            "description": "Compound chest exercise...",
            "equipment": "BARBELL",
            "image_url": "https://...",
            "is_global": true,
            "created_by_user_id": null,
            "organization_id": null,
            "muscle_contributions": {
                "CHEST": 1.0,
                "FRONT_DELTS": 0.5,
                "TRICEPS": 0.75
            },
            "created_at": "2025-11-22T...",
            "updated_at": "2025-11-22T..."
        }
    """
    
    __tablename__ = "exercises"
    
    # Basic Information
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True,
        comment="Exercise name (e.g., 'Barbell Bench Press')"
    )
    
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
        comment="Exercise description and instructions"
    )
    
    equipment: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Equipment type enum value (BARBELL, DUMBBELL, etc.)"
    )
    
    image_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="URL to exercise demonstration image or video"
    )
    
    # Ownership & Scope
    is_global: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
        comment="True if admin-created exercise available to all organizations"
    )
    
    created_by_user_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="User who created the exercise (None for global exercises)"
    )
    
    organization_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="Organization that owns the exercise (None for global exercises)"
    )
    
    # Muscle Targeting (JSONB for flexible structure)
    muscle_contributions: Mapped[Dict[str, float]] = mapped_column(
        JSONB,
        nullable=False,
        comment="Mapping of muscle groups to volume contribution levels (0.25, 0.5, 0.75, 1.0)"
    )
    
    # Table Arguments - Indexes and Constraints
    __table_args__ = (
        # Composite index for filtering organization exercises
        Index(
            "ix_exercises_org_global",
            "organization_id",
            "is_global",
            postgresql_where=text("is_global = false")
        ),
        
        # Full-text search index on name and description (PostgreSQL specific)
        Index(
            "ix_exercises_search",
            text("to_tsvector('english', name || ' ' || COALESCE(description, ''))"),
            postgresql_using="gin"
        ),
        
        # Unique constraint: name must be unique within organization scope
        Index(
            "ix_exercises_name_org_unique",
            "name",
            "organization_id",
            unique=True,
            postgresql_where=text("organization_id IS NOT NULL")
        ),
        
        # Unique constraint: global exercise names must be unique
        Index(
            "ix_exercises_name_global_unique",
            "name",
            unique=True,
            postgresql_where=text("is_global = true")
        ),
        
        # Index for filtering by equipment type
        Index("ix_exercises_equipment", "equipment"),
        
        # GIN index for JSONB muscle_contributions (enables efficient queries on JSON keys)
        Index(
            "ix_exercises_muscle_contributions",
            "muscle_contributions",
            postgresql_using="gin"
        ),
        
        {"comment": "Resistance training exercises with muscle targeting and volume contributions"}
    )
    
    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return (
            f"<ExerciseModel(id={self.id}, name='{self.name}', "
            f"equipment='{self.equipment}', is_global={self.is_global})>"
        )
    
    @classmethod
    def create_from_entity(cls, exercise: Any) -> "ExerciseModel":
        """
        Create model instance from Exercise entity.
        
        Args:
            exercise: Exercise entity instance
            
        Returns:
            ExerciseModel: SQLAlchemy model instance
        """
        # Convert muscle contributions to dict for JSONB storage
        muscle_contributions_dict = {
            muscle.value: contribution.value
            for muscle, contribution in exercise.muscle_contributions.items()
        }
        
        return cls(
            id=exercise.id,
            name=exercise.name,
            description=exercise.description,
            equipment=exercise.equipment.value,
            image_url=exercise.image_url,
            is_global=exercise.is_global,
            created_by_user_id=exercise.created_by_user_id,
            organization_id=exercise.organization_id,
            muscle_contributions=muscle_contributions_dict,
            created_at=exercise.created_at,
            updated_at=exercise.updated_at,
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert model to dictionary for API responses.
        
        Returns:
            Dict with all exercise attributes
        """
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "equipment": self.equipment,
            "image_url": self.image_url,
            "is_global": self.is_global,
            "created_by_user_id": str(self.created_by_user_id) if self.created_by_user_id else None,
            "organization_id": str(self.organization_id) if self.organization_id else None,
            "muscle_contributions": self.muscle_contributions,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
