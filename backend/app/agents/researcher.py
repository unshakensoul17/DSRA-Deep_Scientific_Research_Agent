"""
DSRA V2 — Research Agent
==========================
Routes individual search queries to the appropriate engine adapter.
"""

from typing import ClassVar
import aiohttp

from app.agents.base import BaseAgent
from app.retrievers.arxiv import ArxivAdapter
from app.retrievers.google_cse import GoogleCSEAdapter
from app.retrievers.pubmed import PubMedAdapter
from app.retrievers.semantic_scholar import SemanticScholarAdapter
from app.retrievers.wikipedia import WikipediaAdapter
from app.schemas.agents.all_agents import ResearchAgentInput, ResearchAgentOutput
from app.schemas.common import SourceType


class ResearchAgent(BaseAgent[ResearchAgentInput, ResearchAgentOutput]):
    """
    Agent in charge of executing search queries using specific platform adapters.
    """

    name: ClassVar[str] = "ResearchAgent"

    @property
    def system_prompt(self) -> str:
        return "You are a Research Retrieval Agent tasked with fetching documents matching query criteria."

    async def execute(self, input_data: ResearchAgentInput) -> ResearchAgentOutput:
        """
        Creates an ephemeral client session and queries the target adapter.
        """
        source_type = input_data.query.source_type
        query_text = input_data.query.query_text
        max_results = input_data.max_results

        async with aiohttp.ClientSession() as session:
            # 1. Map to correct retriever adapter
            if source_type == SourceType.ARXIV:
                adapter = ArxivAdapter(session)
            elif source_type == SourceType.SEMANTIC_SCHOLAR:
                adapter = SemanticScholarAdapter(session)
            elif source_type == SourceType.PUBMED:
                adapter = PubMedAdapter(session)
            elif source_type == SourceType.WIKIPEDIA:
                adapter = WikipediaAdapter(session)
            elif source_type == SourceType.GOOGLE_CSE:
                adapter = GoogleCSEAdapter(session)
            else:
                raise ValueError(f"Unsupported source type: {source_type}")

            # 2. Run retrieval
            raw_results = await adapter.search(query_text, max_results=max_results)

            # 3. Enrich metadata (map back to session and query IDs)
            for res in raw_results:
                res.session_id = input_data.session_id
                res.query_id = input_data.query.id

            return ResearchAgentOutput(
                session_id=input_data.session_id,
                results=raw_results,
            )
