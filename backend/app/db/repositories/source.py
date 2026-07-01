"""
DSRA V2 — Source Repository
============================
Database operations for the Source model.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.source import Source
from app.db.repositories.base import BaseRepository


class SourceRepository(BaseRepository[Source]):

    def __init__(self, db_session: AsyncSession):
        super().__init__(Source, db_session)

    async def get_by_session_id(self, session_id: UUID) -> list[Source]:
        """Fetch all sources associated with a specific research session."""
        query = select(Source).where(Source.session_id == session_id)
        result = await self.db_session.execute(query)
        return list(result.scalars().all())

    async def get_by_session_and_type(self, session_id: UUID, source_type: str) -> list[Source]:
        """Fetch sources filtered by their source type (e.g. arXiv)."""
        query = (
            select(Source)
            .where(Source.session_id == session_id)
            .where(Source.source_type == source_type)
        )
        result = await self.db_session.execute(query)
        return list(result.scalars().all())
