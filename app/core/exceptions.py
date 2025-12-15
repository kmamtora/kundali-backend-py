"""
Custom exception classes and global exception handlers.

This module defines custom exception classes for the application
and provides global exception handlers that map exceptions to
appropriate HTTP status codes with trace_id in error responses.
"""

from typing import Any

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.telemetry import get_trace_id


# ============================================================================
# Custom Exception Classes
# ============================================================================

class AppException(Exception):
    """
    Base exception for application-specific errors.
    
    All custom exceptions should inherit from this class.
    """
    
    def __init__(
        self,
        message: str = "An application error occurred",
        code: str = "APP_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        """
        Initialize application exception.
        
        Args:
            message: Human-readable error message
            code: Machine-readable error code
            details: Additional error details
        """
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)


class EntityNotFoundError(AppException):
    """Exception raised when an entity is not found in the repository."""
    
    def __init__(
        self,
        entity_type: str,
        entity_id: Any,
        details: dict[str, Any] | None = None,
    ) -> None:
        """
        Initialize entity not found error.
        
        Args:
            entity_type: Type of entity (e.g., "User", "Task")
            entity_id: ID of the entity that was not found
            details: Additional error details
        """
        message = f"{entity_type} with ID {entity_id} not found"
        code = f"{entity_type.upper()}_NOT_FOUND"
        super().__init__(message=message, code=code, details=details)


class ValidationError(AppException):
    """Exception raised when business rule validation fails."""
    
    def __init__(
        self,
        message: str = "Validation failed",
        field: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """
        Initialize validation error.
        
        Args:
            message: Validation error message
            field: Field that failed validation (optional)
            details: Additional error details
        """
        code = "VALIDATION_ERROR"
        error_details = details or {}
        if field:
            error_details["field"] = field
        super().__init__(message=message, code=code, details=error_details)





class DuplicateEntityError(AppException):
    """Exception raised when attempting to create a duplicate entity."""
    
    def __init__(
        self,
        entity_type: str,
        field: str,
        value: Any,
        details: dict[str, Any] | None = None,
    ) -> None:
        """
        Initialize duplicate entity error.
        
        Args:
            entity_type: Type of entity (e.g., "User", "Task")
            field: Field that has duplicate value
            value: Duplicate value
            details: Additional error details
        """
        message = f"{entity_type} with {field} '{value}' already exists"
        code = f"DUPLICATE_{entity_type.upper()}"
        error_details = details or {}
        error_details.update({"field": field, "value": str(value)})
        super().__init__(message=message, code=code, details=error_details)


class DatabaseError(AppException):
    """Exception raised when a database operation fails."""
    
    def __init__(
        self,
        message: str = "Database operation failed",
        operation: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """
        Initialize database error.
        
        Args:
            message: Database error message
            operation: Database operation that failed (optional)
            details: Additional error details
        """
        error_details = details or {}
        if operation:
            error_details["operation"] = operation
        super().__init__(message=message, code="DATABASE_ERROR", details=error_details)


class CacheError(AppException):
    """Exception raised when a cache operation fails."""
    
    def __init__(
        self,
        message: str = "Cache operation failed",
        operation: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """
        Initialize cache error.
        
        Args:
            message: Cache error message
            operation: Cache operation that failed (optional)
            details: Additional error details
        """
        error_details = details or {}
        if operation:
            error_details["operation"] = operation
        super().__init__(message=message, code="CACHE_ERROR", details=error_details)


class ExternalServiceError(AppException):
    """Exception raised when an external service call fails."""
    
    def __init__(
        self,
        service_name: str,
        message: str = "External service call failed",
        details: dict[str, Any] | None = None,
    ) -> None:
        """
        Initialize external service error.
        
        Args:
            service_name: Name of the external service
            message: Error message
            details: Additional error details
        """
        error_details = details or {}
        error_details["service"] = service_name
        super().__init__(
            message=f"{service_name}: {message}",
            code="EXTERNAL_SERVICE_ERROR",
            details=error_details,
        )


class RateLimitExceededError(AppException):
    """Exception raised when rate limit is exceeded."""
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: int | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """
        Initialize rate limit exceeded error.
        
        Args:
            message: Rate limit error message
            retry_after: Seconds until rate limit resets (optional)
            details: Additional error details
        """
        error_details = details or {}
        if retry_after:
            error_details["retry_after"] = retry_after
        super().__init__(message=message, code="RATE_LIMIT_EXCEEDED", details=error_details)


# ============================================================================
# Exception Handlers
# ============================================================================

async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """
    Handle custom application exceptions.
    
    Maps custom exceptions to appropriate HTTP status codes and
    includes trace_id in the error response.
    
    Args:
        request: FastAPI request object
        exc: Application exception
        
    Returns:
        JSONResponse with error details
    """
    # Determine HTTP status code based on exception type
    status_code_map = {
        EntityNotFoundError: status.HTTP_404_NOT_FOUND,
        ValidationError: status.HTTP_400_BAD_REQUEST,

        DuplicateEntityError: status.HTTP_409_CONFLICT,
        DatabaseError: status.HTTP_500_INTERNAL_SERVER_ERROR,
        CacheError: status.HTTP_500_INTERNAL_SERVER_ERROR,
        ExternalServiceError: status.HTTP_502_BAD_GATEWAY,
        RateLimitExceededError: status.HTTP_429_TOO_MANY_REQUESTS,
    }
    
    status_code = status_code_map.get(type(exc), status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # Build error response
    error_response = {
        "error": {
            "code": exc.code,
            "message": exc.message,
            "details": exc.details,
            "trace_id": get_trace_id(),
        }
    }
    
    # Add retry_after header for rate limit errors
    headers = {}
    if isinstance(exc, RateLimitExceededError) and "retry_after" in exc.details:
        headers["Retry-After"] = str(exc.details["retry_after"])
    

    
    return JSONResponse(
        status_code=status_code,
        content=error_response,
        headers=headers if headers else None,
    )


async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    """
    Handle HTTP exceptions from FastAPI/Starlette.
    
    Formats HTTP exceptions with consistent error structure and trace_id.
    
    Args:
        request: FastAPI request object
        exc: HTTP exception
        
    Returns:
        JSONResponse with error details
    """
    error_response = {
        "error": {
            "code": f"HTTP_{exc.status_code}",
            "message": exc.detail,
            "details": {},
            "trace_id": get_trace_id(),
        }
    }
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response,
        headers=exc.headers,
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """
    Handle Pydantic validation errors.
    
    Formats validation errors with detailed field-level error information
    and includes trace_id.
    
    Args:
        request: FastAPI request object
        exc: Validation error
        
    Returns:
        JSONResponse with validation error details
    """
    # Format validation errors
    errors = []
    for error in exc.errors():
        error_dict = {
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
        }
        if "ctx" in error:
            error_dict["context"] = error["ctx"]
        errors.append(error_dict)
    
    error_response = {
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "Request validation failed",
            "details": {"errors": errors},
            "trace_id": get_trace_id(),
        }
    }
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response,
    )


async def sqlalchemy_exception_handler(
    request: Request,
    exc: SQLAlchemyError,
) -> JSONResponse:
    """
    Handle SQLAlchemy database errors.
    
    Provides a generic error response for database errors without
    exposing sensitive database details.
    
    Args:
        request: FastAPI request object
        exc: SQLAlchemy error
        
    Returns:
        JSONResponse with error details
    """
    error_response = {
        "error": {
            "code": "DATABASE_ERROR",
            "message": "A database error occurred",
            "details": {},
            "trace_id": get_trace_id(),
        }
    }
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response,
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle unexpected exceptions.
    
    Provides a generic error response for unhandled exceptions
    without exposing sensitive implementation details.
    
    Args:
        request: FastAPI request object
        exc: Unhandled exception
        
    Returns:
        JSONResponse with error details
    """
    error_response = {
        "error": {
            "code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred",
            "details": {},
            "trace_id": get_trace_id(),
        }
    }
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response,
    )
