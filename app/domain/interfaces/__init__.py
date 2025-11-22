"""Domain interfaces package."""
from app.domain.interfaces.repository import IRepository
from app.domain.interfaces.user_repository import IUserRepository

__all__ = ["IRepository", "IUserRepository"]
