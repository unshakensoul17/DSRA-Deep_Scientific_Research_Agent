"""
DSRA V2 — Planner Agent
=========================
Decomposes user research topics into structured search query plans.
Uses the PlannerPrompt template and returns a validated ResearchPlan model.
"""

from typing import ClassVar

from app.agents.base import BaseAgent
from app.llm.prompts.planner import planner_prompt
from app.schemas.agents.planner import ResearchGoal, ResearchPlan


class PlannerAgent(BaseAgent[ResearchGoal, ResearchPlan]):
    """
    Agent responsible for breaking down a research goal into targeted query plans.
    """

    name: ClassVar[str] = "PlannerAgent"

    @property
    def system_prompt(self) -> str:
        return planner_prompt.system_template

    async def execute(self, input_data: ResearchGoal) -> ResearchPlan:
        """
        Executes the planning model using the centralized LLMGateway.
        """
        # Build prompt messages
        messages = [
            {"role": "system", "content": self.system_prompt},
            {
                "role": "user",
                "content": (
                    f"Create a research plan for the topic: '{input_data.topic}'.\n"
                    f"Requested Depth level: {input_data.depth} (1=Shallow, 2=Normal, 3=Deep).\n"
                    f"Focus Areas to emphasize: {', '.join(input_data.focus_areas) if input_data.focus_areas else 'None specified'}.\n"
                    f"Prefer these source engines: {', '.join([str(p) for p in input_data.source_preferences])}.\n"
                    f"Ensure you return a valid JSON plan containing 'queries' (SearchQuery list), "
                    f"'estimated_complexity' (0.0 to 1.0), 'suggested_depth', and 'reasoning' fields."
                ),
            },
        ]

        # Call gateway for validated Pydantic model response
        plan = await self.llm.get_structured_completion(
            messages=messages,
            response_schema=ResearchPlan,
            temperature=0.2,
        )

        # Ensure session_id matches input session
        plan.session_id = input_data.session_id
        plan.topic = input_data.topic

        return plan
