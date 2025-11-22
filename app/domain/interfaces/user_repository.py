"""User repository interface."""
from abc import abstractmethod
from app.domain.interfaces.repository import IRepository
from app.domain.entities.user import User


class IUserRepository(IRepository[User]):
    """User repository interface."""

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None:
        """Get user by email address."""
        pass

    @abstractmethod
    async def exists_by_email(self, email: str) -> bool:
        """Check if user exists by email."""
        pass
