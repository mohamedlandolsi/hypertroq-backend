"""Base entity class for domain entities."""
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4


class Entity:
    """Base class for all domain entities with identity."""

    def __init__(self, id: UUID | None = None) -> None:
        """Initialize entity with unique identifier."""
        self._id = id or uuid4()
        self._created_at = datetime.utcnow()
        self._updated_at = datetime.utcnow()

    @property
    def id(self) -> UUID:
        """Get entity ID."""
        return self._id

    @property
    def created_at(self) -> datetime:
        """Get creation timestamp."""
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        """Get last update timestamp."""
        return self._updated_at

    def __eq__(self, other: Any) -> bool:
        """Check equality based on ID."""
        if not isinstance(other, Entity):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        """Hash based on ID."""
        return hash(self.id)
