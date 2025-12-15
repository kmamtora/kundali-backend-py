"""
Pandit Profile model.
"""

import uuid
from typing import TYPE_CHECKING
from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class PanditProfile(Base, TimestampMixin):
    """Profile for Pandits (Astrologers)."""
    __tablename__ = "pandit_profiles"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), unique=True, nullable=True)
    information: Mapped[str] = mapped_column(String, nullable=False)
    is_active_chat: Mapped[str] = mapped_column(String, default="Offline", nullable=False)
    is_active_call: Mapped[str] = mapped_column(String, default="Offline", nullable=False)
    is_active_live: Mapped[str] = mapped_column(String, default="Offline", nullable=False)
    
    # ARRAY types for lists of strings
    language: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)
    experience: Mapped[str] = mapped_column(String, nullable=False)
    qualification: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)
    astrotype: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)
    
    tag: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship()
