from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.auth import SendOtpRequest, VerifyOtpRequest, VerifyOtpResponse, DisableAccountRequest
from app.services.auth_service import AuthService
from app.dependencies.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/otp", status_code=status.HTTP_200_OK)
async def send_otp(
    request: SendOtpRequest,
    session: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Send OTP to the provided mobile number.
    """
    auth_service = AuthService(session)
    await auth_service.send_otp(request.mobile_no)
    return {"message": "Otp Sent"}


@router.post("/verify", response_model=VerifyOtpResponse, status_code=status.HTTP_200_OK)
async def verify_otp(
    request: VerifyOtpRequest,
    session: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Verify OTP and return access tokens.
    """
    auth_service = AuthService(session)
    return await auth_service.verify_otp(request.mobile_no, request.otp, request.fcm_token)


@router.post("/delete", status_code=status.HTTP_200_OK)
async def delete_account(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Disable the current user's account.
    """
    # Note: Express route was named '/delete' but function was disableAccount.
    # Logic only sets isActive = false.
    auth_service = AuthService(session)
    await auth_service.disable_account(current_user.id)
    return {"message": "Account deleted"}
