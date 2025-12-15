from typing import List, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.pandit_repository import PanditRepository
from app.repositories.profile_repository import ProfileRepository
from app.repositories.user_repository import UserRepository
from app.repositories.follower_repository import FollowerRepository
from app.schemas.profile import FullProfileResponse, ProfileUpdateRequest
from app.schemas.pandit import PanditUpdateRequest
from app.services.profile_service import ProfileService

class PanditService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.pandit_repo = PanditRepository(session)
        self.profile_repo = ProfileRepository(session)
        self.user_repo = UserRepository(session) # Helper for full profile formatting
        self.follower_repo = FollowerRepository(session)

    async def get_all_pandits(self, current_user_id: UUID) -> List[FullProfileResponse]:
        # Logic: fetch all, format like getFullProfileById
        # But for LIST, Express controller returns `exist` which is a list of User objects with nested relations.
        # "const formattedUsers = exist.map(...)" was commented out in Express code?
        # But "res.status(200).json(exist);" returns the raw object.
        # We need to format it properly.
        # I'll reuse FullProfileResponse for consistency.
        
        users = await self.pandit_repo.get_all_pandits()
        
        # We need to check filtering for each? Optimally valid in SQL.
        # check_is_following logic is N+1 here if we do it for everyone.
        # Express logic: 
        # followers: { where: { userId: req.user.id } }
        # This checks if CURRENT user follows filtering inside the query.
        # I didn't verify if I can easily do that with my Repo.
        # My Repo `get_all_pandits` uses `selectinload(User.followers)`.
        # This loads ALL followers. Which is bad for performance if millions.
        # But Express logic filtered it!
        # "followers: { where: { userId: req.user.id } }" -> returning ONLY if following.
        # Then `isFollowing: exist.followers.length > 0`.
        
        # NOTE: I should update Repo to optimise this, but for now strict porting:
        # I'll loop and basic check or just return simple data?
        # Plan says "get_all_pandits".
        
        response = []
        for user in users:
            # Check isFollowing logic manually or rely on loaded followers?
            # If I loaded ALL followers, I can check python side.
            # Ideally: filtered load.
            
            # Assuming simple small scale for now.
            is_following = False
            # Check if current_user_id is in followers
            # User.followers is a list of Follower objects.
            # Follower object has user_id (the follower) and following_id (the pandit).
            # So we check if any follower.user_id == current_user_id
            if user.followers:
                 for f in user.followers:
                     if f.user_id == current_user_id:
                         is_following = True
                         break
            
            follower_count = len(user.followers) if user.followers else 0

            response.append(FullProfileResponse(
                mobile_no=user.mobile_no,
                profile=user.profile,
                pandit_profile=user.pandit_profile,
                rate=user.rate,
                follower_count=follower_count,
                is_following=is_following
            ))
        return response

    async def update_pandit_profile(self, user_id: UUID, data: PanditUpdateRequest) -> Any:
        # 1. Update PanditProfile (upsert)
        pandit_data = data.model_dump(include={'information', 'language', 'experience', 'astrotype', 'qualification'}, exclude_none=True)
        # Express upsert: "tag: """ hardcoded.
        
        # 2. Update Profile (fname, lname, email)
        profile_data = data.model_dump(include={'firstName', 'lastName', 'email'}, exclude_none=True)
        # map firstName -> fname if needed.
        if 'firstName' in profile_data:
            profile_data['fname'] = profile_data.pop('firstName')
        if 'lastName' in profile_data:
            profile_data['lname'] = profile_data.pop('lastName')

        updated_pandit = None
        if pandit_data:
             updated_pandit = await self.pandit_repo.upsert_pandit_profile(user_id, pandit_data)
        
        if profile_data:
             await self.profile_repo.update_profile(user_id, profile_data)

        # Express returns "exist" which is the result of upserting panditProfile.
        return updated_pandit

    async def update_status(self, user_id: UUID, status_type: str, status_value: str) -> None:
        # Check simple validation if needed? Repository handles updates.
        # Express logic cancels active calls if statusType is "Call".
        await self.pandit_repo.update_pandit_status(user_id, status_type, status_value)
        if status_type == "Call":
            await self.pandit_repo.cancel_active_calls(user_id)

    async def follow_pandit(self, follower_id: UUID, pandit_id: UUID) -> None:
        await self.follower_repo.follow_user(follower_id, pandit_id)

    async def unfollow_pandit(self, follower_id: UUID, pandit_id: UUID) -> None:
        await self.follower_repo.unfollow_user(follower_id, pandit_id)

