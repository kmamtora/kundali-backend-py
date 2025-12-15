from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import User
from app.models.follower import Follower


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_mobile(self, mobile_no: str) -> User | None:
        stmt = select(User).where(User.mobile_no == mobile_no)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_user(self, mobile_no: str, otp: str, otp_expires: datetime) -> User:
        user = User(
            mobile_no=mobile_no,
            otp=otp,
            otp_expires=otp_expires,
            is_active=True
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def update_otp(self, user_id: UUID, otp: str, otp_expires: datetime, is_active: bool = True) -> User:
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(otp=otp, otp_expires=otp_expires, is_active=is_active)
            .returning(User)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.scalar_one()

    async def get_by_id(self, user_id: UUID) -> User | None:
        stmt = select(User).where(User.id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def deactivate_user(self, user_id: UUID) -> None:
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(is_active=False)
        )
        await self.session.execute(stmt)
        await self.session.commit()

    async def get_full_profile(self, user_id: UUID) -> User | None:
        stmt = (
            select(User)
            .where(User.id == user_id)
            .options(
                selectinload(User.profile),
                selectinload(User.pandit_profile),
                selectinload(User.rate),
                selectinload(User.followers) # To count strictly, usually we count in DB.
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def check_is_following(self, user_id: UUID, target_id: UUID) -> bool:
        stmt = select(Follower).where(
            Follower.user_id == user_id,
            Follower.following_id == target_id,
            Follower.is_active == True
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None
