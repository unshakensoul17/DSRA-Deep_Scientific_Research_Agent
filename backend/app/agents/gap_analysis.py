"""
DSRA V2 — Gap Analysis Agent
==============================
Evaluates claim coverage against the research goal and generates gap-filling search queries.
"""

from typing import ClassVar

from app.agents.base import BaseAgent
from app.llm.prompts.gap_analysis import gap_analysis_prompt
from app.schemas.agents.all_agents import (
    GapAnalysisAgentInput,
    GapAnalysisAgentOutput,
    GapAnalysisLLMOutput,
    RuntimeResearchGap,
)
from app.schemas.common import SearchQuery


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

        # Call gateway with LLM-facing schema (no runtime session_id)
        llm_output = await self.llm.get_structured_completion(
            messages=messages,
            response_schema=GapAnalysisLLMOutput,
            temperature=0.1,
        )

        # Map LLMSearchQuery items to runtime SearchQuery with fresh IDs
        def _to_search_query(lq) -> SearchQuery:
            return SearchQuery(
                query_text=lq.query_text,
                source_type=lq.source_type,
                priority=max(0.0, min(lq.priority or 1.0, 1.0)),
                filters=lq.filters,
            )

        new_queries = [_to_search_query(q) for q in llm_output.new_queries]

        # Convert gap suggested queries similarly
        gaps = []
        for g in llm_output.gaps:
            mapped_suggestions = [_to_search_query(q) for q in g.suggested_queries]
            gaps.append(RuntimeResearchGap(
                description=g.description,
                severity=g.severity,
                suggested_queries=mapped_suggestions,
            ))

        return GapAnalysisAgentOutput(
            session_id=input_data.session_id,
            gaps=gaps,
            has_critical_gaps=llm_output.has_critical_gaps,
            should_iterate=llm_output.should_iterate,
            new_queries=new_queries,
            iteration_reasoning=llm_output.iteration_reasoning,
            coverage_score=llm_output.coverage_score,
        )
