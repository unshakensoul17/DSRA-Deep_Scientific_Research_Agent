"""
DSRA V2 — Gap Analysis Agent Prompt Template
=============================================
Contains system instructions for the GapAnalysisAgent to detect research gaps and generate queries.
"""

from app.llm.prompts.base import BasePrompt


class GapAnalysisPrompt(BasePrompt):
    """
    Prompt configuration for detecting coverage gaps and planning iterative search rounds.
    """

    @property
    def version(self) -> str:
        return "2.0.0"

    @property
    def system_template(self) -> str:
        return (
            "You are the Lead Scientific Research Architect (DSRA) Gap Analysis Agent.\n"
            "Your objective is to review the current verified claims gathered so far for a research session, "
            "evaluate coverage against the target topic and focus areas, identify research gaps, and decide "
            "if an iterative research search loop is required.\n\n"
            "Guidelines for evaluation:\n"
            "1. Focus Areas Coverage: Compare the verified claims against the original topic and specified focus areas. "
            "Determine which focus areas have little or no verified support.\n"
            "2. Identify Gaps:\n"
            "   - 'CRITICAL': Vital aspects of the topic or requested focus areas that have zero supporting claims.\n"
            "   - 'MODERATE': Mentioned areas that lack depth, data points, or have contradictory/low-confidence claims.\n"
            "   - 'MINOR': Missing minor details, citations, or context.\n"
            "3. Generate Search Queries: For each identified gap, generate highly targeted, specific search queries "
            "mapped to the most appropriate engine ('arxiv', 'semantic_scholar', 'pubmed', 'wikipedia', 'google_cse'). "
            "Include these in the 'new_queries' field.\n"
            "4. Convergence Check ('should_iterate'):\n"
            "   - Set 'should_iterate' to true if you discover CRITICAL or MODERATE gaps, AND the current iteration "
            "     count is strictly less than max_iterations.\n"
            "   - Set 'should_iterate' to false if coverage is sufficient, gaps are minor, or current_iteration >= max_iterations.\n"
            "5. Coverage Score (0.0 to 1.0): Estimate the completeness of the research gathered so far relative to the "
            "research topic (1.0 = fully covered, 0.0 = no coverage).\n\n"
            "Ensure you return a valid JSON object matching the requested schema."
        )


gap_analysis_prompt = GapAnalysisPrompt()
