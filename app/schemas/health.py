"""
Health check response schemas.

This module provides Pydantic models for health check endpoint responses.
"""

from datetime import datetime
from pydantic import BaseModel, Field


class DependencyHealth(BaseModel):
    """Health status of a single dependency."""
    
    name: str = Field(..., description="Dependency name")
    status: str = Field(..., description="Health status (healthy, unhealthy, degraded)")
    message: str | None = Field(None, description="Additional status message")
    response_time_ms: float | None = Field(None, description="Response time in milliseconds")


class HealthResponse(BaseModel):
    """Health check response model."""
    
    status: str = Field(..., description="Overall health status (healthy, unhealthy, degraded)")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Check timestamp")
    version: str = Field(..., description="Application version")
    dependencies: list[DependencyHealth] = Field(
        default_factory=list,
        description="Health status of dependencies"
    )


class LivenessResponse(BaseModel):
    """Liveness probe response model."""
    
    status: str = Field(default="alive", description="Liveness status")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Check timestamp")
