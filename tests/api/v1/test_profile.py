import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock
from uuid import uuid4
from app.models.user import User
from app.dependencies.auth import get_current_user
from app.cmd.main import app
from app.schemas.profile import FullProfileResponse, ProfileResponse

@pytest.fixture
def mock_profile_service():
    with patch("app.api.v1.profile.ProfileService") as mock:
        service_instance = mock.return_value
        service_instance.update_profile = AsyncMock()
        service_instance.get_full_profile = AsyncMock()
        yield service_instance

@pytest.mark.asyncio
async def test_update_profile(client: AsyncClient, mock_profile_service):
    user_id = uuid4()
    mock_user = User(id=user_id, mobile_no="+918888888888", is_active=True)
    app.dependency_overrides[get_current_user] = lambda: mock_user

    payload = {"fname": "John", "lname": "Doe"}
    mock_profile_service.update_profile.return_value = {"id": user_id, "fname": "John", "lname": "Doe"}

    try:
        # ID in path is ignored per logic, but must be there
        response = await client.patch(f"/api/v1/profile/user/{user_id}", json=payload)
        assert response.status_code == 200
        assert response.json()["fname"] == "John"
        mock_profile_service.update_profile.assert_called_once()
    finally:
        if get_current_user in app.dependency_overrides:
            del app.dependency_overrides[get_current_user]

@pytest.mark.asyncio
async def test_get_full_profile(client: AsyncClient, mock_profile_service):
    user_id = uuid4()
    target_id = uuid4()
    mock_user = User(id=user_id, mobile_no="+918888888888", is_active=True)
    app.dependency_overrides[get_current_user] = lambda: mock_user

    mock_response = FullProfileResponse(
        mobile_no="+919999999999",
        profile=ProfileResponse(
            id=target_id, user_id=target_id, gender=True, is_user=True, is_active=True, fname="Jane"
        ),
        panditProfile=None,
        rate=None,
        followerCount=10,
        isFollowing=True
    )
    mock_profile_service.get_full_profile.return_value = mock_response

    try:
        response = await client.get(f"/api/v1/profile/user/{target_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["followerCount"] == 10
        assert data["isFollowing"] is True
        assert data["profile"]["fname"] == "Jane"
        mock_profile_service.get_full_profile.assert_called_once_with(target_id, user_id)
    finally:
        if get_current_user in app.dependency_overrides:
            del app.dependency_overrides[get_current_user]
