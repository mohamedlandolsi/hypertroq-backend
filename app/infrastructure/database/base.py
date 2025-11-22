"""Database base classes and mixins."""
from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import DateTime, Boolean, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, declared_attr
from sqlalchemy.dialects.postgresql import UUID


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    
    @declared_attr.directive
    def __tablename__(cls) -> str:
        """Generate __tablename__ automatically from class name."""
        return cls.__name__.lower() + 's'


class UUIDMixin:
    """Mixin that adds a UUID primary key to a model."""
    
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        index=True,
        doc="Unique identifier"
    )


class TimestampMixin:
    """Mixin that adds created_at and updated_at timestamps to a model."""
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Timestamp when record was created"
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="Timestamp when record was last updated"
    )


class SoftDeleteMixin:
    """Mixin that adds soft delete support to a model."""
    
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        doc="Flag indicating if record is soft deleted"
    )
    
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp when record was soft deleted"
    )
    
    def soft_delete(self) -> None:
        """Mark this record as deleted."""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
    
    def restore(self) -> None:
        """Restore a soft-deleted record."""
        self.is_deleted = False
        self.deleted_at = None


class BaseModel(Base, UUIDMixin, TimestampMixin):
    """
    Base model class with UUID, timestamps, and common functionality.
    
    Inherit from this class for models that need:
    - UUID primary key
    - created_at and updated_at timestamps
    """
    __abstract__ = True
    
    def to_dict(self) -> dict[str, Any]:
        """Convert model instance to dictionary."""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
    
    def __repr__(self) -> str:
        """String representation of the model."""
        return f"<{self.__class__.__name__}(id={self.id})>"


class SoftDeleteModel(BaseModel, SoftDeleteMixin):
    """
    Base model class with UUID, timestamps, and soft delete support.
    
    Inherit from this class for models that need:
    - UUID primary key
    - created_at and updated_at timestamps
    - Soft delete functionality
    """
    __abstract__ = True
