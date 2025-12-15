"""
Cache service for Redis operations.

This module provides a cache service with async Redis client support,
including methods for get, set, delete, and exists operations with TTL support.
Implements JSON serialization/deserialization for complex data types.
"""

import json
from typing import Any

import redis.asyncio as redis

from app.core.settings import settings


class CacheService:
    """
    Redis cache service with async operations.
    
    Provides methods for caching data with TTL support and automatic
    JSON serialization/deserialization for complex data types.
    """
    
    def __init__(self, redis_client: redis.Redis) -> None:
        """
        Initialize cache service with Redis client.
        
        Args:
            redis_client: Async Redis client instance
        """
        self.redis = redis_client
    
    async def get(self, key: str) -> Any | None:
        """
        Get value from cache by key.
        
        Automatically deserializes JSON data. Returns None if key doesn't exist.
        
        Args:
            key: Cache key to retrieve
            
        Returns:
            Cached value or None if not found
        """
        value = await self.redis.get(key)
        if value is None:
            return None
        
        try:
            # Try to deserialize as JSON
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            # Return raw value if not JSON
            return value.decode("utf-8") if isinstance(value, bytes) else value
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
    ) -> bool:
        """
        Set value in cache with optional TTL.
        
        Automatically serializes complex data types to JSON.
        
        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized if not string/bytes)
            ttl: Time to live in seconds (uses default from settings if not provided)
            
        Returns:
            True if successful, False otherwise
        """
        # Use default TTL from settings if not provided
        if ttl is None:
            ttl = settings.CACHE_TTL
        
        # Serialize value to JSON if it's not already a string or bytes
        if not isinstance(value, (str, bytes)):
            try:
                value = json.dumps(value)
            except (TypeError, ValueError):
                # If serialization fails, convert to string
                value = str(value)
        
        # Set value with TTL
        if ttl > 0:
            result = await self.redis.setex(key, ttl, value)
        else:
            result = await self.redis.set(key, value)
        
        return bool(result)
    
    async def delete(self, key: str) -> bool:
        """
        Delete key from cache.
        
        Args:
            key: Cache key to delete
            
        Returns:
            True if key was deleted, False if key didn't exist
        """
        result = await self.redis.delete(key)
        return bool(result)
    
    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.
        
        Args:
            key: Cache key to check
            
        Returns:
            True if key exists, False otherwise
        """
        result = await self.redis.exists(key)
        return bool(result)
    
    async def get_many(self, keys: list[str]) -> dict[str, Any]:
        """
        Get multiple values from cache by keys.
        
        Args:
            keys: List of cache keys to retrieve
            
        Returns:
            Dictionary mapping keys to their values (excludes non-existent keys)
        """
        if not keys:
            return {}
        
        values = await self.redis.mget(keys)
        result = {}
        
        for key, value in zip(keys, values, strict=False):
            if value is not None:
                try:
                    result[key] = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    result[key] = value.decode("utf-8") if isinstance(value, bytes) else value
        
        return result
    
    async def set_many(
        self,
        mapping: dict[str, Any],
        ttl: int | None = None,
    ) -> bool:
        """
        Set multiple key-value pairs in cache.
        
        Args:
            mapping: Dictionary of key-value pairs to cache
            ttl: Time to live in seconds (uses default from settings if not provided)
            
        Returns:
            True if successful, False otherwise
        """
        if not mapping:
            return True
        
        # Use default TTL from settings if not provided
        if ttl is None:
            ttl = settings.CACHE_TTL
        
        # Serialize values
        serialized_mapping = {}
        for key, value in mapping.items():
            if not isinstance(value, (str, bytes)):
                try:
                    serialized_mapping[key] = json.dumps(value)
                except (TypeError, ValueError):
                    serialized_mapping[key] = str(value)
            else:
                serialized_mapping[key] = value
        
        # Use pipeline for atomic operation
        async with self.redis.pipeline() as pipe:
            for key, value in serialized_mapping.items():
                if ttl > 0:
                    pipe.setex(key, ttl, value)
                else:
                    pipe.set(key, value)
            await pipe.execute()
        
        return True
    
    async def delete_many(self, keys: list[str]) -> int:
        """
        Delete multiple keys from cache.
        
        Args:
            keys: List of cache keys to delete
            
        Returns:
            Number of keys deleted
        """
        if not keys:
            return 0
        
        result = await self.redis.delete(*keys)
        return int(result)
    
    async def clear_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching a pattern.
        
        Args:
            pattern: Redis key pattern (e.g., "user:*")
            
        Returns:
            Number of keys deleted
        """
        keys = []
        async for key in self.redis.scan_iter(match=pattern):
            keys.append(key)
        
        if keys:
            return await self.delete_many([k.decode("utf-8") if isinstance(k, bytes) else k for k in keys])
        
        return 0
    
    async def increment(self, key: str, amount: int = 1) -> int:
        """
        Increment a numeric value in cache.
        
        Args:
            key: Cache key
            amount: Amount to increment by (default: 1)
            
        Returns:
            New value after increment
        """
        result = await self.redis.incrby(key, amount)
        return int(result)
    
    async def decrement(self, key: str, amount: int = 1) -> int:
        """
        Decrement a numeric value in cache.
        
        Args:
            key: Cache key
            amount: Amount to decrement by (default: 1)
            
        Returns:
            New value after decrement
        """
        result = await self.redis.decrby(key, amount)
        return int(result)
    
    async def expire(self, key: str, ttl: int) -> bool:
        """
        Set expiration time for a key.
        
        Args:
            key: Cache key
            ttl: Time to live in seconds
            
        Returns:
            True if expiration was set, False if key doesn't exist
        """
        result = await self.redis.expire(key, ttl)
        return bool(result)
    
    async def ttl(self, key: str) -> int:
        """
        Get remaining time to live for a key.
        
        Args:
            key: Cache key
            
        Returns:
            TTL in seconds, -1 if key exists but has no expiration, -2 if key doesn't exist
        """
        result = await self.redis.ttl(key)
        return int(result)
    
    async def ping(self) -> bool:
        """
        Check if Redis connection is alive.
        
        Returns:
            True if connection is alive, False otherwise
        """
        try:
            await self.redis.ping()
            return True
        except Exception:
            return False
    
    async def close(self) -> None:
        """Close Redis connection."""
        await self.redis.aclose()
