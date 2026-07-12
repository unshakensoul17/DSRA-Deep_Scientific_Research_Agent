"""
DSRA V2 — Planner Agent
=========================
Decomposes user research topics into structured search query plans.
Uses the PlannerPrompt template and returns a validated ResearchPlan model.
"""

from typing import ClassVar

from app.agents.base import BaseAgent
from app.llm.prompts.planner import planner_prompt
from app.schemas.agents.planner import PlannerLLMPlan, ResearchGoal, ResearchPlan
from app.schemas.common import SearchQuery, SourceType


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
                    f"Session ID: {input_data.session_id}.\n"
                    f"Requested Depth level: {input_data.depth} (1=Shallow, 2=Normal, 3=Deep).\n"
                    f"Focus Areas to emphasize: {', '.join(input_data.focus_areas) if input_data.focus_areas else 'None specified'}.\n"
                    "Prefer these source_type values: "
                    f"{', '.join([getattr(p, 'value', str(p)) for p in input_data.source_preferences])}.\n"
                    f"Allowed source_type values: {', '.join([source.value for source in SourceType])}.\n"
                    "Return only a valid JSON object containing 'queries', 'estimated_complexity', "
                    "'suggested_depth', 'focus_areas', and 'reasoning'. Each query must use exactly "
                    "'query_text', 'source_type', 'priority', and 'filters'. Do not use 'query' or 'engine'."
                ),
            },
        ]

        # Call gateway for validated Pydantic model response
        llm_plan = await self.llm.get_structured_completion(
            messages=messages,
            response_schema=PlannerLLMPlan,
            temperature=0.2,
        )

        return ResearchPlan(
            session_id=input_data.session_id,
            topic=input_data.topic,
            queries=[
                SearchQuery(
                    query_text=query.query_text,
                    source_type=query.source_type,
                    priority=query.priority,
                    filters=query.filters,
                )
                for query in llm_plan.queries
            ],
            estimated_complexity=llm_plan.estimated_complexity,
            suggested_depth=llm_plan.suggested_depth,
            focus_areas=input_data.focus_areas or llm_plan.focus_areas,
            reasoning=llm_plan.reasoning,
        )
