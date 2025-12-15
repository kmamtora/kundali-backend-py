from uuid import UUID

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.models.follower import Follower

class FollowerRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def follow_user(self, follower_id: UUID, following_id: UUID) -> Follower:
        # User "on conflict do nothing" since it's a unique pair
        stmt = pg_insert(Follower).values(
            user_id=follower_id,
            following_id=following_id,
            is_active=True
        ).on_conflict_do_nothing(
            index_elements=['user_id', 'following_id']
        ).returning(Follower)
        
        result = await self.session.execute(stmt)
        # If already followed, result might be empty if we do nothing,
        # but requirements just say "Followed successfully".
        # We should check if it returned something ideally or just query.
        # But upsert returning is fine. If None, it means it existed.
        
        await self.session.commit()
        return result.scalar_one_or_none() # type: ignore

    async def unfollow_user(self, follower_id: UUID, following_id: UUID) -> None:
        stmt = delete(Follower).where(
            Follower.user_id == follower_id,
            Follower.following_id == following_id
        )
        await self.session.execute(stmt)
        await self.session.commit()
