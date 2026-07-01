"""
DSRA V2 — Wikipedia Search Adapter
====================================
Queries the Wikipedia API to retrieve general context and definition snippets.
"""

import urllib.parse
import aiohttp

from app.core.logging import get_logger
from app.retrievers.base import BaseRetrieverAdapter
from app.schemas.common import SourceResult, SourceType

log = get_logger(__name__)


class WikipediaAdapter(BaseRetrieverAdapter):

    @property
    def source_type(self) -> SourceType:
        return SourceType.WIKIPEDIA

    async def search(self, query: str, max_results: int = 10) -> list[SourceResult]:
        """Search Wikipedia API."""
        encoded_query = urllib.parse.quote(query)
        url = (
            f"https://en.wikipedia.org/w/api.php?action=query&list=search"
            f"&srsearch={encoded_query}&utf8=&format=json&srlimit={max_results}"
        )

        try:
            log.debug("wikipedia_search_started", query=query)
            async with self.session.get(url, timeout=10) as response:
                if response.status != 200:
                    log.warning("wikipedia_api_error_status", status=response.status)
                    return []
                data = await response.json()

            search_results = data.get("query", {}).get("search", [])
            results = []
            for item in search_results:
                title = item.get("title") or "Untitled"
                page_id = item.get("pageid")
                snippet = item.get("snippet") or ""

                # Strip HTML tags from snippet returned by wikipedia API
                import re
                clean_snippet = re.sub(r"<[^>]*>", "", snippet)

                # Page URL representation
                url_str = f"https://en.wikipedia.org/?curid={page_id}" if page_id else None

                results.append(
                    SourceResult(
                        title=title,
                        url=url_str,
                        snippet=clean_snippet,
                        full_content=clean_snippet,
                        source_type=self.source_type,
                        authors=["Wikipedia Contributors"],
                    )
                )

            log.info("wikipedia_search_finished", count=len(results))
            return results

        except Exception as e:
            log.error("wikipedia_search_failed", error=str(e))
            return []
