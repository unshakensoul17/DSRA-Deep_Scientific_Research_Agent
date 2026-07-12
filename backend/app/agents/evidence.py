"""
DSRA V2 — Evidence Extraction Agent
====================================
Analyzes retrieved source documents to extract atomic claims and evaluate source quality.
"""

from typing import ClassVar

from app.agents.base import BaseAgent
from app.llm.prompts.evidence import evidence_prompt
from app.schemas.agents.all_agents import EvidenceAgentInput, EvidenceAgentOutput, EvidenceLLMOutput
from app.schemas.common import EvidencePiece


class EvidenceAgent(BaseAgent[EvidenceAgentInput, EvidenceAgentOutput]):
    """
    Agent responsible for extracting claims and evaluating source reliability scores.
    """

    name: ClassVar[str] = "EvidenceAgent"

    @property
    def system_prompt(self) -> str:
        return evidence_prompt.system_template

    async def execute(self, input_data: EvidenceAgentInput) -> EvidenceAgentOutput:
        """
        Runs claim extraction against the provided pool of sources.
        """
        # Format sources list as context for the model
        sources_context = []
        for idx, src in enumerate(input_data.sources):
            sources_context.append(
                f"Source [{idx}] UUID: {src.id}\n"
                f"Title: {src.title}\n"
                f"Type: {src.source_type}\n"
                f"Authors: {', '.join(src.authors) if src.authors else 'Unknown'}\n"
                f"Year: {src.year or 'Unknown'}\n"
                f"Citations: {src.citation_count or 0}\n"
                f"Content: {src.full_content or src.snippet}\n"
                "----------------------------------------"
            )

        messages = [
            {"role": "system", "content": self.system_prompt},
            {
                "role": "user",
                "content": (
                    f"Research Topic: {input_data.research_topic}\n"
                    f"Focus Areas: {', '.join(input_data.focus_areas) if input_data.focus_areas else 'None'}\n\n"
                    "Analyze the following sources and extract atomic claims relevant to the topic. "
                    "Also estimate the quality score for each source based on its attributes:\n\n"
                    f"{chr(10).join(sources_context)}"
                ),
            },
        ]

        # Call gateway for validated Pydantic model response
        llm_output = await self.llm.get_structured_completion(
            messages=messages,
            response_schema=EvidenceLLMOutput,
            temperature=0.1,
        )

        output = EvidenceAgentOutput(
            session_id=input_data.session_id,
            evidence_pieces=[
                EvidencePiece(
                    session_id=input_data.session_id,
                    claim_text=piece.claim_text,
                    source_id=piece.source_id,
                    relevance_score=piece.relevance_score,
                    excerpt=piece.excerpt,
                    page_or_section=piece.page_or_section,
                    iteration=piece.iteration,
                )
                for piece in llm_output.evidence_pieces
            ],
            source_quality_scores=llm_output.source_quality_scores,
            deduplication_removed=llm_output.deduplication_removed,
            total_sources_processed=llm_output.total_sources_processed,
        )

        return output
