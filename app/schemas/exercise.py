"""
Exercise Pydantic schemas for request/response validation.

Includes comprehensive validation for exercise creation, updates, filtering,
and muscle contribution tracking.
"""

from typing import Dict, List
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator

from app.domain.value_objects.equipment import Equipment
from app.domain.value_objects.muscle_groups import MuscleGroup
from app.domain.value_objects.volume_contribution import VolumeContribution


# ==================== Request Schemas ====================


class ExerciseCreate(BaseModel):
    """
    Exercise creation request schema.
    
    Creates a new exercise with muscle targeting and volume contributions.
    For organization-specific exercises, organization_id is set from authenticated user.
    """
    
    name: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="Exercise name (e.g., 'Barbell Bench Press')",
        examples=["Barbell Bench Press"],
    )
    
    description: str = Field(
        default="",
        max_length=500,
        description="Exercise description and instructions",
        examples=["Compound chest exercise performed lying on a flat bench"],
    )
    
    equipment: Equipment = Field(
        ...,
        description="Equipment type used for this exercise",
        examples=[Equipment.BARBELL],
    )
    
    muscle_contributions: Dict[MuscleGroup, VolumeContribution] = Field(
        ...,
        description="Mapping of muscle groups to volume contribution levels",
        examples=[{
            "CHEST": 1.0,
            "FRONT_DELTS": 0.5,
            "TRICEPS": 0.75
        }],
    )
    
    image_url: HttpUrl | None = Field(
        default=None,
        description="URL to exercise demonstration image or video",
        examples=["https://example.com/exercises/bench-press.jpg"],
    )
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "name": "Barbell Bench Press",
                "description": "Compound chest exercise performed lying on a flat bench. Lower the bar to chest level, then press back up.",
                "equipment": "BARBELL",
                "muscle_contributions": {
                    "CHEST": 1.0,
                    "FRONT_DELTS": 0.5,
                    "TRICEPS": 0.75
                },
                "image_url": "https://example.com/exercises/bench-press.jpg"
            }
        },
    )
    
    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate exercise name is not empty after stripping whitespace."""
        if not v or not v.strip():
            raise ValueError("Exercise name cannot be empty or contain only whitespace")
        return v.strip()
    
    @field_validator("muscle_contributions")
    @classmethod
    def validate_muscle_contributions(cls, v: Dict[MuscleGroup, VolumeContribution]) -> Dict[MuscleGroup, VolumeContribution]:
        """
        Validate muscle contributions meet business rules.
        
        Rules:
            - At least one muscle group must be targeted
            - Total contribution should be >= 1.0
            - At least one muscle must have PRIMARY (1.0) contribution
        """
        if not v:
            raise ValueError("Exercise must target at least one muscle group")
        
        total_contribution = sum(contribution.value for contribution in v.values())
        
        if total_contribution < 1.0:
            raise ValueError(
                f"Total muscle contribution ({total_contribution:.2f}) must be >= 1.0. "
                f"Exercise should have at least one primary target."
            )
        
        has_primary = any(
            contribution == VolumeContribution.PRIMARY for contribution in v.values()
        )
        
        if not has_primary:
            raise ValueError(
                "Exercise must have at least one muscle with PRIMARY (1.0) contribution"
            )
        
        return v


class ExerciseUpdate(BaseModel):
    """
    Exercise update request schema.
    
    All fields are optional. Only provided fields will be updated.
    """
    
    name: str | None = Field(
        default=None,
        min_length=3,
        max_length=100,
        description="Updated exercise name",
        examples=["Barbell Flat Bench Press"],
    )
    
    description: str | None = Field(
        default=None,
        max_length=500,
        description="Updated exercise description",
        examples=["Updated description with more detailed instructions"],
    )
    
    equipment: Equipment | None = Field(
        default=None,
        description="Updated equipment type",
        examples=[Equipment.DUMBBELL],
    )
    
    muscle_contributions: Dict[MuscleGroup, VolumeContribution] | None = Field(
        default=None,
        description="Updated muscle group targeting",
        examples=[{
            "CHEST": 1.0,
            "FRONT_DELTS": 0.75,
            "TRICEPS": 0.5
        }],
    )
    
    image_url: HttpUrl | None = Field(
        default=None,
        description="Updated image URL (set to null to remove)",
        examples=["https://example.com/exercises/new-image.jpg"],
    )
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "name": "Barbell Flat Bench Press",
                "description": "Updated description with more detailed form cues",
                "equipment": "BARBELL",
                "muscle_contributions": {
                    "CHEST": 1.0,
                    "FRONT_DELTS": 0.5,
                    "TRICEPS": 0.75
                }
            }
        },
    )
    
    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str | None) -> str | None:
        """Validate exercise name if provided."""
        if v is not None:
            if not v or not v.strip():
                raise ValueError("Exercise name cannot be empty or contain only whitespace")
            return v.strip()
        return v
    
    @field_validator("muscle_contributions")
    @classmethod
    def validate_muscle_contributions(cls, v: Dict[MuscleGroup, VolumeContribution] | None) -> Dict[MuscleGroup, VolumeContribution] | None:
        """Validate muscle contributions if provided."""
        if v is not None:
            if not v:
                raise ValueError("Exercise must target at least one muscle group")
            
            total_contribution = sum(contribution.value for contribution in v.values())
            
            if total_contribution < 1.0:
                raise ValueError(
                    f"Total muscle contribution ({total_contribution:.2f}) must be >= 1.0"
                )
            
            has_primary = any(
                contribution == VolumeContribution.PRIMARY for contribution in v.values()
            )
            
            if not has_primary:
                raise ValueError(
                    "Exercise must have at least one muscle with PRIMARY (1.0) contribution"
                )
        
        return v


class ExerciseFilter(BaseModel):
    """
    Exercise filtering and pagination schema.
    
    Supports full-text search, equipment filtering, muscle targeting,
    and global/organization scope filtering.
    """
    
    search: str | None = Field(
        default=None,
        max_length=100,
        description="Full-text search query (name and description)",
        examples=["bench press"],
    )
    
    equipment: Equipment | None = Field(
        default=None,
        description="Filter by equipment type",
        examples=[Equipment.BARBELL],
    )
    
    muscle_group: MuscleGroup | None = Field(
        default=None,
        description="Filter by targeted muscle group (any contribution level)",
        examples=[MuscleGroup.CHEST],
    )
    
    is_global: bool | None = Field(
        default=None,
        description="Filter by global (admin) vs organization-specific exercises. None returns both.",
        examples=[True],
    )
    
    skip: int = Field(
        default=0,
        ge=0,
        description="Number of records to skip (for pagination)",
        examples=[0],
    )
    
    limit: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Maximum number of records to return (1-100)",
        examples=[20],
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "search": "press",
                "equipment": "BARBELL",
                "muscle_group": "CHEST",
                "is_global": True,
                "skip": 0,
                "limit": 20
            }
        }
    )


# ==================== Response Schemas ====================


class MuscleContributionResponse(BaseModel):
    """
    Muscle group contribution response schema.
    
    Represents a single muscle's volume contribution in an exercise.
    """
    
    muscle: MuscleGroup = Field(
        ...,
        description="Muscle group identifier",
        examples=[MuscleGroup.CHEST],
    )
    
    muscle_name: str = Field(
        ...,
        description="Human-readable muscle group name",
        examples=["Chest"],
    )
    
    contribution: VolumeContribution = Field(
        ...,
        description="Volume contribution level (0.25, 0.5, 0.75, or 1.0)",
        examples=[VolumeContribution.PRIMARY],
    )
    
    contribution_percentage: int = Field(
        ...,
        description="Contribution as percentage (25, 50, 75, or 100)",
        examples=[100],
    )
    
    contribution_label: str = Field(
        ...,
        description="Human-readable contribution level",
        examples=["Primary (100%)"],
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "muscle": "CHEST",
                "muscle_name": "Chest",
                "contribution": 1.0,
                "contribution_percentage": 100,
                "contribution_label": "Primary (100%)"
            }
        }
    )


class ExerciseResponse(BaseModel):
    """
    Exercise response schema.
    
    Returns complete exercise data including computed fields
    like primary/secondary muscles and total contribution.
    """
    
    id: UUID = Field(
        ...,
        description="Unique exercise identifier",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    
    name: str = Field(
        ...,
        description="Exercise name",
        examples=["Barbell Bench Press"],
    )
    
    description: str = Field(
        ...,
        description="Exercise description and instructions",
        examples=["Compound chest exercise performed lying on a flat bench"],
    )
    
    equipment: Equipment = Field(
        ...,
        description="Equipment type used",
        examples=[Equipment.BARBELL],
    )
    
    equipment_name: str = Field(
        ...,
        description="Human-readable equipment name",
        examples=["Barbell"],
    )
    
    image_url: str | None = Field(
        ...,
        description="URL to exercise demonstration image or video",
        examples=["https://example.com/exercises/bench-press.jpg"],
    )
    
    is_global: bool = Field(
        ...,
        description="True if admin-created exercise available to all organizations",
        examples=[True],
    )
    
    created_by_user_id: UUID | None = Field(
        ...,
        description="User who created the exercise (None for global exercises)",
        examples=["660e8400-e29b-41d4-a716-446655440000"],
    )
    
    organization_id: UUID | None = Field(
        ...,
        description="Organization that owns the exercise (None for global exercises)",
        examples=["770e8400-e29b-41d4-a716-446655440000"],
    )
    
    muscle_contributions: List[MuscleContributionResponse] = Field(
        ...,
        description="List of muscle groups targeted with contribution levels",
    )
    
    primary_muscles: List[str] = Field(
        ...,
        description="List of primary target muscles (1.0 contribution)",
        examples=[["Chest"]],
    )
    
    secondary_muscles: List[str] = Field(
        ...,
        description="List of secondary target muscles (< 1.0 contribution), ordered by contribution",
        examples=[["Triceps", "Front Delts"]],
    )
    
    total_contribution: float = Field(
        ...,
        description="Sum of all muscle contributions",
        examples=[2.25],
    )
    
    is_compound: bool = Field(
        ...,
        description="True if exercise targets multiple muscle groups",
        examples=[True],
    )
    
    created_at: str = Field(
        ...,
        description="ISO 8601 timestamp of creation",
        examples=["2025-11-22T12:00:00Z"],
    )
    
    updated_at: str = Field(
        ...,
        description="ISO 8601 timestamp of last update",
        examples=["2025-11-22T12:00:00Z"],
    )
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Barbell Bench Press",
                "description": "Compound chest exercise performed lying on a flat bench",
                "equipment": "BARBELL",
                "equipment_name": "Barbell",
                "image_url": "https://example.com/exercises/bench-press.jpg",
                "is_global": True,
                "created_by_user_id": None,
                "organization_id": None,
                "muscle_contributions": [
                    {
                        "muscle": "CHEST",
                        "muscle_name": "Chest",
                        "contribution": 1.0,
                        "contribution_percentage": 100,
                        "contribution_label": "Primary (100%)"
                    },
                    {
                        "muscle": "TRICEPS",
                        "muscle_name": "Triceps",
                        "contribution": 0.75,
                        "contribution_percentage": 75,
                        "contribution_label": "High (75%)"
                    },
                    {
                        "muscle": "FRONT_DELTS",
                        "muscle_name": "Front Delts",
                        "contribution": 0.5,
                        "contribution_percentage": 50,
                        "contribution_label": "Moderate (50%)"
                    }
                ],
                "primary_muscles": ["Chest"],
                "secondary_muscles": ["Triceps", "Front Delts"],
                "total_contribution": 2.25,
                "is_compound": True,
                "created_at": "2025-11-22T12:00:00Z",
                "updated_at": "2025-11-22T12:00:00Z"
            }
        }
    )


class ExerciseListResponse(BaseModel):
    """
    Paginated exercise list response schema.
    
    Returns list of exercises with pagination metadata.
    """
    
    items: List[ExerciseResponse] = Field(
        ...,
        description="List of exercises in current page",
    )
    
    total: int = Field(
        ...,
        ge=0,
        description="Total number of exercises matching filter",
        examples=[150],
    )
    
    page: int = Field(
        ...,
        ge=1,
        description="Current page number (1-indexed)",
        examples=[1],
    )
    
    page_size: int = Field(
        ...,
        ge=1,
        description="Number of items per page",
        examples=[20],
    )
    
    total_pages: int = Field(
        ...,
        ge=0,
        description="Total number of pages",
        examples=[8],
    )
    
    has_next: bool = Field(
        ...,
        description="True if there are more pages",
        examples=[True],
    )
    
    has_previous: bool = Field(
        ...,
        description="True if there are previous pages",
        examples=[False],
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "name": "Barbell Bench Press",
                        "description": "Compound chest exercise",
                        "equipment": "BARBELL",
                        "equipment_name": "Barbell",
                        "image_url": "https://example.com/exercises/bench-press.jpg",
                        "is_global": True,
                        "created_by_user_id": None,
                        "organization_id": None,
                        "muscle_contributions": [],
                        "primary_muscles": ["Chest"],
                        "secondary_muscles": ["Triceps", "Front Delts"],
                        "total_contribution": 2.25,
                        "is_compound": True,
                        "created_at": "2025-11-22T12:00:00Z",
                        "updated_at": "2025-11-22T12:00:00Z"
                    }
                ],
                "total": 150,
                "page": 1,
                "page_size": 20,
                "total_pages": 8,
                "has_next": True,
                "has_previous": False
            }
        }
    )


class ExerciseSummaryResponse(BaseModel):
    """
    Lightweight exercise summary for lists and dropdowns.
    
    Minimal response with just essential fields.
    """
    
    id: UUID = Field(..., description="Exercise identifier")
    name: str = Field(..., description="Exercise name")
    equipment: Equipment = Field(..., description="Equipment type")
    equipment_name: str = Field(..., description="Equipment display name")
    primary_muscles: List[str] = Field(..., description="Primary target muscles")
    is_global: bool = Field(..., description="Global or organization-specific")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Barbell Bench Press",
                "equipment": "BARBELL",
                "equipment_name": "Barbell",
                "primary_muscles": ["Chest"],
                "is_global": True
            }
        }
    )
