"""
DSRA V2 — Visualization Agent
==============================
Parses findings to generate datasets for maps, timelines, and relation graphs.
"""

from typing import ClassVar

from app.agents.base import BaseAgent
from app.llm.prompts.visualization import visualization_prompt
from app.schemas.agents.all_agents import (
    VisualizationAgentInput,
    VisualizationBundle,
    VisualizationLLMOutput,
)


class VisualizationAgent(BaseAgent[VisualizationAgentInput, VisualizationBundle]):
    """
    Agent responsible for translating reports into visual data representations.
    """

    name: ClassVar[str] = "VisualizationAgent"

    @property
    def system_prompt(self) -> str:
        return visualization_prompt.system_template

    async def execute(self, input_data: VisualizationAgentInput) -> VisualizationBundle:
        """
        Creates visualization payload based on claims and report draft content.
        """
        claims_context = []
        for idx, vc in enumerate(input_data.verified_claims):
            claims_context.append(
                f"Claim [{idx}] UUID: {vc.id}\n"
                f"Text: '{vc.text}'\n"
                f"Status: {vc.status}\n"
                f"Confidence: {vc.confidence}\n"
                "----------------------------------------"
            )

        user_content = (
            f"Report Title: {input_data.report.title}\n"
            f"Conclusion Summary: {input_data.report.conclusion[:500]}...\n\n"
            "### Verified Claims Pool:\n"
            f"{chr(10).join(claims_context) if claims_context else 'No claims.'}"
        )

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_content},
        ]

        # Call gateway with LLM-facing schema (no runtime session_id)
        llm_output = await self.llm.get_structured_completion(
            messages=messages,
            response_schema=VisualizationLLMOutput,
            temperature=0.1,
        )

        # Assemble runtime VisualizationBundle with correct session_id
        return VisualizationBundle(
            session_id=input_data.session_id,
            tables=llm_output.tables,
            timeline=llm_output.timeline,
            knowledge_nodes=llm_output.knowledge_nodes,
            knowledge_edges=llm_output.knowledge_edges,
            confidence_distribution=llm_output.confidence_distribution,
            source_type_distribution=llm_output.source_type_distribution,
        )
