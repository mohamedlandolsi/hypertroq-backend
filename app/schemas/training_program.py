"""
Training Program Schemas for API requests and responses.

Defines Pydantic models for program creation, updates, filtering, and responses.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

from app.domain.entities.training_split import TrainingSplitType
from app.domain.entities.training_structure import StructureType


# ==================== Input Schemas ====================


class WorkoutExerciseInput(BaseModel):
    """Input schema for exercise within a workout session.
    
    Examples:
        {
            "exercise_id": "123e4567-e89b-12d3-a456-426614174000",
            "sets": 4,
            "order_in_session": 1,
            "notes": "Focus on form, 3-0-1-0 tempo"
        }
    """
    
    exercise_id: UUID = Field(
        description="ID of the exercise to perform"
    )
    sets: int = Field(
        ge=1,
        le=10,
        description="Number of sets to perform"
    )
    order_in_session: int = Field(
        ge=1,
        description="Position of exercise in workout (1-indexed)"
    )
    notes: str | None = Field(
        default=None,
        max_length=500,
        description="Optional notes for this exercise"
    )
    
    @field_validator("notes")
    @classmethod
    def validate_notes(cls, v: str | None) -> str | None:
        """Clean and validate notes."""
        if v is not None:
            v = v.strip()
            if not v:
                return None
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "exercise_id": "123e4567-e89b-12d3-a456-426614174000",
                "sets": 4,
                "order_in_session": 1,
                "notes": "Focus on form"
            }
        }


class WeeklyStructureInput(BaseModel):
    """Input schema for weekly training structure.
    
    Examples:
        {
            "days_per_week": 4,
            "selected_days": ["MON", "TUE", "THU", "FRI"]
        }
    """
    
    days_per_week: int = Field(
        ge=3,
        le=7,
        description="Number of training days per week"
    )
    selected_days: list[str] = Field(
        min_length=3,
        max_length=7,
        description="Selected training days (MON, TUE, WED, etc.)"
    )
    
    @field_validator("selected_days")
    @classmethod
    def validate_days(cls, v: list[str]) -> list[str]:
        """Validate day abbreviations."""
        valid_days = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
        for day in v:
            if day not in valid_days:
                raise ValueError(f"Invalid day '{day}'. Must be one of: {', '.join(valid_days)}")
        if len(v) != len(set(v)):
            raise ValueError("Selected days must not contain duplicates")
        return v
    
    @model_validator(mode="after")
    def validate_consistency(self) -> "WeeklyStructureInput":
        """Validate days match count."""
        if len(self.selected_days) != self.days_per_week:
            raise ValueError(
                f"Number of selected days ({len(self.selected_days)}) must match "
                f"days_per_week ({self.days_per_week})"
            )
        return self
    
    class Config:
        json_schema_extra = {
            "example": {
                "days_per_week": 4,
                "selected_days": ["MON", "TUE", "THU", "FRI"]
            }
        }


class CyclicStructureInput(BaseModel):
    """Input schema for cyclic training structure.
    
    Examples:
        {
            "days_on": 3,
            "days_off": 1
        }
    """
    
    days_on: int = Field(
        ge=1,
        le=6,
        description="Consecutive training days"
    )
    days_off: int = Field(
        ge=1,
        le=3,
        description="Consecutive rest days"
    )
    
    @model_validator(mode="after")
    def validate_cycle(self) -> "CyclicStructureInput":
        """Validate cycle length and frequency."""
        cycle_length = self.days_on + self.days_off
        if cycle_length > 9:
            raise ValueError("Total cycle length should not exceed 9 days")
        
        training_frequency = (self.days_on / cycle_length) * 7
        if training_frequency < 3:
            raise ValueError("Cycle results in less than 3 training days per week (minimum recommended)")
        
        return self
    
    class Config:
        json_schema_extra = {
            "example": {
                "days_on": 3,
                "days_off": 1
            }
        }


class SessionCreate(BaseModel):
    """Schema for creating a workout session.
    
    Examples:
        {
            "name": "Upper Body A",
            "day_number": 1,
            "order_in_program": 1,
            "exercises": [
                {
                    "exercise_id": "123e4567-e89b-12d3-a456-426614174000",
                    "sets": 4,
                    "order_in_session": 1,
                    "notes": "Bench press - focus on form"
                }
            ]
        }
    """
    
    name: str = Field(
        min_length=3,
        max_length=100,
        description="Session name (e.g., 'Upper Body A')"
    )
    day_number: int = Field(
        ge=1,
        description="Day number in program sequence"
    )
    order_in_program: int = Field(
        ge=1,
        description="Order of this session in program"
    )
    exercises: list[WorkoutExerciseInput] = Field(
        default_factory=list,
        description="List of exercises in session (can be empty, exercises can be added later)"
    )
    
    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Clean and validate name."""
        v = v.strip()
        if not v:
            raise ValueError("Session name cannot be empty")
        return v
    
    @field_validator("exercises")
    @classmethod
    def validate_exercises(cls, v: list[WorkoutExerciseInput]) -> list[WorkoutExerciseInput]:
        """Validate exercise ordering if exercises are provided."""
        # Allow empty exercises - sessions can be created first, exercises added later
        if not v:
            return v
        
        orders = [ex.order_in_session for ex in v]
        if len(orders) != len(set(orders)):
            raise ValueError("Exercise order_in_session values must be unique")
        
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Upper Body A",
                "day_number": 1,
                "order_in_program": 1,
                "exercises": [
                    {
                        "exercise_id": "123e4567-e89b-12d3-a456-426614174000",
                        "sets": 4,
                        "order_in_session": 1,
                        "notes": "Bench press"
                    },
                    {
                        "exercise_id": "223e4567-e89b-12d3-a456-426614174001",
                        "sets": 3,
                        "order_in_session": 2,
                        "notes": "Barbell rows"
                    }
                ]
            }
        }


class SessionUpdate(BaseModel):
    """Schema for updating a workout session (all fields optional).
    
    Examples:
        {
            "name": "Upper Body A - Modified",
            "exercises": [...]
        }
    """
    
    name: str | None = Field(
        default=None,
        min_length=3,
        max_length=100,
        description="Session name"
    )
    day_number: int | None = Field(
        default=None,
        ge=1,
        description="Day number in program sequence"
    )
    order_in_program: int | None = Field(
        default=None,
        ge=1,
        description="Order in program"
    )
    exercises: list[WorkoutExerciseInput] | None = Field(
        default=None,
        min_length=1,
        description="List of exercises"
    )
    
    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str | None) -> str | None:
        """Clean and validate name."""
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Session name cannot be empty")
        return v


class ProgramCreate(BaseModel):
    """Schema for creating a training program.
    
    Examples:
        {
            "name": "Upper/Lower 4-Day Split",
            "description": "Classic upper/lower split for intermediate lifters",
            "split_type": "UPPER_LOWER",
            "structure_type": "WEEKLY",
            "structure_config": {
                "days_per_week": 4,
                "selected_days": ["MON", "TUE", "THU", "FRI"]
            },
            "duration_weeks": 8,
            "sessions": [...]
        }
    """
    
    name: str = Field(
        min_length=3,
        max_length=100,
        description="Program name"
    )
    description: str = Field(
        default="",
        max_length=2000,
        description="Program description and notes"
    )
    split_type: TrainingSplitType = Field(
        description="Type of training split"
    )
    structure_type: StructureType = Field(
        description="Weekly or cyclic structure"
    )
    structure_config: WeeklyStructureInput | CyclicStructureInput | None = Field(
        default=None,
        description="Structure configuration (type depends on structure_type). If not provided, defaults will be used."
    )
    duration_weeks: int | None = Field(
        default=None,
        ge=1,
        le=52,
        description="Recommended program duration in weeks"
    )
    sessions: list[SessionCreate] = Field(
        default_factory=list,
        description="List of workout sessions (can be empty, sessions can be added later)"
    )
    
    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Clean and validate name."""
        v = v.strip()
        if not v:
            raise ValueError("Program name cannot be empty")
        return v
    
    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str) -> str:
        """Clean description."""
        return v.strip()
    
    @model_validator(mode="after")
    def validate_structure_match(self) -> "ProgramCreate":
        """Validate structure config matches structure type or set defaults."""
        # If no structure_config provided, set sensible defaults
        if self.structure_config is None:
            if self.structure_type == StructureType.WEEKLY:
                # Default to 4 days: Mon, Tue, Thu, Fri
                self.structure_config = WeeklyStructureInput(
                    days_per_week=4,
                    selected_days=["MON", "TUE", "THU", "FRI"]
                )
            else:  # CYCLIC
                # Default to 3 on, 1 off
                self.structure_config = CyclicStructureInput(
                    days_on=3,
                    days_off=1
                )
        else:
            # Validate provided config matches type
            if self.structure_type == StructureType.WEEKLY:
                if not isinstance(self.structure_config, WeeklyStructureInput):
                    raise ValueError("structure_config must be WeeklyStructureInput for WEEKLY type")
            elif self.structure_type == StructureType.CYCLIC:
                if not isinstance(self.structure_config, CyclicStructureInput):
                    raise ValueError("structure_config must be CyclicStructureInput for CYCLIC type")
        return self
    
    @field_validator("sessions")
    @classmethod
    def validate_sessions(cls, v: list[SessionCreate]) -> list[SessionCreate]:
        """Validate session constraints."""
        # Allow empty sessions list - sessions can be added later
        if not v:
            return v  # Return empty list, sessions can be added later
        
        # Check unique day numbers
        day_numbers = [s.day_number for s in v]
        if len(day_numbers) != len(set(day_numbers)):
            raise ValueError("Session day_numbers must be unique")
        
        # Check unique order
        orders = [s.order_in_program for s in v]
        if len(orders) != len(set(orders)):
            raise ValueError("Session order_in_program values must be unique")
        
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Upper/Lower 4-Day Split",
                "description": "Classic upper/lower split for intermediate lifters focusing on hypertrophy",
                "split_type": "UPPER_LOWER",
                "structure_type": "WEEKLY",
                "structure_config": {
                    "days_per_week": 4,
                    "selected_days": ["MON", "TUE", "THU", "FRI"]
                },
                "duration_weeks": 8,
                "sessions": [
                    {
                        "name": "Upper Body A",
                        "day_number": 1,
                        "order_in_program": 1,
                        "exercises": [
                            {
                                "exercise_id": "123e4567-e89b-12d3-a456-426614174000",
                                "sets": 4,
                                "order_in_session": 1,
                                "notes": "Bench press"
                            }
                        ]
                    }
                ]
            }
        }


class ProgramUpdate(BaseModel):
    """Schema for updating a training program (all fields optional).
    
    Examples:
        {
            "name": "Updated Program Name",
            "description": "New description",
            "duration_weeks": 12
        }
    """
    
    name: str | None = Field(
        default=None,
        min_length=3,
        max_length=100,
        description="Program name"
    )
    description: str | None = Field(
        default=None,
        max_length=2000,
        description="Program description"
    )
    duration_weeks: int | None = Field(
        default=None,
        ge=1,
        le=52,
        description="Program duration in weeks"
    )
    
    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str | None) -> str | None:
        """Clean and validate name."""
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Program name cannot be empty")
        return v
    
    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str | None) -> str | None:
        """Clean description."""
        if v is not None:
            v = v.strip()
        return v


class ProgramFilter(BaseModel):
    """Schema for filtering and paginating programs.
    
    Examples:
        {
            "search": "upper lower",
            "split_type": "UPPER_LOWER",
            "is_template": true,
            "skip": 0,
            "limit": 20
        }
    """
    
    search: str | None = Field(
        default=None,
        max_length=100,
        description="Search term for name/description"
    )
    split_type: TrainingSplitType | None = Field(
        default=None,
        description="Filter by split type"
    )
    structure_type: StructureType | None = Field(
        default=None,
        description="Filter by structure type"
    )
    is_template: bool | None = Field(
        default=None,
        description="Filter templates vs user programs"
    )
    skip: int = Field(
        default=0,
        ge=0,
        description="Number of records to skip (pagination)"
    )
    limit: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Maximum number of records to return"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "search": "upper lower",
                "split_type": "UPPER_LOWER",
                "is_template": True,
                "skip": 0,
                "limit": 20
            }
        }


# ==================== Response Schemas ====================


class WorkoutExerciseResponse(BaseModel):
    """Response schema for exercise in workout session.
    
    Examples:
        {
            "exercise_id": "123e4567-e89b-12d3-a456-426614174000",
            "exercise_name": "Barbell Bench Press",
            "sets": 4,
            "order_in_session": 1,
            "notes": "Focus on form"
        }
    """
    
    exercise_id: UUID
    exercise_name: str | None = None
    sets: int
    order_in_session: int
    notes: str | None = None
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "exercise_id": "123e4567-e89b-12d3-a456-426614174000",
                "exercise_name": "Barbell Bench Press",
                "sets": 4,
                "order_in_session": 1,
                "notes": "Focus on form"
            }
        }


class SessionResponse(BaseModel):
    """Response schema for workout session with computed totals.
    
    Examples:
        {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "program_id": "223e4567-e89b-12d3-a456-426614174001",
            "name": "Upper Body A",
            "day_number": 1,
            "order_in_program": 1,
            "exercises": [...],
            "total_sets": 15,
            "exercise_count": 5,
            "created_at": "2025-11-23T10:00:00Z",
            "updated_at": "2025-11-23T10:00:00Z"
        }
    """
    
    id: UUID
    program_id: UUID
    name: str
    day_number: int
    order_in_program: int
    exercises: list[WorkoutExerciseResponse]
    total_sets: int
    exercise_count: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "program_id": "223e4567-e89b-12d3-a456-426614174001",
                "name": "Upper Body A",
                "day_number": 1,
                "order_in_program": 1,
                "exercises": [
                    {
                        "exercise_id": "323e4567-e89b-12d3-a456-426614174002",
                        "exercise_name": "Barbell Bench Press",
                        "sets": 4,
                        "order_in_session": 1,
                        "notes": None
                    }
                ],
                "total_sets": 15,
                "exercise_count": 5,
                "created_at": "2025-11-23T10:00:00Z",
                "updated_at": "2025-11-23T10:00:00Z"
            }
        }


class MuscleVolumeResponse(BaseModel):
    """Response schema for muscle group volume.
    
    Examples:
        {
            "muscle": "CHEST",
            "muscle_name": "Chest",
            "sets_per_week": 16.0,
            "status": "optimal"
        }
    """
    
    muscle: str
    muscle_name: str
    sets_per_week: float
    status: str = Field(
        description="Volume status: 'low' (<10), 'optimal' (10-20), 'high' (20-25), 'excessive' (>25)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "muscle": "CHEST",
                "muscle_name": "Chest",
                "sets_per_week": 16.0,
                "status": "optimal"
            }
        }


class ProgramStatsResponse(BaseModel):
    """Response schema for program statistics.
    
    Examples:
        {
            "total_sessions": 4,
            "total_sets": 60,
            "avg_sets_per_session": 15.0,
            "weekly_volume": [...],
            "training_frequency": 4.0
        }
    """
    
    total_sessions: int
    total_sets: int
    avg_sets_per_session: float
    weekly_volume: list[MuscleVolumeResponse]
    training_frequency: float = Field(
        description="Average training days per week"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_sessions": 4,
                "total_sets": 60,
                "avg_sets_per_session": 15.0,
                "weekly_volume": [
                    {
                        "muscle": "CHEST",
                        "muscle_name": "Chest",
                        "sets_per_week": 16.0,
                        "status": "optimal"
                    }
                ],
                "training_frequency": 4.0
            }
        }


class ProgramResponse(BaseModel):
    """Response schema for training program with all details and stats.
    
    Examples:
        {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "name": "Upper/Lower 4-Day Split",
            "description": "Classic upper/lower split...",
            "split_type": "UPPER_LOWER",
            "structure_type": "WEEKLY",
            "structure_config": {...},
            "is_template": true,
            "duration_weeks": 8,
            "sessions": [...],
            "stats": {...},
            "created_at": "2025-11-23T10:00:00Z",
            "updated_at": "2025-11-23T10:00:00Z"
        }
    """
    
    id: UUID
    name: str
    description: str
    split_type: str
    structure_type: str
    structure_config: dict[str, Any]
    is_template: bool
    created_by_user_id: UUID | None = None
    organization_id: UUID | None = None
    duration_weeks: int | None = None
    sessions: list[SessionResponse]
    stats: ProgramStatsResponse | None = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Upper/Lower 4-Day Split",
                "description": "Classic upper/lower split for intermediate lifters",
                "split_type": "UPPER_LOWER",
                "structure_type": "WEEKLY",
                "structure_config": {
                    "days_per_week": 4,
                    "selected_days": ["MON", "TUE", "THU", "FRI"]
                },
                "is_template": True,
                "created_by_user_id": None,
                "organization_id": None,
                "duration_weeks": 8,
                "sessions": [],
                "stats": {
                    "total_sessions": 4,
                    "total_sets": 60,
                    "avg_sets_per_session": 15.0,
                    "weekly_volume": [],
                    "training_frequency": 4.0
                },
                "created_at": "2025-11-23T10:00:00Z",
                "updated_at": "2025-11-23T10:00:00Z"
            }
        }


class ProgramListItemResponse(BaseModel):
    """Response schema for program in list view (summary without sessions).
    
    Examples:
        {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "name": "Upper/Lower 4-Day Split",
            "description": "Classic upper/lower split...",
            "split_type": "UPPER_LOWER",
            "structure_type": "WEEKLY",
            "is_template": true,
            "duration_weeks": 8,
            "session_count": 4,
            "created_at": "2025-11-23T10:00:00Z"
        }
    """
    
    id: UUID
    name: str
    description: str
    split_type: str
    structure_type: str
    is_template: bool
    duration_weeks: int | None = None
    session_count: int
    created_at: datetime
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Upper/Lower 4-Day Split",
                "description": "Classic upper/lower split for intermediate lifters",
                "split_type": "UPPER_LOWER",
                "structure_type": "WEEKLY",
                "is_template": True,
                "duration_weeks": 8,
                "session_count": 4,
                "created_at": "2025-11-23T10:00:00Z"
            }
        }


class ProgramListResponse(BaseModel):
    """Response schema for paginated program list.
    
    Examples:
        {
            "items": [...],
            "total": 25,
            "page": 1,
            "page_size": 20,
            "has_more": true
        }
    """
    
    items: list[ProgramListItemResponse]
    total: int = Field(description="Total number of programs matching filter")
    page: int = Field(description="Current page number (1-indexed)")
    page_size: int = Field(description="Number of items per page")
    has_more: bool = Field(description="Whether there are more pages")
    
    class Config:
        json_schema_extra = {
            "example": {
                "items": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "name": "Upper/Lower 4-Day Split",
                        "description": "Classic upper/lower split",
                        "split_type": "UPPER_LOWER",
                        "structure_type": "WEEKLY",
                        "is_template": True,
                        "duration_weeks": 8,
                        "session_count": 4,
                        "created_at": "2025-11-23T10:00:00Z"
                    }
                ],
                "total": 25,
                "page": 1,
                "page_size": 20,
                "has_more": True
            }
        }


class CloneProgramRequest(BaseModel):
    """Request schema for cloning a program from template.
    
    Examples:
        {
            "template_id": "123e4567-e89b-12d3-a456-426614174000",
            "new_name": "My Custom Upper/Lower Split"
        }
    """
    
    template_id: UUID = Field(description="ID of template program to clone")
    new_name: str | None = Field(
        default=None,
        min_length=3,
        max_length=100,
        description="Optional custom name for cloned program"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "template_id": "123e4567-e89b-12d3-a456-426614174000",
                "new_name": "My Custom Upper/Lower Split"
            }
        }


class ScheduleGenerateRequest(BaseModel):
    """Request schema for generating program schedule.
    
    Examples:
        {
            "start_date": "2025-11-25",
            "weeks": 8
        }
    """
    
    start_date: str = Field(
        description="Start date in YYYY-MM-DD format"
    )
    weeks: int | None = Field(
        default=None,
        ge=1,
        le=52,
        description="Number of weeks to generate (uses program duration if not specified)"
    )
    
    @field_validator("start_date")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        """Validate date format."""
        from datetime import datetime
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError("start_date must be in YYYY-MM-DD format")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "start_date": "2025-11-25",
                "weeks": 8
            }
        }


class ScheduledSessionResponse(BaseModel):
    """Response schema for scheduled workout session.
    
    Examples:
        {
            "session_id": "123e4567-e89b-12d3-a456-426614174000",
            "session_name": "Upper Body A",
            "scheduled_date": "2025-11-25",
            "day_of_week": "MON",
            "cycle_day": null
        }
    """
    
    session_id: UUID
    session_name: str
    scheduled_date: str = Field(description="Date in YYYY-MM-DD format")
    day_of_week: str | None = Field(description="Day abbreviation for weekly schedules")
    cycle_day: int | None = Field(description="Cycle day number for cyclic schedules")
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "123e4567-e89b-12d3-a456-426614174000",
                "session_name": "Upper Body A",
                "scheduled_date": "2025-11-25",
                "day_of_week": "MON",
                "cycle_day": None
            }
        }


class ScheduleResponse(BaseModel):
    """Response schema for generated program schedule.
    
    Examples:
        {
            "program_id": "123e4567-e89b-12d3-a456-426614174000",
            "program_name": "Upper/Lower 4-Day Split",
            "start_date": "2025-11-25",
            "end_date": "2026-01-19",
            "weeks": 8,
            "scheduled_sessions": [...]
        }
    """
    
    program_id: UUID
    program_name: str
    start_date: str
    end_date: str
    weeks: int
    scheduled_sessions: list[ScheduledSessionResponse]
    
    class Config:
        json_schema_extra = {
            "example": {
                "program_id": "123e4567-e89b-12d3-a456-426614174000",
                "program_name": "Upper/Lower 4-Day Split",
                "start_date": "2025-11-25",
                "end_date": "2026-01-19",
                "weeks": 8,
                "scheduled_sessions": [
                    {
                        "session_id": "123e4567-e89b-12d3-a456-426614174000",
                        "session_name": "Upper Body A",
                        "scheduled_date": "2025-11-25",
                        "day_of_week": "MON",
                        "cycle_day": None
                    }
                ]
            }
        }
