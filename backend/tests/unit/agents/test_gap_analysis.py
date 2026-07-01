"""
Unit tests for the GapAnalysisAgent.
"""

from unittest.mock import AsyncMock, patch
import uuid
import pytest

from app.agents.gap_analysis import GapAnalysisAgent
from app.schemas.agents.all_agents import GapAnalysisAgentInput, GapAnalysisAgentOutput, ResearchGap
from app.schemas.common import GapSeverity, SearchQuery, SourceType, VerificationStatus, VerifiedClaim


@pytest.mark.asyncio
async def test_gap_analysis_agent_execution() -> None:
    session_uuid = uuid.uuid4()
    
    # 1. Prepare input
    claims = [
        VerifiedClaim(
            session_id=session_uuid,
            text="CRISPR therapies demonstrate 90% clinical efficacy in sickle cell patients.",
            confidence=0.92,
            status=VerificationStatus.VERIFIED,
            supporting_source_ids=[uuid.uuid4()],
            contradicting_source_ids=[],
            reasoning="Supported by high-quality sources.",
        )
    ]
    agent_input = GapAnalysisAgentInput(
        session_id=session_uuid,
        research_plan_topic=" sickle cell gene editing efficacy and clinical safety",
        research_plan_focus_areas=["efficacy", "safety"],
        verified_claims=claims,
        sources_count=1,
        current_iteration=0,
        max_iterations=3,
    )

    # 2. Prepare mock output from LLMGateway
    mock_output = GapAnalysisAgentOutput(
        session_id=session_uuid,
        gaps=[
            ResearchGap(
                description="Lacking clinical safety trials data and off-target risks analysis.",
                severity=GapSeverity.CRITICAL,
                suggested_queries=[
                    SearchQuery(query_text="CRISPR gene editing safety trials", source_type=SourceType.PUBMED)
                ],
            )
        ],
        has_critical_gaps=True,
        should_iterate=True,
        new_queries=[
            SearchQuery(query_text="CRISPR gene editing safety trials", source_type=SourceType.PUBMED)
        ],
        iteration_reasoning="Critical safety gap detected; need to query PubMed for safety profiles.",
        coverage_score=0.5,
    )

    # 3. Patch LLMGateway execution
    with patch("app.agents.base.llm_gateway.get_structured_completion", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_output

        agent = GapAnalysisAgent()
        result = await agent.run(agent_input)

        # 4. Assertions
        assert isinstance(result, GapAnalysisAgentOutput)
        assert result.should_iterate is True
        assert len(result.new_queries) == 1
        assert result.new_queries[0].source_type == SourceType.PUBMED
        assert result.coverage_score == 0.5
        mock_get.assert_called_once()
