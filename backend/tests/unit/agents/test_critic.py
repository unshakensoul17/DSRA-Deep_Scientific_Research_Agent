"""
Unit tests for the CriticAgent.
"""

from unittest.mock import AsyncMock, patch
import uuid
import pytest

from app.agents.critic import CriticAgent
from app.schemas.agents.all_agents import CriticAgentInput, CritiqueResult, CritiqueScore
from app.schemas.common import ReportDraft, ReportSection, ReportReference, SourceType


@pytest.mark.asyncio
async def test_critic_agent_execution() -> None:
    session_uuid = uuid.uuid4()
    draft_uuid = uuid.uuid4()
    source_uuid = uuid.uuid4()
    
    # 1. Prepare input
    draft = ReportDraft(
        id=draft_uuid,
        session_id=session_uuid,
        title="CRISPR Editing Efficacy Draft",
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
        references=[
            ReportReference(
                source_id=source_uuid,
                citation_key="Frangoul2021",
                title="CRISPR gene editing therapy",
                source_type=SourceType.PUBMED,
            )
        ],
        methodology_description="Retrieved via PubMed and arXiv databases with cross-referenced verified claims.",
        limitations="Limited clinical sample size and lack of long-term ten-year follow-up statistics.",
        conclusion="Highly promising results indicating that gene editing therapies are viable options for genetic disorders.",
    )
    agent_input = CriticAgentInput(
        session_id=session_uuid,
        draft=draft,
        verified_claims=[],
        sources=[],
        revision_number=0,
        max_revisions=3,
    )

    # 2. Prepare mock critique result
    mock_output = CritiqueResult(
        session_id=session_uuid,
        draft_id=draft_uuid,
        scores=[
            CritiqueScore(dimension="Coverage", score=6.5, feedback="Missing detailed methodology sections.")
        ],
        overall_score=6.5,
        strengths=["Clear writing style."],
        weaknesses=["Missing methodology sections."],
        missing_points=["More trials metadata needed."],
        revision_required=True,
        revision_instructions=["Add section discussing methods."],
        approved=False,
    )

    # 3. Patch LLMGateway execution
    with patch("app.agents.base.llm_gateway.get_structured_completion", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_output

        agent = CriticAgent()
        result = await agent.run(agent_input)

        # 4. Assertions
        assert isinstance(result, CritiqueResult)
        assert result.overall_score == 6.5
        assert result.revision_required is True
        assert len(result.revision_instructions) == 1
        mock_get.assert_called_once()
