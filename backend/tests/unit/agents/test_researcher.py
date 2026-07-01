"""
Unit tests for the ResearchAgent.
"""

from unittest.mock import AsyncMock, patch
import uuid
import pytest

from app.agents.researcher import ResearchAgent
from app.schemas.agents.all_agents import ResearchAgentInput, ResearchAgentOutput
from app.schemas.common import SearchQuery, SourceResult, SourceType


@pytest.mark.asyncio
async def test_research_agent_arxiv_routing() -> None:
    session_uuid = uuid.uuid4()
    query_uuid = uuid.uuid4()
    query_item = SearchQuery(
        id=query_uuid,
        query_text="Quantum machine learning",
        source_type=SourceType.ARXIV,
    )
    agent_input = ResearchAgentInput(
        session_id=session_uuid,
        query=query_item,
        max_results=5,
    )

    mock_sources = [
        SourceResult(
            session_id=session_uuid,
            query_id=query_uuid,
            title="QML foundations",
            snippet="Introduction to quantum learning.",
            source_type=SourceType.ARXIV,
        )
    ]

    # Patch the ArxivAdapter.search method
    with patch("app.agents.researcher.ArxivAdapter.search", new_callable=AsyncMock) as mock_search:
        mock_search.return_value = mock_sources

        agent = ResearchAgent()
        result = await agent.run(agent_input)

        assert isinstance(result, ResearchAgentOutput)
        assert len(result.results) == 1
        assert result.results[0].title == "QML foundations"
        assert result.results[0].query_id == query_uuid
        mock_search.assert_called_once_with("Quantum machine learning", max_results=5)
