"""
DSRA V2 — Writer Agent
=======================
Compiles academic research reports based on verified claims and references.
"""

from typing import ClassVar
import uuid

from app.agents.base import BaseAgent
from app.llm.prompts.writer import writer_prompt
from app.schemas.agents.all_agents import WriterAgentInput
from app.schemas.common import ReportDraft, ReportStatus


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

        # Call gateway for validated Pydantic model response
        output = await self.llm.get_structured_completion(
            messages=messages,
            response_schema=ReportDraft,
            temperature=0.3,
        )

        # Enforce ID settings and metadata consistency
        output.session_id = input_data.session_id
        if not output.id:
            output.id = uuid.uuid4()
        output.status = ReportStatus.DRAFT

        return output
