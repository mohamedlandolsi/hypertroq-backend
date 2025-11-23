"""
Custom exceptions for the application.

Provides domain-specific exceptions with consistent error codes,
status codes, and error messages.
"""

from typing import Any


class ErrorCode:
    """
    Error codes for all application exceptions.
    
    Provides consistent error codes for client-side error handling
    and internationalization.
    """
    
    # Generic errors
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    
    # Authentication errors (401)
    AUTHENTICATION_REQUIRED = "AUTHENTICATION_REQUIRED"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    TOKEN_INVALID = "TOKEN_INVALID"
    EMAIL_NOT_VERIFIED = "EMAIL_NOT_VERIFIED"
    
    # Authorization errors (403)
    PERMISSION_DENIED = "PERMISSION_DENIED"
    INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS"
    ADMIN_REQUIRED = "ADMIN_REQUIRED"
    ORGANIZATION_ACCESS_DENIED = "ORGANIZATION_ACCESS_DENIED"
    
    # Not found errors (404)
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    USER_NOT_FOUND = "USER_NOT_FOUND"
    ORGANIZATION_NOT_FOUND = "ORGANIZATION_NOT_FOUND"
    PROGRAM_NOT_FOUND = "PROGRAM_NOT_FOUND"
    SESSION_NOT_FOUND = "SESSION_NOT_FOUND"
    EXERCISE_NOT_FOUND = "EXERCISE_NOT_FOUND"
    
    # Validation errors (422)
    INVALID_INPUT = "INVALID_INPUT"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    INVALID_EMAIL = "INVALID_EMAIL"
    INVALID_PASSWORD = "INVALID_PASSWORD"
    PASSWORD_TOO_WEAK = "PASSWORD_TOO_WEAK"
    INVALID_UUID = "INVALID_UUID"
    INVALID_DATE_FORMAT = "INVALID_DATE_FORMAT"
    
    # Subscription errors (402)
    SUBSCRIPTION_REQUIRED = "SUBSCRIPTION_REQUIRED"
    PRO_TIER_REQUIRED = "PRO_TIER_REQUIRED"
    FEATURE_NOT_AVAILABLE = "FEATURE_NOT_AVAILABLE"
    SUBSCRIPTION_EXPIRED = "SUBSCRIPTION_EXPIRED"
    SUBSCRIPTION_CANCELLED = "SUBSCRIPTION_CANCELLED"
    
    # Rate limit errors (429)
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    TOO_MANY_REQUESTS = "TOO_MANY_REQUESTS"
    AI_QUERY_LIMIT_EXCEEDED = "AI_QUERY_LIMIT_EXCEEDED"
    
    # Conflict errors (409)
    RESOURCE_ALREADY_EXISTS = "RESOURCE_ALREADY_EXISTS"
    EMAIL_ALREADY_REGISTERED = "EMAIL_ALREADY_REGISTERED"
    DUPLICATE_ENTRY = "DUPLICATE_ENTRY"
    
    # Business logic errors (400)
    INVALID_OPERATION = "INVALID_OPERATION"
    ACCOUNT_DISABLED = "ACCOUNT_DISABLED"
    ACCOUNT_DELETED = "ACCOUNT_DELETED"
    INVALID_FILE_TYPE = "INVALID_FILE_TYPE"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    INVALID_MUSCLE_GROUP = "INVALID_MUSCLE_GROUP"
    INVALID_EQUIPMENT = "INVALID_EQUIPMENT"


class AppException(Exception):
    """
    Base exception for all application exceptions.
    
    Attributes:
        message: Human-readable error message
        error_code: Machine-readable error code
        status_code: HTTP status code
        details: Additional error context
    """
    
    def __init__(
        self,
        message: str,
        error_code: str = ErrorCode.INTERNAL_SERVER_ERROR,
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ) -> None:
        """
        Initialize application exception.
        
        Args:
            message: Human-readable error message
            error_code: Machine-readable error code
            status_code: HTTP status code
            details: Additional error context
        """
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)
    
    def __str__(self) -> str:
        """Return string representation."""
        return f"{self.error_code}: {self.message}"
    
    def __repr__(self) -> str:
        """Return detailed representation."""
        return (
            f"{self.__class__.__name__}("
            f"message={self.message!r}, "
            f"error_code={self.error_code!r}, "
            f"status_code={self.status_code}, "
            f"details={self.details!r})"
        )


class AuthenticationException(AppException):
    """
    Authentication failed exception (401 Unauthorized).
    
    Raised when:
    - User is not authenticated
    - Credentials are invalid
    - Token is expired or invalid
    - Email is not verified
    """
    
    def __init__(
        self,
        message: str = "Authentication required",
        error_code: str = ErrorCode.AUTHENTICATION_REQUIRED,
        details: dict[str, Any] | None = None,
    ) -> None:
        """
        Initialize authentication exception.
        
        Args:
            message: Human-readable error message
            error_code: Machine-readable error code
            details: Additional error context
        """
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=401,
            details=details,
        )


class AuthorizationException(AppException):
    """
    Authorization failed exception (403 Forbidden).
    
    Raised when:
    - User lacks required permissions
    - User is not admin but admin access required
    - User cannot access another organization's resources
    """
    
    def __init__(
        self,
        message: str = "Permission denied",
        error_code: str = ErrorCode.PERMISSION_DENIED,
        details: dict[str, Any] | None = None,
    ) -> None:
        """
        Initialize authorization exception.
        
        Args:
            message: Human-readable error message
            error_code: Machine-readable error code
            details: Additional error context
        """
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=403,
            details=details,
        )


class NotFoundException(AppException):
    """
    Resource not found exception (404 Not Found).
    
    Raised when:
    - Requested resource does not exist
    - User/organization/program/exercise not found
    """
    
    def __init__(
        self,
        message: str = "Resource not found",
        error_code: str = ErrorCode.RESOURCE_NOT_FOUND,
        details: dict[str, Any] | None = None,
    ) -> None:
        """
        Initialize not found exception.
        
        Args:
            message: Human-readable error message
            error_code: Machine-readable error code
            details: Additional error context
        """
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=404,
            details=details,
        )


class ValidationException(AppException):
    """
    Validation failed exception (422 Unprocessable Entity).
    
    Raised when:
    - Request data is invalid
    - Required fields are missing
    - Data format is incorrect
    - Business rules validation fails
    """
    
    def __init__(
        self,
        message: str = "Validation failed",
        error_code: str = ErrorCode.VALIDATION_ERROR,
        details: dict[str, Any] | None = None,
    ) -> None:
        """
        Initialize validation exception.
        
        Args:
            message: Human-readable error message
            error_code: Machine-readable error code
            details: Additional error context (field errors)
        """
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=422,
            details=details,
        )


class SubscriptionRequiredException(AppException):
    """
    Subscription required exception (402 Payment Required).
    
    Raised when:
    - User tries to access PRO features on FREE tier
    - Subscription has expired
    - Subscription has been cancelled
    - Feature not available for current subscription tier
    """
    
    def __init__(
        self,
        message: str = "This feature requires a PRO subscription",
        error_code: str = ErrorCode.SUBSCRIPTION_REQUIRED,
        details: dict[str, Any] | None = None,
    ) -> None:
        """
        Initialize subscription required exception.
        
        Args:
            message: Human-readable error message
            error_code: Machine-readable error code
            details: Additional error context (required tier, upgrade URL)
        """
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=402,
            details=details,
        )


class RateLimitException(AppException):
    """
    Rate limit exceeded exception (429 Too Many Requests).
    
    Raised when:
    - User exceeds API rate limits
    - Too many requests in time window
    - AI query limit exceeded for FREE tier
    """
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        error_code: str = ErrorCode.RATE_LIMIT_EXCEEDED,
        details: dict[str, Any] | None = None,
    ) -> None:
        """
        Initialize rate limit exception.
        
        Args:
            message: Human-readable error message
            error_code: Machine-readable error code
            details: Additional error context (limit, reset time)
        """
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=429,
            details=details,
        )


class ConflictException(AppException):
    """
    Resource conflict exception (409 Conflict).
    
    Raised when:
    - Resource already exists
    - Email already registered
    - Duplicate entry
    """
    
    def __init__(
        self,
        message: str = "Resource already exists",
        error_code: str = ErrorCode.RESOURCE_ALREADY_EXISTS,
        details: dict[str, Any] | None = None,
    ) -> None:
        """
        Initialize conflict exception.
        
        Args:
            message: Human-readable error message
            error_code: Machine-readable error code
            details: Additional error context
        """
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=409,
            details=details,
        )


class BadRequestException(AppException):
    """
    Bad request exception (400 Bad Request).
    
    Raised when:
    - Invalid operation requested
    - Account is disabled/deleted
    - Invalid file type or size
    - Business logic violation
    """
    
    def __init__(
        self,
        message: str = "Bad request",
        error_code: str = ErrorCode.INVALID_OPERATION,
        details: dict[str, Any] | None = None,
    ) -> None:
        """
        Initialize bad request exception.
        
        Args:
            message: Human-readable error message
            error_code: Machine-readable error code
            details: Additional error context
        """
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=400,
            details=details,
        )


# Convenience factory functions for common exceptions


def user_not_found(user_id: str | None = None) -> NotFoundException:
    """Create user not found exception."""
    details = {"user_id": user_id} if user_id else {}
    return NotFoundException(
        message="User not found",
        error_code=ErrorCode.USER_NOT_FOUND,
        details=details,
    )


def organization_not_found(org_id: str | None = None) -> NotFoundException:
    """Create organization not found exception."""
    details = {"organization_id": org_id} if org_id else {}
    return NotFoundException(
        message="Organization not found",
        error_code=ErrorCode.ORGANIZATION_NOT_FOUND,
        details=details,
    )


def program_not_found(program_id: str | None = None) -> NotFoundException:
    """Create program not found exception."""
    details = {"program_id": program_id} if program_id else {}
    return NotFoundException(
        message="Program not found",
        error_code=ErrorCode.PROGRAM_NOT_FOUND,
        details=details,
    )


def exercise_not_found(exercise_id: str | None = None) -> NotFoundException:
    """Create exercise not found exception."""
    details = {"exercise_id": exercise_id} if exercise_id else {}
    return NotFoundException(
        message="Exercise not found",
        error_code=ErrorCode.EXERCISE_NOT_FOUND,
        details=details,
    )


def invalid_credentials() -> AuthenticationException:
    """Create invalid credentials exception."""
    return AuthenticationException(
        message="Invalid email or password",
        error_code=ErrorCode.INVALID_CREDENTIALS,
    )


def token_expired() -> AuthenticationException:
    """Create token expired exception."""
    return AuthenticationException(
        message="Authentication token has expired",
        error_code=ErrorCode.TOKEN_EXPIRED,
    )


def token_invalid() -> AuthenticationException:
    """Create invalid token exception."""
    return AuthenticationException(
        message="Invalid authentication token",
        error_code=ErrorCode.TOKEN_INVALID,
    )


def email_not_verified() -> AuthenticationException:
    """Create email not verified exception."""
    return AuthenticationException(
        message="Email address not verified. Please check your email for verification link.",
        error_code=ErrorCode.EMAIL_NOT_VERIFIED,
    )


def admin_required() -> AuthorizationException:
    """Create admin required exception."""
    return AuthorizationException(
        message="Administrator privileges required",
        error_code=ErrorCode.ADMIN_REQUIRED,
    )


def insufficient_permissions(resource: str | None = None) -> AuthorizationException:
    """Create insufficient permissions exception."""
    details = {"resource": resource} if resource else {}
    return AuthorizationException(
        message="You do not have permission to perform this action",
        error_code=ErrorCode.INSUFFICIENT_PERMISSIONS,
        details=details,
    )


def pro_tier_required(feature: str | None = None) -> SubscriptionRequiredException:
    """Create PRO tier required exception."""
    details = {"feature": feature, "upgrade_url": "/pricing"} if feature else {"upgrade_url": "/pricing"}
    return SubscriptionRequiredException(
        message=f"This feature ({feature}) requires a PRO subscription" if feature else "PRO subscription required",
        error_code=ErrorCode.PRO_TIER_REQUIRED,
        details=details,
    )


def ai_query_limit_exceeded(limit: int, reset_date: str | None = None) -> RateLimitException:
    """Create AI query limit exceeded exception."""
    details = {"limit": limit}
    if reset_date:
        details["reset_date"] = reset_date
    
    return RateLimitException(
        message=f"AI query limit exceeded. FREE tier allows {limit} queries per month. Upgrade to PRO for unlimited queries.",
        error_code=ErrorCode.AI_QUERY_LIMIT_EXCEEDED,
        details=details,
    )


def rate_limit_exceeded(limit: int, window: str, retry_after: int | None = None) -> RateLimitException:
    """Create rate limit exceeded exception."""
    details = {"limit": limit, "window": window}
    if retry_after:
        details["retry_after"] = retry_after
    
    return RateLimitException(
        message=f"Rate limit exceeded. Maximum {limit} requests per {window}.",
        error_code=ErrorCode.RATE_LIMIT_EXCEEDED,
        details=details,
    )


def email_already_registered(email: str | None = None) -> ConflictException:
    """Create email already registered exception."""
    details = {"email": email} if email else {}
    return ConflictException(
        message="Email address is already registered",
        error_code=ErrorCode.EMAIL_ALREADY_REGISTERED,
        details=details,
    )


def invalid_file_type(allowed_types: list[str] | None = None) -> BadRequestException:
    """Create invalid file type exception."""
    details = {"allowed_types": allowed_types} if allowed_types else {}
    message = f"Invalid file type. Allowed types: {', '.join(allowed_types)}" if allowed_types else "Invalid file type"
    return BadRequestException(
        message=message,
        error_code=ErrorCode.INVALID_FILE_TYPE,
        details=details,
    )


def file_too_large(max_size: int) -> BadRequestException:
    """Create file too large exception."""
    max_size_mb = max_size / (1024 * 1024)
    return BadRequestException(
        message=f"File too large. Maximum size: {max_size_mb:.1f} MB",
        error_code=ErrorCode.FILE_TOO_LARGE,
        details={"max_size_bytes": max_size, "max_size_mb": max_size_mb},
    )


def account_disabled() -> BadRequestException:
    """Create account disabled exception."""
    return BadRequestException(
        message="Account has been disabled. Please contact support.",
        error_code=ErrorCode.ACCOUNT_DISABLED,
    )
