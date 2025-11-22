"""Security utilities for authentication and authorization."""
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
import secrets
from jose import JWTError, jwt, ExpiredSignatureError
from passlib.context import CryptContext
from fastapi import HTTPException, status

from app.core.config import settings


# Password hashing context with secure configuration
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12  # Higher rounds for better security
)


# Exception classes for better error handling
class InvalidTokenError(HTTPException):
    """Raised when token is invalid."""
    def __init__(self, detail: str = "Could not validate credentials"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class TokenExpiredError(HTTPException):
    """Raised when token has expired."""
    def __init__(self, detail: str = "Token has expired"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


# Password functions
def hash_password(password: str) -> str:
    """
    Hash a plain password using bcrypt.
    
    Args:
        password: Plain text password to hash
        
    Returns:
        Hashed password string
        
    Raises:
        ValueError: If password is empty or too weak
    """
    if not password or len(password) < 8:
        raise ValueError("Password must be at least 8 characters long")
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to compare against
        
    Returns:
        True if password matches, False otherwise
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """
    Alias for hash_password for backward compatibility.
    
    Args:
        password: Plain text password to hash
        
    Returns:
        Hashed password string
    """
    return hash_password(password)


# JWT Token functions
def create_access_token(
    subject: str | Any,
    expires_delta: Optional[timedelta] = None,
    additional_claims: Optional[Dict[str, Any]] = None
) -> str:
    """
    Create a JWT access token.
    
    Args:
        subject: Token subject (usually user ID)
        expires_delta: Custom expiration time delta
        additional_claims: Additional claims to include in token
        
    Returns:
        Encoded JWT token string
    """
    now = datetime.now(timezone.utc)
    
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {
        "exp": expire,
        "iat": now,
        "sub": str(subject),
        "type": "access",
        "jti": secrets.token_urlsafe(16)  # Unique token ID
    }
    
    # Add any additional claims
    if additional_claims:
        to_encode.update(additional_claims)
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(
    subject: str | Any,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT refresh token.
    
    Args:
        subject: Token subject (usually user ID)
        expires_delta: Custom expiration time delta
        
    Returns:
        Encoded JWT token string
    """
    now = datetime.now(timezone.utc)
    
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode = {
        "exp": expire,
        "iat": now,
        "sub": str(subject),
        "type": "refresh",
        "jti": secrets.token_urlsafe(16)
    }
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def decode_token(token: str) -> Dict[str, Any]:
    """
    Decode and verify a JWT token.
    
    Args:
        token: JWT token string to decode
        
    Returns:
        Token payload as dictionary
        
    Raises:
        TokenExpiredError: If token has expired
        InvalidTokenError: If token is invalid
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except ExpiredSignatureError:
        raise TokenExpiredError("Token has expired")
    except JWTError as e:
        raise InvalidTokenError(f"Invalid token: {str(e)}")
    except Exception as e:
        raise InvalidTokenError(f"Could not validate credentials: {str(e)}")


def verify_token_type(payload: Dict[str, Any], expected_type: str) -> None:
    """
    Verify that the token is of the expected type.
    
    Args:
        payload: Decoded token payload
        expected_type: Expected token type ('access' or 'refresh')
        
    Raises:
        InvalidTokenError: If token type doesn't match
    """
    token_type = payload.get("type")
    if token_type != expected_type:
        raise InvalidTokenError(
            f"Invalid token type. Expected {expected_type}, got {token_type}"
        )


def verify_token_subject(payload: Dict[str, Any]) -> str:
    """
    Verify and extract subject from token payload.
    
    Args:
        payload: Decoded token payload
        
    Returns:
        Token subject (user ID)
        
    Raises:
        InvalidTokenError: If subject is missing
    """
    subject = payload.get("sub")
    if not subject:
        raise InvalidTokenError("Token subject (sub) is missing")
    return subject


# Utility functions
def generate_secure_token(length: int = 32) -> str:
    """
    Generate a cryptographically secure random token.
    
    Args:
        length: Length of the token in bytes
        
    Returns:
        URL-safe random token string
    """
    return secrets.token_urlsafe(length)


def constant_time_compare(val1: str, val2: str) -> bool:
    """
    Perform constant-time string comparison to prevent timing attacks.
    
    Args:
        val1: First string to compare
        val2: Second string to compare
        
    Returns:
        True if strings match, False otherwise
    """
    return secrets.compare_digest(val1.encode(), val2.encode())
