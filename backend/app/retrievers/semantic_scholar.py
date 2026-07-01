"""
DSRA V2 — Semantic Scholar Retrieval Adapter
=============================================
Queries the Semantic Scholar graph API to fetch paper abstracts and citation counts.
"""

import urllib.parse
import aiohttp

from app.config.settings import get_settings
from app.core.logging import get_logger
from app.retrievers.base import BaseRetrieverAdapter
from app.schemas.common import SourceResult, SourceType

log = get_logger(__name__)
settings = get_settings()


class SemanticScholarAdapter(BaseRetrieverAdapter):

    @property
    def source_type(self) -> SourceType:
        return SourceType.SEMANTIC_SCHOLAR

    async def search(self, query: str, max_results: int = 10) -> list[SourceResult]:
        """Search Semantic Scholar database."""
        encoded_query = urllib.parse.quote(query)
        fields = "title,url,abstract,authors,year,citationCount,externalIds"
        url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={encoded_query}&limit={max_results}&fields={fields}"

        # Inject API key if available
        headers = {}
        if settings.semantic_scholar_api_key:
            headers["x-api-key"] = settings.semantic_scholar_api_key

        try:
            log.debug("semantic_scholar_search_started", query=query)
            async with self.session.get(url, headers=headers, timeout=10) as response:
                if response.status != 200:
                    log.warning("semantic_scholar_api_error_status", status=response.status)
                    return []
                data = await response.json()

            results = []
            papers = data.get("data", [])
            for paper in papers:
                title = paper.get("title") or "Untitled"
                url_str = paper.get("url")
                abstract = paper.get("abstract") or ""
                year = paper.get("year")
                citations = paper.get("citationCount")
                
                # DOI
                external_ids = paper.get("externalIds") or {}
                doi = external_ids.get("DOI")

                # Parse authors list
                authors = []
                paper_authors = paper.get("authors") or []
                for author in paper_authors:
                    name = author.get("name")
                    if name:
                        authors.append(name)

                # Skip papers with no title or text contents
                if not abstract and not title:
                    continue

                results.append(
                    SourceResult(
                        title=title,
                        url=url_str or None,
                        snippet=abstract[:500] + "..." if len(abstract) > 500 else abstract,
                        full_content=abstract or title,
                        source_type=self.source_type,
                        authors=authors,
                        year=year,
                        doi=doi,
                        citation_count=citations,
                    )
                )

            log.info("semantic_scholar_search_finished", count=len(results))
            return results

        except Exception as e:
            log.error("semantic_scholar_search_failed", error=str(e))
            return []
