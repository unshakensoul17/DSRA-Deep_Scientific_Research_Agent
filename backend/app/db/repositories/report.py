"""
DSRA V2 — Report Repository
============================
Database operations for the Report model.
"""

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.report import Report
from app.db.repositories.base import BaseRepository


class ReportRepository(BaseRepository[Report]):

    def __init__(self, db_session: AsyncSession):
        super().__init__(Report, db_session)

    async def get_by_session_id(self, session_id: UUID) -> Optional[Report]:
        """Fetch the latest report associated with a session."""
        query = select(Report).where(Report.session_id == session_id).order_by(Report.created_at.desc())
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()

    async def get_all_by_user_id(self, user_id: UUID, skip: int = 0, limit: int = 100) -> list[Report]:
        """Fetch reports for all sessions owned by a specific user."""
        from app.db.models.research_session import ResearchSession
        query = (
            select(Report)
            .join(ResearchSession)
            .where(ResearchSession.user_id == user_id)
            .offset(skip)
            .limit(limit)
        )
        result = await self.db_session.execute(query)
        return list(result.scalars().all())
