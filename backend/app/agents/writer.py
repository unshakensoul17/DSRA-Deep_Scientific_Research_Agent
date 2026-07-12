"""
DSRA V2 — Writer Agent
=======================
Compiles academic research reports based on verified claims and references.
"""

from typing import ClassVar
import uuid

from app.agents.base import BaseAgent
from app.llm.prompts.writer import writer_prompt
from app.schemas.agents.all_agents import WriterAgentInput, WriterLLMOutput
from app.schemas.common import ReportDraft, ReportReference, ReportSection, ReportStatus, SourceType


class WriterAgent(BaseAgent[WriterAgentInput, ReportDraft]):
    """
    Agent responsible for writing report drafts.
    """

    name: ClassVar[str] = "WriterAgent"

    @property
    def system_prompt(self) -> str:
        return writer_prompt.system_template

    async def execute(self, input_data: WriterAgentInput) -> ReportDraft:
        """
        Generates a new report draft.
        """
        # Serialize verified claims to text
        claims_context = []
        for idx, vc in enumerate(input_data.verified_claims):
            claims_context.append(
                f"Claim [{idx}] UUID: {vc.id}\n"
                f"Text: '{vc.text}'\n"
                f"Status: {vc.status}\n"
                f"Confidence: {vc.confidence}\n"
                f"Reasoning: {vc.reasoning}\n"
                "----------------------------------------"
            )

        # Serialize sources reference pool
        sources_context = []
        for idx, src in enumerate(input_data.sources):
            sources_context.append(
                f"Source [{idx}] UUID: {src.id}\n"
                f"Title: {src.title}\n"
                f"Authors: {', '.join(src.authors) if src.authors else 'Unknown'}\n"
                f"Year: {src.year or 'Unknown'}\n"
                f"Venue: {src.source_type}\n"
                "----------------------------------------"
            )

        user_content = (
            f"Research Plan Topic: {input_data.research_plan_topic}\n"
            f"Focus Areas: {', '.join(input_data.research_plan_focus_areas) if input_data.research_plan_focus_areas else 'None'}\n\n"
            "### Verified Claims List:\n"
            f"{chr(10).join(claims_context) if claims_context else 'No verified claims.'}\n\n"
            "### Source Reference Pool:\n"
            f"{chr(10).join(sources_context) if sources_context else 'No reference sources.'}\n\n"
        )

        if input_data.previous_draft:
            user_content += (
                f"\n### Previous Draft Title: {input_data.previous_draft.title}\n"
                f"Executive Summary: {input_data.previous_draft.executive_summary}\n"
                "Please rewrite and revise according to the criticism details below.\n"
            )
        if input_data.critique:
            user_content += (
                f"\n### Critique Feedback (Overall Score: {input_data.critique.overall_score}/10.0):\n"
                f"Revision Instructions:\n"
                + "\n".join(f"- {instruction}" for instruction in input_data.critique.revision_instructions)
                + "\n"
            )

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_content},
        ]

        # Call gateway with LLM-facing schema (no runtime UUIDs)
        llm_output = await self.llm.get_structured_completion(
            messages=messages,
            response_schema=WriterLLMOutput,
            temperature=0.3,
        )

        # Build a lookup from string source_id -> real source UUIDs
        source_id_map = {str(src.id): src.id for src in input_data.sources}

        # Convert LLM sections to runtime ReportSection objects
        runtime_sections = [
            ReportSection(title=sec.title, content=sec.content)
            for sec in llm_output.sections
        ]

        # Convert LLM references to runtime ReportReference objects, matching real source IDs
        runtime_references = []
        for ref in llm_output.references:
            real_source_id = source_id_map.get(ref.source_id)
            if real_source_id is None:
                # Hallucinated ID — try to match by title, then skip if not found
                matched = next(
                    (src for src in input_data.sources if src.title == ref.title), None
                )
                real_source_id = matched.id if matched else None
            if real_source_id is None:
                continue  # Skip orphaned references to avoid FK violations

            try:
                source_type_val = SourceType(ref.source_type)
            except ValueError:
                source_type_val = SourceType.ARXIV

            runtime_references.append(
                ReportReference(
                    source_id=real_source_id,
                    citation_key=ref.citation_key,
                    title=ref.title,
                    url=ref.url,
                    authors=ref.authors,
                    year=ref.year,
                    source_type=source_type_val,
                    doi=ref.doi,
                )
            )

        # Assemble runtime ReportDraft with correct IDs
        draft = ReportDraft(
            id=uuid.uuid4(),
            session_id=input_data.session_id,
            title=llm_output.title,
            executive_summary=llm_output.executive_summary,
            sections=runtime_sections,
            key_findings=llm_output.key_findings,
            references=runtime_references,
            methodology_description=llm_output.methodology_description,
            limitations=llm_output.limitations,
            conclusion=llm_output.conclusion,
            revision=llm_output.revision,
            status=ReportStatus.DRAFT,
        )
        return draft
