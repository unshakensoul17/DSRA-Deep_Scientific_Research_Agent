"""Agent schemas — EvidenceAgent, VerificationAgent, GapAnalysisAgent, CriticAgent, WriterAgent, ExportAgent."""

from datetime import datetime
from typing import Literal, Optional
from uuid import UUID, uuid4

from pydantic import Field

from app.schemas.common import (
    DSRABaseModel,
    EvidencePiece,
    ExportFormat,
    GapSeverity,
    ReportDraft,
    SearchQuery,
    SourceResult,
    VerificationStatus,
    VerifiedClaim,
)


# ── EvidenceAgent ─────────────────────────────────────────────────────────────

class EvidenceAgentInput(DSRABaseModel):
    session_id: UUID
    sources: list[SourceResult] = Field(..., min_length=1)
    research_topic: str
    focus_areas: list[str] = Field(default_factory=list)


class EvidenceAgentOutput(DSRABaseModel):
    session_id: UUID
    evidence_pieces: list[EvidencePiece]
    source_quality_scores: dict[str, float]  # source_id (str) → quality_score
    deduplication_removed: int = Field(ge=0)
    total_sources_processed: int = Field(ge=0)


# ── VerificationAgent ─────────────────────────────────────────────────────────

class VerificationAgentInput(DSRABaseModel):
    session_id: UUID
    evidence_pieces: list[EvidencePiece]
    sources: list[SourceResult]
    research_topic: str


class VerificationAgentOutput(DSRABaseModel):
    session_id: UUID
    verified_claims: list[VerifiedClaim]
    contradictions_found: int = Field(ge=0)
    high_confidence_claims: int = Field(ge=0)
    verification_coverage: float = Field(ge=0.0, le=1.0)


# ── GapAnalysisAgent ──────────────────────────────────────────────────────────

class ResearchGap(DSRABaseModel):
    description: str = Field(..., min_length=10)
    severity: GapSeverity
    suggested_queries: list[SearchQuery] = Field(default_factory=list)


class GapAnalysisAgentInput(DSRABaseModel):
    session_id: UUID
    research_plan_topic: str
    research_plan_focus_areas: list[str]
    verified_claims: list[VerifiedClaim]
    sources_count: int = Field(ge=0)
    current_iteration: int = Field(ge=0)
    max_iterations: int = Field(ge=1)


class GapAnalysisAgentOutput(DSRABaseModel):
    session_id: UUID
    gaps: list[ResearchGap] = Field(default_factory=list)
    has_critical_gaps: bool
    should_iterate: bool
    new_queries: list[SearchQuery] = Field(default_factory=list)
    iteration_reasoning: str
    coverage_score: float = Field(ge=0.0, le=1.0)


# ── CriticAgent ───────────────────────────────────────────────────────────────

class CritiqueScore(DSRABaseModel):
    dimension: str
    score: float = Field(ge=0.0, le=10.0)
    feedback: str = Field(..., min_length=10)


class CriticAgentInput(DSRABaseModel):
    session_id: UUID
    draft: ReportDraft
    verified_claims: list[VerifiedClaim]
    sources: list[SourceResult]
    revision_number: int = Field(ge=0)
    max_revisions: int = Field(ge=1)


class CritiqueResult(DSRABaseModel):
    session_id: UUID
    draft_id: UUID
    scores: list[CritiqueScore] = Field(..., min_length=1)
    overall_score: float = Field(ge=0.0, le=10.0)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    missing_points: list[str] = Field(default_factory=list)
    revision_required: bool
    revision_instructions: list[str] = Field(default_factory=list)
    approved: bool


# ── WriterAgent ───────────────────────────────────────────────────────────────

class WriterAgentInput(DSRABaseModel):
    session_id: UUID
    research_plan_topic: str
    research_plan_focus_areas: list[str]
    verified_claims: list[VerifiedClaim]
    sources: list[SourceResult]
    previous_draft: Optional[ReportDraft] = None
    critique: Optional[CritiqueResult] = None


# WriterAgent output IS ReportDraft (defined in common.py)


# ── VisualizationAgent ────────────────────────────────────────────────────────

class TableVisualization(DSRABaseModel):
    title: str
    headers: list[str] = Field(..., min_length=1)
    rows: list[list[str]] = Field(default_factory=list)
    caption: Optional[str] = None


class TimelineEvent(DSRABaseModel):
    year: int = Field(ge=1900, le=2100)
    event: str = Field(..., min_length=5)
    source_id: Optional[UUID] = None
    significance: Literal["HIGH", "MEDIUM", "LOW"] = "MEDIUM"


class KnowledgeNode(DSRABaseModel):
    id: str
    label: str
    node_type: Literal["concept", "entity", "finding"]
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class KnowledgeEdge(DSRABaseModel):
    source: str
    target: str
    relationship: str


class VisualizationAgentInput(DSRABaseModel):
    session_id: UUID
    report: ReportDraft
    verified_claims: list[VerifiedClaim]
    sources: list[SourceResult]


class VisualizationBundle(DSRABaseModel):
    session_id: UUID
    tables: list[TableVisualization] = Field(default_factory=list)
    timeline: list[TimelineEvent] = Field(default_factory=list)
    knowledge_nodes: list[KnowledgeNode] = Field(default_factory=list)
    knowledge_edges: list[KnowledgeEdge] = Field(default_factory=list)
    confidence_distribution: dict[str, int] = Field(default_factory=dict)
    source_type_distribution: dict[str, int] = Field(default_factory=dict)


# ── ExportAgent ───────────────────────────────────────────────────────────────

class ExportAgentInput(DSRABaseModel):
    session_id: UUID
    report: ReportDraft
    visualization: VisualizationBundle
    sources: list[SourceResult]
    export_formats: list[ExportFormat] = Field(
        default_factory=lambda: [ExportFormat.PDF, ExportFormat.MARKDOWN, ExportFormat.JSON]
    )


class ExportBundle(DSRABaseModel):
    session_id: UUID
    report_id: UUID
    pdf_path: Optional[str] = None
    markdown_path: Optional[str] = None
    html_path: Optional[str] = None
    json_path: Optional[str] = None
    export_completed_at: datetime = Field(default_factory=datetime.utcnow)
    file_sizes: dict[str, int] = Field(default_factory=dict)
