"""User entity."""
from datetime import datetime
from uuid import UUID
from app.domain.entities.base import Entity


class User(Entity):
    """User domain entity."""

    def __init__(
        self,
        email: str,
        hashed_password: str,
        full_name: str | None = None,
        is_active: bool = True,
        is_superuser: bool = False,
        id: UUID | None = None,
    ) -> None:
        """Initialize User entity."""
        super().__init__(id)
        self._email = email
        self._hashed_password = hashed_password
        self._full_name = full_name
        self._is_active = is_active
        self._is_superuser = is_superuser

    @property
    def email(self) -> str:
        """Get user email."""
        return self._email

    @property
    def hashed_password(self) -> str:
        """Get hashed password."""
        return self._hashed_password

    @property
    def full_name(self) -> str | None:
        """Get full name."""
        return self._full_name

    @property
    def is_active(self) -> bool:
        """Check if user is active."""
        return self._is_active

    @property
    def is_superuser(self) -> bool:
        """Check if user is superuser."""
        return self._is_superuser

    def activate(self) -> None:
        """Activate user account."""
        self._is_active = True

    def deactivate(self) -> None:
        """Deactivate user account."""
        self._is_active = False

    def update_password(self, hashed_password: str) -> None:
        """Update user password."""
        self._hashed_password = hashed_password

    def update_profile(self, full_name: str | None = None, email: str | None = None) -> None:
        """Update user profile."""
        if full_name is not None:
            self._full_name = full_name
        if email is not None:
            self._email = email
