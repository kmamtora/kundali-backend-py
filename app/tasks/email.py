"""
Email background tasks.

This module provides Celery tasks for sending emails asynchronously
with retry logic and exponential backoff.
"""

import logging
from typing import Any

from celery import Task
from celery.exceptions import MaxRetriesExceededError

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


class EmailTask(Task):
    """
    Base task class for email operations with custom retry logic.
    
    Implements exponential backoff with jitter for failed email sends.
    """
    
    autoretry_for = (Exception,)
    retry_kwargs = {"max_retries": 5}
    retry_backoff = True
    retry_backoff_max = 600  # 10 minutes
    retry_jitter = True


@celery_app.task(
    base=EmailTask,
    bind=True,
    name="app.tasks.email.send_email",
    queue="email",
)
def send_email(
    self: Task,
    to_email: str,
    subject: str,
    body: str,
    from_email: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """
    Send an email asynchronously.
    
    This is a sample task that demonstrates the structure for email sending.
    In production, integrate with an actual email service (SendGrid, SES, etc.).
    
    Args:
        self: Task instance (injected by bind=True)
        to_email: Recipient email address
        subject: Email subject line
        body: Email body content
        from_email: Sender email address (optional)
        **kwargs: Additional email parameters
    
    Returns:
        dict: Result containing status and message details
    
    Raises:
        MaxRetriesExceededError: If all retry attempts are exhausted
    """
    try:
        logger.info(
            "Sending email",
            extra={
                "task_id": self.request.id,
                "to_email": to_email,
                "subject": subject,
                "from_email": from_email,
            },
        )
        
        # TODO: Integrate with actual email service
        # Example integrations:
        # - SendGrid: sendgrid.SendGridAPIClient()
        # - AWS SES: boto3.client('ses')
        # - SMTP: smtplib.SMTP()
        
        # Simulate email sending
        # In production, replace this with actual email service call
        result = {
            "status": "success",
            "to_email": to_email,
            "subject": subject,
            "message_id": f"msg_{self.request.id}",
            "task_id": self.request.id,
        }
        
        logger.info(
            "Email sent successfully",
            extra={
                "task_id": self.request.id,
                "to_email": to_email,
                "message_id": result["message_id"],
            },
        )
        
        return result
        
    except Exception as exc:
        logger.error(
            "Failed to send email",
            extra={
                "task_id": self.request.id,
                "to_email": to_email,
                "error": str(exc),
                "retry_count": self.request.retries,
            },
            exc_info=True,
        )
        
        try:
            # Retry with exponential backoff
            raise self.retry(exc=exc)
        except MaxRetriesExceededError:
            logger.error(
                "Max retries exceeded for email task",
                extra={
                    "task_id": self.request.id,
                    "to_email": to_email,
                    "max_retries": self.max_retries,
                },
            )
            raise


@celery_app.task(
    base=EmailTask,
    bind=True,
    name="app.tasks.email.send_welcome_email",
    queue="email",
)
def send_welcome_email(
    self: Task,
    user_email: str,
    user_name: str,
) -> dict[str, Any]:
    """
    Send a welcome email to a new user.
    
    Args:
        self: Task instance (injected by bind=True)
        user_email: New user's email address
        user_name: New user's full name
    
    Returns:
        dict: Result from send_email task
    """
    subject = "Welcome to Enterprise API!"
    body = f"""
    Hello {user_name},
    
    Welcome to Enterprise API! We're excited to have you on board.
    
    Your account has been successfully created and you can now start using our services.
    
    If you have any questions, please don't hesitate to reach out to our support team.
    
    Best regards,
    The Enterprise API Team
    """
    
    return send_email(
        to_email=user_email,
        subject=subject,
        body=body.strip(),
    )





@celery_app.task(
    bind=True,
    name="app.tasks.email.send_bulk_emails",
    queue="email",
)
def send_bulk_emails(
    self: Task,
    recipients: list[str],
    subject: str,
    body: str,
) -> dict[str, Any]:
    """
    Send emails to multiple recipients.
    
    This task chains individual email tasks for each recipient.
    
    Args:
        self: Task instance (injected by bind=True)
        recipients: List of recipient email addresses
        subject: Email subject line
        body: Email body content
    
    Returns:
        dict: Summary of bulk email operation
    """
    logger.info(
        "Starting bulk email send",
        extra={
            "task_id": self.request.id,
            "recipient_count": len(recipients),
        },
    )
    
    # Queue individual email tasks
    task_ids = []
    for recipient in recipients:
        result = send_email.delay(
            to_email=recipient,
            subject=subject,
            body=body,
        )
        task_ids.append(result.id)
    
    logger.info(
        "Bulk email tasks queued",
        extra={
            "task_id": self.request.id,
            "queued_tasks": len(task_ids),
        },
    )
    
    return {
        "status": "queued",
        "recipient_count": len(recipients),
        "task_ids": task_ids,
        "parent_task_id": self.request.id,
    }
