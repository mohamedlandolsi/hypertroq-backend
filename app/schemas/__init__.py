"""
Pydantic schemas for API request/response validation.
"""

from app.schemas.auth import (
    MessageResponse,
    PasswordReset,
    PasswordResetConfirm,
    TokenRefresh,
    TokenResponse,
    UserLogin,
    UserRegister,
    UserResponse,
)
from app.schemas.exercise import (
    ExerciseCreate,
    ExerciseFilter,
    ExerciseListResponse,
    ExerciseResponse,
    ExerciseSummaryResponse,
    ExerciseUpdate,
    MuscleContributionResponse,
)
from app.schemas.training_program import (
    CloneProgramRequest,
    CyclicStructureInput,
    MuscleVolumeResponse,
    ProgramCreate,
    ProgramFilter,
    ProgramListItemResponse,
    ProgramListResponse,
    ProgramResponse,
    ProgramStatsResponse,
    ProgramUpdate,
    ScheduledSessionResponse,
    ScheduleGenerateRequest,
    ScheduleResponse,
    SessionCreate,
    SessionResponse,
    SessionUpdate,
    WeeklyStructureInput,
    WorkoutExerciseInput,
    WorkoutExerciseResponse,
)

__all__ = [
    # Auth schemas
    "UserRegister",
    "UserLogin",
    "TokenRefresh",
    "PasswordReset",
    "PasswordResetConfirm",
    "TokenResponse",
    "UserResponse",
    "MessageResponse",
    # Exercise schemas
    "ExerciseCreate",
    "ExerciseUpdate",
    "ExerciseFilter",
    "ExerciseResponse",
    "ExerciseListResponse",
    "ExerciseSummaryResponse",
    "MuscleContributionResponse",
    # Training program schemas
    "ProgramCreate",
    "ProgramUpdate",
    "ProgramFilter",
    "ProgramResponse",
    "ProgramListResponse",
    "ProgramListItemResponse",
    "ProgramStatsResponse",
    "SessionCreate",
    "SessionUpdate",
    "SessionResponse",
    "WorkoutExerciseInput",
    "WorkoutExerciseResponse",
    "MuscleVolumeResponse",
    "WeeklyStructureInput",
    "CyclicStructureInput",
    "CloneProgramRequest",
    "ScheduleGenerateRequest",
    "ScheduleResponse",
    "ScheduledSessionResponse",
]
