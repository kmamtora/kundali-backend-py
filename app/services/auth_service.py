import random
from datetime import datetime, timedelta, timezone
from uuid import UUID
import bcrypt

from fastapi import HTTPException, status
from jose import jwt
from twilio.rest import Client
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import settings
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.repositories.profile_repository import ProfileRepository
from app.schemas.auth import VerifyOtpResponse, TokenResponse


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)
        self.profile_repo = ProfileRepository(session)
        
        # Initialize Twilio Client only if credentials are set
        self.twilio_client = None
        if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
            self.twilio_client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

    def _generate_otp(self) -> str:
        # Generate random 4 digit number
        return str(random.randint(1000, 9999))

    def _hash_otp(self, otp: str) -> str:
        # bcrypt.hashpw requires bytes
        # bcrypt.gensalt() generates a salt
        hashed = bcrypt.hashpw(otp.encode('utf-8'), bcrypt.gensalt())
        return hashed.decode('utf-8')

    def _verify_hash(self, plain_otp: str, hashed_otp: str) -> bool:
        # bcrypt.checkpw requires bytes
        return bcrypt.checkpw(plain_otp.encode('utf-8'), hashed_otp.encode('utf-8'))

    def create_access_token(self, data: dict, expires_delta: timedelta | None = None) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        return encoded_jwt

    def create_refresh_token(self, data: dict) -> str:
        # Refresh tokens last longer
        expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode = data.copy()
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        return encoded_jwt

    async def send_sms(self, to: str, body: str) -> None:
        if not self.twilio_client:
            print(f"Twilio not configured. Mock SMS to {to}: {body}")
            return
        
        try:
            self.twilio_client.messages.create(
                body=body,
                from_=settings.TWILIO_FROM_NUMBER,
                to=to
            )
        except Exception as e:
            # Log error but don't crash? Express code logged error.
            print(f"Error sending SMS: {e}")

    async def send_otp(self, mobile_no: str) -> None:
        otp = ""
        # Hardcoded OTPs from Express logic
        if mobile_no == "+918888888888" or mobile_no == "+919999999999":
            otp = "1234"
        else:
            otp = self._generate_otp()
            await self.send_sms(mobile_no, f"Your OTP is {otp}")

        hashed_otp = self._hash_otp(otp)
        # Expires in 10 minutes
        otp_expires = datetime.now(timezone.utc) + timedelta(minutes=10)

        existing_user = await self.user_repo.get_by_mobile(mobile_no)
        if existing_user:
            await self.user_repo.update_otp(
                user_id=existing_user.id,
                otp=hashed_otp,
                otp_expires=otp_expires,
                is_active=True # Reactivate if was inactive, per logic
            )
        else:
            await self.user_repo.create_user(
                mobile_no=mobile_no,
                otp=hashed_otp,
                otp_expires=otp_expires
            )

    async def verify_otp(self, mobile_no: str, otp: str, fcm_token: str | None) -> VerifyOtpResponse:
        user = await self.user_repo.get_by_mobile(mobile_no)
        
        if not user or not user.is_active:
             raise HTTPException(status_code=400, detail="Invalid or expired OTP")

        # Check expiration
        # Note: SQLAlchemy returns datetime with timezone info if using DateTime(timezone=True)
        # Ensure we compare correctly. 
        if user.otp_expires < datetime.now(timezone.utc):
             raise HTTPException(status_code=400, detail="Invalid or expired OTP")

        if not self._verify_hash(otp, user.otp):
             raise HTTPException(status_code=400, detail="Invalid or expired OTP")

        # OTP is valid.
        # Check profile
        profile = await self.profile_repo.get_by_user_id(user.id)
        
        # Upsert logic from Express:
        # if (!_.isEmpty(exist) && _.isEmpty(exist?.profile)) -> create profile
        # if exists -> check isUser -> findFirst (just re-fetching)
        
        # Basically ensures profile exists and has is_user=True
        profile = await self.profile_repo.upsert_user_profile(user.id)
        
        # Update FCM
        if fcm_token:
            await self.profile_repo.update_fcm_key(user.id, fcm_token)

        # Generate tokens
        token_data = {"sub": str(user.id)}
        access_token = self.create_access_token(token_data)
        refresh_token = self.create_refresh_token(token_data)
        
        return VerifyOtpResponse(
            id=user.id,
            mobile_no=user.mobile_no,
            token=access_token,
            refresh_token=refresh_token,
            profile_exists=True, # We just upserted it
            is_active=user.is_active
        )

    async def disable_account(self, user_id: UUID) -> None:
        await self.user_repo.deactivate_user(user_id)
