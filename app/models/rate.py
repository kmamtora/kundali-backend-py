"""
Rate model.
"""

import uuid
from typing import TYPE_CHECKING
from sqlalchemy import Boolean, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class Rate(Base, TimestampMixin):
    """Rates set by Pandits for various services."""
    __tablename__ = "rates"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), unique=True, nullable=True)
    audio_rate: Mapped[int] = mapped_column(Integer, nullable=False)
    chat_rate: Mapped[int] = mapped_column(Integer, nullable=False)
    video_rate: Mapped[int] = mapped_column(Integer, nullable=False)
    live_rate: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool | None] = mapped_column(Boolean, default=True, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="rate")
