"""
DSRA V2 — ResearchSession Repository
======================================
Database operations for the ResearchSession model.
Handles atomic state transitions and related collections query.
"""

from typing import Optional
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.research_session import ResearchSession
from app.db.repositories.base import BaseRepository
from app.schemas.common import SessionState


class ResearchSessionRepository(BaseRepository[ResearchSession]):
    """
    Query repository for managing ResearchSession lifecycle.
    """

    def __init__(self, db_session: AsyncSession):
        super().__init__(ResearchSession, db_session)

    async def get_by_id_with_relationships(self, session_id: UUID) -> Optional[ResearchSession]:
        """Fetch session with all its collections loaded (avoiding lazy load errors)."""
        query = (
            select(ResearchSession)
            .where(ResearchSession.id == session_id)
            .options(
                selectinload(ResearchSession.queries),
                selectinload(ResearchSession.sources),
                selectinload(ResearchSession.claims),
                selectinload(ResearchSession.reports),
                selectinload(ResearchSession.execution_logs),
            )
        )
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()

    async def update_state(self, session_id: UUID, new_state: SessionState) -> bool:
        """Update session state atomically in the DB."""
        stmt = (
            update(ResearchSession)
            .where(ResearchSession.id == session_id)
            .values(state=new_state, updated_at=self.db_session.info.get("now", None) or None)
        )
        result = await self.db_session.execute(stmt)
        return result.rowcount > 0

    async def increment_iteration(self, session_id: UUID) -> Optional[int]:
        """Increment execution loop iteration counter."""
        session = await self.get_by_id(session_id)
        if session:
            session.iteration_count += 1
            return session.iteration_count
        return None
