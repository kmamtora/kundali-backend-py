"""
Task management endpoints.

This module provides endpoints to trigger and check the status of
background tasks using Celery.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from celery.result import AsyncResult


from app.schemas.task import (
    TaskStatusResponse,
    SendEmailRequest,
    SendWelcomeEmailRequest,
    SendBulkEmailsRequest,
    TaskSubmittedResponse,
)
from app.tasks.celery_app import celery_app
from app.tasks.email import (
    send_email,
    send_welcome_email,
    send_bulk_emails,
)

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get(
    "/{task_id}",
    response_model=TaskStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get task status",
    description="Check the status of a background task by its ID.",
)
async def get_task_status(
        task_id: str,
    ) -> TaskStatusResponse:
    """
    Get the status of a background task.
    
    Retrieves the current status and result of a Celery task by its ID.
    
    Args:
        task_id: Celery task ID
        
    Returns:
        TaskStatusResponse: Task status and result information
    """
    # Get task result from Celery
    task_result = AsyncResult(task_id, app=celery_app)
    
    # Prepare response based on task state
    response = TaskStatusResponse(
        task_id=task_id,
        status=task_result.state,
        result=None,
        error=None,
    )
    
    if task_result.successful():
        # Task completed successfully
        response.result = task_result.result
    elif task_result.failed():
        # Task failed
        response.error = str(task_result.info) if task_result.info else "Task failed"
    
    return response


@router.post(
    "/email/send",
    response_model=TaskSubmittedResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Send email",
    description="Queue an email to be sent asynchronously.",
)
async def trigger_send_email(
    email_request: SendEmailRequest,
) -> TaskSubmittedResponse:
    """
    Trigger an email send task.
    
    Queues an email to be sent asynchronously by a Celery worker.
    
    Args:
        email_request: Email details (recipient, subject, body)
        
    Returns:
        TaskSubmittedResponse: Task ID and status
    """
    # Queue the email task
    task = send_email.delay(
        to_email=email_request.to_email,
        subject=email_request.subject,
        body=email_request.body,
        from_email=email_request.from_email,
    )
    
    return TaskSubmittedResponse(
        task_id=task.id,
        status="PENDING",
        message=f"Email task queued successfully. Task ID: {task.id}",
    )


@router.post(
    "/email/welcome",
    response_model=TaskSubmittedResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Send welcome email",
    description="Queue a welcome email to be sent to a new user.",
)
async def trigger_welcome_email(
    welcome_request: SendWelcomeEmailRequest,
) -> TaskSubmittedResponse:
    """
    Trigger a welcome email task.
    
    Queues a welcome email to be sent to a newUser.
    
    Args:
        welcome_request: Welcome email details (user email and name)
        
    Returns:
        TaskSubmittedResponse: Task ID and status
    """
    # Queue the welcome email task
    task = send_welcome_email.delay(
        user_email=welcome_request.user_email,
        user_name=welcome_request.user_name,
    )
    
    return TaskSubmittedResponse(
        task_id=task.id,
        status="PENDING",
        message=f"Welcome email task queued successfully. Task ID: {task.id}",
    )


@router.post(
    "/email/bulk",
    response_model=TaskSubmittedResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Send bulk emails",
    description="Queue bulk emails to be sent to multiple recipients.",
)
async def trigger_bulk_emails(
    bulk_request: SendBulkEmailsRequest,
) -> TaskSubmittedResponse:
    """
    Trigger a bulk email task.
    
    Queues emails to be sent to multiple recipients. Each recipient
    will receive the same email content.
    
    Args:
        bulk_request: Bulk email details (recipients, subject, body)
        
    Returns:
        TaskSubmittedResponse: Task ID and status
    """
    # Validate recipient count
    if len(bulk_request.recipients) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 100 recipients allowed per bulk email request",
        )
    
    # Queue the bulk email task
    task = send_bulk_emails.delay(
        recipients=bulk_request.recipients,
        subject=bulk_request.subject,
        body=bulk_request.body,
    )
    
    return TaskSubmittedResponse(
        task_id=task.id,
        status="PENDING",
        message=f"Bulk email task queued successfully. Task ID: {task.id}. "
                f"Sending to {len(bulk_request.recipients)} recipients.",
    )


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_200_OK,
    summary="Revoke task",
    description="Revoke (cancel) a pending or running task.",
)
async def revoke_task(
    task_id: str,
) -> dict[str, str]:
    """
    Revoke a background task.
    
    Attempts to cancel a pending or running task. Note that tasks that
    have already started may not be immediately cancelled.
    
    Args:
        task_id: Celery task ID
        
    Returns:
        dict: Success message
    """
    # Revoke the task
    celery_app.control.revoke(task_id, terminate=True)
    
    return {
        "message": f"Task {task_id} revoked successfully",
        "task_id": task_id,
    }
