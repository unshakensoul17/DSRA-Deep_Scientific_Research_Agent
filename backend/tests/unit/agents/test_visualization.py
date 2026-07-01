"""
Unit tests for the VisualizationAgent.
"""

from unittest.mock import AsyncMock, patch
import uuid
import pytest

from app.agents.visualization import VisualizationAgent
from app.schemas.agents.all_agents import (
    VisualizationAgentInput,
    VisualizationBundle,
    TableVisualization,
    TimelineEvent,
    KnowledgeNode,
    KnowledgeEdge,
)
from app.schemas.common import ReportDraft, ReportSection, ReportReference, SourceType


@pytest.mark.asyncio
async def test_visualization_agent_execution() -> None:
    session_uuid = uuid.uuid4()
    source_uuid = uuid.uuid4()
    
    # 1. Prepare input
    report = ReportDraft(
        id=uuid.uuid4(),
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
    agent_input = VisualizationAgentInput(
        session_id=session_uuid,
        report=report,
        verified_claims=[],
        sources=[],
    )

    # 2. Prepare mock bundle output
    mock_output = VisualizationBundle(
        session_id=session_uuid,
        tables=[
            TableVisualization(
                title="Clinical Trial Comparison",
                headers=["Trial ID", "Efficacy Rate"],
                rows=[["Trial A", "90%"], ["Trial B", "85%"]],
            )
        ],
        timeline=[
            TimelineEvent(
                year=2021,
                event="First successful CRISPR sickle cell treatment trial report.",
                significance="HIGH",
            )
        ],
        knowledge_nodes=[
            KnowledgeNode(id="crispr", label="CRISPR CAS-9", node_type="concept"),
            KnowledgeNode(id="sickle", label="Sickle Cell Anemia", node_type="entity"),
        ],
        knowledge_edges=[
            KnowledgeEdge(source="crispr", target="sickle", relationship="treats")
        ],
        confidence_distribution={"HIGH": 1},
        source_type_distribution={"pubmed": 1},
    )

    # 3. Patch LLMGateway execution
    with patch("app.agents.base.llm_gateway.get_structured_completion", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_output

        agent = VisualizationAgent()
        result = await agent.run(agent_input)

        # 4. Assertions
        assert isinstance(result, VisualizationBundle)
        assert len(result.tables) == 1
        assert result.tables[0].title == "Clinical Trial Comparison"
        assert len(result.timeline) == 1
        assert result.timeline[0].year == 2021
        assert len(result.knowledge_nodes) == 2
        mock_get.assert_called_once()
