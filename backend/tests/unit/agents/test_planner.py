"""
Unit tests for the PlannerAgent.
"""

from unittest.mock import AsyncMock, patch
import uuid
import pytest

from app.agents.planner import PlannerAgent
from app.schemas.agents.planner import ResearchGoal, ResearchPlan
from app.schemas.common import ResearchDepth, SearchQuery, SourceType


@pytest.mark.asyncio
async def test_planner_agent_execution() -> None:
    # 1. Prepare input
    session_uuid = uuid.uuid4()
    goal = ResearchGoal(
        session_id=session_uuid,
        topic="CRISPR gene therapy for sickle cell anemia",
        depth=ResearchDepth.NORMAL,
        focus_areas=["clinical safety", "efficacy"],
        source_preferences=[SourceType.ARXIV, SourceType.PUBMED],
    )

    # 2. Prepare mock output expected from LLMGateway
    mock_plan = ResearchPlan(
        session_id=session_uuid,
        topic=goal.topic,
        queries=[
            SearchQuery(query_text="CRISPR clinical trials sickle cell anemia", source_type=SourceType.PUBMED),
            SearchQuery(query_text="CRISPR gene editing therapy off-target effects", source_type=SourceType.ARXIV),
        ],
        estimated_complexity=0.7,
        suggested_depth=ResearchDepth.NORMAL,
        focus_areas=goal.focus_areas,
        reasoning="Topic requires medical trials (PubMed) and mechanical preprints (arXiv).",
    )

    # 3. Patch LLMGateway execution
    with patch("app.agents.base.llm_gateway.get_structured_completion", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_plan

        agent = PlannerAgent()
        result = await agent.run(goal)

        # 4. Assertions
        assert isinstance(result, ResearchPlan)
        assert result.session_id == session_uuid
        assert len(result.queries) == 2
        assert result.queries[0].source_type == SourceType.PUBMED
        assert result.estimated_complexity == 0.7
        mock_get.assert_called_once()
