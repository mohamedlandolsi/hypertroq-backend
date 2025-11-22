"""Value objects package."""
from app.domain.value_objects.base import ValueObject
from app.domain.value_objects.email import Email

__all__ = ["ValueObject", "Email"]
