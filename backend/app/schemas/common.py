"""
DSRA V2 — Shared Pydantic Schemas
====================================
Common types used across all agents, retrievers, and API layers.
This module is the single source of truth for shared domain types.

Import hierarchy:
  schemas.common → agents schemas → api schemas
  schemas.common → db models (via enums)
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator


# ═══════════════════════════════════════════════════════════════════
# Enumerations
# ═══════════════════════════════════════════════════════════════════

class SourceType(str, Enum):
    ARXIV = "arxiv"
    SEMANTIC_SCHOLAR = "semantic_scholar"
    WIKIPEDIA = "wikipedia"
    GOOGLE_CSE = "google_cse"
    PUBMED = "pubmed"


class ResearchDepth(int, Enum):
    SHALLOW = 1
    NORMAL = 2
    DEEP = 3


class SessionState(str, Enum):
    CREATED = "CREATED"
    PLANNING = "PLANNING"
    RETRIEVAL = "RETRIEVAL"
    EVIDENCE_EXTRACTION = "EVIDENCE_EXTRACTION"
    VERIFICATION = "VERIFICATION"
    GAP_ANALYSIS = "GAP_ANALYSIS"
    ITERATING = "ITERATING"
    WRITING = "WRITING"
    CRITIQUE = "CRITIQUE"
    VISUALIZATION = "VISUALIZATION"
    EXPORT = "EXPORT"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

    @classmethod
    def terminal_states(cls) -> set["SessionState"]:
        return {cls.COMPLETED, cls.FAILED, cls.CANCELLED}

    @classmethod
    def active_states(cls) -> set["SessionState"]:
        return set(cls) - cls.terminal_states()


class VerificationStatus(str, Enum):
    VERIFIED = "VERIFIED"
    CONTRADICTED = "CONTRADICTED"
    UNVERIFIED = "UNVERIFIED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class ReportStatus(str, Enum):
    DRAFT = "DRAFT"
    FINAL = "FINAL"


class GapSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    MODERATE = "MODERATE"
    MINOR = "MINOR"


class ExportFormat(str, Enum):
    PDF = "pdf"
    MARKDOWN = "markdown"
    HTML = "html"
    JSON = "json"


# ═══════════════════════════════════════════════════════════════════
# Base Model Configuration
# ═══════════════════════════════════════════════════════════════════

class DSRABaseModel(BaseModel):
    """
    Base model for all DSRA schemas.
    Allows standard type coercion (like strings to enums) during validation.
    """
    model_config = ConfigDict(
        strict=False,
        use_enum_values=True,
        populate_by_name=True,
        frozen=False,
    )


# ═══════════════════════════════════════════════════════════════════
# Core Domain Types
# ═══════════════════════════════════════════════════════════════════

class SearchQuery(DSRABaseModel):
    """A specific search query to be executed by a ResearchAgent."""
    id: UUID = Field(default_factory=uuid4)
    query_text: str = Field(..., min_length=3, max_length=300)
    source_type: SourceType
    priority: float = Field(default=1.0, ge=0.0, le=1.0)
    filters: dict[str, Any] = Field(default_factory=dict)
    # Example filters:
    # arXiv: {"categories": ["cs.AI", "cs.LG"], "date_from": "2020"}
    # SemanticScholar: {"fields_of_study": ["Medicine"], "year": "2020-2024"}
    # PubMed: {"mesh_terms": ["CRISPR"], "publication_types": ["Clinical Trial"]}

    @model_validator(mode="before")
    @classmethod
    def normalize_llm_aliases(cls, data: Any) -> Any:
        """Accept common LLM/legacy keys while storing the canonical contract."""
        if not isinstance(data, dict):
            return data

        normalized = dict(data)
        if "query_text" not in normalized and "query" in normalized:
            normalized["query_text"] = normalized["query"]
        if "source_type" not in normalized and "engine" in normalized:
            normalized["source_type"] = normalized["engine"]
        return normalized


class SourceResult(DSRABaseModel):
    """
    A single document retrieved from a source.
    Produced by RetrieverAdapters, consumed by EvidenceAgent.
    """
    id: UUID = Field(default_factory=uuid4)
    session_id: Optional[UUID] = None
    query_id: Optional[UUID] = None
    title: str = Field(..., min_length=1, max_length=1000)
    url: Optional[str] = None
    snippet: str = Field(..., min_length=1)
    full_content: Optional[str] = Field(
        default=None,
        description="Full text retrieved for NORMAL/DEEP depth sessions"
    )
    source_type: SourceType
    quality_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    authors: list[str] = Field(default_factory=list)
    year: Optional[int] = Field(default=None, ge=1900, le=2100)
    doi: Optional[str] = None
    citation_count: Optional[int] = Field(default=None, ge=0)
    fetched_at: datetime = Field(default_factory=datetime.utcnow)


class EvidencePiece(DSRABaseModel):
    """
    An atomic, falsifiable claim extracted from a SourceResult.
    Produced by EvidenceAgent. One claim per piece.
    """
    id: UUID = Field(default_factory=uuid4)
    session_id: UUID
    claim_text: str = Field(
        ...,
        min_length=10,
        description="A single, atomic, falsifiable claim"
    )
    source_id: UUID
    relevance_score: float = Field(ge=0.0, le=1.0)
    excerpt: str = Field(
        ...,
        description="The exact text passage from the source supporting this claim"
    )
    page_or_section: Optional[str] = None
    iteration: int = Field(default=0, ge=0)


class VerifiedClaim(DSRABaseModel):
    """
    An EvidencePiece that has been cross-referenced and assigned a confidence score.
    Produced by VerificationAgent. Consumed by WriterAgent and GapAnalysisAgent.
    """
    id: UUID = Field(default_factory=uuid4)
    session_id: UUID
    text: str = Field(..., min_length=10)
    confidence: float = Field(ge=0.0, le=1.0)
    status: VerificationStatus = VerificationStatus.UNVERIFIED
    supporting_source_ids: list[UUID] = Field(default_factory=list)
    contradicting_source_ids: list[UUID] = Field(default_factory=list)
    reasoning: str = Field(..., min_length=10)
    iteration: int = Field(default=0, ge=0)


class ReportReference(DSRABaseModel):
    """A formatted citation reference in the final report."""
    source_id: UUID
    citation_key: str = Field(..., description="e.g. '[Frangoul, 2021]'")
    title: str
    url: Optional[str] = None
    authors: list[str] = Field(default_factory=list)
    year: Optional[int] = None
    source_type: SourceType
    doi: Optional[str] = None


class ReportSection(DSRABaseModel):
    """A single section of the research report."""
    title: str
    content: str = Field(..., min_length=100)
    claim_ids: list[UUID] = Field(
        default_factory=list,
        description="IDs of VerifiedClaims referenced in this section"
    )

    @property
    def word_count(self) -> int:
        return len(self.content.split())


class ReportDraft(DSRABaseModel):
    """
    A complete research report draft.
    Produced by WriterAgent, evaluated by CriticAgent.
    """
    id: UUID = Field(default_factory=uuid4)
    session_id: UUID
    title: str = Field(..., min_length=5)
    executive_summary: str = Field(..., min_length=150)
    sections: list[ReportSection] = Field(..., min_length=5)
    key_findings: list[str] = Field(..., min_length=3)
    references: list[ReportReference] = Field(default_factory=list)
    methodology_description: str = Field(..., min_length=50)
    limitations: str = Field(..., min_length=50)
    conclusion: str = Field(..., min_length=100)
    revision: int = Field(default=0, ge=0)
    status: ReportStatus = ReportStatus.DRAFT
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ═══════════════════════════════════════════════════════════════════
# SSE Event Types
# ═══════════════════════════════════════════════════════════════════

class SSEEventType(str, Enum):
    SESSION_STATE_CHANGED = "session_state_changed"
    AGENT_STARTED = "agent_started"
    AGENT_COMPLETED = "agent_completed"
    AGENT_FAILED = "agent_failed"
    SOURCE_BATCH_FETCHED = "source_batch_fetched"
    EVIDENCE_EXTRACTED = "evidence_extracted"
    CLAIM_VERIFIED = "claim_verified"
    GAP_DETECTED = "gap_detected"
    REPORT_SECTION_COMPLETE = "report_section_complete"
    RESEARCH_COMPLETE = "research_complete"
    ERROR = "error"
    HEARTBEAT = "heartbeat"


class SSEEvent(DSRABaseModel):
    """Structured SSE event payload."""
    event: SSEEventType
    session_id: UUID
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: dict[str, Any] = Field(default_factory=dict)

    def to_sse_string(self) -> str:
        """Format as proper SSE wire format."""
        import json
        payload = {
            "session_id": str(self.session_id),
            "timestamp": self.timestamp.isoformat(),
            **self.data,
        }
        return f"event: {self.event}\ndata: {json.dumps(payload)}\n\n"


# ═══════════════════════════════════════════════════════════════════
# Pagination
# ═══════════════════════════════════════════════════════════════════

class PaginationParams(DSRABaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class PaginatedResponse(DSRABaseModel):
    """Generic paginated response wrapper."""
    total: int = Field(ge=0)
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    total_pages: int = Field(ge=0)

    @classmethod
    def from_count(cls, total: int, page: int, page_size: int) -> "PaginatedResponse":
        import math
        return cls(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=math.ceil(total / page_size) if total > 0 else 0,
        )
