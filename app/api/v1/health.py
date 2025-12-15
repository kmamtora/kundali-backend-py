"""
Health check endpoints.

This module provides health check endpoints for liveness and readiness probes.
Checks connectivity to database, Redis, and Celery.
"""

import time
from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis

from app.core.settings import settings
from app.dependencies.database import get_db
from app.dependencies.cache import get_redis_client
from app.schemas.health import HealthResponse, LivenessResponse, DependencyHealth
from app.tasks.celery_app import celery_app

router = APIRouter(tags=["health"])


@router.get(
    "/health/live",
    response_model=LivenessResponse,
    status_code=status.HTTP_200_OK,
    summary="Liveness probe",
    description="Check if the application is running. Always returns 200 if the app is up.",
)
async def liveness_check() -> LivenessResponse:
    """
    Liveness probe endpoint.
    
    This endpoint is used by Kubernetes to determine if the application
    is running and should be restarted if it fails.
    
    Returns:
        LivenessResponse: Simple status indicating the app is alive
    """
    return LivenessResponse(status="alive")


@router.get(
    "/health/ready",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Readiness probe",
    description="Check if the application and all dependencies are ready to serve traffic.",
)
async def readiness_check(
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis_client),
) -> HealthResponse:
    """
    Readiness probe endpoint.
    
    This endpoint checks the health of all critical dependencies:
    - Database (PostgreSQL)
    - Cache (Redis)
    - Task Queue (Celery)
    
    Returns HTTP 200 if all dependencies are healthy, otherwise returns
    the status with details about which dependencies are unhealthy.
    
    Args:
        db: Database session
        redis_client: Redis client
        
    Returns:
        HealthResponse: Detailed health status of all dependencies
    """
    dependencies: list[DependencyHealth] = []
    overall_status = "healthy"
    
    # Check database connectivity
    db_health = await _check_database(db)
    dependencies.append(db_health)
    if db_health.status != "healthy":
        overall_status = "unhealthy"
    
    # Check Redis connectivity
    redis_health = await _check_redis(redis_client)
    dependencies.append(redis_health)
    if redis_health.status != "healthy":
        overall_status = "unhealthy"
    
    # Check Celery connectivity
    celery_health = await _check_celery()
    dependencies.append(celery_health)
    if celery_health.status != "healthy":
        # Celery being down is degraded, not unhealthy
        if overall_status == "healthy":
            overall_status = "degraded"
    
    return HealthResponse(
        status=overall_status,
        version=settings.APP_VERSION,
        dependencies=dependencies,
    )


async def _check_database(db: AsyncSession) -> DependencyHealth:
    """
    Check database connectivity.
    
    Args:
        db: Database session
        
    Returns:
        DependencyHealth: Database health status
    """
    start_time = time.time()
    
    try:
        # Execute simple query to check connectivity
        await db.execute(text("SELECT 1"))
        response_time = (time.time() - start_time) * 1000
        
        return DependencyHealth(
            name="database",
            status="healthy",
            message="Database connection successful",
            response_time_ms=round(response_time, 2),
        )
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        
        return DependencyHealth(
            name="database",
            status="unhealthy",
            message=f"Database connection failed: {str(e)}",
            response_time_ms=round(response_time, 2),
        )


async def _check_redis(redis_client: redis.Redis) -> DependencyHealth:
    """
    Check Redis connectivity.
    
    Args:
        redis_client: Redis client
        
    Returns:
        DependencyHealth: Redis health status
    """
    start_time = time.time()
    
    try:
        # Ping Redis to check connectivity
        await redis_client.ping()
        response_time = (time.time() - start_time) * 1000
        
        return DependencyHealth(
            name="redis",
            status="healthy",
            message="Redis connection successful",
            response_time_ms=round(response_time, 2),
        )
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        
        return DependencyHealth(
            name="redis",
            status="unhealthy",
            message=f"Redis connection failed: {str(e)}",
            response_time_ms=round(response_time, 2),
        )


async def _check_celery() -> DependencyHealth:
    """
    Check Celery connectivity.
    
    Returns:
        DependencyHealth: Celery health status
    """
    start_time = time.time()
    
    try:
        # Check if Celery workers are available
        inspect = celery_app.control.inspect()
        stats = inspect.stats()
        
        response_time = (time.time() - start_time) * 1000
        
        if stats:
            worker_count = len(stats)
            return DependencyHealth(
                name="celery",
                status="healthy",
                message=f"Celery workers available: {worker_count}",
                response_time_ms=round(response_time, 2),
            )
        else:
            return DependencyHealth(
                name="celery",
                status="unhealthy",
                message="No Celery workers available",
                response_time_ms=round(response_time, 2),
            )
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        
        return DependencyHealth(
            name="celery",
            status="unhealthy",
            message=f"Celery check failed: {str(e)}",
            response_time_ms=round(response_time, 2),
        )
