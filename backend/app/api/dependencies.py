"""
DSRA V2 — API Route Dependencies
=================================
Provides reusable FastAPI dependency injections for database sessions,
authentication contexts, and rate limiters.
"""

from typing import Optional
import uuid

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.security.api_key import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.db.models.user import User
from app.db.repositories.user import UserRepository
from app.db.session import get_db_session

# Security Schemes
security_bearer = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_current_user(
    db: AsyncSession = Depends(get_db_session),
    token_credentials: Optional[HTTPAuthorizationCredentials] = Security(security_bearer),
    api_key: Optional[str] = Security(api_key_header),
) -> User:
    """
    Authenticate request via JWT bearer token or custom API Key header.
    Returns the authenticated User model.
    """
    user_repo = UserRepository(db)
    
    # 1. API Key Auth
    if api_key:
        user = await user_repo.get_by_api_key(api_key)
        if user:
            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Inactive user account"
                )
            return user

    # 2. JWT Bearer Auth
    if token_credentials:
        token = token_credentials.credentials
        payload = decode_token(token)
        if payload and payload.get("type") == "access":
            user_id_str = payload.get("sub")
            if user_id_str:
                try:
                    user_id = uuid.UUID(user_id_str)
                    user = await user_repo.get_by_id(user_id)
                    if user:
                        if not user.is_active:
                            raise HTTPException(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Inactive user account"
                            )
                        return user
                except ValueError:
                    pass

    # Unauthenticated
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
