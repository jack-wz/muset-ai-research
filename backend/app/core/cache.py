"""Redis caching strategies."""
import json
import logging
from functools import wraps
from typing import Any, Callable, Optional, TypeVar, Union

import redis.asyncio as redis
from redis.asyncio import Redis

from app.core.config import settings
from app.core.metrics import track_cache_operation

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CacheManager:
    """Redis cache manager."""

    def __init__(self, redis_url: Optional[str] = None):
        """Initialize cache manager.

        Args:
            redis_url: Redis connection URL
        """
        self.redis_url = redis_url or settings.redis_url
        self._client: Optional[Redis] = None

    async def get_client(self) -> Redis:
        """Get Redis client.

        Returns:
            Redis client instance
        """
        if self._client is None:
            self._client = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                max_connections=settings.redis_max_connections,
            )
        return self._client

    async def close(self) -> None:
        """Close Redis connection."""
        if self._client:
            await self._client.close()
            self._client = None

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        try:
            client = await self.get_client()
            value = await client.get(key)

            if value is not None:
                track_cache_operation("get", "hit")
                logger.debug(f"Cache hit for key: {key}")
                return json.loads(value)
            else:
                track_cache_operation("get", "miss")
                logger.debug(f"Cache miss for key: {key}")
                return None
        except Exception as e:
            track_cache_operation("get", "error")
            logger.error(f"Cache get error for key {key}: {str(e)}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        expire: Optional[int] = None,
    ) -> bool:
        """Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            expire: Expiration time in seconds

        Returns:
            True if successful, False otherwise
        """
        try:
            client = await self.get_client()
            serialized = json.dumps(value)

            if expire:
                await client.setex(key, expire, serialized)
            else:
                await client.set(key, serialized)

            track_cache_operation("set", "success")
            logger.debug(f"Cache set for key: {key} (expire: {expire}s)")
            return True
        except Exception as e:
            track_cache_operation("set", "error")
            logger.error(f"Cache set error for key {key}: {str(e)}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete value from cache.

        Args:
            key: Cache key

        Returns:
            True if successful, False otherwise
        """
        try:
            client = await self.get_client()
            await client.delete(key)
            track_cache_operation("delete", "success")
            logger.debug(f"Cache delete for key: {key}")
            return True
        except Exception as e:
            track_cache_operation("delete", "error")
            logger.error(f"Cache delete error for key {key}: {str(e)}")
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """Delete keys matching pattern.

        Args:
            pattern: Key pattern (e.g., "user:*")

        Returns:
            Number of keys deleted
        """
        try:
            client = await self.get_client()
            keys = await client.keys(pattern)
            if keys:
                deleted = await client.delete(*keys)
                logger.debug(f"Deleted {deleted} keys matching pattern: {pattern}")
                return deleted
            return 0
        except Exception as e:
            logger.error(f"Cache delete pattern error for {pattern}: {str(e)}")
            return 0

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if key exists, False otherwise
        """
        try:
            client = await self.get_client()
            return await client.exists(key) > 0
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {str(e)}")
            return False

    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment value in cache.

        Args:
            key: Cache key
            amount: Amount to increment by

        Returns:
            New value or None if error
        """
        try:
            client = await self.get_client()
            return await client.incrby(key, amount)
        except Exception as e:
            logger.error(f"Cache increment error for key {key}: {str(e)}")
            return None

    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration on key.

        Args:
            key: Cache key
            seconds: Expiration time in seconds

        Returns:
            True if successful, False otherwise
        """
        try:
            client = await self.get_client()
            return await client.expire(key, seconds)
        except Exception as e:
            logger.error(f"Cache expire error for key {key}: {str(e)}")
            return False


# Global cache manager
cache_manager = CacheManager()


def cached(
    key_prefix: str,
    expire: int = 300,
    key_builder: Optional[Callable[..., str]] = None,
):
    """Decorator for caching function results.

    Args:
        key_prefix: Cache key prefix
        expire: Expiration time in seconds
        key_builder: Custom key builder function

    Returns:
        Decorated function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            # Build cache key
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                # Default key building
                key_parts = [key_prefix]
                if args:
                    key_parts.extend(str(arg) for arg in args)
                if kwargs:
                    key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
                cache_key = ":".join(key_parts)

            # Try to get from cache
            cached_value = await cache_manager.get(cache_key)
            if cached_value is not None:
                return cached_value

            # Execute function
            result = await func(*args, **kwargs)

            # Store in cache
            await cache_manager.set(cache_key, result, expire)

            return result

        return wrapper
    return decorator


class CacheStrategy:
    """Cache strategies for different use cases."""

    @staticmethod
    async def cache_aside(
        key: str,
        fetch_func: Callable[[], T],
        expire: int = 300,
    ) -> Optional[T]:
        """Cache-aside (lazy loading) strategy.

        Args:
            key: Cache key
            fetch_func: Function to fetch data if not in cache
            expire: Expiration time in seconds

        Returns:
            Cached or fetched value
        """
        # Try to get from cache
        cached_value = await cache_manager.get(key)
        if cached_value is not None:
            return cached_value

        # Fetch from source
        value = await fetch_func() if asyncio.iscoroutinefunction(fetch_func) else fetch_func()

        # Store in cache
        if value is not None:
            await cache_manager.set(key, value, expire)

        return value

    @staticmethod
    async def write_through(
        key: str,
        value: Any,
        write_func: Callable[[Any], None],
        expire: int = 300,
    ) -> bool:
        """Write-through strategy.

        Args:
            key: Cache key
            value: Value to write
            write_func: Function to write to persistent storage
            expire: Expiration time in seconds

        Returns:
            True if successful, False otherwise
        """
        # Write to persistent storage first
        try:
            if asyncio.iscoroutinefunction(write_func):
                await write_func(value)
            else:
                write_func(value)
        except Exception as e:
            logger.error(f"Write-through storage error: {str(e)}")
            return False

        # Write to cache
        return await cache_manager.set(key, value, expire)

    @staticmethod
    async def write_behind(
        key: str,
        value: Any,
        write_func: Callable[[Any], None],
        expire: int = 300,
    ) -> bool:
        """Write-behind (write-back) strategy.

        Args:
            key: Cache key
            value: Value to write
            write_func: Function to write to persistent storage
            expire: Expiration time in seconds

        Returns:
            True if cache write successful, False otherwise
        """
        # Write to cache first
        cache_success = await cache_manager.set(key, value, expire)

        # Schedule write to persistent storage
        # (in production, use a task queue like Celery)
        try:
            if asyncio.iscoroutinefunction(write_func):
                await write_func(value)
            else:
                write_func(value)
        except Exception as e:
            logger.error(f"Write-behind storage error: {str(e)}")

        return cache_success


# Import asyncio for coroutine checks
import asyncio
