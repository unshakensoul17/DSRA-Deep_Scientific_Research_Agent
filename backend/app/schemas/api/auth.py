"""
DSRA V2 — API Request and Response Schemas
============================================
Pydantic models representing API contracts for request payloads
and response bodies.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import EmailStr, Field

from app.schemas.common import DSRABaseModel


class UserRegisterRequest(DSRABaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


class UserLoginRequest(DSRABaseModel):
    email: EmailStr
    password: str


class TokenResponse(DSRABaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenRefreshRequest(DSRABaseModel):
    refresh_token: str


class TokenRefreshResponse(DSRABaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(DSRABaseModel):
    id: UUID
    email: EmailStr
    created_at: datetime
