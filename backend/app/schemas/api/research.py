"""
DSRA V2 — Research API Schemas
================================
Request and response models for research session lifecycle management.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import Field

from app.schemas.common import (
    DSRABaseModel,
    ResearchDepth,
    SessionState,
    SourceType,
)


class ResearchSessionCreateRequest(DSRABaseModel):
    topic: str = Field(..., min_length=3, max_length=500)
    depth: ResearchDepth = Field(default=ResearchDepth.NORMAL, strict=False)
    max_sources_per_query: int = Field(default=10, ge=1, le=50)
    source_preferences: list[SourceType] = Field(
        default_factory=lambda: [SourceType.ARXIV, SourceType.SEMANTIC_SCHOLAR, SourceType.WIKIPEDIA],
        strict=False
    )
    focus_areas: list[str] = Field(default_factory=list)
    max_iterations: int = Field(default=3, ge=1, le=5)


class ResearchSessionResponse(DSRABaseModel):
    session_id: UUID
    topic: str
    state: SessionState
    depth: ResearchDepth = Field(..., strict=False)
    iteration_count: int
    max_iterations: int
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None


class ResearchSessionDetailResponse(ResearchSessionResponse):
    sources_count: int
    claims_count: int
    verified_claims_count: int
    report_id: Optional[UUID] = None
    agent_timeline: list[dict] = Field(default_factory=list)


class ResearchSessionStartResponse(DSRABaseModel):
    session_id: UUID
    state: SessionState
    stream_url: str
