"""
DSRA V2 — Authentication & API Security Unit Tests
===================================================
Verifies registration, login, token refresh, endpoint guards,
and user profile access using mocked database sessions.
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI, status
from httpx import ASGITransport, AsyncClient

from app.core.security import create_access_token, get_password_hash
from app.db.models.user import User
from app.main import app


@pytest.fixture
def mock_db_session():
    """Mock the AsyncSession local database context."""
    session = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.execute = AsyncMock()
    return session


@pytest.mark.asyncio
async def test_register_user_success(mock_db_session):
    """Verifies that user register succeeds and hashes passwords correctly."""
    email = "test@dsra.com"
    password = "securepassword123"
    
    mock_user_repo = MagicMock()
    mock_user_repo.get_by_email = AsyncMock(return_value=None)
    mock_user_repo.create = AsyncMock()

    # Override dependencies
    from app.db.session import get_db_session
    app.dependency_overrides[get_db_session] = lambda: mock_db_session

    with patch("app.api.v1.routers.auth.UserRepository", return_value=mock_user_repo):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post(
                "/api/v1/auth/register",
                json={"email": email, "password": password}
            )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["email"] == email
    assert "id" in data
    mock_user_repo.create.assert_called_once()
    
    # Cleanup overrides
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_register_user_duplicate_email(mock_db_session):
    """Verifies duplicate registration attempts are blocked with 400 Bad Request."""
    email = "existing@dsra.com"
    password = "securepassword123"
    
    existing_user = User(
        id=uuid.uuid4(),
        email=email,
        hashed_password="somehashvalue",
        is_active=True
    )
    
    mock_user_repo = MagicMock()
    mock_user_repo.get_by_email = AsyncMock(return_value=existing_user)

    from app.db.session import get_db_session
    app.dependency_overrides[get_db_session] = lambda: mock_db_session

    with patch("app.api.v1.routers.auth.UserRepository", return_value=mock_user_repo):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post(
                "/api/v1/auth/register",
                json={"email": email, "password": password}
            )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "already exists" in response.json()["detail"]
    
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_login_user_success(mock_db_session):
    """Verifies that login issues access and refresh tokens upon valid credentials."""
    email = "user@dsra.com"
    password = "correct_password"
    user_id = uuid.uuid4()
    
    existing_user = User(
        id=user_id,
        email=email,
        hashed_password=get_password_hash(password),
        is_active=True
    )
    
    mock_user_repo = MagicMock()
    mock_user_repo.get_by_email = AsyncMock(return_value=existing_user)

    from app.db.session import get_db_session
    app.dependency_overrides[get_db_session] = lambda: mock_db_session

    with patch("app.api.v1.routers.auth.UserRepository", return_value=mock_user_repo):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post(
                "/api/v1/auth/login",
                json={"email": email, "password": password}
            )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_me_unauthorized():
    """Verifies access to private routes without tokens is blocked with 401 Unauthorized."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/auth/me")
        
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "credentials" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_me_authenticated(mock_db_session):
    """Verifies access to profile details using valid access token is successful."""
    user_id = uuid.uuid4()
    email = "verified@dsra.com"
    
    current_user = User(
        id=user_id,
        email=email,
        is_active=True,
        created_at=datetime.now(timezone.utc)
    )
    
    mock_user_repo = MagicMock()
    mock_user_repo.get_by_id = AsyncMock(return_value=current_user)

    from app.db.session import get_db_session
    app.dependency_overrides[get_db_session] = lambda: mock_db_session

    token = create_access_token(subject=user_id)
    headers = {"Authorization": f"Bearer {token}"}

    with patch("app.api.dependencies.UserRepository", return_value=mock_user_repo):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get("/api/v1/auth/me", headers=headers)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == email
    assert data["id"] == str(user_id)
    app.dependency_overrides.clear()
