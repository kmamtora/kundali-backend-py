"""
Prometheus metrics collection and exposition.

This module provides metrics collection for monitoring application performance,
including request duration, count, active connections, and cache hit/miss rates.
"""

import time
from typing import Any, Callable

from fastapi import Request, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.settings import settings


# ============================================================================
# Metric Definitions
# ============================================================================

# Request metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "status_code"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

http_requests_in_progress = Gauge(
    "http_requests_in_progress",
    "Number of HTTP requests currently being processed",
    ["method", "endpoint"],
)

# Database metrics
db_connections_active = Gauge(
    "db_connections_active",
    "Number of active database connections",
)

db_connections_idle = Gauge(
    "db_connections_idle",
    "Number of idle database connections",
)

db_query_duration_seconds = Histogram(
    "db_query_duration_seconds",
    "Database query duration in seconds",
    ["operation"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)

# Cache metrics
cache_hits_total = Counter(
    "cache_hits_total",
    "Total number of cache hits",
    ["cache_key_prefix"],
)

cache_misses_total = Counter(
    "cache_misses_total",
    "Total number of cache misses",
    ["cache_key_prefix"],
)

cache_operations_duration_seconds = Histogram(
    "cache_operations_duration_seconds",
    "Cache operation duration in seconds",
    ["operation"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5),
)

# Background task metrics
celery_tasks_total = Counter(
    "celery_tasks_total",
    "Total number of Celery tasks",
    ["task_name", "status"],
)

celery_task_duration_seconds = Histogram(
    "celery_task_duration_seconds",
    "Celery task duration in seconds",
    ["task_name"],
    buckets=(0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0, 300.0, 600.0),
)

celery_queue_length = Gauge(
    "celery_queue_length",
    "Number of tasks in Celery queue",
    ["queue_name"],
)

# Authentication metrics
auth_attempts_total = Counter(
    "auth_attempts_total",
    "Total number of authentication attempts",
    ["status"],
)

auth_tokens_issued_total = Counter(
    "auth_tokens_issued_total",
    "Total number of authentication tokens issued",
    ["token_type"],
)

# Application metrics
app_info = Gauge(
    "app_info",
    "Application information",
    ["version", "environment"],
)

# Set application info
app_info.labels(
    version=settings.APP_VERSION,
    environment=settings.ENVIRONMENT,
).set(1)


# ============================================================================
# Metrics Middleware
# ============================================================================

class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware for collecting HTTP request metrics.
    
    Tracks:
    - Request count by method, endpoint, and status code
    - Request duration by method and endpoint
    - Active requests in progress
    """
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Any],
    ) -> Response:
        """
        Process request and collect metrics.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware or route handler
        
        Returns:
            Response: HTTP response
        """
        # Skip metrics endpoint itself
        if request.url.path == settings.METRICS_ENDPOINT:
            return await call_next(request)
        
        # Get endpoint path (use route path if available, otherwise URL path)
        endpoint = request.url.path
        if hasattr(request, "scope") and "route" in request.scope:
            route = request.scope["route"]
            if hasattr(route, "path"):
                endpoint = route.path
        
        method = request.method
        
        # Increment in-progress gauge
        http_requests_in_progress.labels(method=method, endpoint=endpoint).inc()
        
        # Track request duration
        start_time = time.time()
        
        try:
            # Process request
            response = await call_next(request)
            
            # Record metrics
            duration = time.time() - start_time
            status_code = response.status_code
            
            http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status_code=status_code,
            ).inc()
            
            http_request_duration_seconds.labels(
                method=method,
                endpoint=endpoint,
            ).observe(duration)
            
            return response
            
        except Exception as exc:
            # Record error metrics
            duration = time.time() - start_time
            
            http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status_code=500,
            ).inc()
            
            http_request_duration_seconds.labels(
                method=method,
                endpoint=endpoint,
            ).observe(duration)
            
            raise
            
        finally:
            # Decrement in-progress gauge
            http_requests_in_progress.labels(method=method, endpoint=endpoint).dec()


# ============================================================================
# Metrics Helper Functions
# ============================================================================

def record_cache_hit(cache_key_prefix: str = "default") -> None:
    """
    Record a cache hit.
    
    Args:
        cache_key_prefix: Prefix of the cache key for categorization
    """
    cache_hits_total.labels(cache_key_prefix=cache_key_prefix).inc()


def record_cache_miss(cache_key_prefix: str = "default") -> None:
    """
    Record a cache miss.
    
    Args:
        cache_key_prefix: Prefix of the cache key for categorization
    """
    cache_misses_total.labels(cache_key_prefix=cache_key_prefix).inc()


def record_cache_operation(operation: str, duration: float) -> None:
    """
    Record cache operation duration.
    
    Args:
        operation: Type of cache operation (get, set, delete)
        duration: Operation duration in seconds
    """
    cache_operations_duration_seconds.labels(operation=operation).observe(duration)


def record_db_query(operation: str, duration: float) -> None:
    """
    Record database query duration.
    
    Args:
        operation: Type of database operation (select, insert, update, delete)
        duration: Query duration in seconds
    """
    db_query_duration_seconds.labels(operation=operation).observe(duration)


def update_db_connection_metrics(active: int, idle: int) -> None:
    """
    Update database connection pool metrics.
    
    Args:
        active: Number of active connections
        idle: Number of idle connections
    """
    db_connections_active.set(active)
    db_connections_idle.set(idle)


def record_celery_task(task_name: str, status: str, duration: float | None = None) -> None:
    """
    Record Celery task execution.
    
    Args:
        task_name: Name of the Celery task
        status: Task status (success, failure, retry)
        duration: Task duration in seconds (optional)
    """
    celery_tasks_total.labels(task_name=task_name, status=status).inc()
    
    if duration is not None:
        celery_task_duration_seconds.labels(task_name=task_name).observe(duration)


def update_celery_queue_length(queue_name: str, length: int) -> None:
    """
    Update Celery queue length metric.
    
    Args:
        queue_name: Name of the Celery queue
        length: Number of tasks in queue
    """
    celery_queue_length.labels(queue_name=queue_name).set(length)


def record_auth_attempt(success: bool) -> None:
    """
    Record authentication attempt.
    
    Args:
        success: Whether authentication was successful
    """
    status = "success" if success else "failure"
    auth_attempts_total.labels(status=status).inc()


def record_token_issued(token_type: str = "access") -> None:
    """
    Record authentication token issuance.
    
    Args:
        token_type: Type of token (access, refresh)
    """
    auth_tokens_issued_total.labels(token_type=token_type).inc()


# ============================================================================
# Metrics Endpoint Handler
# ============================================================================

async def metrics_handler() -> Response:
    """
    Handle metrics endpoint request.
    
    Returns Prometheus-formatted metrics for scraping.
    
    Returns:
        Response: HTTP response with metrics in Prometheus format
    """
    metrics_data = generate_latest()
    
    return Response(
        content=metrics_data,
        media_type=CONTENT_TYPE_LATEST,
    )
