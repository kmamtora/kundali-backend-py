from typing import Sequence
from uuid import UUID

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.models.user import User
from app.models.pandit_profile import PanditProfile
from app.models.profile import Profile
from app.models.voice_call import VoiceCall
from sqlalchemy import update, literal


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

    async def update_pandit_status(self, user_id: UUID, status_type: str, status_value: str) -> None:
        # statusType: Call, Chat, Live
        # Express logic: 
        # if (statusType === "Call") update isActiveCall ... if true, cancel active calls later? 
        # Actually Express logic cancels calls if statusType is Call (regardless of value? Or if turning OFF?)
        # Wait, Express code:
        # if (statusType === "Call") update...
        #   update... isActiveCall
        #   await prisma.voiceCall.updateMany({ where: { receiverId: id, endTime: null }, data: { status: 'CANCELLED' } })
        #   It cancels active calls EVERY time status is updated for Call? 
        #   Logic says: "if (statusType === 'Call') ... update ... THEN cancel calls".
        #   So yes, it seems to clear lines.
        
        updates = {}
        if status_type == "Call":
            updates["is_active_call"] = status_value
        elif status_type == "Chat":
            updates["is_active_chat"] = status_value
        elif status_type == "Live":
            updates["is_active_live"] = status_value
        
        if updates:
            stmt = update(PanditProfile).where(PanditProfile.user_id == user_id).values(**updates)
            await self.session.execute(stmt)
            await self.session.commit()

    async def cancel_active_calls(self, receiver_id: UUID) -> None:
        # Update active calls (endTime is null) to CANCELLED
        # VoiceCall model has `end_time` and `status`
        stmt = (
            update(VoiceCall)
            .where(
                VoiceCall.receiver_id == receiver_id,
                VoiceCall.end_time == None
            )
            .values(status="CANCELLED")
        )
        await self.session.execute(stmt)
        await self.session.commit()

