"""
Kundali model.
"""

import uuid
from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class Kundali(Base, TimestampMixin):
    """Kundali record."""
    __tablename__ = "kundalis"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    gender: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, comment="True for Male, False for Female")
    bdate: Mapped[str] = mapped_column(String, nullable=False, comment="Birth date")
    btime: Mapped[str] = mapped_column(String, nullable=False, comment="Birth time")
    bplace: Mapped[str] = mapped_column(String, nullable=False, comment="Birth place")
    room_name: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
