"""Agent schemas — PlannerAgent input/output contracts."""

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import Field

from app.schemas.common import (
    DSRABaseModel,
    ResearchDepth,
    SearchQuery,
    SourceType,
)


class ResearchGoal(DSRABaseModel):
    """
    Input to PlannerAgent.
    Created from user API request and stored at session start.
    """
    session_id: UUID
    topic: str = Field(..., min_length=3, max_length=500)
    depth: ResearchDepth = ResearchDepth.NORMAL
    max_sources_per_query: int = Field(default=10, ge=1, le=50)
    source_preferences: list[SourceType] = Field(
        default_factory=lambda: list(SourceType)
    )
    focus_areas: list[str] = Field(default_factory=list)
    language: str = Field(default="en", pattern=r"^[a-z]{2}$")


class ResearchPlan(DSRABaseModel):
    """
    Output of PlannerAgent.
    Contains all search queries and metadata for the research session.
    """
    session_id: UUID
    topic: str
    queries: list[SearchQuery] = Field(..., min_length=1)
    estimated_complexity: float = Field(ge=0.0, le=1.0)
    suggested_depth: ResearchDepth
    focus_areas: list[str] = Field(default_factory=list)
    reasoning: str = Field(..., min_length=10)
    created_at: datetime = Field(default_factory=datetime.utcnow)
