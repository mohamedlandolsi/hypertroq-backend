"""SQLAlchemy User model."""
from datetime import datetime
from sqlalchemy import Boolean, String, ForeignKey, Enum as SQLEnum, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.infrastructure.database.base import BaseModel
from app.domain.entities.user import UserRole


class UserModel(BaseModel):
    """SQLAlchemy User model mapping to users table."""

    __tablename__ = "users"

    # Basic Information
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
        doc="User's email address (unique, indexed)"
    )
    
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Bcrypt hashed password"
    )
    
    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="User's full name"
    )

    # Status Flags
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        doc="Whether the account is active"
    )
    
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether the email has been verified"
    )

    # Role
    role: Mapped[str] = mapped_column(
        SQLEnum(UserRole, name="user_role"),
        default=UserRole.USER,
        nullable=False,
        doc="User role (USER or ADMIN)"
    )

    # Organization Relationship
    organization_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Foreign key to organization"
    )

    # Optional Profile Image
    profile_image_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        doc="URL to user's profile image"
    )

    # Deletion Grace Period
    deletion_requested_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp when account deletion was requested (for 30-day grace period)"
    )

    # Relationships
    organization: Mapped["OrganizationModel"] = relationship(
        "OrganizationModel",
        back_populates="users",
        lazy="joined"
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"

