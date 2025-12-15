from uuid import UUID
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.profile_repository import ProfileRepository
from app.repositories.user_repository import UserRepository
from app.schemas.profile import ProfileUpdateRequest, FullProfileResponse

class ProfileService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.profile_repo = ProfileRepository(session)
        self.user_repo = UserRepository(session)

    async def update_profile(self, user_id: UUID, data: ProfileUpdateRequest) -> dict:
        # Express logic: upsert profile with provided data.
        # We need to convert Pydantic model to dict, excluding None/Unset?
        # Express ignores nulls? "const { fname... } = req.body".
        # Prisma upsert uses these values.
        # We will use exclude_unset=True to only update what was sent.
        
        update_data = data.model_dump(exclude_unset=True)
        
        # Express logic uses upsert. Our repo has upsert_user_profile (which creates default)
        # and update_profile. 
        # But we added upsert logic? No, we added update_profile. 
        # The prompt mentioned "upsert" in express.
        # "exist = await prisma.profile.upsert({...})"
        # If it doesn't exist, it creates it.
        # I should use an upsert flow.
        
        # Check if profile exists (optimization or just use upsert).
        # In repo I added `update_profile` which is strictly UPDATE.
        # I should probably ensure it exists first or use upsert.
        # Let's use `upsert_user_profile` to ensure it exists, then update?
        # Or better: implement a true upsert in repo?
        # Repo has `upsert_user_profile` which returns Profile, but it hardcodes `is_user=True`.
        # I can call `upsert_user_profile` first (which is cheap if exists) then `update_profile`?
        # Or modify repo to accept data in upsert.
        
        # Given current repo state:
        # 1. Ensure profile exists (upsert default)
        # 2. Update with data
        # This matches "upsert" semantic loosely (create if not exists)
        
        await self.profile_repo.upsert_user_profile(user_id)
        if update_data:
            updated_profile = await self.profile_repo.update_profile(user_id, update_data)
            return updated_profile
        
        # Use existing if no data updated
        return await self.profile_repo.get_by_user_id(user_id)

    async def get_full_profile(self, target_user_id: UUID, current_user_id: UUID) -> FullProfileResponse:
        user = await self.user_repo.get_full_profile(target_user_id)
        if not user:
            raise HTTPException(status_code=400, detail="Unable to retrieve profile")

        # Check following status
        is_following = await self.user_repo.check_is_following(current_user_id, target_user_id)
        
        # Calculate follower count
        # In loading strategies, user.followers is a list.
        follower_count = len(user.followers) if user.followers else 0

        return FullProfileResponse(
            mobile_no=user.mobile_no,
            profile=user.profile,
            pandit_profile=user.pandit_profile,
            rate=user.rate,
            follower_count=follower_count,
            is_following=is_following
        )
