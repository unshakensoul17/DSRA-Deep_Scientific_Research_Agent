"""
DSRA V2 — Load Testing Script
===============================
Simulates concurrent scientific research sessions execution to verify
non-blocking asynchronous orchestrator performance and database connection pooling.
"""

import asyncio
import time
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.orchestrator import ResearchOrchestrator
from app.schemas.common import SessionState, SourceType, ResearchDepth, SourceResult, EvidencePiece, VerifiedClaim, VerificationStatus, ReportDraft, ReportSection, ReportReference
from app.schemas.agents.all_agents import GapAnalysisAgentOutput, CritiqueResult, CritiqueScore, VisualizationBundle, ExportBundle
from app.db.models.research_session import ResearchSession
from app.db.models.user import User


class MockAsyncSession:
    """Mock session simulating DB interaction with a slight delay to mimic DB operations."""
    def __init__(self):
        self.commit_count = 0
        self.added_entities = []

    async def commit(self):
        self.commit_count += 1
        await asyncio.sleep(0.01)  # Simulate DB IO lag

    async def rollback(self):
        await asyncio.sleep(0.005)

    async def refresh(self, obj):
        await asyncio.sleep(0.005)

    def add(self, obj):
        self.added_entities.append(obj)

    def execute(self, *args, **kwargs):
        pass


async def run_single_mock_session(session_index: int):
    """Executes a full research session flow using mock agents and a dedicated DB session."""
    session_id = uuid.uuid4()
    source_id = uuid.uuid4()
    claim_id = uuid.uuid4()
    
    # Create fake DB session and session record
    db_session = MockAsyncSession()
    session_record = ResearchSession(
        id=session_id,
        user_id=uuid.uuid4(),
        topic=f"Load test topic index {session_index}",
        state=SessionState.CREATED,
        depth=ResearchDepth.NORMAL,
        max_iterations=2,
        iteration_count=0,
        sources=[],
        claims=[],
        reports=[],
        execution_logs=[],
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    # Mock get_by_id to return our session record
    mock_session_repo = MagicMock()
    mock_session_repo.get_by_id = AsyncMock(return_value=session_record)

    # Setup Agent Mock Outputs
    from app.schemas.common import SearchQuery
    mock_plan = MagicMock()
    mock_plan.queries = [
        SearchQuery(id=uuid.uuid4(), query_text=f"Query {session_index}-1", source_type=SourceType.ARXIV, filters={}),
        SearchQuery(id=uuid.uuid4(), query_text=f"Query {session_index}-2", source_type=SourceType.WIKIPEDIA, filters={})
    ]
    mock_plan.topic = session_record.topic
    mock_plan.focus_areas = []
    mock_plan.estimated_complexity = "moderate"

    mock_research_output = MagicMock()
    mock_source = SourceResult(
        id=source_id,
        session_id=session_id,
        query_id=uuid.uuid4(),
        title=f"Source Title {session_index}",
        url="http://example.com/source",
        snippet="Snippet for load test.",
        full_content="Full content.",
        source_type=SourceType.ARXIV,
        authors=["Author"],
        year=2026,
        doi=None,
        citation_count=5,
        quality_score=0.8,
    )
    mock_research_output.results = [mock_source]

    mock_evidence_output = MagicMock()
    mock_evidence_piece = EvidencePiece(
        id=claim_id,
        session_id=session_id,
        claim_text=f"Claim text for load test {session_index}.",
        source_id=source_id,
        relevance_score=0.9,
        excerpt="Excerpt"
    )
    mock_evidence_output.evidence_pieces = [mock_evidence_piece]
    mock_evidence_output.source_quality_scores = {str(source_id): 0.8}

    mock_verification_output = MagicMock()
    mock_verified_claim = VerifiedClaim(
        id=claim_id,
        session_id=session_id,
        text=f"Claim text for load test {session_index}.",
        confidence=0.9,
        status=VerificationStatus.VERIFIED,
        supporting_source_ids=[source_id],
        contradicting_source_ids=[],
        reasoning="Verified claim."
    )
    mock_verification_output.verified_claims = [mock_verified_claim]
    mock_verification_output.contradictions_found = 0

    mock_gap_output = GapAnalysisAgentOutput(
        session_id=session_id,
        gaps=[],
        has_critical_gaps=False,
        should_iterate=False,
        new_queries=[],
        iteration_reasoning="None",
        coverage_score=1.0
    )

    mock_writer_output = ReportDraft(
        id=uuid.uuid4(),
        session_id=session_id,
        title=f"Final Report {session_index}",
        executive_summary=(
            "Executive summary regarding clinical CRISPR therapies. This detailed summary "
            "reviews clinical outcomes, patient safety profiles, and molecular research findings "
            "associated with gene therapy interventions. It provides a comprehensive synthesis of "
            "all gathered data across phase trials."
        ),
        sections=[
            ReportSection(title="Section 1", content="Content text that is also definitely longer than 100 characters to prevent Pydantic string validation error during the run."),
            ReportSection(title="Section 2", content="Content text that is also definitely longer than 100 characters to prevent Pydantic string validation error during the run."),
            ReportSection(title="Section 3", content="Content text that is also definitely longer than 100 characters to prevent Pydantic string validation error during the run."),
            ReportSection(title="Section 4", content="Content text that is also definitely longer than 100 characters to prevent Pydantic string validation error during the run."),
            ReportSection(title="Section 5", content="Content text that is also definitely longer than 100 characters to prevent Pydantic string validation error during the run.")
        ],
        key_findings=["Finding 1", "Finding 2", "Finding 3"],
        methodology_description="Retrieved via PubMed and arXiv databases with cross-referenced verified claims and academic databases.",
        limitations="Limited clinical sample size and lack of long-term ten-year follow-up statistics and clinical trial results.",
        conclusion="Highly promising results indicating that gene editing therapies are viable options for genetic disorders and represent a major breakthrough in somatic medicine.",
        references=[
            ReportReference(source_id=source_id, citation_key="Key", title="Title", source_type=SourceType.ARXIV)
        ]
    )

    mock_critic_output = CritiqueResult(
        session_id=session_id,
        draft_id=mock_writer_output.id,
        scores=[CritiqueScore(dimension="Coverage", score=9.0, feedback="Coverage is excellent.")],
        overall_score=9.0,
        strengths=["Writing clear"],
        weaknesses=[],
        missing_points=[],
        revision_required=False,
        revision_instructions=[],
        approved=True
    )

    mock_viz_output = VisualizationBundle(
        session_id=session_id,
        tables=[],
        timeline=[],
        knowledge_nodes=[],
        knowledge_edges=[],
        confidence_distribution={},
        source_type_distribution={}
    )

    mock_export_output = ExportBundle(
        session_id=session_id,
        report_id=mock_writer_output.id,
        markdown_path="/tmp/report.md",
        json_path="/tmp/report.json",
        html_path="/tmp/report.html",
        pdf_path="/tmp/report.pdf",
        file_sizes={"markdown": 100, "json": 150, "html": 200, "pdf": 300}
    )

    orchestrator = ResearchOrchestrator(db_session)
    orchestrator.session_repo = mock_session_repo

    with patch("app.agents.planner.PlannerAgent.run", AsyncMock(return_value=mock_plan)), \
         patch("app.agents.researcher.ResearchAgent.run", AsyncMock(return_value=mock_research_output)), \
         patch("app.agents.evidence.EvidenceAgent.run", AsyncMock(return_value=mock_evidence_output)), \
         patch("app.agents.verification.VerificationAgent.run", AsyncMock(return_value=mock_verification_output)), \
         patch("app.agents.gap_analysis.GapAnalysisAgent.run", AsyncMock(return_value=mock_gap_output)), \
         patch("app.agents.writer.WriterAgent.run", AsyncMock(return_value=mock_writer_output)), \
         patch("app.agents.critic.CriticAgent.run", AsyncMock(return_value=mock_critic_output)), \
         patch("app.agents.visualization.VisualizationAgent.run", AsyncMock(return_value=mock_viz_output)), \
         patch("app.agents.export.ExportAgent.run", AsyncMock(return_value=mock_export_output)), \
         patch("app.core.events.event_broker.publish", AsyncMock()):
         
        await orchestrator.run_research_session(session_id)
        
    return session_record.state


async def main():
    concurrency_limit = 20
    print(f"Starting load test with {concurrency_limit} concurrent research sessions...")
    
    start_time = time.perf_counter()
    
    tasks = [run_single_mock_session(i) for i in range(concurrency_limit)]
    results = await asyncio.gather(*tasks)
    
    duration = time.perf_counter() - start_time
    
    success_count = sum(1 for r in results if r == SessionState.COMPLETED)
    print(f"Load test completed in {duration:.2f} seconds.")
    print(f"Successful sessions: {success_count}/{concurrency_limit}")
    
    assert success_count == concurrency_limit, "Some sessions did not complete successfully!"
    print("Load test passed!")

if __name__ == "__main__":
    asyncio.run(main())
