"""
DSRA V2 — Verification Agent
=============================
Cross-references extracted claims against source documents to assign status and confidence.
"""

from typing import ClassVar

from app.agents.base import BaseAgent
from app.llm.prompts.verification import verification_prompt
from app.schemas.agents.all_agents import (
    VerificationAgentInput,
    VerificationAgentOutput,
    VerificationLLMOutput,
)
from app.schemas.common import VerifiedClaim


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

        # Call gateway with LLM-facing schema (no runtime UUIDs)
        llm_output = await self.llm.get_structured_completion(
            messages=messages,
            response_schema=VerificationLLMOutput,
            temperature=0.1,
        )

        # Map LLM claims to runtime VerifiedClaim objects with correct IDs
        verified_claims = [
            VerifiedClaim(
                session_id=input_data.session_id,
                text=lc.text,
                confidence=lc.confidence,
                status=lc.status,
                supporting_source_ids=[],
                contradicting_source_ids=[],
                reasoning=lc.reasoning,
                iteration=lc.iteration,
            )
            for lc in llm_output.verified_claims
        ]

        return VerificationAgentOutput(
            session_id=input_data.session_id,
            verified_claims=verified_claims,
            contradictions_found=llm_output.contradictions_found,
            high_confidence_claims=llm_output.high_confidence_claims,
            verification_coverage=llm_output.verification_coverage,
        )
