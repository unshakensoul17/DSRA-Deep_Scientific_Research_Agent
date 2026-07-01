"""
DSRA V2 — End-to-End Workflow Integration Tests
================================================
Verifies research session orchestration pipeline execution:
- Mocks external API boundaries (LLMs and retrievers).
- Validates the sequential multi-agent state transitions.
- Ensures DB repository operations and SSE event broker publishing.
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.core.orchestrator import ResearchOrchestrator
from app.schemas.common import (
    SessionState,
    SourceType,
    ResearchDepth,
    SourceResult,
    EvidencePiece,
    VerifiedClaim,
    VerificationStatus,
    ReportDraft,
    ReportSection,
    ReportReference,
)
from app.schemas.agents.all_agents import (
    GapAnalysisAgentOutput,
    CritiqueResult,
    CritiqueScore,
    VisualizationBundle,
    ExportBundle,
)
from app.db.models.research_session import ResearchSession
from app.db.models.user import User


@pytest.fixture
def mock_db_session():
    """Mock database AsyncSession context."""
    session = MagicMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.refresh = AsyncMock()
    session.execute = MagicMock()
    return session


@pytest.fixture
def test_user():
    """Returns a test user record."""
    return User(
        id=uuid.uuid4(),
        email="owner@dsra.com",
        is_active=True,
        created_at=datetime.now(timezone.utc)
    )


@pytest.mark.asyncio
async def test_full_research_workflow_success(mock_db_session, test_user):
    """
    Verifies that run_research_session executes all agent phases sequentially,
    records execution metrics, commits entities to the DB, and completes successfully.
    """
    session_id = uuid.uuid4()
    source_id = uuid.uuid4()
    claim_id = uuid.uuid4()
    
    # 1. Setup mock session database record
    session_record = ResearchSession(
        id=session_id,
        user_id=test_user.id,
        topic="Integration testing of DSRA multi-agent workflow system",
        state=SessionState.CREATED,
        depth=ResearchDepth.NORMAL,
        max_iterations=3,
        iteration_count=0,
        sources=[],
        claims=[],
        reports=[],
        execution_logs=[],
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    # Mock repos inside the orchestrator
    mock_session_repo = MagicMock()
    mock_session_repo.get_by_id = AsyncMock(return_value=session_record)
    
    # 2. Mock Agent Outputs with proper Pydantic schemas
    # A. Planner Output
    from app.schemas.common import SearchQuery
    mock_plan = MagicMock()
    mock_plan.queries = [
        SearchQuery(id=uuid.uuid4(), query_text="Query 1", source_type=SourceType.ARXIV, filters={}),
        SearchQuery(id=uuid.uuid4(), query_text="Query 2", source_type=SourceType.WIKIPEDIA, filters={})
    ]
    mock_plan.topic = session_record.topic
    mock_plan.focus_areas = []
    mock_plan.estimated_complexity = "moderate"
    
    # B. Researcher Output
    mock_research_output = MagicMock()
    mock_source = SourceResult(
        id=source_id,
        session_id=session_id,
        query_id=uuid.uuid4(),
        title="Mock Scientific Source Title",
        url="http://example.com/source",
        snippet="This is a scientific snippet about the topic.",
        full_content="Full content here.",
        source_type=SourceType.ARXIV,
        authors=["Dr. Test"],
        year=2026,
        doi=None,
        citation_count=10,
        quality_score=0.85,
    )
    mock_research_output.results = [mock_source, mock_source]

    # C. Evidence Output
    mock_evidence_output = MagicMock()
    mock_evidence_piece = EvidencePiece(
        id=claim_id,
        session_id=session_id,
        claim_text="Atomic scientific claim verified by test.",
        source_id=source_id,
        relevance_score=0.9,
        excerpt="excerpt text"
    )
    mock_evidence_output.evidence_pieces = [mock_evidence_piece]
    mock_evidence_output.source_quality_scores = {str(source_id): 0.85}

    # D. Verification Output
    mock_verification_output = MagicMock()
    mock_verified_claim = VerifiedClaim(
        id=claim_id,
        session_id=session_id,
        text="Atomic scientific claim verified by test.",
        confidence=0.95,
        status=VerificationStatus.VERIFIED,
        supporting_source_ids=[source_id],
        contradicting_source_ids=[],
        reasoning="Verified claim passes strict check."
    )
    mock_verification_output.verified_claims = [mock_verified_claim]
    mock_verification_output.contradictions_found = 0

    # E. Gap Analysis Output
    mock_gap_output = GapAnalysisAgentOutput(
        session_id=session_id,
        gaps=[],
        has_critical_gaps=False,
        should_iterate=False,
        new_queries=[],
        iteration_reasoning="None",
        coverage_score=1.0
    )

    # F. Writer Output
    mock_writer_output = ReportDraft(
        id=uuid.uuid4(),
        session_id=session_id,
        title="Final Integration Test Scientific Report",
        executive_summary=(
            "Executive summary regarding clinical CRISPR therapies. This detailed summary "
            "reviews clinical outcomes, patient safety profiles, and molecular research findings "
            "associated with gene therapy interventions."
        ),
        sections=[
            ReportSection(
                title="Introduction",
                content=(
                    "CRISPR therapies are advancing rapidly in medical applications. Clinical trials show strong progress "
                    "and efficacy in modifying genetic markers for sickle cell patients."
                ),
            ),
            ReportSection(
                title="Literature Review",
                content=(
                    "Numerous papers highlight safety risks and double strand break dynamics during Cas9 targeting. "
                    "This section discusses the broad scientific consensus around current editing strategies."
                ),
            ),
            ReportSection(
                title="Clinical Efficacy",
                content=(
                    "Recent patient trial metadata demonstrates significant hemoglobin level improvement. Efficacy rates "
                    "remain stable across various trial phases, yielding strong confidence."
                ),
            ),
            ReportSection(
                title="Safety and Risks",
                content=(
                    "Off-target sequencing continues to be a concern, but recent high-fidelity nucleases show "
                    "significant reduction in error frequency, making therapies much safer."
                ),
            ),
            ReportSection(
                title="Future Outlook",
                content=(
                    "In-vivo targeting optimization represents the next frontier in molecular biology, with potential "
                    "for direct somatic treatments without ex-vivo cell transplant."
                ),
            ),
        ],
        key_findings=[
            "High clinical efficacy (over 90%) achieved in early trials.",
            "Off-target mutations reduced using high-fidelity nucleases.",
            "Long-term stability of hemoglobin levels observed in patients.",
        ],
        methodology_description="Retrieved via PubMed and arXiv databases with cross-referenced verified claims.",
        limitations="Limited clinical sample size and lack of long-term ten-year follow-up statistics.",
        conclusion="Highly promising results indicating that gene editing therapies are viable options for genetic disorders.",
        references=[
            ReportReference(source_id=source_id, citation_key="Test2026", title="Ref title", source_type=SourceType.ARXIV)
        ]
    )

    # G. Critic Output
    mock_critic_output = CritiqueResult(
        session_id=session_id,
        draft_id=mock_writer_output.id,
        scores=[
            CritiqueScore(dimension="Coverage", score=9.0, feedback="Excellent coverage")
        ],
        overall_score=9.0,
        strengths=["Writing clear"],
        weaknesses=[],
        missing_points=[],
        revision_required=False,
        revision_instructions=[],
        approved=True
    )

    # H. Visualization Output
    mock_viz_output = VisualizationBundle(
        session_id=session_id,
        tables=[],
        timeline=[],
        knowledge_nodes=[],
        knowledge_edges=[],
        confidence_distribution={},
        source_type_distribution={}
    )

    # I. Export Output
    mock_export_output = ExportBundle(
        session_id=session_id,
        report_id=mock_writer_output.id,
        markdown_path="/tmp/report.md",
        json_path="/tmp/report.json",
        html_path="/tmp/report.html",
        pdf_path="/tmp/report.pdf",
        file_sizes={"markdown": 100, "json": 150, "html": 200, "pdf": 300}
    )

    # Setup orchestrator with mocks
    orchestrator = ResearchOrchestrator(mock_db_session)
    orchestrator.session_repo = mock_session_repo
    
    # 3. Patch agents run methods
    with patch("app.agents.planner.PlannerAgent.run", AsyncMock(return_value=mock_plan)), \
         patch("app.agents.researcher.ResearchAgent.run", AsyncMock(return_value=mock_research_output)), \
         patch("app.agents.evidence.EvidenceAgent.run", AsyncMock(return_value=mock_evidence_output)), \
         patch("app.agents.verification.VerificationAgent.run", AsyncMock(return_value=mock_verification_output)), \
         patch("app.agents.gap_analysis.GapAnalysisAgent.run", AsyncMock(return_value=mock_gap_output)), \
         patch("app.agents.writer.WriterAgent.run", AsyncMock(return_value=mock_writer_output)), \
         patch("app.agents.critic.CriticAgent.run", AsyncMock(return_value=mock_critic_output)), \
         patch("app.agents.visualization.VisualizationAgent.run", AsyncMock(return_value=mock_viz_output)), \
         patch("app.agents.export.ExportAgent.run", AsyncMock(return_value=mock_export_output)), \
         patch("app.core.events.event_broker.publish", AsyncMock()) as mock_publish:
         
        # Run orchestrator task
        await orchestrator.run_research_session(session_id)

    # 4. Assertions
    # Verify session transitioned to COMPLETED
    assert session_record.state == SessionState.COMPLETED
    assert session_record.completed_at is not None

    # Verify database commits were executed
    assert mock_db_session.commit.call_count >= 5
    
    # Verify mock_publish published SSE events
    assert mock_publish.called
    
    # Verify log audit records were added to DB session
    assert mock_db_session.add.call_count >= 5
