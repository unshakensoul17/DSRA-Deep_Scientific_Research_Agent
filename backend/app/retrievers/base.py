"""
DSRA V2 — Base Retriever Adapter
=================================
Abstract interface defining execution protocols for API retrieval adapters.
"""

from abc import ABC, abstractmethod
import aiohttp

from app.schemas.common import SourceResult, SourceType


class BaseRetrieverAdapter(ABC):
    """
    Base class for specific search API adapters.
    Utilizes sharing a single aiohttp ClientSession.
    """

    def __init__(self, session: aiohttp.ClientSession) -> None:
        self.session = session

    @property
    @abstractmethod
    def source_type(self) -> SourceType:
        """The source enum handled by this adapter."""
        pass

    @abstractmethod
    async def search(self, query: str, max_results: int = 10) -> list[SourceResult]:
        """
        Asynchronously search the target API.
        Must catch API connection errors and return validated SourceResult lists.
        """
        pass
