"""
DSRA V2 — Claim Repository
===========================
Database operations for Claim and VerificationResult models.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.claim import Claim
from app.db.repositories.base import BaseRepository


class ClaimRepository(BaseRepository[Claim]):

    def __init__(self, db_session: AsyncSession):
        super().__init__(Claim, db_session)

    async def get_by_session_id(self, session_id: UUID) -> list[Claim]:
        """Fetch all claims for a session with their verification results loaded."""
        query = (
            select(Claim)
            .where(Claim.session_id == session_id)
            .options(selectinload(Claim.verification_results))
        )
        result = await self.db_session.execute(query)
        return list(result.scalars().all())

    async def get_by_status(self, session_id: UUID, status: str) -> list[Claim]:
        """Fetch claims filtered by verification status."""
        query = (
            select(Claim)
            .where(Claim.session_id == session_id)
            .where(Claim.status == status)
            .options(selectinload(Claim.verification_results))
        )
        result = await self.db_session.execute(query)
        return list(result.scalars().all())
