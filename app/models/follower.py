"""
Follower model.
"""

import uuid
from typing import TYPE_CHECKING
from sqlalchemy import Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class Follower(Base, TimestampMixin):
    """User following relationship."""
    __tablename__ = "followers"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, comment="The user who is following")
    following_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, comment="The user being followed")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    follower: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    following: Mapped["User"] = relationship("User", foreign_keys=[following_id])

    __table_args__ = (
        UniqueConstraint("user_id", "following_id", name="uq_follower_user_following"),
    )
