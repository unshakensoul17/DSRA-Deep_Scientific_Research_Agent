"""
DSRA V2 — Source Database Model
================================
Stores raw or full-text retrieved documents for auditability and verification.
"""

from datetime import datetime
from typing import Any, Optional
import uuid

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.schemas.common import SourceType


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("research_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    query_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("research_queries.id", ondelete="SET NULL"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    snippet: Mapped[str] = mapped_column(Text, nullable=False)
    full_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_type: Mapped[SourceType] = mapped_column(
        Enum(SourceType, native_enum=False), nullable=False
    )
    quality_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    authors: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    doi: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    citation_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )

    # Relationships
    session = relationship("ResearchSession", back_populates="sources")
    query = relationship("ResearchQuery", back_populates="sources")

    def __repr__(self) -> str:
        return f"<Source id={self.id} type={self.source_type} title={self.title[:30]}>"
