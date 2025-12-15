"""
Rate limiting middleware using token bucket algorithm.

This module provides distributed rate limiting using Redis for storage
and implements the token bucket algorithm for rate limiting.
"""

import time
from typing import Callable

import redis.asyncio as redis
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.settings import settings
from app.services.cache import CacheService


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using token bucket algorithm.
    
    Implements distributed rate limiting with Redis backend:
    - Per-client rate limiting (by IP or API key)
    - Configurable limits per minute and hour
    - Token bucket algorithm for smooth rate limiting
    - Rate limit headers in responses
    """
    
    def __init__(self, app) -> None:
        """
        Initialize rate limiting middleware.
        
        Args:
            app: FastAPI application instance
        """
        super().__init__(app)
        # Create Redis client for rate limiting
        self.redis_client = redis.from_url(
            settings.REDIS_URL,
            max_connections=settings.REDIS_POOL_SIZE,
            decode_responses=False,
            socket_connect_timeout=5,
            socket_keepalive=True,
        )
        self.cache = CacheService(self.redis_client)
        self.enabled = settings.RATE_LIMIT_ENABLED
        self.limit_per_minute = settings.RATE_LIMIT_PER_MINUTE
        self.limit_per_hour = settings.RATE_LIMIT_PER_HOUR
    
    def _get_client_identifier(self, request: Request) -> str:
        """
        Get unique identifier for the client.
        
        Priority:
        1. API key from header (X-API-Key)
        2. User ID from request state (if authenticated)
        3. Client IP address
        
        Args:
            request: HTTP request
            
        Returns:
            str: Unique client identifier
        """
        # Check for API key
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"apikey:{api_key}"
        

        
        # Fall back to IP address
        client_host = request.client.host if request.client else "unknown"
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Use first IP in X-Forwarded-For chain
            client_host = forwarded_for.split(",")[0].strip()
        
        return f"ip:{client_host}"
    
    async def _check_rate_limit(
        self,
        client_id: str,
        window: str,
        limit: int,
        window_seconds: int,
    ) -> tuple[bool, int, int]:
        """
        Check rate limit using token bucket algorithm.
        
        Args:
            client_id: Client identifier
            window: Time window identifier (minute or hour)
            limit: Maximum requests allowed in window
            window_seconds: Window duration in seconds
            
        Returns:
            tuple: (allowed, remaining, reset_time)
                - allowed: Whether request is allowed
                - remaining: Remaining requests in window
                - reset_time: Unix timestamp when window resets
        """
        key = f"ratelimit:{client_id}:{window}"
        current_time = int(time.time())
        
        # Get current count and window start time
        data = await self.cache.get(key)
        
        if data is None:
            # First request in this window
            count = 1
            window_start = current_time
            await self.cache.set(
                key,
                {"count": count, "window_start": window_start},
                ttl=window_seconds,
            )
            remaining = limit - count
            reset_time = window_start + window_seconds
            return True, remaining, reset_time
        
        count = data.get("count", 0)
        window_start = data.get("window_start", current_time)
        
        # Check if window has expired
        if current_time - window_start >= window_seconds:
            # Start new window
            count = 1
            window_start = current_time
            await self.cache.set(
                key,
                {"count": count, "window_start": window_start},
                ttl=window_seconds,
            )
            remaining = limit - count
            reset_time = window_start + window_seconds
            return True, remaining, reset_time
        
        # Check if limit exceeded
        if count >= limit:
            remaining = 0
            reset_time = window_start + window_seconds
            return False, remaining, reset_time
        
        # Increment count
        count += 1
        await self.cache.set(
            key,
            {"count": count, "window_start": window_start},
            ttl=window_seconds,
        )
        
        remaining = limit - count
        reset_time = window_start + window_seconds
        return True, remaining, reset_time
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        """
        Process request with rate limiting.
        
        Args:
            request: HTTP request
            call_next: Next middleware or route handler
            
        Returns:
            Response: HTTP response with rate limit headers
        """
        # Skip rate limiting if disabled
        if not self.enabled:
            return await call_next(request)
        
        # Skip rate limiting for health check endpoints
        if request.url.path.startswith("/health"):
            return await call_next(request)
        
        # Get client identifier
        client_id = self._get_client_identifier(request)
        
        # Check per-minute rate limit
        allowed_minute, remaining_minute, reset_minute = await self._check_rate_limit(
            client_id,
            "minute",
            self.limit_per_minute,
            60,
        )
        
        # Check per-hour rate limit
        allowed_hour, remaining_hour, reset_hour = await self._check_rate_limit(
            client_id,
            "hour",
            self.limit_per_hour,
            3600,
        )
        
        # Use the most restrictive limit
        allowed = allowed_minute and allowed_hour
        remaining = min(remaining_minute, remaining_hour)
        reset_time = reset_minute if remaining_minute < remaining_hour else reset_hour
        
        # Add rate limit headers
        headers = {
            "X-RateLimit-Limit": str(self.limit_per_minute),
            "X-RateLimit-Remaining": str(max(0, remaining)),
            "X-RateLimit-Reset": str(reset_time),
        }
        
        # If rate limit exceeded, return 429 response
        if not allowed:
            retry_after = reset_time - int(time.time())
            headers["Retry-After"] = str(max(1, retry_after))
            
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": "Rate limit exceeded. Please try again later.",
                        "retry_after": retry_after,
                    }
                },
                headers=headers,
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers to response
        for header_name, header_value in headers.items():
            response.headers[header_name] = header_value
        
        return response
