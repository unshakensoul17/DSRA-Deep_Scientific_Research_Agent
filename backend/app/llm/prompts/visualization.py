"""
DSRA V2 — Visualization Agent Prompt Template
==============================================
Contains system instructions for the VisualizationAgent to compile graph and timeline datasets.
"""

from app.llm.prompts.base import BasePrompt


class VisualizationPrompt(BasePrompt):
    """
    Prompt configuration for compiling tables, timeline events, and concept graphs from the report.
    """

    @property
    def version(self) -> str:
        return "2.0.0"

    @property
    def system_template(self) -> str:
        return (
            "You are the Lead Scientific Research Architect (DSRA) Visualization Agent.\n"
            "Your objective is to extract structured dataset views from the research report, "
            "enabling rich timeline, tabular, and interactive network graph rendering.\n\n"
            "Guidelines for extraction:\n"
            "1. Tables ('tables'): Extract key structured comparisons, metric summaries, or data trials "
            "   into simple row/column formats.\n"
            "2. Timeline ('timeline'): Identify key historical dates, clinical trials, or milestones mentioned "
            "   in the report, parsing the exact year (ge 1900) and significance.\n"
            "3. Network Graph ('knowledge_nodes' and 'knowledge_edges'): Represent concepts, entities, or "
            "   findings as nodes, and link them using relationships (e.g. 'A inhibits B', 'X is a marker of Y').\n"
            "4. Distributions: Count frequency of source types used (e.g. {'pubmed': 3, 'arxiv': 2}) and "
            "   claims confidence levels (e.g. {'high': 4, 'medium': 1}).\n\n"
            "Ensure you return a valid JSON object matching the requested schema."
        )


visualization_prompt = VisualizationPrompt()
