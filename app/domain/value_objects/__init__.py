"""Value objects package."""
from app.domain.value_objects.base import ValueObject
from app.domain.value_objects.email import Email
from app.domain.value_objects.equipment import Equipment
from app.domain.value_objects.muscle_groups import MuscleGroup
from app.domain.value_objects.volume_contribution import VolumeContribution

__all__ = [
    "ValueObject",
    "Email",
    "Equipment",
    "MuscleGroup",
    "VolumeContribution",
]
