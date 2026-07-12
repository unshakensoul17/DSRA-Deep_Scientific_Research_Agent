"""Agent schemas — EvidenceAgent, VerificationAgent, GapAnalysisAgent, CriticAgent, WriterAgent, ExportAgent."""

from datetime import datetime
from typing import Any, Literal, Optional
from uuid import UUID, uuid4

from pydantic import Field, model_validator

from app.schemas.common import (
    DSRABaseModel,
    EvidencePiece,
    ExportFormat,
    GapSeverity,
    ReportDraft,
    ReportSection,
    SearchQuery,
    SourceResult,
    SourceType,
    VerificationStatus,
    VerifiedClaim,
)


# ── EvidenceAgent ─────────────────────────────────────────────────────────────

class EvidenceAgentInput(DSRABaseModel):
    session_id: UUID
    sources: list[SourceResult] = Field(..., min_length=1)
    research_topic: str
    focus_areas: list[str] = Field(default_factory=list)


class EvidenceExtractionPiece(DSRABaseModel):
    """LLM-facing evidence piece without runtime-generated identifiers."""
    claim_text: str = Field(..., min_length=10)
    source_id: UUID
    relevance_score: float = Field(ge=0.0, le=1.0)
    excerpt: str
    page_or_section: Optional[str] = None
    iteration: int = Field(default=0, ge=0)

    @model_validator(mode="before")
    @classmethod
    def normalize_llm_aliases(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        normalized = dict(data)
        normalized.pop("id", None)
        return normalized


class EvidenceLLMOutput(DSRABaseModel):
    session_id: UUID
    evidence_pieces: list[EvidenceExtractionPiece]
    source_quality_scores: dict[str, float]
    deduplication_removed: int = Field(ge=0)
    total_sources_processed: int = Field(ge=0)


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


class LLMVerifiedClaim(DSRABaseModel):
    """LLM-facing verified claim — no runtime UUIDs required."""
    text: str = Field(..., min_length=10)
    confidence: float = Field(ge=0.0, le=1.0)
    status: VerificationStatus = VerificationStatus.UNVERIFIED
    supporting_source_ids: list[str] = Field(default_factory=list)
    contradicting_source_ids: list[str] = Field(default_factory=list)
    reasoning: str = Field(..., min_length=10)
    iteration: int = Field(default=0, ge=0)

    @model_validator(mode="before")
    @classmethod
    def strip_runtime_ids(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        cleaned = dict(data)
        cleaned.pop("id", None)
        cleaned.pop("session_id", None)
        return cleaned


class VerificationLLMOutput(DSRABaseModel):
    """LLM-facing output for VerificationAgent — no top-level runtime UUIDs."""
    verified_claims: list[LLMVerifiedClaim]
    contradictions_found: int = Field(ge=0)
    high_confidence_claims: int = Field(ge=0)
    verification_coverage: float = Field(ge=0.0, le=1.0)

    @model_validator(mode="before")
    @classmethod
    def strip_runtime_ids(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        cleaned = dict(data)
        cleaned.pop("session_id", None)
        return cleaned


class VerificationAgentOutput(DSRABaseModel):
    session_id: UUID
    verified_claims: list[VerifiedClaim]
    contradictions_found: int = Field(ge=0)
    high_confidence_claims: int = Field(ge=0)
    verification_coverage: float = Field(ge=0.0, le=1.0)


# ── GapAnalysisAgent ──────────────────────────────────────────────────────────

class LLMSearchQuery(DSRABaseModel):
    """LLM-facing search query without runtime id field."""
    query_text: str = Field(..., min_length=3, max_length=300)
    source_type: SourceType
    priority: float = Field(default=1.0, ge=0.0, le=1.0)
    filters: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def strip_and_normalize(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        cleaned = dict(data)
        cleaned.pop("id", None)
        # accept legacy LLM key aliases
        if "query_text" not in cleaned and "query" in cleaned:
            cleaned["query_text"] = cleaned.pop("query")
        if "source_type" not in cleaned and "engine" in cleaned:
            cleaned["source_type"] = cleaned.pop("engine")
        return cleaned


class ResearchGap(DSRABaseModel):
    """LLM-facing gap model — suggested_queries use LLMSearchQuery (no runtime id)."""
    description: str = Field(..., min_length=10)
    severity: GapSeverity
    suggested_queries: list[LLMSearchQuery] = Field(default_factory=list)


class RuntimeResearchGap(DSRABaseModel):
    """Runtime gap model — suggested_queries use full SearchQuery with id."""
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


class GapAnalysisLLMOutput(DSRABaseModel):
    """LLM-facing output for GapAnalysisAgent — no runtime session_id."""
    gaps: list[ResearchGap] = Field(default_factory=list)
    has_critical_gaps: bool
    should_iterate: bool
    new_queries: list[LLMSearchQuery] = Field(default_factory=list)
    iteration_reasoning: str
    coverage_score: float = Field(ge=0.0, le=1.0)

    @model_validator(mode="before")
    @classmethod
    def strip_runtime_ids(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        cleaned = dict(data)
        cleaned.pop("session_id", None)
        return cleaned


class GapAnalysisAgentOutput(DSRABaseModel):
    session_id: UUID
    gaps: list[RuntimeResearchGap] = Field(default_factory=list)
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

    @model_validator(mode="before")
    @classmethod
    def strip_runtime_ids(cls, data: Any) -> Any:
        """Strip hallucinated session_id/draft_id — the agent always overrides them."""
        if not isinstance(data, dict):
            return data
        cleaned = dict(data)
        cleaned.pop("session_id", None)
        cleaned.pop("draft_id", None)
        # Provide placeholder UUIDs so Pydantic won't fail — agent overrides them
        cleaned.setdefault("session_id", str(uuid4()))
        cleaned.setdefault("draft_id", str(uuid4()))
        return cleaned


# ── WriterAgent ───────────────────────────────────────────────────────────────

class WriterAgentInput(DSRABaseModel):
    session_id: UUID
    research_plan_topic: str
    research_plan_focus_areas: list[str]
    verified_claims: list[VerifiedClaim]
    sources: list[SourceResult]
    previous_draft: Optional[ReportDraft] = None
    critique: Optional[CritiqueResult] = None


class LLMReportSection(DSRABaseModel):
    """LLM-facing report section — no UUID claim_ids list."""
    title: str
    content: str = Field(..., min_length=100)
    claim_ids: list[str] = Field(default_factory=list)  # Accept strings; agent converts


class LLMReportReference(DSRABaseModel):
    """LLM-facing reference — source_id as string to avoid UUID hallucination errors."""
    source_id: str  # string; agent matches against real source IDs
    citation_key: str
    title: str
    url: Optional[str] = None
    authors: list[str] = Field(default_factory=list)
    year: Optional[int] = None
    source_type: str = "unknown"
    doi: Optional[str] = None


class WriterLLMOutput(DSRABaseModel):
    """LLM-facing output for WriterAgent — no runtime UUIDs required."""
    title: str = Field(..., min_length=5)
    executive_summary: str = Field(..., min_length=150)
    sections: list[LLMReportSection] = Field(..., min_length=1)
    key_findings: list[str] = Field(..., min_length=1)
    references: list[LLMReportReference] = Field(default_factory=list)
    methodology_description: str = Field(..., min_length=50)
    limitations: str = Field(..., min_length=50)
    conclusion: str = Field(..., min_length=100)
    revision: int = Field(default=0, ge=0)

    @model_validator(mode="before")
    @classmethod
    def strip_runtime_ids(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        cleaned = dict(data)
        cleaned.pop("id", None)
        cleaned.pop("session_id", None)
        cleaned.pop("status", None)
        cleaned.pop("created_at", None)
        return cleaned


# WriterAgent runtime output IS ReportDraft (defined in common.py)


# ── VisualizationAgent ────────────────────────────────────────────────────────

class TableVisualization(DSRABaseModel):
    title: str
    headers: list[str] = Field(..., min_length=1)
    rows: list[list[str]] = Field(default_factory=list)
    caption: Optional[str] = None


class TimelineEvent(DSRABaseModel):
    year: int = Field(ge=1900, le=2100)
    event: str = Field(..., min_length=5)
    source_id: Optional[str] = None  # String to avoid UUID hallucination; converted by agent
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


class VisualizationLLMOutput(DSRABaseModel):
    """LLM-facing output for VisualizationAgent — no runtime session_id."""
    tables: list[TableVisualization] = Field(default_factory=list)
    timeline: list[TimelineEvent] = Field(default_factory=list)
    knowledge_nodes: list[KnowledgeNode] = Field(default_factory=list)
    knowledge_edges: list[KnowledgeEdge] = Field(default_factory=list)
    confidence_distribution: dict[str, int] = Field(default_factory=dict)
    source_type_distribution: dict[str, int] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def strip_runtime_ids(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        cleaned = dict(data)
        cleaned.pop("session_id", None)
        return cleaned


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


# ── ResearchAgent ─────────────────────────────────────────────────────────────

class ResearchAgentInput(DSRABaseModel):
    session_id: UUID
    query: SearchQuery
    max_results: int = Field(default=10, ge=1, le=50)


class ResearchAgentOutput(DSRABaseModel):
    session_id: UUID
    query: SearchQuery
    results: list[SourceResult]
    fetch_duration_ms: int = Field(ge=0)
    error: Optional[str] = None
