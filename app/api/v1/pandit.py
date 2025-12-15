from typing import Annotated, List, Any
from uuid import UUID

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.profile import FullProfileResponse
from app.schemas.pandit import PanditUpdateRequest
from app.services.pandit_service import PanditService
from app.services.profile_service import ProfileService

router = APIRouter(prefix="/pandit", tags=["Pandit"])

@router.get("", response_model=List[FullProfileResponse], status_code=status.HTTP_200_OK)
async def get_all_pandits(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Get all active pandits.
    """
    pandit_service = PanditService(session)
    return await pandit_service.get_all_pandits(current_user.id)


@router.get("/{id}", response_model=FullProfileResponse, status_code=status.HTTP_200_OK)
async def get_pandit_by_id(
    id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Get full profile by ID (Reuses profile services get_full_profile).
    """
    try:
        target_uuid = UUID(id)
    except ValueError:
         raise HTTPException(status_code=400, detail="Invalid UUID format")
         
    profile_service = ProfileService(session)
    return await profile_service.get_full_profile(target_uuid, current_user.id)


@router.patch("/{id}", status_code=status.HTTP_200_OK)
async def update_pandit_profile(
    id: str,
    request: PanditUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Update Pandit Profile + Basic Profile Info.
    Note: ID in path is IGNORED for security, using current_user.id.
    """
    pandit_service = PanditService(session)
    # Use current_user.id, ignoring path param 'id'
    updated = await pandit_service.update_pandit_profile(current_user.id, request)
    return updated
