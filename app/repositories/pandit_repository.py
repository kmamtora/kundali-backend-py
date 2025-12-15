from typing import Sequence
from uuid import UUID

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.models.user import User
from app.models.pandit_profile import PanditProfile
from app.models.profile import Profile


class PanditRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all_pandits(self) -> Sequence[User]:
        # Logic: 
        # where: { isActive: true, profile: { isUser: false } }
        # order by: panditProfile.updatedAt desc
        
        stmt = (
            select(User)
            .join(User.profile) # Inner join for filtering
            .outerjoin(User.pandit_profile) # Join for ordering
            .where(
                User.is_active == True,
                Profile.is_user == False # Pandit profiles have is_user=False per Express logic?
                # Express: "profile: { isUser: false }"
            )
            .order_by(desc(PanditProfile.updated_at))
            .options(
                selectinload(User.profile),
                selectinload(User.pandit_profile),
                selectinload(User.rate),
                selectinload(User.followers) # Should be counted ideally
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def upsert_pandit_profile(self, user_id: UUID, data: dict) -> PanditProfile:
        stmt = pg_insert(PanditProfile).values(
            user_id=user_id,
            tag="", # Default from Express
            **data
        ).on_conflict_do_update(
            index_elements=['user_id'],
            set_={
                'tag': "", # Default from Express upsert
                **data
            }
        ).returning(PanditProfile)
        
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.scalar_one()
