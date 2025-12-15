from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr

from app.schemas.profile import FullProfileResponse

class PanditUpdateRequest(BaseModel):
    # Fields for PanditProfile
    information: Optional[str] = None
    language: Optional[List[str]] = None
    experience: Optional[str] = None
    astrotype: Optional[List[str]] = None
    qualification: Optional[List[str]] = None
    
    # Fields for User Profile (merged update)
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    email: Optional[EmailStr] = None


class PanditListResponse(BaseModel):
    # reuse FullProfileResponse or similar?
    # Express code: "res.status(200).json(exist);" where exist is list of users.
    # So it returns a list of User objects which contain profile, panditProfile, etc.
    # We can reuse FullProfileResponse but valid it's a list.
    pass
