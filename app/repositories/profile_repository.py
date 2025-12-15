from uuid import UUID
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.models.profile import Profile


class ProfileRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_user_id(self, user_id: UUID) -> Profile | None:
        stmt = select(Profile).where(Profile.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_profile(self, user_id: UUID, data: dict) -> Profile:
        stmt = (
            update(Profile)
            .where(Profile.user_id == user_id)
            .values(**data)
            .returning(Profile)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.scalar_one()

    async def upsert_user_profile(self, user_id: UUID) -> Profile:
        """
        Upsert logic:
        If profile exists -> update is_user=True
        If not -> create with is_user=True, user_id=user_id
        """
        stmt = pg_insert(Profile).values(
            user_id=user_id,
            is_user=True,
            is_active=True
        ).on_conflict_do_update(
            index_elements=['user_id'],
            set_={
                'is_user': True,
                'is_active': True
            }
        ).returning(Profile)
        
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.scalar_one()

    async def update_fcm_key(self, user_id: UUID, fcm_key: str | None) -> Profile:
        stmt = (
            update(Profile)
            .where(Profile.user_id == user_id)
            .values(fcm_key=fcm_key)
            .returning(Profile)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.scalar_one()
