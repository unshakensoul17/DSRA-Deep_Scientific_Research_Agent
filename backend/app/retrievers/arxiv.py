"""
DSRA V2 — arXiv Retrieval Adapter
==================================
Queries the arXiv XML query API to retrieve scientific preprints.
"""

import urllib.parse
import xml.etree.ElementTree as ET
from uuid import uuid4

import aiohttp

from app.core.logging import get_logger
from app.retrievers.base import BaseRetrieverAdapter
from app.schemas.common import SourceResult, SourceType

log = get_logger(__name__)


class ArxivAdapter(BaseRetrieverAdapter):

    @property
    def source_type(self) -> SourceType:
        return SourceType.ARXIV

    async def search(self, query: str, max_results: int = 10) -> list[SourceResult]:
        """Search arXiv and parse XML output."""
        encoded_query = urllib.parse.quote(query)
        url = f"http://export.arxiv.org/api/query?search_query=all:{encoded_query}&max_results={max_results}"

        try:
            log.debug("arxiv_search_started", query=query)
            async with self.session.get(url, timeout=10) as response:
                if response.status != 200:
                    log.warning("arxiv_api_error_status", status=response.status)
                    return []
                xml_data = await response.text()

            # Parse XML feed namespace mappings
            root = ET.fromstring(xml_data)
            ns = {
                "atom": "http://www.w3.org/2005/Atom",
                "arxiv": "http://arxiv.org/schemas/atom",
            }

            results = []
            for entry in root.findall("atom:entry", ns):
                title_node = entry.find("atom:title", ns)
                summary_node = entry.find("atom:summary", ns)
                id_node = entry.find("atom:id", ns)
                published_node = entry.find("atom:published", ns)

                title = title_node.text.strip().replace("\n", " ") if title_node is not None else "Untitled"
                summary = summary_node.text.strip() if summary_node is not None else ""
                url_str = id_node.text.strip() if id_node is not None else ""

                # Extract publish year
                year = None
                if published_node is not None and published_node.text:
                    try:
                        year = int(published_node.text.split("-")[0])
                    except ValueError:
                        pass

                # Extract authors list
                authors = []
                for author in entry.findall("atom:author", ns):
                    name_node = author.find("atom:name", ns)
                    if name_node is not None and name_node.text:
                        authors.append(name_node.text.strip())

                # Build model
                results.append(
                    SourceResult(
                        title=title,
                        url=url_str or None,
                        snippet=summary[:500] + "..." if len(summary) > 500 else summary,
                        full_content=summary,  # Abstract is treated as full text for arXiv
                        source_type=self.source_type,
                        authors=authors,
                        year=year,
                    )
                )

            log.info("arxiv_search_finished", count=len(results))
            return results

        except Exception as e:
            log.error("arxiv_search_failed", error=str(e))
            return []
