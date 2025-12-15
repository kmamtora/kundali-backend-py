"""
OpenTelemetry tracing configuration and setup.

This module provides centralized OpenTelemetry configuration with auto-instrumentation
for FastAPI, SQLAlchemy, Redis, HTTP clients, and Celery.
"""

from typing import Any

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.celery import CeleryInstrumentor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.trace.sampling import (
    ALWAYS_OFF,
    ALWAYS_ON,
    ParentBasedTraceIdRatio,
    Sampler,
)

from app.core.settings import settings


def get_sampler() -> Sampler:
    """
    Get the configured trace sampler based on settings.
    
    Returns:
        Sampler: Configured OpenTelemetry sampler
    """
    sampler_type = settings.OTEL_TRACES_SAMPLER.lower()
    
    if sampler_type == "always_off":
        return ALWAYS_OFF
    elif sampler_type == "always_on":
        return ALWAYS_ON
    elif sampler_type == "traceidratio":
        return ParentBasedTraceIdRatio(settings.OTEL_TRACES_SAMPLER_ARG)
    else:
        # Default to always_on
        return ALWAYS_ON


def setup_telemetry() -> TracerProvider | None:
    """
    Set up OpenTelemetry tracing with auto-instrumentation.
    
    Configures:
    - Resource with service name and attributes
    - Trace provider with sampling
    - OTLP exporter for sending traces
    - Auto-instrumentation for FastAPI, SQLAlchemy, Redis, HTTP clients, Celery
    
    Returns:
        TracerProvider | None: Configured tracer provider or None if disabled
    """
    if not settings.OTEL_ENABLED:
        return None
    
    # Create resource with service information
    resource = Resource.create(
        attributes={
            "service.name": settings.OTEL_SERVICE_NAME,
            "service.version": settings.APP_VERSION,
            "deployment.environment": settings.ENVIRONMENT,
        }
    )
    
    # Create tracer provider with sampling
    sampler = get_sampler()
    provider = TracerProvider(resource=resource, sampler=sampler)
    
    # Configure OTLP exporter
    otlp_exporter = OTLPSpanExporter(
        endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT,
        insecure=settings.OTEL_EXPORTER_OTLP_INSECURE,
    )
    
    # Add batch span processor for efficient export
    provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
    
    # Add console exporter in development for debugging
    if settings.is_development and settings.DEBUG:
        console_exporter = ConsoleSpanExporter()
        provider.add_span_processor(BatchSpanProcessor(console_exporter))
    
    # Set as global tracer provider
    trace.set_tracer_provider(provider)
    
    # Auto-instrument libraries
    # Note: FastAPI instrumentation is done separately in the app initialization
    # to ensure proper app instance is instrumented
    
    # Instrument SQLAlchemy
    SQLAlchemyInstrumentor().instrument()
    
    # Instrument Redis
    RedisInstrumentor().instrument()
    
    # Instrument HTTPX
    HTTPXClientInstrumentor().instrument()
    
    # Instrument Celery
    CeleryInstrumentor().instrument()
    
    return provider


def instrument_fastapi_app(app: Any) -> None:
    """
    Instrument a FastAPI application with OpenTelemetry.
    
    This should be called after the FastAPI app is created to ensure
    proper instrumentation of all routes and middleware.
    
    Args:
        app: FastAPI application instance
    """
    if not settings.OTEL_ENABLED:
        return
    
    FastAPIInstrumentor.instrument_app(app)


def get_tracer(name: str) -> trace.Tracer:
    """
    Get a tracer instance for creating custom spans.
    
    Args:
        name: Name of the tracer (typically module or component name)
    
    Returns:
        trace.Tracer: Tracer instance for creating spans
    """
    return trace.get_tracer(name)


def get_current_span() -> trace.Span:
    """
    Get the current active span.
    
    Returns:
        trace.Span: Current active span
    """
    return trace.get_current_span()


def get_trace_id() -> str:
    """
    Get the current trace ID as a hex string.
    
    Returns:
        str: Trace ID in hex format, or empty string if no active span
    """
    span = get_current_span()
    if span and span.get_span_context().is_valid:
        return format(span.get_span_context().trace_id, "032x")
    return ""


def get_span_id() -> str:
    """
    Get the current span ID as a hex string.
    
    Returns:
        str: Span ID in hex format, or empty string if no active span
    """
    span = get_current_span()
    if span and span.get_span_context().is_valid:
        return format(span.get_span_context().span_id, "016x")
    return ""


def shutdown_telemetry() -> None:
    """
    Shutdown telemetry and flush any pending spans.
    
    Should be called during application shutdown to ensure all
    traces are exported before the application exits.
    """
    if not settings.OTEL_ENABLED:
        return
    
    provider = trace.get_tracer_provider()
    if isinstance(provider, TracerProvider):
        provider.shutdown()
