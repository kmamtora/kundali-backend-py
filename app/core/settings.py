"""
Application settings and configuration management.

This module provides centralized configuration using Pydantic BaseSettings
with support for environment variable loading from .env files.
"""

from typing import Any
from pydantic import Field, field_validator, PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings with environment variable support.
    
    All settings can be overridden via environment variables.
    Loads from .env file if present.
    """
    
    # ============================================================================
    # Application Settings
    # ============================================================================
    APP_NAME: str = Field(default="Enterprise FastAPI", description="Application name")
    APP_VERSION: str = Field(default="1.0.0", description="Application version")
    DEBUG: bool = Field(default=False, description="Debug mode")
    ENVIRONMENT: str = Field(default="development", description="Environment (development, staging, production)")
    API_V1_PREFIX: str = Field(default="/api/v1", description="API v1 route prefix")
    
    # ============================================================================
    # Database Settings (PostgreSQL)
    # ============================================================================
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/enterprise_api",
        description="Async PostgreSQL database URL"
    )
    DB_POOL_SIZE: int = Field(default=20, description="Database connection pool size")
    DB_MAX_OVERFLOW: int = Field(default=10, description="Maximum overflow connections")
    DB_POOL_TIMEOUT: int = Field(default=30, description="Pool timeout in seconds")
    DB_POOL_RECYCLE: int = Field(default=3600, description="Connection recycle time in seconds")
    DB_ECHO: bool = Field(default=False, description="Echo SQL queries (for debugging)")
    
    # ============================================================================
    # Redis Settings
    # ============================================================================
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL"
    )
    REDIS_POOL_SIZE: int = Field(default=10, description="Redis connection pool size")
    CACHE_TTL: int = Field(default=3600, description="Default cache TTL in seconds")
    SESSION_TTL: int = Field(default=86400, description="Session TTL in seconds (24 hours)")
    

    
    # ============================================================================
    # CORS Settings
    # ============================================================================
    CORS_ORIGINS: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="Allowed CORS origins"
    )
    CORS_ALLOW_CREDENTIALS: bool = Field(default=True, description="Allow credentials in CORS")
    CORS_ALLOW_METHODS: list[str] = Field(
        default=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        description="Allowed HTTP methods"
    )
    CORS_ALLOW_HEADERS: list[str] = Field(
        default=["*"],
        description="Allowed headers"
    )
    CORS_MAX_AGE: int = Field(default=600, description="CORS preflight cache duration in seconds")
    
    # ============================================================================
    # Rate Limiting Settings
    # ============================================================================
    RATE_LIMIT_ENABLED: bool = Field(default=True, description="Enable rate limiting")
    RATE_LIMIT_PER_MINUTE: int = Field(
        default=60,
        description="Default rate limit per minute per client"
    )
    RATE_LIMIT_PER_HOUR: int = Field(
        default=1000,
        description="Default rate limit per hour per client"
    )
    RATE_LIMIT_STORAGE_URL: str | None = Field(
        default=None,
        description="Rate limit storage URL (uses REDIS_URL if not set)"
    )
    
    # ============================================================================
    # Celery Settings
    # ============================================================================
    CELERY_BROKER_URL: str | None = Field(
        default=None,
        description="Celery broker URL (uses REDIS_URL if not set)"
    )
    CELERY_RESULT_BACKEND: str | None = Field(
        default=None,
        description="Celery result backend URL (uses REDIS_URL if not set)"
    )
    CELERY_TASK_SERIALIZER: str = Field(default="json", description="Task serialization format")
    CELERY_RESULT_SERIALIZER: str = Field(default="json", description="Result serialization format")
    CELERY_ACCEPT_CONTENT: list[str] = Field(default=["json"], description="Accepted content types")
    CELERY_TIMEZONE: str = Field(default="UTC", description="Celery timezone")
    CELERY_TASK_TIME_LIMIT: int = Field(
        default=1800,
        description="Task time limit in seconds (30 minutes)"
    )
    CELERY_TASK_SOFT_TIME_LIMIT: int = Field(
        default=1500,
        description="Task soft time limit in seconds (25 minutes)"
    )
    
    # ============================================================================
    # OpenTelemetry / Observability Settings
    # ============================================================================
    OTEL_ENABLED: bool = Field(default=True, description="Enable OpenTelemetry tracing")
    OTEL_SERVICE_NAME: str = Field(
        default="enterprise-api",
        description="Service name for tracing"
    )
    OTEL_EXPORTER_OTLP_ENDPOINT: str = Field(
        default="http://localhost:4317",
        description="OTLP exporter endpoint"
    )
    OTEL_EXPORTER_OTLP_INSECURE: bool = Field(
        default=True,
        description="Use insecure connection for OTLP"
    )
    OTEL_TRACES_SAMPLER: str = Field(
        default="always_on",
        description="Trace sampling strategy (always_on, always_off, traceidratio)"
    )
    OTEL_TRACES_SAMPLER_ARG: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Trace sampler argument (for traceidratio)"
    )

    # ============================================================================
    # Twilio Settings
    # ============================================================================
    TWILIO_ACCOUNT_SID: str | None = Field(default=None, description="Twilio Account SID")
    TWILIO_AUTH_TOKEN: str | None = Field(default=None, description="Twilio Auth Token")
    TWILIO_FROM_NUMBER: str | None = Field(default=None, description="Twilio From Number")

    # ============================================================================
    # JWT Settings
    # ============================================================================
    JWT_SECRET_KEY: str = Field(default="changethis", description="JWT Secret Key")
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT Algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, description="Access token expiration in minutes")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, description="Refresh token expiration in days")
    
    # ============================================================================
    # Logging Settings
    # ============================================================================
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_FORMAT: str = Field(default="json", description="Log format (json or text)")
    LOG_FILE: str | None = Field(default=None, description="Log file path (None for stdout only)")
    
    # ============================================================================
    # Metrics Settings
    # ============================================================================
    METRICS_ENABLED: bool = Field(default=True, description="Enable Prometheus metrics")
    METRICS_ENDPOINT: str = Field(default="/metrics", description="Metrics endpoint path")
    
    # ============================================================================
    # Health Check Settings
    # ============================================================================
    HEALTH_CHECK_ENABLED: bool = Field(default=True, description="Enable health check endpoints")
    HEALTH_CHECK_PATH_LIVE: str = Field(
        default="/health/live",
        description="Liveness probe endpoint"
    )
    HEALTH_CHECK_PATH_READY: str = Field(
        default="/health/ready",
        description="Readiness probe endpoint"
    )
    
    # ============================================================================
    # API Documentation Settings
    # ============================================================================
    DOCS_ENABLED: bool = Field(default=True, description="Enable API documentation")
    DOCS_URL: str = Field(default="/docs", description="Swagger UI documentation URL")
    REDOC_URL: str = Field(default="/redoc", description="ReDoc documentation URL")
    OPENAPI_URL: str = Field(default="/openapi.json", description="OpenAPI schema URL")
    
    # ============================================================================
    # Security Settings
    # ============================================================================
    ALLOWED_HOSTS: list[str] = Field(default=["*"], description="Allowed host headers")
    TRUSTED_PROXIES: list[str] = Field(default=[], description="Trusted proxy IP addresses")
    
    # Input sanitization
    SANITIZE_INPUTS: bool = Field(default=True, description="Enable input sanitization")
    MAX_REQUEST_SIZE: int = Field(
        default=10485760,
        description="Maximum request size in bytes (10MB)"
    )
    
    # ============================================================================
    # Pagination Settings
    # ============================================================================
    DEFAULT_PAGE_SIZE: int = Field(default=20, description="Default pagination page size")
    MAX_PAGE_SIZE: int = Field(default=100, description="Maximum pagination page size")
    
    # ============================================================================
    # Model Configuration
    # ============================================================================
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )
    
    # ============================================================================
    # Validators
    # ============================================================================
    
    @field_validator("RATE_LIMIT_STORAGE_URL", mode="before")
    @classmethod
    def set_rate_limit_storage_url(cls, v: str | None, info: Any) -> str:
        """Set rate limit storage URL to REDIS_URL if not provided."""
        if v is None and "REDIS_URL" in info.data:
            return info.data["REDIS_URL"]
        return v or "redis://localhost:6379/0"
    
    @field_validator("CELERY_BROKER_URL", mode="before")
    @classmethod
    def set_celery_broker_url(cls, v: str | None, info: Any) -> str:
        """Set Celery broker URL to REDIS_URL if not provided."""
        if v is None and "REDIS_URL" in info.data:
            return info.data["REDIS_URL"]
        return v or "redis://localhost:6379/0"
    
    @field_validator("CELERY_RESULT_BACKEND", mode="before")
    @classmethod
    def set_celery_result_backend(cls, v: str | None, info: Any) -> str:
        """Set Celery result backend URL to REDIS_URL if not provided."""
        if v is None and "REDIS_URL" in info.data:
            return info.data["REDIS_URL"]
        return v or "redis://localhost:6379/0"
    
    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is one of the standard levels."""
        allowed_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in allowed_levels:
            raise ValueError(f"LOG_LEVEL must be one of {allowed_levels}")
        return v_upper
    
    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment is one of the expected values."""
        allowed_envs = ["development", "staging", "production", "test"]
        v_lower = v.lower()
        if v_lower not in allowed_envs:
            raise ValueError(f"ENVIRONMENT must be one of {allowed_envs}")
        return v_lower
    
    # ============================================================================
    # Helper Properties
    # ============================================================================
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.ENVIRONMENT == "development"
    
    @property
    def is_test(self) -> bool:
        """Check if running in test environment."""
        return self.ENVIRONMENT == "test"
    



# Global settings instance
settings = Settings()
