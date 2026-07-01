"""
DSRA V2 — Research Sessions & Reports Router Unit Tests
=========================================================
Verifies session creation, list filtering, detail reports access,
and checks workspace ownership and authentication constraints.
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import status
from httpx import ASGITransport, AsyncClient

from app.core.security import create_access_token
from app.db.models.user import User
from app.db.models.research_session import ResearchSession
from app.schemas.common import SessionState, ResearchDepth
from app.main import app


@pytest.fixture
def mock_db_session():
    """Mock database AsyncSession context."""
    session = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.execute = AsyncMock()
    return session


@pytest.fixture
def test_user():
    """Returns a test user record."""
    return User(
        id=uuid.uuid4(),
        email="owner@dsra.com",
        is_active=True,
        created_at=datetime.now(timezone.utc)
    )


@pytest.fixture
def auth_headers(test_user):
    """Returns headers with a valid bearer token for the test user."""
    token = create_access_token(subject=test_user.id)
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_create_session(mock_db_session, test_user, auth_headers):
    """Verifies successful creation of a new research session."""
    topic = "CRISPR gene editing therapy off-target repair mechanics"
    
    mock_session_repo = MagicMock()
    mock_session_repo.create = AsyncMock()

    mock_user_repo = MagicMock()
    mock_user_repo.get_by_id = AsyncMock(return_value=test_user)

    from app.db.session import get_db_session
    app.dependency_overrides[get_db_session] = lambda: mock_db_session

    with patch("app.api.dependencies.UserRepository", return_value=mock_user_repo), \
         patch("app.api.v1.routers.research.ResearchSessionRepository", return_value=mock_session_repo):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post(
                "/api/v1/sessions",
                json={"topic": topic, "depth": 2, "max_iterations": 3},
                headers=auth_headers
            )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["topic"] == topic
    assert "session_id" in data
    mock_session_repo.create.assert_called_once()

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_session_details_owner_success(mock_db_session, test_user, auth_headers):
    """Verifies that the session owner can view details of their workspace."""
    session_id = uuid.uuid4()
    session_record = ResearchSession(
        id=session_id,
        user_id=test_user.id,
        topic="CRISPR repair",
        state=SessionState.CREATED,
        depth=ResearchDepth.NORMAL,
        max_iterations=3,
        iteration_count=0,
        sources=[],
        claims=[],
        reports=[],
        execution_logs=[],
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    mock_session_repo = MagicMock()
    mock_session_repo.get_by_id_with_relationships = AsyncMock(return_value=session_record)

    mock_user_repo = MagicMock()
    mock_user_repo.get_by_id = AsyncMock(return_value=test_user)

    from app.db.session import get_db_session
    app.dependency_overrides[get_db_session] = lambda: mock_db_session

    with patch("app.api.dependencies.UserRepository", return_value=mock_user_repo), \
         patch("app.api.v1.routers.research.ResearchSessionRepository", return_value=mock_session_repo):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get(f"/api/v1/sessions/{session_id}", headers=auth_headers)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["session_id"] == str(session_id)
    assert data["topic"] == "CRISPR repair"

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_session_details_non_owner_forbidden(mock_db_session, test_user, auth_headers):
    """Verifies that fetching details of another user's session returns 403 Forbidden."""
    session_id = uuid.uuid4()
    other_user_id = uuid.uuid4()
    
    session_record = ResearchSession(
        id=session_id,
        user_id=other_user_id, # not test_user.id
        topic="Secret CRISPR research",
        state=SessionState.CREATED,
        depth=ResearchDepth.NORMAL,
        max_iterations=3,
        iteration_count=0,
        sources=[],
        claims=[],
        reports=[],
        execution_logs=[],
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    mock_session_repo = MagicMock()
    mock_session_repo.get_by_id_with_relationships = AsyncMock(return_value=session_record)

    mock_user_repo = MagicMock()
    mock_user_repo.get_by_id = AsyncMock(return_value=test_user)

    from app.db.session import get_db_session
    app.dependency_overrides[get_db_session] = lambda: mock_db_session

    with patch("app.api.dependencies.UserRepository", return_value=mock_user_repo), \
         patch("app.api.v1.routers.research.ResearchSessionRepository", return_value=mock_session_repo):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get(f"/api/v1/sessions/{session_id}", headers=auth_headers)

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "access forbidden" in response.json()["detail"].lower()

    app.dependency_overrides.clear()
