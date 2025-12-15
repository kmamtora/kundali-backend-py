"""
Cache dependency for FastAPI dependency injection.

This module provides Redis connection pooling and cache service
dependency injection for FastAPI endpoints.
"""

from collections.abc import AsyncGenerator
from typing import Annotated

import redis.asyncio as redis
from fastapi import Depends

from app.core.settings import settings
from app.services.cache import CacheService


# Global Redis connection pool
_redis_pool: redis.ConnectionPool | None = None


def get_redis_pool() -> redis.ConnectionPool:
    """
    Get or create Redis connection pool.
    
    Creates a singleton connection pool for Redis connections with
    configured pool size and connection settings.
    
    Returns:
        Redis connection pool instance
    """
    global _redis_pool
    
    if _redis_pool is None:
        _redis_pool = redis.ConnectionPool.from_url(
            settings.REDIS_URL,
            max_connections=settings.REDIS_POOL_SIZE,
            decode_responses=False,  # We handle decoding in CacheService
            socket_connect_timeout=5,
            socket_keepalive=True,
            health_check_interval=30,
        )
    
    return _redis_pool


async def get_redis_client() -> AsyncGenerator[redis.Redis, None]:
    """
    Get Redis client from connection pool.
    
    FastAPI dependency that provides an async Redis client instance
    from the connection pool. Automatically closes the connection
    when the request is complete.
    
    Yields:
        Async Redis client instance
    """
    pool = get_redis_pool()
    client = redis.Redis(connection_pool=pool)
    
    try:
        yield client
    finally:
        await client.aclose()


async def get_cache_service(
    redis_client: Annotated[redis.Redis, Depends(get_redis_client)],
) -> CacheService:
    """
    Get cache service instance.
    
    FastAPI dependency that provides a CacheService instance
    with an injected Redis client.
    
    Args:
        redis_client: Redis client from dependency injection
        
    Returns:
        CacheService instance
    """
    return CacheService(redis_client)


async def close_redis_pool() -> None:
    """
    Close Redis connection pool.
    
    Should be called during application shutdown to properly
    close all Redis connections in the pool.
    """
    global _redis_pool
    
    if _redis_pool is not None:
        await _redis_pool.aclose()
        _redis_pool = None


# Type alias for cache service dependency
CacheServiceDep = Annotated[CacheService, Depends(get_cache_service)]
