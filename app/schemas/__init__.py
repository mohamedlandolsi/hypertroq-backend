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
]
