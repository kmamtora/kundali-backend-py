"""
User model.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.profile import Profile
    from app.models.pandit_profile import PanditProfile
    from app.models.rate import Rate
    from app.models.follower import Follower
    from app.models.message import Message
    from app.models.rating import Rating
    from app.models.voice_call import VoiceCall
    from app.models.wallet import Wallet


class User(Base, TimestampMixin):
    """
    User model representing a registered user in the system.
    """
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        comment="Unique identifier for the user",
    )
    mobile_no: Mapped[str] = mapped_column(String, nullable=False, comment="User mobile number")
    otp: Mapped[str] = mapped_column(String, nullable=False, comment="One Time Password")
    otp_expires: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        nullable=False,
        comment="Expiration time for the OTP",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether the user account is active",
    )

    # Relationships
    # Note: These will be defined in subsequent batches as related models are created
    # followers: Mapped[list["Follower"]] = relationship(...)
    # following: Mapped[list["Follower"]] = relationship(...)
    # messages: Mapped[list["Message"]] = relationship(...)
    # pandit_profile: Mapped["PanditProfile"] = relationship(...)
    # profile: Mapped["Profile"] = relationship(...)
    # ratings: Mapped[list["Rating"]] = relationship(...)
    # voice_calls: Mapped[list["VoiceCall"]] = relationship(...)
    # wallet: Mapped[list["Wallet"]] = relationship(...)
    # rate: Mapped["Rate"] = relationship(...)
