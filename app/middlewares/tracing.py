"""
OpenTelemetry tracing middleware for trace context injection and propagation.

This module provides middleware to ensure trace context is properly injected
and propagated across all requests, even when automatic instrumentation
might not capture everything.
"""

from typing import Callable

from fastapi import Request, Response
from opentelemetry import trace
from opentelemetry.propagate import extract, inject
from opentelemetry.trace import SpanKind, Status, StatusCode
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.settings import settings


class TracingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for OpenTelemetry trace context injection and propagation.
    
    Ensures:
    - Trace context is extracted from incoming requests
    - New spans are created for each request
    - Trace context is propagated to downstream services
    - Request metadata is added to spans
    - Errors are properly recorded in spans
    """
    
    def __init__(self, app) -> None:
        """
        Initialize tracing middleware.
        
        Args:
            app: FastAPI application instance
        """
        super().__init__(app)
        self.enabled = settings.OTEL_ENABLED
        self.tracer = trace.get_tracer(__name__)
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        """
        Process request with trace context injection and propagation.
        
        Args:
            request: HTTP request
            call_next: Next middleware or route handler
            
        Returns:
            Response: HTTP response with trace headers
        """
        # Skip tracing if disabled
        if not self.enabled:
            return await call_next(request)
        
        # Extract trace context from incoming request headers
        context = extract(request.headers)
        
        # Create span for this request
        span_name = f"{request.method} {request.url.path}"
        
        with self.tracer.start_as_current_span(
            span_name,
            context=context,
            kind=SpanKind.SERVER,
        ) as span:
            # Add request attributes to span
            span.set_attribute("http.method", request.method)
            span.set_attribute("http.url", str(request.url))
            span.set_attribute("http.scheme", request.url.scheme)
            span.set_attribute("http.host", request.url.hostname or "")
            span.set_attribute("http.target", request.url.path)
            
            if request.url.query:
                span.set_attribute("http.query", request.url.query)
            
            if request.client:
                span.set_attribute("http.client_ip", request.client.host)
            
            # Add user agent
            user_agent = request.headers.get("user-agent")
            if user_agent:
                span.set_attribute("http.user_agent", user_agent)
            
            # Add correlation ID if available
            if hasattr(request.state, "correlation_id"):
                span.set_attribute("correlation_id", request.state.correlation_id)
            
            # Add user ID if authenticated
            if hasattr(request.state, "user") and request.state.user:
                user_id = getattr(request.state.user, "id", None)
                if user_id:
                    span.set_attribute("user.id", str(user_id))
            
            try:
                # Process request
                response = await call_next(request)
                
                # Add response attributes to span
                span.set_attribute("http.status_code", response.status_code)
                
                # Set span status based on HTTP status code
                if response.status_code >= 500:
                    span.set_status(Status(StatusCode.ERROR))
                elif response.status_code >= 400:
                    span.set_status(Status(StatusCode.ERROR))
                else:
                    span.set_status(Status(StatusCode.OK))
                
                # Inject trace context into response headers
                carrier = {}
                inject(carrier)
                for key, value in carrier.items():
                    response.headers[key] = value
                
                # Add trace ID to response headers for debugging
                span_context = span.get_span_context()
                if span_context.is_valid:
                    trace_id = format(span_context.trace_id, "032x")
                    span_id = format(span_context.span_id, "016x")
                    response.headers["X-Trace-ID"] = trace_id
                    response.headers["X-Span-ID"] = span_id
                
                return response
                
            except Exception as exc:
                # Record exception in span
                span.record_exception(exc)
                span.set_status(Status(StatusCode.ERROR, str(exc)))
                
                # Re-raise exception to be handled by error handlers
                raise
