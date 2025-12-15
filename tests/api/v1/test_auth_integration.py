import pytest
from httpx import AsyncClient
from app.services.auth_service import AuthService
from app.models.user import User
from uuid import uuid4
from unittest.mock import AsyncMock, patch, MagicMock
from app.core.database import get_db
from app.core.settings import settings
from jose import jwt
from datetime import datetime, timedelta, timezone
from app.cmd.main import app

@pytest.mark.asyncio
async def test_auth_header_integration(client: AsyncClient):
    # 1. Create a valid token
    user_id = uuid4()
    token_data = {"sub": str(user_id)}
    expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    token_data.update({"exp": expire})
    token = jwt.encode(token_data, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    
    # 2. Mock the DB interaction in get_current_user
    # We need to mock UserRepository.get_by_id to return a user
    mock_user = User(id=user_id, mobile_no="+918888888888", is_active=True)
    
    # We need to patch UserRepository inside the dependency.
    # Since get_current_user instantiates UserRepository(session), 
    # and session is injected via Depends(get_db), we can mock the session.
    
    mock_session = AsyncMock()
    # Mock execute result
    # We need the result object to have a synchronous scalar_one_or_none method
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_user
    mock_session.execute.return_value = mock_result
    
    async def override_get_db():
        yield mock_session
        
    app.dependency_overrides[get_db] = override_get_db
    
    # 3. Make request WITH Authorization header
    # Targeting /auth/delete which is protected
    headers = {"Authorization": f"Bearer {token}"}
    
    # Use patch auth service for the delete logic itself to avoid errors there
    with patch("app.api.v1.auth.AuthService") as mock_service_cls:
        mock_instance = mock_service_cls.return_value
        mock_instance.disable_account = AsyncMock()
        
        response = await client.post("/api/v1/auth/delete", headers=headers)
        
        # 4. Verify
        assert response.status_code == 200
        assert response.json() == {"message": "Account deleted"}

    # Clean up
    del app.dependency_overrides[get_db]
