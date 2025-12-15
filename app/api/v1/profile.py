from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.profile import ProfileUpdateRequest, ProfileResponse, FullProfileResponse
from app.services.profile_service import ProfileService

router = APIRouter(prefix="/profile", tags=["Profile"])

@router.patch("/user/{id}", status_code=status.HTTP_200_OK)
async def update_user_profile(
    id: str, # Express uses :id but largely ignores it or expects it to match user?
             # Express: const { id } = req.user; (It IGNORES path param :id completely!)
    request: ProfileUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Update the current user's profile.
    Note: The 'id' in the path is ignored to match Express security logic 
    (which uses req.user.id), preventing users from updating others' profiles.
    """
    profile_service = ProfileService(session)
    # Use current_user.id, ignoring path param 'id'
    updated_profile = await profile_service.update_profile(current_user.id, request)
    return updated_profile


@router.get("/user/{id}", response_model=FullProfileResponse, status_code=status.HTTP_200_OK)
async def get_full_profile_by_id(
    id: str, # Express parses this as Int? "parseInt(id)". But our ID is UUID.
             # User model uses UUID. If express used Int, migration might have issues if data mismatch.
             # Assuming we are fully migrated to UUIDs as per Plan.
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Get full profile by User ID.
    """
    try:
        target_uuid = UUID(id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    profile_service = ProfileService(session)
    return await profile_service.get_full_profile(target_uuid, current_user.id)
