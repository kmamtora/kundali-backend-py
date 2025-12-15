"""
FastAPI application entrypoint.

This module initializes the FastAPI application with all middleware,
routers, exception handlers, and lifecycle management.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1 import health, tasks
from app.core.database import close_db, init_db
from app.core.exceptions import (
    AppException,
    app_exception_handler,
    generic_exception_handler,
    http_exception_handler,
    sqlalchemy_exception_handler,
    validation_exception_handler,
)
from app.core.metrics import MetricsMiddleware, metrics_handler
from app.core.settings import settings
from app.core.telemetry import (
    instrument_fastapi_app,
    setup_telemetry,
    shutdown_telemetry,
)
from app.dependencies.cache import close_redis_pool
from app.middlewares.logging import LoggingMiddleware
from app.middlewares.rate_limit import RateLimitMiddleware
from app.middlewares.tracing import TracingMiddleware


# ============================================================================
# Lifespan Context Manager
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan context manager.
    
    Handles startup and shutdown events for the FastAPI application,
    including database initialization, telemetry setup, and cleanup.
    
    Args:
        app: FastAPI application instance
        
    Yields:
        None
    """
    # ========================================================================
    # Startup
    # ========================================================================
    
    # Initialize OpenTelemetry tracing
    setup_telemetry()
    
    # Instrument FastAPI app with OpenTelemetry
    instrument_fastapi_app(app)
    
    # Initialize database connection
    try:
        await init_db()
    except Exception as e:
        # Log error but don't prevent startup
        # Health checks will report database as unhealthy
        print(f"Warning: Database initialization failed: {e}")
    
    yield
    
    # ========================================================================
    # Shutdown
    # ========================================================================
    
    # Close database connections
    await close_db()
    
    # Close Redis connection pool
    await close_redis_pool()
    
    # Shutdown telemetry and flush pending spans
    shutdown_telemetry()


# ============================================================================
# Application Factory
# ============================================================================

def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.
    
    Initializes the FastAPI application with:
    - API documentation configuration
    - Middleware stack (CORS, rate limiting, logging, tracing, metrics)
    - API routers
    - Exception handlers
    - Lifespan management
    
    Returns:
        Configured FastAPI application instance
    """
    # Create FastAPI app with configuration
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "Enterprise-grade REST API built with FastAPI. "
            "Provides production-ready foundation with modern Python tooling, "
            "clean architecture patterns, comprehensive observability, "
            "and cloud-native deployment capabilities.\n\n"
            "## Features\n\n"
            "- **Background Tasks**: Asynchronous task processing with Celery\n"
            "- **Caching**: Redis-based caching for improved performance\n"
            "- **Observability**: OpenTelemetry tracing, structured logging, and Prometheus metrics\n"
            "- **Rate Limiting**: Token bucket algorithm for API rate limiting\n"
            "- **Health Checks**: Liveness and readiness probes for Kubernetes\n\n"
            "## Rate Limiting\n\n"
            "API requests are rate limited to prevent abuse. Rate limit information is included in response headers:\n\n"
            "- `X-RateLimit-Limit`: Maximum requests allowed in the time window\n"
            "- `X-RateLimit-Remaining`: Remaining requests in the current window\n"
            "- `X-RateLimit-Reset`: Time when the rate limit resets (Unix timestamp)\n\n"
            "## Error Responses\n\n"
            "All error responses follow a consistent format:\n\n"
            "```json\n"
            "{\n"
            '  "error": {\n'
            '    "code": "ERROR_CODE",\n'
            '    "message": "Human-readable error message",\n'
            '    "details": {},\n'
            '    "trace_id": "abc123"\n'
            "  }\n"
            "}\n"
            "```\n\n"
            "The `trace_id` can be used for debugging and correlating logs."
        ),
        docs_url=settings.DOCS_URL if settings.DOCS_ENABLED else None,
        redoc_url=settings.REDOC_URL if settings.DOCS_ENABLED else None,
        openapi_url=settings.OPENAPI_URL if settings.DOCS_ENABLED else None,
        lifespan=lifespan,
        # Contact information
        contact={
            "name": "API Support",
            "email": "support@example.com",
        },
        # License information
        license_info={
            "name": "MIT",
            "url": "https://opensource.org/licenses/MIT",
        },
        # OpenAPI tags with descriptions
        openapi_tags=[
            {
                "name": "root",
                "description": "API root and information endpoints",
            },
            {
                "name": "health",
                "description": (
                    "Health check endpoints for monitoring and orchestration. "
                    "Use `/health/live` for liveness probes and `/health/ready` for readiness probes."
                ),
            },

            {
                "name": "tasks",
                "description": (
                    "Background task management and monitoring. "
                    "Submit tasks for asynchronous processing and check their status. "
                    "Powered by Celery for reliable task execution."
                ),
            },
        ],
        # Swagger UI configuration
        swagger_ui_parameters={
            "persistAuthorization": True,
            "displayRequestDuration": True,
            "filter": True,
            "tryItOutEnabled": True,
            "syntaxHighlight.theme": "monokai",
            "defaultModelsExpandDepth": 2,
            "defaultModelExpandDepth": 2,
            "docExpansion": "list",
        },
        # Security schemes for OpenAPI
        swagger_ui_init_oauth={
            "usePkceWithAuthorizationCodeGrant": True,
        },
    )
    
    # Add security scheme to OpenAPI schema
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        
        from fastapi.openapi.utils import get_openapi
        
        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
            tags=app.openapi_tags,
        )
        
        # Add security schemes
        # openapi_schema["components"]["securitySchemes"] = {}
        
        # Add security requirement to all endpoints that need authentication
        # (This is handled by individual endpoints, but we document it here)
        
        # Add response examples for common error codes
        if "components" not in openapi_schema:
            openapi_schema["components"] = {}
        
        if "responses" not in openapi_schema["components"]:
            openapi_schema["components"]["responses"] = {}
        

        
        openapi_schema["components"]["responses"]["NotFoundError"] = {
            "description": "Resource not found",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code": "ENTITY_NOT_FOUND",
                            "message": "Resource not found",
                            "details": {},
                            "trace_id": "abc123def456",
                        }
                    }
                }
            },
        }
        
        openapi_schema["components"]["responses"]["ValidationError"] = {
            "description": "Request validation failed",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code": "VALIDATION_ERROR",
                            "message": "Request validation failed",
                            "details": {
                                "errors": [
                                    {
                                        "field": "email",
                                        "message": "value is not a valid email address",
                                        "type": "value_error.email",
                                    }
                                ]
                            },
                            "trace_id": "abc123def456",
                        }
                    }
                }
            },
        }
        
        openapi_schema["components"]["responses"]["RateLimitError"] = {
            "description": "Rate limit exceeded",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code": "RATE_LIMIT_EXCEEDED",
                            "message": "Rate limit exceeded",
                            "details": {"retry_after": 60},
                            "trace_id": "abc123def456",
                        }
                    }
                }
            },
        }
        
        app.openapi_schema = openapi_schema
        return app.openapi_schema
    
    app.openapi = custom_openapi
    
    # ========================================================================
    # Middleware Stack (order matters - first added is outermost)
    # ========================================================================
    
    # 1. CORS Middleware (outermost - handles preflight requests)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=settings.CORS_ALLOW_METHODS,
        allow_headers=settings.CORS_ALLOW_HEADERS,
        max_age=settings.CORS_MAX_AGE,
    )
    
    # 2. Metrics Middleware (track all requests)
    if settings.METRICS_ENABLED:
        app.add_middleware(MetricsMiddleware)
    
    # 3. Tracing Middleware (inject trace context)
    if settings.OTEL_ENABLED:
        app.add_middleware(TracingMiddleware)
    
    # 4. Logging Middleware (structured logging with correlation ID)
    app.add_middleware(LoggingMiddleware)
    
    # 5. Rate Limiting Middleware (innermost - after logging)
    if settings.RATE_LIMIT_ENABLED:
        app.add_middleware(RateLimitMiddleware)
    
    # ========================================================================
    # Exception Handlers
    # ========================================================================
    
    # Custom application exceptions
    app.add_exception_handler(AppException, app_exception_handler)
    
    # HTTP exceptions
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    
    # Validation errors
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    
    # Database errors
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
    
    # Generic exception handler (catch-all)
    app.add_exception_handler(Exception, generic_exception_handler)
    
    # ========================================================================
    # API Routers
    # ========================================================================
    
    # Health check endpoints (no prefix)
    app.include_router(health.router)
    
    # API v1 endpoints
    # API v1 endpoints
    app.include_router(tasks.router, prefix=settings.API_V1_PREFIX)
    
    # ========================================================================
    # Metrics Endpoint
    # ========================================================================
    
    if settings.METRICS_ENABLED:
        @app.get(
            settings.METRICS_ENDPOINT,
            include_in_schema=False,
            response_class=JSONResponse,
        )
        async def metrics() -> JSONResponse:
            """Prometheus metrics endpoint."""
            return await metrics_handler()
    
    # ========================================================================
    # Root Endpoint
    # ========================================================================
    
    @app.get(
        "/",
        include_in_schema=True,
        tags=["root"],
        summary="API root",
        description="Get API information and available endpoints",
    )
    async def root() -> dict[str, str]:
        """
        API root endpoint.
        
        Returns basic information about the API and links to documentation.
        
        Returns:
            dict: API information
        """
        return {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "docs": settings.DOCS_URL if settings.DOCS_ENABLED else "disabled",
            "redoc": settings.REDOC_URL if settings.DOCS_ENABLED else "disabled",
            "health": "/health/ready",
        }
    
    return app


# ============================================================================
# Application Instance
# ============================================================================

# Create application instance
app = create_app()


# ============================================================================
# Development Server
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.cmd.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.is_development,
        log_level=settings.LOG_LEVEL.lower(),
    )
