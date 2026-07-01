"""
Unit tests for the ExportAgent.
"""

import os
import shutil
import tempfile
import uuid
import pytest

from app.agents.export import ExportAgent
from app.schemas.agents.all_agents import ExportAgentInput, VisualizationBundle
from app.schemas.common import ReportDraft, ReportSection, ReportReference, SourceType


@pytest.mark.asyncio
async def test_export_agent_execution() -> None:
    session_uuid = uuid.uuid4()
    source_uuid = uuid.uuid4()
    
    # 1. Prepare fully valid inputs
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

    visualization = VisualizationBundle(
        session_id=session_uuid,
        tables=[],
        timeline=[],
        knowledge_nodes=[],
        knowledge_edges=[],
        confidence_distribution={},
        source_type_distribution={},
    )

    from app.schemas.common import ExportFormat
    agent_input = ExportAgentInput(
        session_id=session_uuid,
        report=report,
        visualization=visualization,
        sources=[],
        export_formats=[ExportFormat.PDF, ExportFormat.MARKDOWN, ExportFormat.HTML, ExportFormat.JSON]
    )

    # 2. Use a temporary directory for tests to avoid writing to local data dir
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Patch the settings export directory path
        from unittest.mock import patch, MagicMock
        mock_settings = MagicMock()
        mock_settings.export_base_dir = tmp_dir
        
        with patch("app.agents.export.get_settings", return_value=mock_settings):
            agent = ExportAgent()
            result = await agent.run(agent_input)

            # 3. Assertions
            assert result.session_id == session_uuid
            assert result.report_id == report.id
            assert result.markdown_path is not None
            assert result.json_path is not None
            assert result.html_path is not None
            assert result.pdf_path is not None

            # Verify files were actually created
            assert os.path.exists(result.markdown_path)
            assert os.path.exists(result.json_path)
            assert os.path.exists(result.html_path)
            assert os.path.exists(result.pdf_path)

            # Verify sizes are tracked
            assert result.file_sizes["markdown"] > 0
            assert result.file_sizes["json"] > 0
            assert result.file_sizes["html"] > 0
            assert result.file_sizes["pdf"] > 0