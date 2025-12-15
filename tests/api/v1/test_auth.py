import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock
from app.schemas.auth import VerifyOtpResponse
from app.dependencies.auth import get_current_user
from app.models.user import User
from uuid import uuid4
from app.cmd.main import app

@pytest.fixture
def mock_auth_service():
    with patch("app.api.v1.auth.AuthService") as mock:
        service_instance = mock.return_value
        service_instance.send_otp = AsyncMock()
        service_instance.verify_otp = AsyncMock()
        service_instance.disable_account = AsyncMock()
        yield service_instance

@pytest.mark.asyncio
async def test_send_otp(client: AsyncClient, mock_auth_service):
    response = await client.post("/api/v1/auth/otp", json={"mobile_no": "+918888888888"})
    assert response.status_code == 200
    assert response.json() == {"message": "Otp Sent"}
    mock_auth_service.send_otp.assert_called_once_with("+918888888888")

@pytest.mark.asyncio
async def test_verify_otp_success(client: AsyncClient, mock_auth_service):
    mobile_no = "+918888888888"
    otp = "1234"
    
    mock_response = VerifyOtpResponse(
        id="123e4567-e89b-12d3-a456-426614174000",
        mobile_no=mobile_no,
        token="access_token",
        refresh_token="refresh_token",
        message="Login successful",
        profile_exists=True,
        is_active=True
    )
    mock_auth_service.verify_otp.return_value = mock_response

    response = await client.post("/api/v1/auth/verify", json={"mobile_no": mobile_no, "otp": otp})
    assert response.status_code == 200
    data = response.json()
    assert data["token"] == "access_token"
    mock_auth_service.verify_otp.assert_called_once_with(mobile_no, otp, None)

@pytest.mark.asyncio
async def test_disable_account(client: AsyncClient, mock_auth_service):
    # Mock current user
    mock_user = User(id=uuid4(), mobile_no="+918888888888", is_active=True)
    app.dependency_overrides[get_current_user] = lambda: mock_user
    
    try:
        response = await client.post("/api/v1/auth/delete")
        assert response.status_code == 200
        assert response.json() == {"message": "Account deleted"}
        mock_auth_service.disable_account.assert_called_once_with(mock_user.id)
    finally:
        if get_current_user in app.dependency_overrides:
            del app.dependency_overrides[get_current_user]
