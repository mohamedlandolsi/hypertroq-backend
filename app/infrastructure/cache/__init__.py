"""Cache package initialization."""
from app.infrastructure.cache.redis_client import redis_client

__all__ = ["redis_client"]
