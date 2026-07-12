"""
Unit tests for the EvidenceAgent.
"""

from unittest.mock import AsyncMock, patch
import uuid
import pytest

from app.agents.evidence import EvidenceAgent
from app.schemas.agents.all_agents import EvidenceAgentInput, EvidenceAgentOutput, EvidenceExtractionPiece, EvidenceLLMOutput
from app.schemas.common import EvidencePiece, SourceResult, SourceType


@pytest.mark.asyncio
async def test_evidence_agent_execution() -> None:
    session_uuid = uuid.uuid4()
    source_uuid = uuid.uuid4()
    
    # 1. Prepare input
    sources = [
        SourceResult(
            id=source_uuid,
            session_id=session_uuid,
            query_id=uuid.uuid4(),
            title="CRISPR gene editing therapy",
            snippet="CRISPR therapies are showing 90% clinical efficacy in sickle cell patients.",
            source_type=SourceType.PUBMED,
            authors=["Frangoul H"],
            year=2021,
        )
    ]
    agent_input = EvidenceAgentInput(
        session_id=session_uuid,
        sources=sources,
        research_topic=" sickle cell gene editing efficacy",
    )

    # 2. Prepare mock output from LLMGateway
    mock_output = EvidenceLLMOutput(
        session_id=session_uuid,
        evidence_pieces=[
            EvidenceExtractionPiece(
                claim_text="CRISPR therapies demonstrate 90% clinical efficacy in sickle cell patients.",
                source_id=source_uuid,
                relevance_score=0.95,
                excerpt="CRISPR therapies are showing 90% clinical efficacy in sickle cell patients.",
            )
        ],
        source_quality_scores={str(source_uuid): 0.9},
        deduplication_removed=0,
        total_sources_processed=1,
    )

    # 3. Patch LLMGateway execution
    with patch("app.agents.base.llm_gateway.get_structured_completion", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_output

        agent = EvidenceAgent()
        result = await agent.run(agent_input)

        # 4. Assertions
        assert isinstance(result, EvidenceAgentOutput)
        assert len(result.evidence_pieces) == 1
        assert result.evidence_pieces[0].source_id == source_uuid
        assert result.source_quality_scores[str(source_uuid)] == 0.9
        mock_get.assert_called_once()


@pytest.mark.asyncio
async def test_evidence_agent_ignores_hallucinated_piece_ids() -> None:
    session_uuid = uuid.uuid4()
    source_uuid = uuid.uuid4()
    sources = [
        SourceResult(
            id=source_uuid,
            session_id=session_uuid,
            query_id=uuid.uuid4(),
            title="CRISPR gene editing therapy",
            snippet="CRISPR therapies are showing 90% clinical efficacy in sickle cell patients.",
            source_type=SourceType.PUBMED,
        )
    ]
    agent_input = EvidenceAgentInput(
        session_id=session_uuid,
        sources=sources,
        research_topic="sickle cell gene editing efficacy",
    )

    mock_output = EvidenceLLMOutput(
        session_id=session_uuid,
        evidence_pieces=[
            EvidenceExtractionPiece.model_validate(
                {
                    "id": "d4c1bd2b-813d-5f23-ac2b-9g7c2b3d4e5f",
                    "claim_text": "CRISPR therapies demonstrate 90% clinical efficacy in sickle cell patients.",
                    "source_id": str(source_uuid),
                    "relevance_score": 0.95,
                    "excerpt": "CRISPR therapies are showing 90% clinical efficacy in sickle cell patients.",
                }
            )
        ],
        source_quality_scores={str(source_uuid): 0.9},
        deduplication_removed=0,
        total_sources_processed=1,
    )

    with patch("app.agents.base.llm_gateway.get_structured_completion", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_output

        agent = EvidenceAgent()
        result = await agent.run(agent_input)

        assert isinstance(result, EvidenceAgentOutput)
        assert len(result.evidence_pieces) == 1
        assert result.evidence_pieces[0].source_id == source_uuid
        assert result.evidence_pieces[0].session_id == session_uuid
        assert result.source_quality_scores[str(source_uuid)] == 0.9
