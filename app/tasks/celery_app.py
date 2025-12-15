"""
Celery application instance and configuration.

This module provides the Celery app instance configured for background task processing
with Redis as both broker and result backend.
"""

from celery import Celery
from celery.signals import setup_logging

from app.core.settings import settings

# Create Celery app instance
celery_app = Celery(
    "enterprise_api",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.email"],
)

# Configure Celery
celery_app.conf.update(
    # Serialization
    task_serializer=settings.CELERY_TASK_SERIALIZER,
    accept_content=settings.CELERY_ACCEPT_CONTENT,
    result_serializer=settings.CELERY_RESULT_SERIALIZER,
    
    # Timezone
    timezone=settings.CELERY_TIMEZONE,
    enable_utc=True,
    
    # Task execution
    task_track_started=True,
    task_time_limit=settings.CELERY_TASK_TIME_LIMIT,
    task_soft_time_limit=settings.CELERY_TASK_SOFT_TIME_LIMIT,
    
    # Task acknowledgment
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    
    # Worker configuration
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    
    # Result backend
    result_expires=3600,  # Results expire after 1 hour
    result_extended=True,
    
    # Task routing
    task_routes={
        "app.tasks.email.*": {"queue": "email"},
    },
    
    # Retry policy
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=3,
    
    # Beat schedule (for periodic tasks)
    beat_schedule={},
)


@setup_logging.connect
def setup_celery_logging(**kwargs: dict) -> None:
    """
    Configure Celery logging to use application logging configuration.
    
    This prevents Celery from overriding the application's logging setup.
    """
    pass  # Use application's logging configuration


# Task base class configuration
celery_app.Task.autoretry_for = (Exception,)
celery_app.Task.retry_kwargs = {"max_retries": 3}
celery_app.Task.retry_backoff = True
celery_app.Task.retry_backoff_max = 600  # 10 minutes
celery_app.Task.retry_jitter = True
