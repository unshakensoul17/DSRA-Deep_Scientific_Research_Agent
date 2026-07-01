"""
DSRA V2 — Gap Analysis Agent
==============================
Evaluates claim coverage against the research goal and generates gap-filling search queries.
"""

from typing import ClassVar

from app.agents.base import BaseAgent
from app.llm.prompts.gap_analysis import gap_analysis_prompt
from app.schemas.agents.all_agents import GapAnalysisAgentInput, GapAnalysisAgentOutput


class GapAnalysisAgent(BaseAgent[GapAnalysisAgentInput, GapAnalysisAgentOutput]):
    """
    Agent responsible for detecting coverage gaps and suggesting new searches.
    """

    name: ClassVar[str] = "GapAnalysisAgent"

    @property
    def system_prompt(self) -> str:
        return gap_analysis_prompt.system_template

    async def execute(self, input_data: GapAnalysisAgentInput) -> GapAnalysisAgentOutput:
        """
        Runs gap analysis evaluation on current gathered verified claims.
        """
        # Serialize current verified claims to context
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

        messages = [
            {"role": "system", "content": self.system_prompt},
            {
                "role": "user",
                "content": (
                    f"Research Topic: '{input_data.research_plan_topic}'\n"
                    f"Requested Focus Areas: {', '.join(input_data.research_plan_focus_areas) if input_data.research_plan_focus_areas else 'None'}\n"
                    f"Current Iteration: {input_data.current_iteration}\n"
                    f"Max Iterations Limit: {input_data.max_iterations}\n"
                    f"Sources Gathered: {input_data.sources_count}\n\n"
                    "Evaluate if the current verified claims are sufficient, or if new search queries are needed:\n\n"
                    "### Gathered Claims:\n"
                    f"{chr(10).join(claims_context) if claims_context else 'No claims extracted yet.'}"
                ),
            },
        ]

        # Call gateway for validated Pydantic model response
        output = await self.llm.get_structured_completion(
            messages=messages,
            response_schema=GapAnalysisAgentOutput,
            temperature=0.1,
        )

        # Enforce session id mapping
        output.session_id = input_data.session_id
        
        # Enforce that query IDs inside suggested queries are initialized
        for gap in output.gaps:
            for q in gap.suggested_queries:
                q.priority = max(0.0, min(q.priority or 1.0, 1.0))
        for q in output.new_queries:
            q.priority = max(0.0, min(q.priority or 1.0, 1.0))

        return output
