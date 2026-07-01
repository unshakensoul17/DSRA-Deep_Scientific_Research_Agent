"""
DSRA V2 — PubMed PMC Retrieval Adapter
=======================================
Queries PubMed's Entrez E-Utilities API (esearch and esummary) for medical research.
"""

import urllib.parse
import aiohttp

from app.core.logging import get_logger
from app.retrievers.base import BaseRetrieverAdapter
from app.schemas.common import SourceResult, SourceType

log = get_logger(__name__)


class PubMedAdapter(BaseRetrieverAdapter):

    @property
    def source_type(self) -> SourceType:
        return SourceType.PUBMED

    async def search(self, query: str, max_results: int = 10) -> list[SourceResult]:
        """Search PubMed and fetch summary details."""
        encoded_query = urllib.parse.quote(query)
        esearch_url = (
            f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?"
            f"db=pubmed&term={encoded_query}&retmax={max_results}&retmode=json"
        )

        try:
            log.debug("pubmed_search_started", query=query)
            # Step 1: E-Search to fetch IDs
            async with self.session.get(esearch_url, timeout=10) as search_res:
                if search_res.status != 200:
                    log.warning("pubmed_search_api_status_error", status=search_res.status)
                    return []
                search_data = await search_res.json()

            id_list = search_data.get("esearchresult", {}).get("idlist", [])
            if not id_list:
                log.info("pubmed_search_no_ids", query=query)
                return []

            # Step 2: E-Summary to fetch summary cards
            ids_str = ",".join(id_list)
            esummary_url = (
                f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?"
                f"db=pubmed&id={ids_str}&retmode=json"
            )

            async with self.session.get(esummary_url, timeout=10) as summary_res:
                if summary_res.status != 200:
                    log.warning("pubmed_summary_api_status_error", status=summary_res.status)
                    return []
                summary_data = await summary_res.json()

            results = []
            uid_results = summary_data.get("result", {})
            for uid in id_list:
                doc = uid_results.get(uid)
                if not doc:
                    continue

                title = doc.get("title") or "Untitled"
                # Extract year
                pub_date = doc.get("pubdate") or ""
                year = None
                if pub_date:
                    try:
                        year = int(pub_date.split()[0].split("-")[0])
                    except ValueError:
                        pass

                # Extract authors
                authors = []
                for author in doc.get("authors", []):
                    name = author.get("name")
                    if name:
                        authors.append(name)

                # Extract DOI
                doi = None
                for article_id in doc.get("articleids", []):
                    if article_id.get("idtype") == "doi":
                        doi = article_id.get("value")

                snippet = doc.get("source") or ""
                full_content = f"{doc.get('source', '')} - {doc.get('pubtype', '')}"

                results.append(
                    SourceResult(
                        title=title,
                        url=f"https://pubmed.ncbi.nlm.nih.gov/{uid}/",
                        snippet=snippet,
                        full_content=full_content,
                        source_type=self.source_type,
                        authors=authors,
                        year=year,
                        doi=doi,
                    )
                )

            log.info("pubmed_search_finished", count=len(results))
            return results

        except Exception as e:
            log.error("pubmed_search_failed", error=str(e))
            return []
