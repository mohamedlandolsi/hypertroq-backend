"""Redis cache client."""
import json
from typing import Any
import redis.asyncio as aioredis
from app.core.config import settings


class RedisClient:
    """Async Redis client for caching."""

    def __init__(self) -> None:
        """Initialize Redis client."""
        self.redis: aioredis.Redis | None = None

    async def connect(self) -> None:
        """Connect to Redis server."""
        self.redis = await aioredis.from_url(
            str(settings.REDIS_URL),
            encoding="utf-8",
            decode_responses=True
        )

    async def disconnect(self) -> None:
        """Disconnect from Redis server."""
        if self.redis:
            await self.redis.close()

    async def get(self, key: str) -> Any:
        """Get value from cache."""
        if not self.redis:
            return None
        
        value = await self.redis.get(key)
        if value:
            return json.loads(value)
        return None

    async def set(
        self,
        key: str,
        value: Any,
        expire: int = settings.REDIS_CACHE_TTL
    ) -> bool:
        """Set value in cache with expiration."""
        if not self.redis:
            return False
        
        serialized = json.dumps(value)
        return await self.redis.setex(key, expire, serialized)

    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if not self.redis:
            return False
        
        return await self.redis.delete(key) > 0

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        if not self.redis:
            return False
        
        return await self.redis.exists(key) > 0

    async def incr(self, key: str) -> int:
        """Increment value of key by 1."""
        if not self.redis:
            return 0
        
        return await self.redis.incr(key)

    async def setex(self, key: str, seconds: int, value: Any) -> bool:
        """Set key with expiration in seconds."""
        if not self.redis:
            return False
        
        return await self.redis.setex(key, seconds, value)

    async def ttl(self, key: str) -> int:
        """Get time to live for key in seconds."""
        if not self.redis:
            return -1
        
        return await self.redis.ttl(key)

    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration for key in seconds."""
        if not self.redis:
            return False
        
        return await self.redis.expire(key, seconds)

    async def ping(self) -> bool:
        """Ping Redis server to test connection."""
        if not self.redis:
            return False
        
        try:
            await self.redis.ping()
            return True
        except Exception:
            return False


# Global Redis client instance
redis_client = RedisClient()
