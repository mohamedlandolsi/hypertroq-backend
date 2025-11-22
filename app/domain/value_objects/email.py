"""Email value object."""
import re
from app.domain.value_objects.base import ValueObject


class Email(ValueObject):
    """Email value object with validation."""

    EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

    def __init__(self, value: str) -> None:
        """Initialize email with validation."""
        self._validate(value)
        self._value = value.lower()

    @property
    def value(self) -> str:
        """Get email value."""
        return self._value

    def _validate(self, value: str) -> None:
        """Validate email format."""
        if not value or not isinstance(value, str):
            raise ValueError("Email must be a non-empty string")
        
        if not self.EMAIL_REGEX.match(value):
            raise ValueError(f"Invalid email format: {value}")

    def __str__(self) -> str:
        """String representation."""
        return self._value
