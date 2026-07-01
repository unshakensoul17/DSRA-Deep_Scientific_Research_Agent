"""
DSRA V2 — Google Custom Search Engine (CSE) Adapter
===================================================
Queries Google's Custom Search JSON API if credentials are provided.
"""

import urllib.parse
import aiohttp

from app.config.settings import get_settings
from app.core.logging import get_logger
from app.retrievers.base import BaseRetrieverAdapter
from app.schemas.common import SourceResult, SourceType

log = get_logger(__name__)
settings = get_settings()


class GoogleCSEAdapter(BaseRetrieverAdapter):

    @property
    def source_type(self) -> SourceType:
        return SourceType.GOOGLE_CSE

    async def search(self, query: str, max_results: int = 10) -> list[SourceResult]:
        """Search Google Custom Search Engine."""
        api_key = settings.google_api_key
        cx = settings.google_cse_id

        if not api_key or not cx:
            log.warning("google_cse_credentials_missing", api_key_present=bool(api_key), cx_present=bool(cx))
            return []

        encoded_query = urllib.parse.quote(query)
        url = f"https://www.googleapis.com/customsearch/v1?key={api_key}&cx={cx}&q={encoded_query}&num={max_results}"

        try:
            log.debug("google_cse_search_started", query=query)
            async with self.session.get(url, timeout=10) as response:
                if response.status != 200:
                    log.warning("google_cse_api_error_status", status=response.status)
                    return []
                data = await response.json()

            items = data.get("items", [])
            results = []
            for item in items:
                title = item.get("title") or "Untitled"
                link = item.get("link")
                snippet = item.get("snippet") or ""

                results.append(
                    SourceResult(
                        title=title,
                        url=link,
                        snippet=snippet,
                        full_content=snippet,
                        source_type=self.source_type,
                    )
                )

            log.info("google_cse_search_finished", count=len(results))
            return results

        except Exception as e:
            log.error("google_cse_search_failed", error=str(e))
            return []
