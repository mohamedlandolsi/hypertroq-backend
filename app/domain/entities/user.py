"""User entity."""
from datetime import datetime
from enum import Enum
from uuid import UUID
from app.domain.entities.base import Entity
from app.domain.value_objects.email import Email


class UserRole(str, Enum):
    """User role enumeration."""
    USER = "USER"
    ADMIN = "ADMIN"


class User(Entity):
    """User domain entity."""

    def __init__(
        self,
        email: str,
        hashed_password: str,
        full_name: str,
        organization_id: UUID,
        role: UserRole = UserRole.USER,
        is_active: bool = True,
        is_verified: bool = False,
        profile_image_url: str | None = None,
        id: UUID | None = None,
    ) -> None:
        """Initialize User entity.
        
        Args:
            email: User's email address (validated)
            hashed_password: Bcrypt hashed password
            full_name: User's full name
            organization_id: UUID of the organization this user belongs to
            role: User role (USER or ADMIN)
            is_active: Whether the account is active
            is_verified: Whether the email has been verified
            profile_image_url: Optional URL to profile image
            id: Optional UUID (generated if not provided)
            
        Raises:
            ValueError: If email format is invalid or full_name is empty
        """
        super().__init__(id)
        
        # Validate and set email using Email value object
        email_vo = Email(email)
        self._email = email_vo.value
        
        # Validate full_name
        if not full_name or not full_name.strip():
            raise ValueError("Full name cannot be empty")
        
        # Validate hashed_password
        if not hashed_password or len(hashed_password) < 20:
            raise ValueError("Invalid hashed password")
        
        self._hashed_password = hashed_password
        self._full_name = full_name.strip()
        self._organization_id = organization_id
        self._role = role
        self._is_active = is_active
        self._is_verified = is_verified
        self._profile_image_url = profile_image_url

    @property
    def email(self) -> str:
        """Get user email."""
        return self._email

    @property
    def hashed_password(self) -> str:
        """Get hashed password."""
        return self._hashed_password

    @property
    def full_name(self) -> str:
        """Get full name."""
        return self._full_name

    @property
    def organization_id(self) -> UUID:
        """Get organization ID."""
        return self._organization_id

    @property
    def role(self) -> UserRole:
        """Get user role."""
        return self._role

    @property
    def is_active(self) -> bool:
        """Check if user is active."""
        return self._is_active

    @property
    def is_verified(self) -> bool:
        """Check if user email is verified."""
        return self._is_verified

    @property
    def profile_image_url(self) -> str | None:
        """Get profile image URL."""
        return self._profile_image_url

    def is_admin(self) -> bool:
        """Check if user has admin role."""
        return self._role == UserRole.ADMIN

    def activate(self) -> None:
        """Activate user account."""
        self._is_active = True

    def deactivate(self) -> None:
        """Deactivate user account."""
        self._is_active = False

    def verify_email(self) -> None:
        """Mark email as verified."""
        self._is_verified = True

    def update_password(self, hashed_password: str) -> None:
        """Update user password.
        
        Args:
            hashed_password: New bcrypt hashed password
            
        Raises:
            ValueError: If hashed_password is invalid
        """
        if not hashed_password or len(hashed_password) < 20:
            raise ValueError("Invalid hashed password")
        self._hashed_password = hashed_password

    def update_profile(
        self,
        full_name: str | None = None,
        email: str | None = None,
        profile_image_url: str | None = None
    ) -> None:
        """Update user profile information.
        
        Args:
            full_name: New full name
            email: New email address (will be validated)
            profile_image_url: New profile image URL
            
        Raises:
            ValueError: If email format is invalid or full_name is empty
        """
        if full_name is not None:
            if not full_name.strip():
                raise ValueError("Full name cannot be empty")
            self._full_name = full_name.strip()
            
        if email is not None:
            email_vo = Email(email)
            self._email = email_vo.value
            # Reset verification status when email changes
            self._is_verified = False
            
        if profile_image_url is not None:
            self._profile_image_url = profile_image_url

    def promote_to_admin(self) -> None:
        """Promote user to admin role."""
        self._role = UserRole.ADMIN

    def demote_to_user(self) -> None:
        """Demote user to regular user role."""
        self._role = UserRole.USER
