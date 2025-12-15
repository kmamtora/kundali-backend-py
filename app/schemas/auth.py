from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class SendOtpRequest(BaseModel):
    mobile_no: str = Field(..., description="Mobile number including country code")


class VerifyOtpRequest(BaseModel):
    mobile_no: str
    otp: str
    fcm_token: str | None = None


class VerifyOtpResponse(BaseModel):
    id: UUID
    mobile_no: str
    token: str
    refresh_token: str
    message: str = "Login successful"
    profile_exists: bool = False
    is_active: bool


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class DisableAccountRequest(BaseModel):
    pass
