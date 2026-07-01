"""
DSRA V2 — ResearchQuery Database Model
======================================
Stores specific search queries executed by agents during research iterations.
"""

from datetime import datetime
import uuid

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.schemas.common import SourceType


class ResearchQuery(Base):
    __tablename__ = "research_queries"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("research_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[SourceType] = mapped_column(
        Enum(SourceType, native_enum=False), nullable=False
    )
    iteration: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    filters: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )

    # Relationships
    session = relationship("ResearchSession", back_populates="queries")
    sources = relationship("Source", back_populates="query")

    def __repr__(self) -> str:
        return f"<ResearchQuery id={self.id} type={self.source_type} query={self.query_text[:30]}>"
