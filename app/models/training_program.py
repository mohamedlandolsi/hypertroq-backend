"""
Training Program SQLAlchemy model for database persistence.

Stores training programs with their structure configuration and relationships to sessions.
"""

from typing import Any
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Index, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import BaseModel


class TrainingProgramModel(BaseModel):
    """
    SQLAlchemy model for TrainingProgram entity.
    
    Represents a complete training program with split type, structure, and sessions.
    Programs can be templates (admin-created) or user programs (cloned from templates).
    
    Table Structure:
        - training_programs (main table)
        - Relationships: One-to-many with workout_sessions
        - Indexes: is_template, organization_id, split_type, structure_type
        - JSONB storage for structure_config (WeeklyStructure or CyclicStructure)
    
    Database Schema:
        {
            "id": "uuid",
            "name": "Upper/Lower 4-Day Split",
            "description": "Classic upper/lower split...",
            "split_type": "UPPER_LOWER",
            "structure_type": "WEEKLY",
            "structure_config": {
                "days_per_week": 4,
                "selected_days": ["MON", "TUE", "THU", "FRI"]
            },
            "is_template": true,
            "created_by_user_id": null,
            "organization_id": null,
            "duration_weeks": 8,
            "created_at": "2025-11-23T...",
            "updated_at": "2025-11-23T..."
        }
    """
    
    __tablename__ = "training_programs"
    
    # Basic Information
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True,
        comment="Program name (e.g., 'Upper/Lower 4-Day Split')"
    )
    
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
        comment="Program description and notes"
    )
    
    # Program Configuration
    split_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Training split type enum (UPPER_LOWER, PUSH_PULL_LEGS, etc.)"
    )
    
    structure_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="Structure type enum (WEEKLY, CYCLIC)"
    )
    
    structure_config: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        comment="Structure configuration (WeeklyStructure or CyclicStructure as JSON)"
    )
    
    # Ownership & Template Status
    is_template: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
        comment="True if admin template, False if user program"
    )
    
    created_by_user_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="User who created program (None for templates)"
    )
    
    organization_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="Organization owning program (None for templates)"
    )
    
    # Program Duration
    duration_weeks: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Recommended program duration in weeks"
    )
    
    # Relationships
    sessions: Mapped[list["WorkoutSessionModel"]] = relationship(
        "WorkoutSessionModel",
        back_populates="program",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="WorkoutSessionModel.order_in_program"
    )
    
    # Table Arguments - Indexes and Constraints
    __table_args__ = (
        # Composite index for finding templates
        Index(
            "ix_training_programs_templates",
            "is_template",
            postgresql_where=text("is_template = true")
        ),
        
        # Composite index for finding user programs by organization
        Index(
            "ix_training_programs_org",
            "organization_id",
            "is_template",
            postgresql_where=text("is_template = false")
        ),
        
        # Index for filtering by split type
        Index("ix_training_programs_split_type", "split_type"),
        
        # Index for filtering by structure type
        Index("ix_training_programs_structure_type", "structure_type"),
        
        # GIN index for JSONB structure_config
        Index(
            "ix_training_programs_structure_config",
            "structure_config",
            postgresql_using="gin"
        ),
        
        # Full-text search index on name and description
        Index(
            "ix_training_programs_search",
            text("to_tsvector('english', name || ' ' || COALESCE(description, ''))"),
            postgresql_using="gin"
        ),
        
        # Composite index for user's programs
        Index(
            "ix_training_programs_user",
            "created_by_user_id",
            "organization_id"
        ),
        
        {"comment": "Training programs with split types, structures, and sessions"}
    )
    
    def __repr__(self) -> str:
        """Developer-friendly representation."""
        template_str = " [Template]" if self.is_template else ""
        return (
            f"<TrainingProgramModel(id={self.id}, name='{self.name}', "
            f"split='{self.split_type}'{template_str})>"
        )
    
    @classmethod
    def create_from_entity(cls, program: Any) -> "TrainingProgramModel":
        """
        Create model instance from TrainingProgram entity.
        
        Args:
            program: TrainingProgram entity instance
            
        Returns:
            TrainingProgramModel: SQLAlchemy model instance
            
        Note:
            Sessions should be added separately via relationship
        """
        # Serialize structure_config to dict
        structure_config_dict = program.structure_config.model_dump()
        
        return cls(
            id=program.id,
            name=program.name,
            description=program.description,
            split_type=program.split_type.value,
            structure_type=program.structure_type.value,
            structure_config=structure_config_dict,
            is_template=program.is_template,
            created_by_user_id=program.created_by_user_id,
            organization_id=program.organization_id,
            duration_weeks=program.duration_weeks,
            created_at=program.created_at,
            updated_at=program.updated_at,
        )
    
    def update_from_entity(self, program: Any) -> None:
        """
        Update model from TrainingProgram entity.
        
        Args:
            program: TrainingProgram entity instance
        """
        self.name = program.name
        self.description = program.description
        self.split_type = program.split_type.value
        self.structure_type = program.structure_type.value
        self.structure_config = program.structure_config.model_dump()
        self.is_template = program.is_template
        self.created_by_user_id = program.created_by_user_id
        self.organization_id = program.organization_id
        self.duration_weeks = program.duration_weeks
        self.updated_at = program.updated_at
    
    def to_dict(self) -> dict[str, Any]:
        """
        Convert model to dictionary for API responses.
        
        Returns:
            Dict with all program attributes and session count
        """
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "split_type": self.split_type,
            "structure_type": self.structure_type,
            "structure_config": self.structure_config,
            "is_template": self.is_template,
            "created_by_user_id": str(self.created_by_user_id) if self.created_by_user_id else None,
            "organization_id": str(self.organization_id) if self.organization_id else None,
            "duration_weeks": self.duration_weeks,
            "session_count": len(self.sessions) if self.sessions else 0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def to_dict_with_sessions(self) -> dict[str, Any]:
        """
        Convert model to dictionary including full session details.
        
        Returns:
            Dict with all program attributes and session data
        """
        base_dict = self.to_dict()
        base_dict["sessions"] = [
            session.to_dict() for session in (self.sessions or [])
        ]
        return base_dict


# Import here to avoid circular imports
from app.models.workout_session import WorkoutSessionModel

# Update the relationship back-reference
WorkoutSessionModel.program = relationship(
    "TrainingProgramModel",
    back_populates="sessions"
)
