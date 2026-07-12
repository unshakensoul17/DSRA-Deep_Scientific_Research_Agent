"""
Unit tests for the PlannerAgent.
"""

from unittest.mock import AsyncMock, patch
import uuid
import pytest

from app.agents.planner import PlannerAgent
from app.schemas.agents.planner import PlannerLLMPlan, PlannerSearchQuery, ResearchGoal, ResearchPlan
from app.schemas.common import ResearchDepth, SourceType


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
    mock_plan = PlannerLLMPlan(
        queries=[
            PlannerSearchQuery(query_text="CRISPR clinical trials sickle cell anemia", source_type=SourceType.PUBMED),
            PlannerSearchQuery(query_text="CRISPR gene editing therapy off-target effects", source_type=SourceType.ARXIV),
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


@pytest.mark.asyncio
async def test_planner_agent_normalizes_llm_query_aliases() -> None:
    session_uuid = uuid.uuid4()
    goal = ResearchGoal(
        session_id=session_uuid,
        topic="CRISPR gene therapy for sickle cell anemia",
        depth=ResearchDepth.NORMAL,
        focus_areas=["clinical safety"],
        source_preferences=[SourceType.PUBMED],
    )
    mock_llm_plan = PlannerLLMPlan.model_validate(
        {
            "queries": [
                {
                    "query": "CRISPR sickle cell clinical trial HDR",
                    "engine": "pubmed",
                    "priority": 0.95,
                }
            ],
            "estimated_complexity": 0.8,
            "suggested_depth": 2,
            "reasoning": "This topic needs targeted clinical trial searches.",
        }
    )

    with patch("app.agents.base.llm_gateway.get_structured_completion", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_llm_plan

        agent = PlannerAgent()
        result = await agent.run(goal)

        assert result.session_id == session_uuid
        assert result.topic == goal.topic
        assert result.queries[0].query_text == "CRISPR sickle cell clinical trial HDR"
        assert result.queries[0].source_type == SourceType.PUBMED
    assert result.focus_areas == ["clinical safety"]
    assert mock_get.call_args.kwargs["response_schema"] is PlannerLLMPlan


@pytest.mark.asyncio
async def test_planner_llm_plan_ignores_hallucinated_query_ids() -> None:
    plan = PlannerLLMPlan.model_validate(
        {
            "queries": [
                {
                    "id": "1f6e5g34-9f2c-8e5b-f6a7-b8c9d0e1f2a3",
                    "query": "CRISPR sickle cell clinical trial HDR",
                    "engine": "pubmed",
                    "priority": 0.95,
                }
            ],
            "estimated_complexity": 0.8,
            "suggested_depth": 2,
            "reasoning": "This topic needs targeted clinical trial searches.",
        }
    )

    assert plan.queries[0].query_text == "CRISPR sickle cell clinical trial HDR"
    assert plan.queries[0].source_type == SourceType.PUBMED
