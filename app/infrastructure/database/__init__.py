"""Database package initialization."""
from app.infrastructure.database.connection import (
    get_db,
    db_manager,
    init_database,
    close_database,
    get_engine,
    get_session_maker,
)
from app.infrastructure.database.base import (
    Base,
    BaseModel,
    SoftDeleteModel,
    UUIDMixin,
    TimestampMixin,
    SoftDeleteMixin,
)

__all__ = [
    # Connection
    "get_db",
    "db_manager",
    "init_database",
    "close_database",
    "get_engine",
    "get_session_maker",
    # Base classes
    "Base",
    "BaseModel",
    "SoftDeleteModel",
    "UUIDMixin",
    "TimestampMixin",
    "SoftDeleteMixin",
]
