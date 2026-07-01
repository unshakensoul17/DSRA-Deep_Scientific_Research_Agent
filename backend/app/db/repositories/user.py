"""
DSRA V2 — User Repository
==========================
Database operations for the User model.
"""

from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User
from app.db.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """
    Query repository for managing User records and credentials.
    """

    def __init__(self, db_session: AsyncSession):
        super().__init__(User, db_session)

    async def get_by_email(self, email: str) -> Optional[User]:
        """Fetch user by unique email address."""
        query = select(User).where(User.email == email)
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_api_key(self, api_key: str) -> Optional[User]:
        """Fetch user by unique API key."""
        query = select(User).where(User.api_key == api_key)
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()
