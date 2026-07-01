"""
DSRA V2 — Verification Agent
=============================
Cross-references extracted claims against source documents to assign status and confidence.
"""

from typing import ClassVar

from app.agents.base import BaseAgent
from app.llm.prompts.verification import verification_prompt
from app.schemas.agents.all_agents import VerificationAgentInput, VerificationAgentOutput


class VerificationAgent(BaseAgent[VerificationAgentInput, VerificationAgentOutput]):
    """
    Agent responsible for verifying atomic claims and marking contradictions.
    """

    name: ClassVar[str] = "VerificationAgent"

    @property
    def system_prompt(self) -> str:
        return verification_prompt.system_template

    async def execute(self, input_data: VerificationAgentInput) -> VerificationAgentOutput:
        """
        Verifies and cross-references claims against the source documents.
        """
        # Serialize evidence pieces to be cross-referenced
        claims_context = []
        for idx, ep in enumerate(input_data.evidence_pieces):
            claims_context.append(
                f"Claim [{idx}] UUID: {ep.id}\n"
                f"Text: '{ep.claim_text}'\n"
                f"Source ID: {ep.source_id}\n"
                f"Excerpt: '{ep.excerpt}'\n"
                "----------------------------------------"
            )

        # Serialize source details (excluding full text to save token window space, since snippets and metadata are enough for verification)
        sources_context = []
        for idx, src in enumerate(input_data.sources):
            sources_context.append(
                f"Source UUID: {src.id}\n"
                f"Title: {src.title}\n"
                f"Quality Score: {src.quality_score or 0.5}\n"
                f"Citation Count: {src.citation_count or 0}\n"
                f"Snippet: {src.snippet}\n"
                "----------------------------------------"
            )

        messages = [
            {"role": "system", "content": self.system_prompt},
            {
                "role": "user",
                "content": (
                    f"Research Topic: {input_data.research_topic}\n\n"
                    "Compare the following extracted claims against the pool of sources to identify "
                    "support, contradictions, and verify them:\n\n"
                    "### Claims to Verify:\n"
                    f"{chr(10).join(claims_context)}\n\n"
                    "### Reference Source Pool:\n"
                    f"{chr(10).join(sources_context)}"
                ),
            },
        ]

        # Call gateway for validated Pydantic model response
        output = await self.llm.get_structured_completion(
            messages=messages,
            response_schema=VerificationAgentOutput,
            temperature=0.1,
        )

        # Enforce session id mapping
        output.session_id = input_data.session_id
        for vc in output.verified_claims:
            vc.session_id = input_data.session_id

        return output
