"""
Base SQLAlchemy model with common functionality.

This module provides the declarative base for all SQLAlchemy models
and common base classes with shared functionality.
"""

from datetime import datetime
from typing import Any
from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy models.
    
    This class serves as the declarative base for all database models.
    """
    
    # Type annotation map for common Python types
    type_annotation_map = {
        datetime: DateTime(timezone=True),
    }


class TimestampMixin:
    """
    Mixin that adds created_at and updated_at timestamp columns.
    
    Attributes:
        created_at: Timestamp when the record was created
        updated_at: Timestamp when the record was last updated
    """
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Timestamp when the record was created",
    )
    
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        onupdate=func.now(),
        nullable=True,
        comment="Timestamp when the record was last updated",
    )
