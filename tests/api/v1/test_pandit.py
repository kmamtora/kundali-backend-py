import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock, MagicMock
from uuid import uuid4
from app.models.user import User
from app.dependencies.auth import get_current_user
from app.cmd.main import app
from app.schemas.profile import FullProfileResponse, ProfileResponse
from app.schemas.pandit import PanditUpdateRequest

@pytest.fixture
def mock_pandit_service():
    with patch("app.api.v1.pandit.PanditService") as mock:
        service_instance = mock.return_value
        service_instance.get_all_pandits = AsyncMock()
        service_instance.update_pandit_profile = AsyncMock()
        service_instance.update_status = AsyncMock()
        service_instance.follow_pandit = AsyncMock()
        service_instance.unfollow_pandit = AsyncMock()
        yield service_instance

@pytest.fixture
def mock_profile_service_pandit():
    # Mocking ProfileService called within /pandit/{id}
    with patch("app.api.v1.pandit.ProfileService") as mock:
        service_instance = mock.return_value
        service_instance.get_full_profile = AsyncMock()
        yield service_instance

@pytest.mark.asyncio
async def test_get_all_pandits(client: AsyncClient, mock_pandit_service):
    user_id = uuid4()
    mock_user = User(id=user_id, mobile_no="+918888888888", is_active=True)
    app.dependency_overrides[get_current_user] = lambda: mock_user

    mock_response = [FullProfileResponse(
        mobile_no="+919999999999",
        profile=ProfileResponse(
            id=uuid4(), user_id=uuid4(), gender=True, is_user=False, is_active=True, fname="Guru"
        ),
        panditProfile=None,
        rate=None,
        followerCount=50,
        isFollowing=False
    )]
    mock_pandit_service.get_all_pandits.return_value = mock_response

    try:
        response = await client.get("/api/v1/pandit")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["profile"]["fname"] == "Guru"
        mock_pandit_service.get_all_pandits.assert_called_once_with(user_id)
    finally:
        if get_current_user in app.dependency_overrides:
            del app.dependency_overrides[get_current_user]

@pytest.mark.asyncio
async def test_update_pandit_profile(client: AsyncClient, mock_pandit_service):
    user_id = uuid4()
    mock_user = User(id=user_id, mobile_no="+918888888888", is_active=True)
    app.dependency_overrides[get_current_user] = lambda: mock_user

    payload = {
        "information": "Experienced Astrologer",
        "firstName": "UpdatedName"
    }
    
    # Return value doesn't strictly matter for response body, Express returns object
    mock_pandit_service.update_pandit_profile.return_value = {"id": user_id, "foo": "bar"}

    try:
        response = await client.patch(f"/api/v1/pandit/{user_id}", json=payload)
        assert response.status_code == 200
        # Check call arguments
        mock_pandit_service.update_pandit_profile.assert_called_once()
        # Ensure payload was parsed correctly
        call_args = mock_pandit_service.update_pandit_profile.call_args
        assert call_args[0][0] == user_id
        # Request object
        assert isinstance(call_args[0][1], PanditUpdateRequest)
        assert call_args[0][1].information == "Experienced Astrologer"
        assert call_args[0][1].firstName == "UpdatedName"

    finally:
        if get_current_user in app.dependency_overrides:
            del app.dependency_overrides[get_current_user]

@pytest.mark.asyncio
async def test_update_pandit_status(client: AsyncClient, mock_pandit_service):
    user_id = uuid4()
    mock_user = User(id=user_id, mobile_no="+918888888888", is_active=True)
    app.dependency_overrides[get_current_user] = lambda: mock_user

    payload = {"statusType": "Call", "statusValue": True}
    
    try:
        response = await client.post("/api/v1/pandit/status", json=payload)
        assert response.status_code == 200
        assert response.json() == {"message": "Updated successfully"}
        mock_pandit_service.update_status.assert_called_once_with(user_id, "Call", True)
    finally:
        if get_current_user in app.dependency_overrides:
            del app.dependency_overrides[get_current_user]

@pytest.mark.asyncio
async def test_follow_pandit(client: AsyncClient, mock_pandit_service):
    user_id = uuid4()
    pandit_id = uuid4()
    mock_user = User(id=user_id, mobile_no="+918888888888", is_active=True)
    app.dependency_overrides[get_current_user] = lambda: mock_user

    payload = {"panditId": str(pandit_id)}
    
    try:
        response = await client.post("/api/v1/pandit/follow", json=payload)
        assert response.status_code == 200
        assert response.json() == {"message": "Followed successfully"}
        mock_pandit_service.follow_pandit.assert_called_once_with(user_id, pandit_id)
    finally:
        if get_current_user in app.dependency_overrides:
            del app.dependency_overrides[get_current_user]

@pytest.mark.asyncio
async def test_unfollow_pandit(client: AsyncClient, mock_pandit_service):
    user_id = uuid4()
    pandit_id = uuid4()
    mock_user = User(id=user_id, mobile_no="+918888888888", is_active=True)
    app.dependency_overrides[get_current_user] = lambda: mock_user

    payload = {"panditId": str(pandit_id)}
    
    try:
        response = await client.post("/api/v1/pandit/unfollow", json=payload)
        assert response.status_code == 200
        assert response.json() == {"message": "Unfollowed successfully"}
        mock_pandit_service.unfollow_pandit.assert_called_once_with(user_id, pandit_id)
    finally:
        if get_current_user in app.dependency_overrides:
            del app.dependency_overrides[get_current_user]

