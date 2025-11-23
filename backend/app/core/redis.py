"""
Redis connection and cache management.
"""
import json
from typing import Any, Optional
from redis import asyncio as aioredis

from app.core.config import settings


class RedisClient:
    """Redis client wrapper for caching."""

    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None

    async def connect(self) -> None:
        """Connect to Redis."""
        self.redis = await aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self.redis:
            await self.redis.close()

    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        if not self.redis:
            return None

        value = await self.redis.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return None

    async def set(
        self,
        key: str,
        value: Any,
        expire: int = 3600,
    ) -> bool:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            expire: Expiration time in seconds (default: 1 hour)

        Returns:
            True if successful
        """
        if not self.redis:
            return False

        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            return await self.redis.set(key, value, ex=expire)
        except Exception:
            return False

    async def delete(self, key: str) -> bool:
        """
        Delete value from cache.

        Args:
            key: Cache key

        Returns:
            True if successful
        """
        if not self.redis:
            return False

        return await self.redis.delete(key) > 0

    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if exists
        """
        if not self.redis:
            return False

        return await self.redis.exists(key) > 0

    async def expire(self, key: str, seconds: int) -> bool:
        """
        Set expiration time for key.

        Args:
            key: Cache key
            seconds: Expiration time in seconds

        Returns:
            True if successful
        """
        if not self.redis:
            return False

        return await self.redis.expire(key, seconds)

    async def ping(self) -> bool:
        """
        Ping Redis server.

        Returns:
            True if connected
        """
        if not self.redis:
            return False

        try:
            return await self.redis.ping()
        except Exception:
            return False


# Global Redis client instance
redis_client = RedisClient()
