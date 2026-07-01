"""
DSRA V2 — Export Agent
=======================
Compiles finalized research drafts into PDF, Markdown, HTML, and JSON packages.
"""

from datetime import datetime
import json
import os
from typing import ClassVar
import uuid

from markdown import markdown
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

from app.agents.base import BaseAgent
from app.config.settings import get_settings
from app.schemas.agents.all_agents import ExportAgentInput, ExportBundle
from app.schemas.common import ExportFormat


class ExportAgent(BaseAgent[ExportAgentInput, ExportBundle]):
    """
    Agent responsible for generating download packages on the local filesystem.
    """

    name: ClassVar[str] = "ExportAgent"

    @property
    def system_prompt(self) -> str:
        return "You are the DSRA Export Agent. Your goal is to package the final research artifacts."

    async def execute(self, input_data: ExportAgentInput) -> ExportBundle:
        """
        Builds the exported documents.
        """
        settings = get_settings()
        session_dir = os.path.join(settings.export_base_dir, str(input_data.session_id))
        os.makedirs(session_dir, exist_ok=True)

        bundle = ExportBundle(
            session_id=input_data.session_id,
            report_id=input_data.report.id,
        )

        # 1. Compile Markdown string representation
        md_content = self._generate_markdown(input_data)

        # 2. Export each format requested
        for fmt in input_data.export_formats:
            if fmt == ExportFormat.MARKDOWN:
                md_path = os.path.join(session_dir, "report.md")
                with open(md_path, "w", encoding="utf-8") as f:
                    f.write(md_content)
                bundle.markdown_path = md_path
                bundle.file_sizes["markdown"] = os.path.getsize(md_path)

            elif fmt == ExportFormat.JSON:
                json_path = os.path.join(session_dir, "report.json")
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(input_data.report.model_dump(mode="json"), f, indent=2)
                bundle.json_path = json_path
                bundle.file_sizes["json"] = os.path.getsize(json_path)

            elif fmt == ExportFormat.HTML:
                html_path = os.path.join(session_dir, "report.html")
                html_body = markdown(md_content)
                html_full = self._wrap_html(input_data.report.title, html_body)
                with open(html_path, "w", encoding="utf-8") as f:
                    f.write(html_full)
                bundle.html_path = html_path
                bundle.file_sizes["html"] = os.path.getsize(html_path)

            elif fmt == ExportFormat.PDF:
                pdf_path = os.path.join(session_dir, "report.pdf")
                self._generate_pdf(pdf_path, input_data)
                bundle.pdf_path = pdf_path
                bundle.file_sizes["pdf"] = os.path.getsize(pdf_path)

        bundle.export_completed_at = datetime.utcnow()
        return bundle

    def _generate_markdown(self, input_data: ExportAgentInput) -> str:
        """Helper to serialize report draft to clean markdown."""
        lines = [
            f"# {input_data.report.title}",
            "",
            "## Executive Summary",
            "",
            input_data.report.executive_summary,
            "",
        ]

        # Add findings
        if input_data.report.key_findings:
            lines.append("## Key Findings")
            for finding in input_data.report.key_findings:
                lines.append(f"- {finding}")
            lines.append("")

        # Add sections
        for sec in input_data.report.sections:
            lines.append(f"## {sec.title}")
            lines.append("")
            lines.append(sec.content)
            lines.append("")

        # Add methodology
        lines.append("## Methodology")
        lines.append("")
        lines.append(input_data.report.methodology_description)
        lines.append("")

        # Add limitations
        lines.append("## Limitations")
        lines.append("")
        lines.append(input_data.report.limitations)
        lines.append("")

        # Add conclusion
        lines.append("## Conclusion")
        lines.append("")
        lines.append(input_data.report.conclusion)
        lines.append("")

        # Add references
        if input_data.report.references:
            lines.append("## References")
            for ref in input_data.report.references:
                venue_str = f", *{ref.source_type}*" if ref.source_type else ""
                year_str = f" ({ref.year})" if ref.year else ""
                lines.append(f"- **{ref.citation_key}**: {ref.title}{venue_str}{year_str}")
            lines.append("")

        return "\n".join(lines)

    def _wrap_html(self, title: str, body: str) -> str:
        """Wraps parsed HTML inside a standard CSS layout."""
        return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>
    body {{
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
        color: #1a202c;
        max-width: 800px;
        margin: 40px auto;
        padding: 0 20px;
        line-height: 1.6;
    }}
    h1 {{ border-bottom: 2px solid #e2e8f0; padding-bottom: 10px; color: #2d3748; }}
    h2 {{ margin-top: 30px; border-bottom: 1px solid #edf2f7; padding-bottom: 5px; color: #4a5568; }}
    ul {{ padding-left: 20px; }}
    li {{ margin-bottom: 8px; }}
</style>
</head>
<body>
{body}
</body>
</html>"""

    def _generate_pdf(self, path: str, input_data: ExportAgentInput) -> None:
        """Builds ReportLab document."""
        doc = SimpleDocTemplate(
            path,
            pagesize=letter,
            rightMargin=54,
            leftMargin=54,
            topMargin=54,
            bottomMargin=54
        )

        styles = getSampleStyleSheet()
        
        # Define clean typography styles
        title_style = ParagraphStyle(
            name="PDFTitle",
            parent=styles["Heading1"],
            fontSize=24,
            leading=28,
            textColor=colors.HexColor("#2d3748"),
            spaceAfter=20
        )
        
        h2_style = ParagraphStyle(
            name="PDFH2",
            parent=styles["Heading2"],
            fontSize=16,
            leading=20,
            textColor=colors.HexColor("#4a5568"),
            spaceBefore=15,
            spaceAfter=10
        )

        body_style = ParagraphStyle(
            name="PDFBody",
            parent=styles["Normal"],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#1a202c"),
            spaceAfter=8
        )

        story = []

        # Cover / Header
        story.append(Paragraph(input_data.report.title, title_style))
        story.append(Spacer(1, 15))

        # Executive Summary
        story.append(Paragraph("Executive Summary", h2_style))
        story.append(Paragraph(input_data.report.executive_summary, body_style))
        story.append(Spacer(1, 10))

        # Key Findings
        if input_data.report.key_findings:
            story.append(Paragraph("Key Findings", h2_style))
            for finding in input_data.report.key_findings:
                story.append(Paragraph(f"• {finding}", body_style))
            story.append(Spacer(1, 10))

        # Sections
        for sec in input_data.report.sections:
            story.append(Paragraph(sec.title, h2_style))
            story.append(Paragraph(sec.content, body_style))
            story.append(Spacer(1, 10))

        # Methodology
        story.append(Paragraph("Methodology", h2_style))
        story.append(Paragraph(input_data.report.methodology_description, body_style))
        story.append(Spacer(1, 10))

        # Limitations
        story.append(Paragraph("Limitations", h2_style))
        story.append(Paragraph(input_data.report.limitations, body_style))
        story.append(Spacer(1, 10))

        # Conclusion
        story.append(Paragraph("Conclusion", h2_style))
        story.append(Paragraph(input_data.report.conclusion, body_style))
        story.append(Spacer(1, 10))

        # References
        if input_data.report.references:
            story.append(Paragraph("References", h2_style))
            for ref in input_data.report.references:
                venue_str = f", <i>{ref.source_type}</i>" if ref.source_type else ""
                year_str = f" ({ref.year})" if ref.year else ""
                ref_text = f"<b>{ref.citation_key}</b>: {ref.title}{venue_str}{year_str}"
                story.append(Paragraph(ref_text, body_style))

        doc.build(story)
