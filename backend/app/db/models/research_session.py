"""
DSRA V2 — ResearchSession Database Model
========================================
Stores research sessions, current states, and configured parameters.
"""

from datetime import datetime
from typing import Optional
import uuid

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.schemas.common import ResearchDepth, SessionState


class ResearchSession(Base):
    __tablename__ = "research_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    topic: Mapped[str] = mapped_column(Text, nullable=False)
    state: Mapped[SessionState] = mapped_column(
        Enum(SessionState, native_enum=False), default=SessionState.CREATED, nullable=False, index=True
    )
    depth: Mapped[ResearchDepth] = mapped_column(
        Enum(ResearchDepth, native_enum=False), default=ResearchDepth.NORMAL, nullable=False
    )
    iteration_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_iterations: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    user = relationship("User", back_populates="sessions")
    queries = relationship("ResearchQuery", back_populates="session", cascade="all, delete-orphan")
    sources = relationship("Source", back_populates="session", cascade="all, delete-orphan")
    claims = relationship("Claim", back_populates="session", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="session", cascade="all, delete-orphan")
    execution_logs = relationship("AgentExecutionLog", back_populates="session", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<ResearchSession id={self.id} topic={self.topic[:40]} state={self.state}>"
