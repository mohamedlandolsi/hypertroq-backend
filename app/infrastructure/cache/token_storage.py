"""Token storage service using Redis."""
import logging
from typing import Optional
from uuid import UUID

from app.infrastructure.cache.redis_client import redis_client
from app.core.security import generate_secure_token

logger = logging.getLogger(__name__)


class TokenStorage:
    """Service for storing and retrieving tokens in Redis."""
    
    # Token prefixes for different token types
    PASSWORD_RESET_PREFIX = "pwd_reset:"
    EMAIL_VERIFICATION_PREFIX = "email_verify:"
    
    # Token expiration times (in seconds)
    PASSWORD_RESET_EXPIRY = 3600  # 1 hour
    EMAIL_VERIFICATION_EXPIRY = 86400  # 24 hours
    
    @staticmethod
    async def generate_password_reset_token(user_id: UUID) -> str:
        """
        Generate and store a password reset token.
        
        Args:
            user_id: User UUID
            
        Returns:
            Generated token string
        """
        token = generate_secure_token(32)
        key = f"{TokenStorage.PASSWORD_RESET_PREFIX}{token}"
        
        # Store user_id associated with token
        await redis_client.setex(
            key,
            TokenStorage.PASSWORD_RESET_EXPIRY,
            str(user_id)
        )
        
        logger.info(f"Generated password reset token for user {user_id}")
        return token
    
    @staticmethod
    async def verify_password_reset_token(token: str) -> Optional[UUID]:
        """
        Verify password reset token and return associated user_id.
        
        Args:
            token: Password reset token
            
        Returns:
            User UUID if token is valid, None otherwise
        """
        key = f"{TokenStorage.PASSWORD_RESET_PREFIX}{token}"
        user_id_str = await redis_client.redis.get(key) if redis_client.redis else None
        
        if not user_id_str:
            logger.warning(f"Invalid or expired password reset token: {token[:8]}...")
            return None
        
        try:
            user_id = UUID(user_id_str)
            logger.info(f"Verified password reset token for user {user_id}")
            return user_id
        except (ValueError, AttributeError):
            logger.error(f"Invalid user_id format in token: {user_id_str}")
            return None
    
    @staticmethod
    async def invalidate_password_reset_token(token: str) -> bool:
        """
        Invalidate a password reset token.
        
        Args:
            token: Password reset token
            
        Returns:
            True if token was deleted, False otherwise
        """
        key = f"{TokenStorage.PASSWORD_RESET_PREFIX}{token}"
        deleted = await redis_client.delete(key)
        
        if deleted:
            logger.info(f"Invalidated password reset token: {token[:8]}...")
        
        return deleted
    
    @staticmethod
    async def generate_email_verification_token(user_id: UUID, email: str) -> str:
        """
        Generate and store an email verification token.
        
        Args:
            user_id: User UUID
            email: Email address to verify
            
        Returns:
            Generated token string
        """
        token = generate_secure_token(32)
        key = f"{TokenStorage.EMAIL_VERIFICATION_PREFIX}{token}"
        
        # Store user_id and email associated with token
        value = f"{user_id}:{email}"
        await redis_client.setex(
            key,
            TokenStorage.EMAIL_VERIFICATION_EXPIRY,
            value
        )
        
        logger.info(f"Generated email verification token for user {user_id}")
        return token
    
    @staticmethod
    async def verify_email_verification_token(token: str) -> Optional[tuple[UUID, str]]:
        """
        Verify email verification token and return associated user_id and email.
        
        Args:
            token: Email verification token
            
        Returns:
            Tuple of (user_id, email) if token is valid, None otherwise
        """
        key = f"{TokenStorage.EMAIL_VERIFICATION_PREFIX}{token}"
        value = await redis_client.redis.get(key) if redis_client.redis else None
        
        if not value:
            logger.warning(f"Invalid or expired email verification token: {token[:8]}...")
            return None
        
        try:
            user_id_str, email = value.split(":", 1)
            user_id = UUID(user_id_str)
            logger.info(f"Verified email verification token for user {user_id}")
            return user_id, email
        except (ValueError, AttributeError):
            logger.error(f"Invalid token value format: {value}")
            return None
    
    @staticmethod
    async def invalidate_email_verification_token(token: str) -> bool:
        """
        Invalidate an email verification token.
        
        Args:
            token: Email verification token
            
        Returns:
            True if token was deleted, False otherwise
        """
        key = f"{TokenStorage.EMAIL_VERIFICATION_PREFIX}{token}"
        deleted = await redis_client.delete(key)
        
        if deleted:
            logger.info(f"Invalidated email verification token: {token[:8]}...")
        
        return deleted
    
    @staticmethod
    async def get_all_password_reset_tokens_for_user(user_id: UUID) -> list[str]:
        """
        Get all password reset tokens for a user.
        Useful for invalidating all tokens when password is changed.
        
        Args:
            user_id: User UUID
            
        Returns:
            List of token strings
        """
        if not redis_client.redis:
            return []
        
        pattern = f"{TokenStorage.PASSWORD_RESET_PREFIX}*"
        tokens = []
        
        async for key in redis_client.redis.scan_iter(pattern):
            stored_user_id = await redis_client.redis.get(key)
            if stored_user_id == str(user_id):
                # Extract token from key
                token = key.replace(TokenStorage.PASSWORD_RESET_PREFIX, "")
                tokens.append(token)
        
        return tokens
    
    @staticmethod
    async def invalidate_all_password_reset_tokens_for_user(user_id: UUID) -> int:
        """
        Invalidate all password reset tokens for a user.
        Should be called when password is successfully changed.
        
        Args:
            user_id: User UUID
            
        Returns:
            Number of tokens invalidated
        """
        tokens = await TokenStorage.get_all_password_reset_tokens_for_user(user_id)
        count = 0
        
        for token in tokens:
            if await TokenStorage.invalidate_password_reset_token(token):
                count += 1
        
        logger.info(f"Invalidated {count} password reset tokens for user {user_id}")
        return count


# Global token storage instance
token_storage = TokenStorage()
