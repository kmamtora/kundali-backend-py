from datetime import datetime
from uuid import UUID
from typing import List, Optional

from pydantic import BaseModel, Field, EmailStr


class ProfileUpdateRequest(BaseModel):
    fname: Optional[str] = None
    lname: Optional[str] = None
    email: Optional[EmailStr] = None
    gender: Optional[bool] = None
    bdate: Optional[str] = None  # Keeping as string to match Express (date validation can be added)
    btime: Optional[str] = None
    bplace: Optional[str] = None
    
    # Note: 'qualification' was in request body in express code, but Model uses it in PanditProfile?
    # Checking Express code again: 
    # const { fname, lname, email, gender, bdate, btime, bplace, qualification } = req.body;
    # It updates prisma.profile with fname...bplace. 
    # qualification seems unused in the update query provided in prompt?
    # "update: { fname: fname... bplace: bplace }" -> qualification is missing in update clause.
    # I will include it if needed but maybe it belongs to PanditProfile?
    # The prompt code shows `qualification` extracted but NOT used in the `prisma.profile.upsert`.
    # I will omit it from this specific schema or keep it optional and unused.


class ProfileResponse(BaseModel):
    id: UUID
    user_id: UUID
    email: Optional[str] = None
    fname: Optional[str] = None
    lname: Optional[str] = None
    gender: bool
    bdate: Optional[str] = None
    btime: Optional[str] = None
    bplace: Optional[str] = None
    profile_pic: Optional[str] = None
    profile_video: Optional[str] = None
    is_user: bool
    is_active: bool
    
    class Config:
        from_attributes = True


class PanditProfileResponse(BaseModel):
    id: UUID
    information: str
    is_active_chat: str
    is_active_call: str
    is_active_live: str
    language: List[str]
    experience: str
    qualification: List[str]
    astrotype: List[str]
    tag: str
    
    class Config:
        from_attributes = True


class RateResponse(BaseModel):
    id: UUID
    audio_rate: int
    chat_rate: int
    video_rate: int
    live_rate: int
    
    class Config:
        from_attributes = True


class FullProfileResponse(BaseModel):
    mobile_no: str
    profile: Optional[ProfileResponse] = None
    pandit_profile: Optional[PanditProfileResponse] = Field(None, alias="panditProfile")
    rate: Optional[RateResponse] = None
    follower_count: int = Field(0, alias="followerCount")
    is_following: bool = Field(False, alias="isFollowing")

    class Config:
        from_attributes = True
        populate_by_name = True
