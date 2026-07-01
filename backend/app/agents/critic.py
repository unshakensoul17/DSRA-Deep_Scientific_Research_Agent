"""
DSRA V2 — Critic Agent
=======================
Evaluates report drafts against quality metrics and suggests structural enhancements.
"""

from typing import ClassVar

from app.agents.base import BaseAgent
from app.llm.prompts.critic import critic_prompt
from app.schemas.agents.all_agents import CriticAgentInput, CritiqueResult


class CriticAgent(BaseAgent[CriticAgentInput, CritiqueResult]):
    """
    Agent responsible for reviewing and scoring report drafts.
    """

    name: ClassVar[str] = "CriticAgent"

    @property
    def system_prompt(self) -> str:
        return critic_prompt.system_template

    async def execute(self, input_data: CriticAgentInput) -> CritiqueResult:
        """
        Grades draft and outputs structured improvements instructions.
        """
        # Serialize draft structure
        sections_context = []
        for idx, sec in enumerate(input_data.draft.sections):
            sections_context.append(
                f"Section: {sec.title} (Order: {idx + 1})\n"
                f"Content: {sec.content[:300]}...\n"
                "----------------------------------------"
            )

        user_content = (
            f"Draft Title: {input_data.draft.title}\n"
            f"Executive Summary: {input_data.draft.executive_summary[:500]}...\n\n"
            "### Draft Sections:\n"
            f"{chr(10).join(sections_context)}\n\n"
            f"Revision Number: {input_data.revision_number}\n"
            f"Max Revisions Allowed: {input_data.max_revisions}\n"
        )

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_content},
        ]

        # Call gateway for validated Pydantic model response
        output = await self.llm.get_structured_completion(
            messages=messages,
            response_schema=CritiqueResult,
            temperature=0.1,
        )

        # Enforce consistent IDs
        output.session_id = input_data.session_id
        output.draft_id = input_data.draft.id

        return output
