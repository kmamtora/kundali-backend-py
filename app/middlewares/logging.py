"""
Structured logging middleware with audit capabilities.

This module provides JSON-formatted logging with correlation IDs, trace context,
and comprehensive audit logging for authentication and data changes.
"""

import json
import logging
import time
import uuid
from typing import Any, Callable

from fastapi import Request, Response
from pythonjsonlogger import jsonlogger
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.settings import settings
from app.core.telemetry import get_span_id, get_trace_id


# ============================================================================
# Logger Configuration
# ============================================================================

def setup_logging() -> None:
    """
    Configure structured JSON logging for the application.
    
    Sets up:
    - JSON formatter with custom fields
    - Log level from settings
    - Console handler for stdout
    - Optional file handler
    """
    # Create custom JSON formatter
    log_format = (
        "%(timestamp)s %(level)s %(name)s %(correlation_id)s "
        "%(trace_id)s %(span_id)s %(message)s"
    )
    
    formatter = CustomJsonFormatter(log_format)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(settings.LOG_LEVEL)
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Add console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Add file handler if configured
    if settings.LOG_FILE:
        file_handler = logging.FileHandler(settings.LOG_FILE)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Set log levels for noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """
    Custom JSON formatter that adds trace context and correlation ID.
    """
    
    def add_fields(
        self,
        log_record: dict[str, Any],
        record: logging.LogRecord,
        message_dict: dict[str, Any],
    ) -> None:
        """
        Add custom fields to log record.
        
        Args:
            log_record: Dictionary to be logged as JSON
            record: Python logging record
            message_dict: Dictionary from the log message
        """
        super().add_fields(log_record, record, message_dict)
        
        # Add timestamp
        log_record["timestamp"] = self.formatTime(record, self.datefmt)
        
        # Add log level
        log_record["level"] = record.levelname
        
        # Add logger name
        log_record["logger"] = record.name
        
        # Add trace context if available
        trace_id = get_trace_id()
        span_id = get_span_id()
        
        if trace_id:
            log_record["trace_id"] = trace_id
        if span_id:
            log_record["span_id"] = span_id
        
        # Add correlation ID from context if available
        if hasattr(record, "correlation_id"):
            log_record["correlation_id"] = record.correlation_id
        
        # Add service information
        log_record["service"] = settings.OTEL_SERVICE_NAME
        log_record["environment"] = settings.ENVIRONMENT


# ============================================================================
# Logging Middleware
# ============================================================================

class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for structured request/response logging with correlation IDs.
    
    Logs:
    - Request details (method, path, headers, client)
    - Response details (status, duration)
    - Correlation ID for request tracing
    - Trace and span IDs from OpenTelemetry
    """
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Any],
    ) -> Response:
        """
        Process request and log details.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware or route handler
        
        Returns:
            Response: HTTP response
        """
        # Generate correlation ID
        correlation_id = str(uuid.uuid4())
        
        # Store correlation ID in request state
        request.state.correlation_id = correlation_id
        
        # Get logger
        logger = logging.getLogger(__name__)
        
        # Create log adapter with correlation ID
        log_extra = {"correlation_id": correlation_id}
        
        # Log request
        start_time = time.time()
        
        logger.info(
            "Request started",
            extra={
                **log_extra,
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "client_host": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent"),
            },
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Log response
            logger.info(
                "Request completed",
                extra={
                    **log_extra,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": round(duration * 1000, 2),
                },
            )
            
            # Add correlation ID to response headers
            response.headers["X-Correlation-ID"] = correlation_id
            
            return response
            
        except Exception as exc:
            # Calculate duration
            duration = time.time() - start_time
            
            # Log error
            logger.error(
                "Request failed",
                extra={
                    **log_extra,
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": round(duration * 1000, 2),
                    "error": str(exc),
                    "error_type": type(exc).__name__,
                },
                exc_info=True,
            )
            
            raise


# ============================================================================
# Audit Logging
# ============================================================================

class AuditLogger:
    """
    Audit logger for tracking authentication and data changes.
    
    Provides methods for logging:
    - Authentication attempts (success/failure)
    - Data modifications (create, update, delete)
    - Security events
    """
    
    def __init__(self) -> None:
        """Initialize audit logger."""
        self.logger = logging.getLogger("audit")
    
    def _get_context(self, request: Request | None = None) -> dict[str, Any]:
        """
        Get common audit context.
        
        Args:
            request: Optional HTTP request for additional context
        
        Returns:
            dict: Context dictionary with trace and correlation IDs
        """
        context: dict[str, Any] = {
            "trace_id": get_trace_id(),
            "span_id": get_span_id(),
        }
        
        if request:
            context.update({
                "correlation_id": getattr(request.state, "correlation_id", None),
                "client_host": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent"),
            })
        
        return context
    
    def log_auth_attempt(
        self,
        email: str,
        success: bool,
        request: Request | None = None,
        reason: str | None = None,
    ) -> None:
        """
        Log authentication attempt.
        
        Args:
            email: User email attempting authentication
            success: Whether authentication was successful
            request: Optional HTTP request
            reason: Optional reason for failure
        """
        context = self._get_context(request)
        
        self.logger.info(
            "Authentication attempt",
            extra={
                **context,
                "event_type": "auth_attempt",
                "email": email,
                "success": success,
                "reason": reason,
            },
        )
    
    def log_auth_success(
        self,
        user_id: str,
        email: str,
        request: Request | None = None,
    ) -> None:
        """
        Log successful authentication.
        
        Args:
            user_id: Authenticated user ID
            email: User email
            request: Optional HTTP request
        """
        context = self._get_context(request)
        
        self.logger.info(
            "Authentication successful",
            extra={
                **context,
                "event_type": "auth_success",
                "user_id": user_id,
                "email": email,
            },
        )
    
    def log_auth_failure(
        self,
        email: str,
        reason: str,
        request: Request | None = None,
    ) -> None:
        """
        Log failed authentication.
        
        Args:
            email: User email attempting authentication
            reason: Reason for failure
            request: Optional HTTP request
        """
        context = self._get_context(request)
        
        self.logger.warning(
            "Authentication failed",
            extra={
                **context,
                "event_type": "auth_failure",
                "email": email,
                "reason": reason,
            },
        )
    
    def log_data_create(
        self,
        entity_type: str,
        entity_id: str,
        data: dict[str, Any],
        user_id: str | None = None,
        request: Request | None = None,
    ) -> None:
        """
        Log data creation.
        
        Args:
            entity_type: Type of entity created
            entity_id: ID of created entity
            data: Entity data (sensitive fields should be excluded)
            user_id: User who created the entity
            request: Optional HTTP request
        """
        context = self._get_context(request)
        
        self.logger.info(
            "Data created",
            extra={
                **context,
                "event_type": "data_create",
                "entity_type": entity_type,
                "entity_id": entity_id,
                "user_id": user_id,
                "data": json.dumps(data),
            },
        )
    
    def log_data_update(
        self,
        entity_type: str,
        entity_id: str,
        before: dict[str, Any],
        after: dict[str, Any],
        user_id: str | None = None,
        request: Request | None = None,
    ) -> None:
        """
        Log data modification with before/after states.
        
        Args:
            entity_type: Type of entity updated
            entity_id: ID of updated entity
            before: Entity state before update
            after: Entity state after update
            user_id: User who updated the entity
            request: Optional HTTP request
        """
        context = self._get_context(request)
        
        self.logger.info(
            "Data updated",
            extra={
                **context,
                "event_type": "data_update",
                "entity_type": entity_type,
                "entity_id": entity_id,
                "user_id": user_id,
                "before": json.dumps(before),
                "after": json.dumps(after),
            },
        )
    
    def log_data_delete(
        self,
        entity_type: str,
        entity_id: str,
        data: dict[str, Any],
        user_id: str | None = None,
        request: Request | None = None,
    ) -> None:
        """
        Log data deletion.
        
        Args:
            entity_type: Type of entity deleted
            entity_id: ID of deleted entity
            data: Entity data before deletion
            user_id: User who deleted the entity
            request: Optional HTTP request
        """
        context = self._get_context(request)
        
        self.logger.info(
            "Data deleted",
            extra={
                **context,
                "event_type": "data_delete",
                "entity_type": entity_type,
                "entity_id": entity_id,
                "user_id": user_id,
                "data": json.dumps(data),
            },
        )
    
    def log_security_event(
        self,
        event_type: str,
        description: str,
        severity: str = "info",
        user_id: str | None = None,
        request: Request | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Log security-related event.
        
        Args:
            event_type: Type of security event
            description: Event description
            severity: Event severity (info, warning, error)
            user_id: User associated with event
            request: Optional HTTP request
            **kwargs: Additional context
        """
        context = self._get_context(request)
        
        log_method = getattr(self.logger, severity.lower(), self.logger.info)
        
        log_method(
            description,
            extra={
                **context,
                "event_type": f"security_{event_type}",
                "user_id": user_id,
                **kwargs,
            },
        )


# Global audit logger instance
audit_logger = AuditLogger()
