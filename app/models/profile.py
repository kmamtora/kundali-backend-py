"""
Profile model.
"""

import uuid
from typing import TYPE_CHECKING
from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class Profile(Base, TimestampMixin):
    """User profile information."""
    __tablename__ = "profiles"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), unique=True, nullable=True)
    email: Mapped[str | None] = mapped_column(String, nullable=True)
    fname: Mapped[str | None] = mapped_column(String, nullable=True, comment="First Name")
    lname: Mapped[str | None] = mapped_column(String, nullable=True, comment="Last Name")
    gender: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, comment="True for Male, False for Female")
    bdate: Mapped[str | None] = mapped_column(String, nullable=True, comment="Birth date")
    btime: Mapped[str | None] = mapped_column(String, nullable=True, comment="Birth time")
    bplace: Mapped[str | None] = mapped_column(String, nullable=True, comment="Birth place")
    profile_pic: Mapped[str | None] = mapped_column(String, nullable=True, comment="URL to profile picture")
    profile_video: Mapped[str | None] = mapped_column(String, nullable=True, comment="URL to profile video")
    fcm_key: Mapped[str | None] = mapped_column(String, nullable=True, comment="Firebase Cloud Messaging key")
    is_user: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, comment="True if regular user, False otherwise")
    stripe_cust_id: Mapped[str | None] = mapped_column(String, nullable=True, comment="Stripe Customer ID")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship()
