"""
Unit tests for the VerificationAgent.
"""

from unittest.mock import AsyncMock, patch
import uuid
import pytest

from app.agents.verification import VerificationAgent
from app.schemas.agents.all_agents import VerificationAgentInput, VerificationAgentOutput
from app.schemas.common import EvidencePiece, SourceResult, SourceType, VerificationStatus, VerifiedClaim


@pytest.mark.asyncio
async def test_verification_agent_execution() -> None:
    session_uuid = uuid.uuid4()
    source_uuid = uuid.uuid4()
    claim_uuid = uuid.uuid4()
    
    # 1. Prepare input
    evidence = [
        EvidencePiece(
            id=claim_uuid,
            session_id=session_uuid,
            claim_text="CRISPR therapies demonstrate 90% clinical efficacy in sickle cell patients.",
            source_id=source_uuid,
            relevance_score=0.95,
            excerpt="CRISPR therapies are showing 90% clinical efficacy in sickle cell patients.",
        )
    ]
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
            quality_score=0.9,
        )
    ]
    agent_input = VerificationAgentInput(
        session_id=session_uuid,
        evidence_pieces=evidence,
        sources=sources,
        research_topic="sickle cell gene editing efficacy",
    )

    # 2. Prepare mock output from LLMGateway
    mock_output = VerificationAgentOutput(
        session_id=session_uuid,
        verified_claims=[
            VerifiedClaim(
                id=claim_uuid,
                session_id=session_uuid,
                text="CRISPR therapies demonstrate 90% clinical efficacy in sickle cell patients.",
                confidence=0.92,
                status=VerificationStatus.VERIFIED,
                supporting_source_ids=[source_uuid],
                contradicting_source_ids=[],
                reasoning="Supported by a high quality clinical source with no contradictions.",
            )
        ],
        contradictions_found=0,
        high_confidence_claims=1,
        verification_coverage=1.0,
    )

    # 3. Patch LLMGateway execution
    with patch("app.agents.base.llm_gateway.get_structured_completion", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_output

        agent = VerificationAgent()
        result = await agent.run(agent_input)

        # 4. Assertions
        assert isinstance(result, VerificationAgentOutput)
        assert len(result.verified_claims) == 1
        assert result.verified_claims[0].status == VerificationStatus.VERIFIED
        assert result.verified_claims[0].confidence == 0.92
        mock_get.assert_called_once()
