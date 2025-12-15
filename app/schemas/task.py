"""
Task management Pydantic schemas.

This module defines request and response models for background task
management endpoints.
"""

from typing import Any
from pydantic import BaseModel, Field, EmailStr


class TaskStatusResponse(BaseModel):
    """Task status response model."""
    
    task_id: str = Field(..., description="Celery task ID")
    status: str = Field(..., description="Task status (PENDING, STARTED, SUCCESS, FAILURE, RETRY)")
    result: Any | None = Field(None, description="Task result if completed")
    error: str | None = Field(None, description="Error message if failed")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "task_id": "abc123-def456-ghi789",
                "status": "SUCCESS",
                "result": {"status": "success", "message_id": "msg_123"},
                "error": None,
            }
        }
    }


class SendEmailRequest(BaseModel):
    """Send email task request model."""
    
    to_email: EmailStr = Field(..., description="Recipient email address")
    subject: str = Field(..., min_length=1, max_length=255, description="Email subject")
    body: str = Field(..., min_length=1, description="Email body content")
    from_email: EmailStr | None = Field(None, description="Sender email address (optional)")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "to_email": "user@example.com",
                "subject": "Test Email",
                "body": "This is a test email message.",
                "from_email": "noreply@example.com",
            }
        }
    }


class SendWelcomeEmailRequest(BaseModel):
    """Send welcome email task request model."""
    
    user_email: EmailStr = Field(..., description="New user's email address")
    user_name: str = Field(..., min_length=1, max_length=255, description="New user's full name")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "user_email": "newuser@example.com",
                "user_name": "John Doe",
            }
        }
    }


class SendBulkEmailsRequest(BaseModel):
    """Send bulk emails task request model."""
    
    recipients: list[EmailStr] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="List of recipient email addresses (max 100)",
    )
    subject: str = Field(..., min_length=1, max_length=255, description="Email subject")
    body: str = Field(..., min_length=1, description="Email body content")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "recipients": ["user1@example.com", "user2@example.com"],
                "subject": "Announcement",
                "body": "This is an important announcement.",
            }
        }
    }


class TaskSubmittedResponse(BaseModel):
    """Task submitted response model."""
    
    task_id: str = Field(..., description="Celery task ID")
    status: str = Field(default="PENDING", description="Initial task status")
    message: str = Field(..., description="Success message")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "task_id": "abc123-def456-ghi789",
                "status": "PENDING",
                "message": "Task submitted successfully",
            }
        }
    }
