# DSRA V2 — Agent Contracts

> **Living Document** — Every agent's interface is a binding contract.
> Last updated: 2026-07-01 | Phase: 2

---

## Design Principles

1. **Every agent has ONE responsibility.** If it does two things, split it.
2. **Agents are pure transformers.** Input → processing → output. No side effects except through injected dependencies.
3. **Agents never call each other.** Only the Orchestrator coordinates.
4. **Every agent is independently unit-testable** with mock LLM and mock repositories.
5. **The `BaseAgent` ABC enforces the contract.** If it doesn't implement `execute()`, it won't instantiate.

---

## BaseAgent Contract

```python
class BaseAgent(ABC, Generic[InputT, OutputT]):
    """
    Abstract base for all DSRA agents.
    Enforces: typed I/O, system prompt, retry logic, structured logging, metrics.
    """
    name: ClassVar[str]                    # e.g. "PlannerAgent"
    max_retries: ClassVar[int] = 3
    retry_delay_seconds: ClassVar[float] = 1.0

    @property
    @abstractmethod
    def system_prompt(self) -> str: ...

    @abstractmethod
    async def execute(self, input_data: InputT) -> OutputT: ...

    # Provided by BaseAgent (not overridden):
    async def run(self, input_data: InputT) -> OutputT:
        """Wraps execute() with retry logic, logging, and metrics."""
```

---

## Agent 1 — PlannerAgent

**Responsibility:** Understand the research goal, decompose it into specific search queries, select appropriate sources, and estimate complexity.

**Input Schema:**
```python
class ResearchGoal(BaseModel):
    model_config = ConfigDict(strict=True)

    session_id: UUID
    topic: str = Field(..., min_length=3, max_length=500,
                       description="The research topic entered by the user")
    depth: ResearchDepth = ResearchDepth.NORMAL   # Enum: SHALLOW=1, NORMAL=2, DEEP=3
    max_sources_per_query: int = Field(default=10, ge=1, le=50)
    source_preferences: list[SourceType] = Field(
        default_factory=lambda: list(SourceType)
    )
    focus_areas: list[str] = Field(default_factory=list,
                                   description="Optional user-specified sub-topics to emphasize")
    language: str = Field(default="en", pattern=r"^[a-z]{2}$")
```

**Output Schema:**
```python
class SearchQuery(BaseModel):
    query_text: str = Field(..., min_length=3, max_length=300)
    source_type: SourceType
    priority: float = Field(default=1.0, ge=0.0, le=1.0)
    filters: dict[str, Any] = Field(default_factory=dict)
    # e.g. filters={"date_from": "2020", "category": "cs.AI"}

class ResearchPlan(BaseModel):
    session_id: UUID
    topic: str
    queries: list[SearchQuery] = Field(..., min_length=1)
    estimated_complexity: float = Field(ge=0.0, le=1.0)
    suggested_depth: ResearchDepth
    focus_areas: list[str]
    reasoning: str = Field(..., description="LLM explanation of the plan")
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

**System Prompt Key:** Decomposes topic into 5–15 specific search queries distributed across source types. Returns structured JSON. Does NOT write research — only plans.

**Invariants:**
- Must produce at least 1 query per enabled source type
- `estimated_complexity` must be between 0.0 and 1.0
- Queries must be specific enough to return targeted results (not generic single-word queries)

---

## Agent 2 — ResearchAgent

**Responsibility:** Execute a single `SearchQuery` against its assigned source adapter and return a list of raw `SourceResult` objects. No reasoning. No synthesis.

**Input Schema:**
```python
class ResearchAgentInput(BaseModel):
    session_id: UUID
    query: SearchQuery
    max_results: int = Field(default=10, ge=1, le=50)
```

**Output Schema:**
```python
class SourceResult(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    session_id: UUID
    query_id: UUID
    title: str = Field(..., min_length=1)
    url: Optional[HttpUrl] = None
    snippet: str = Field(..., min_length=1)
    full_content: Optional[str] = None     # Retrieved if depth >= NORMAL
    source_type: SourceType
    quality_score: Optional[float] = None  # Assigned later by EvidenceAgent
    authors: list[str] = Field(default_factory=list)
    year: Optional[int] = Field(default=None, ge=1900, le=2100)
    doi: Optional[str] = None
    citation_count: Optional[int] = None   # SemanticScholar only
    fetched_at: datetime = Field(default_factory=datetime.utcnow)

class ResearchAgentOutput(BaseModel):
    session_id: UUID
    query: SearchQuery
    results: list[SourceResult]
    fetch_duration_ms: int
    error: Optional[str] = None            # Partial success allowed
```

**Design note:** `ResearchAgent` is source-agnostic. It receives a `BaseRetriever` implementation via dependency injection. This means we can test `ResearchAgent` logic independently from network calls.

**Invariants:**
- Never raises an exception — sets `error` field and returns partial results
- `fetched_at` must always be set
- Returns empty list (not None) if source returns nothing

---

## Agent 3 — EvidenceAgent

**Responsibility:** Given a list of `SourceResult` objects, extract specific evidence pieces (claim → source mappings), rank them by relevance, deduplicate, and assign quality scores. No synthesis. No report writing.

**Input Schema:**
```python
class EvidenceAgentInput(BaseModel):
    session_id: UUID
    sources: list[SourceResult] = Field(..., min_length=1)
    research_topic: str
    focus_areas: list[str] = Field(default_factory=list)
```

**Output Schema:**
```python
class EvidencePiece(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    session_id: UUID
    claim_text: str = Field(..., min_length=10,
                             description="A single atomic, falsifiable claim extracted from the source")
    source_id: UUID
    relevance_score: float = Field(ge=0.0, le=1.0)
    excerpt: str = Field(..., description="The exact quote or passage from the source that contains this claim")
    page_or_section: Optional[str] = None
    iteration: int = Field(default=0)

class EvidenceAgentOutput(BaseModel):
    session_id: UUID
    evidence_pieces: list[EvidencePiece]
    source_quality_scores: dict[UUID, float]  # source_id → quality_score
    deduplication_removed: int                # How many duplicates were removed
    total_sources_processed: int
```

**Invariants:**
- Each `EvidencePiece` maps to exactly one `SourceResult` via `source_id`
- `claim_text` must be atomic (one claim per piece, not a paragraph)
- Deduplication uses cosine similarity on claim text embeddings (threshold: 0.92)
- Quality scores are normalized to [0.0, 1.0]

---

## Agent 4 — VerificationAgent

**Responsibility:** Cross-reference evidence pieces against each other and against source content. Assign confidence scores and verification status to each claim. Flag contradictions. Does NOT write — only evaluates.

**Input Schema:**
```python
class VerificationAgentInput(BaseModel):
    session_id: UUID
    evidence_pieces: list[EvidencePiece]
    sources: list[SourceResult]           # Full source context for cross-reference
    research_topic: str
```

**Output Schema:**
```python
class VerificationStatus(str, Enum):
    VERIFIED = "VERIFIED"
    CONTRADICTED = "CONTRADICTED"
    UNVERIFIED = "UNVERIFIED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"

class VerifiedClaim(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    session_id: UUID
    text: str
    confidence: float = Field(ge=0.0, le=1.0)
    status: VerificationStatus
    supporting_source_ids: list[UUID] = Field(default_factory=list)
    contradicting_source_ids: list[UUID] = Field(default_factory=list)
    reasoning: str = Field(..., description="Why this status and confidence was assigned")
    iteration: int = 0

class VerificationAgentOutput(BaseModel):
    session_id: UUID
    verified_claims: list[VerifiedClaim]
    contradictions_found: int
    high_confidence_claims: int           # confidence >= 0.8
    verification_coverage: float          # % of evidence pieces that were verified
```

**Invariants:**
- Every input `EvidencePiece` maps to exactly one `VerifiedClaim`
- `confidence` for `CONTRADICTED` claims must be < 0.5
- `reasoning` must be non-empty
- `supporting_source_ids` must be non-empty for `VERIFIED` claims

---

## Agent 5 — GapAnalysisAgent

**Responsibility:** Compare the set of verified claims against the original research plan to find what's missing, what's underexplored, and what new search queries would fill those gaps. Decide whether another iteration is needed.

**Input Schema:**
```python
class GapAnalysisAgentInput(BaseModel):
    session_id: UUID
    research_plan: ResearchPlan
    verified_claims: list[VerifiedClaim]
    sources_count: int
    current_iteration: int
    max_iterations: int
```

**Output Schema:**
```python
class ResearchGap(BaseModel):
    description: str                     # e.g. "No clinical trial data found"
    severity: Literal["CRITICAL", "MODERATE", "MINOR"]
    suggested_queries: list[SearchQuery]  # Queries to fill this gap

class GapAnalysisOutput(BaseModel):
    session_id: UUID
    gaps: list[ResearchGap]
    has_critical_gaps: bool
    should_iterate: bool                 # False if max_iterations reached or no critical gaps
    new_queries: list[SearchQuery]       # Flattened from all gap.suggested_queries
    iteration_reasoning: str
    coverage_score: float = Field(ge=0.0, le=1.0,
                                   description="How well current evidence covers the research plan")
```

**Invariants:**
- `should_iterate` must be False if `current_iteration >= max_iterations`
- `should_iterate` must be False if `has_critical_gaps` is False
- `coverage_score` < 0.6 implies `has_critical_gaps = True` (configurable threshold)

---

## Agent 6 — WriterAgent

**Responsibility:** Produce a full structured research report from verified claims and source metadata. Every claim in the report must be grounded in a `VerifiedClaim`. Does NOT do research — only writes.

**Input Schema:**
```python
class WriterAgentInput(BaseModel):
    session_id: UUID
    research_plan: ResearchPlan
    verified_claims: list[VerifiedClaim]
    sources: list[SourceResult]
    previous_draft: Optional["ReportDraft"] = None  # Present during revision loop
    critique: Optional["CritiqueResult"] = None     # Present during revision loop
```

**Output Schema:**
```python
class ReportSection(BaseModel):
    title: str
    content: str = Field(..., min_length=100)
    claim_ids: list[UUID] = Field(default_factory=list)  # Claims cited in this section
    word_count: int

class ReportDraft(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    session_id: UUID
    title: str
    executive_summary: str = Field(..., min_length=150)
    sections: list[ReportSection] = Field(..., min_length=5)
    # Required sections: Introduction, Background, Methodology,
    #                    Research Findings, Analysis, Conflicting Views,
    #                    Limitations, Future Work, Conclusion
    key_findings: list[str] = Field(..., min_length=3)
    references: list[ReportReference]
    methodology_description: str
    revision: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ReportReference(BaseModel):
    source_id: UUID
    citation_key: str             # e.g. "[Author, Year]"
    title: str
    url: Optional[str] = None
    authors: list[str]
    year: Optional[int] = None
    source_type: SourceType
```

**Invariants:**
- Every claim in the report body must reference a `VerifiedClaim.id`
- References list must include every source cited anywhere in the report
- `executive_summary` must be >= 150 words
- Each section content must be >= 100 words
- `CONTRADICTED` claims must appear in "Conflicting Views" section only

---

## Agent 7 — CriticAgent

**Responsibility:** Evaluate a `ReportDraft` against a structured rubric. Produce a scored critique and decide whether the report is ready for publication or requires revision. Does NOT rewrite — only evaluates.

**Input Schema:**
```python
class CriticAgentInput(BaseModel):
    session_id: UUID
    draft: ReportDraft
    verified_claims: list[VerifiedClaim]
    sources: list[SourceResult]
    revision_number: int
    max_revisions: int
```

**Output Schema:**
```python
class CritiqueScore(BaseModel):
    dimension: str                       # e.g. "source_diversity", "claim_coverage"
    score: float = Field(ge=0.0, le=10.0)
    feedback: str

class CritiqueResult(BaseModel):
    session_id: UUID
    draft_id: UUID
    scores: list[CritiqueScore]          # One per rubric dimension
    overall_score: float = Field(ge=0.0, le=10.0)
    strengths: list[str]
    weaknesses: list[str]
    missing_points: list[str]
    revision_required: bool              # True if overall_score < threshold
    revision_instructions: list[str]     # Specific, actionable, ordered
    approved: bool                       # True if not revision_required OR max_revisions reached

# Rubric dimensions evaluated:
# - claim_coverage: Are all important verified claims included?
# - source_diversity: Are multiple source types represented?
# - citation_accuracy: Do citations map to actual sources?
# - logical_coherence: Does the argument flow logically?
# - completeness: Are all required sections present and substantive?
# - balance: Are conflicting views represented fairly?
# - clarity: Is the writing clear and professional?
```

**Invariants:**
- `approved` must be True if `revision_number >= max_revisions` (force approval)
- `revision_required` must be False if `approved` is True
- Overall score threshold for approval: 7.0 / 10.0 (configurable)

---

## Agent 8 — VisualizationAgent

**Responsibility:** Generate structured visualization data from the final report and claims. Produces tables, timeline data, and knowledge map data. Does NOT render HTML/images — only produces structured data that the frontend renders.

**Input Schema:**
```python
class VisualizationAgentInput(BaseModel):
    session_id: UUID
    report: ReportDraft
    verified_claims: list[VerifiedClaim]
    sources: list[SourceResult]
```

**Output Schema:**
```python
class TableVisualization(BaseModel):
    title: str
    headers: list[str]
    rows: list[list[str]]
    caption: Optional[str] = None

class TimelineEvent(BaseModel):
    year: int
    event: str
    source_id: Optional[UUID] = None
    significance: Literal["HIGH", "MEDIUM", "LOW"]

class KnowledgeNode(BaseModel):
    id: str
    label: str
    type: Literal["concept", "entity", "finding"]
    confidence: Optional[float] = None

class KnowledgeEdge(BaseModel):
    source: str
    target: str
    relationship: str

class VisualizationBundle(BaseModel):
    session_id: UUID
    tables: list[TableVisualization]
    timeline: list[TimelineEvent]
    knowledge_nodes: list[KnowledgeNode]
    knowledge_edges: list[KnowledgeEdge]
    confidence_distribution: dict[str, int]  # "HIGH/MEDIUM/LOW" → count
    source_type_distribution: dict[str, int] # source_type → count
```

---

## Agent 9 — ExportAgent

**Responsibility:** Take the final approved report and visualization bundle and produce all output formats. Writes files to disk via the configured output path. Returns file paths — never serves files directly.

**Input Schema:**
```python
class ExportAgentInput(BaseModel):
    session_id: UUID
    report: ReportDraft
    visualization: VisualizationBundle
    sources: list[SourceResult]
    export_formats: list[Literal["pdf", "markdown", "html", "json"]] = ["pdf", "markdown", "json"]
```

**Output Schema:**
```python
class ExportBundle(BaseModel):
    session_id: UUID
    report_id: UUID
    pdf_path: Optional[str] = None
    markdown_path: Optional[str] = None
    html_path: Optional[str] = None
    json_path: Optional[str] = None
    export_completed_at: datetime = Field(default_factory=datetime.utcnow)
    file_sizes: dict[str, int] = Field(default_factory=dict)  # format → bytes
```

**Invariants:**
- All output paths are generated from `session_id` — never from user input
- PDF must include all sections, references, and tables
- JSON export must be the full `ReportDraft` serialized with all citations

---

*Document maintained by: Lead Architecture Review*
*Last updated: 2026-07-01*
