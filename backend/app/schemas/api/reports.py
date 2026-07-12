"""
DSRA V2 — Reports API Schemas
==============================
Request and response models for final reports.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import Field

from app.schemas.agents.all_agents import VisualizationBundle
from app.schemas.common import (
    DSRABaseModel,
    ReportReference,
    ReportSection,
    ReportStatus,
)


class ReportListItemResponse(DSRABaseModel):
    id: UUID
    session_id: UUID
    title: str
    executive_summary_snippet: str
    status: ReportStatus
    critique_score: Optional[float] = None
    created_at: datetime


class ReportResponse(DSRABaseModel):
    id: UUID
    session_id: UUID
    title: str
    executive_summary: str
    sections: list[ReportSection]
    key_findings: list[str]
    references: list[ReportReference]
    methodology_description: str
    limitations: str
    conclusion: str
    visualization: Optional[VisualizationBundle] = None
    critique_score: Optional[float] = None
    status: ReportStatus
    export_paths: dict[str, str] = Field(default_factory=dict)
    created_at: datetime
    finalized_at: Optional[datetime] = None
