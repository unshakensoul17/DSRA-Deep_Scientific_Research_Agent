"""
Exposes retrieval adapters and register mapping.
"""

from app.retrievers.base import BaseRetrieverAdapter
from app.retrievers.arxiv import ArxivAdapter
from app.retrievers.semantic_scholar import SemanticScholarAdapter
from app.retrievers.pubmed import PubMedAdapter
from app.retrievers.wikipedia import WikipediaAdapter
from app.retrievers.google_cse import GoogleCSEAdapter

__all__ = [
    "BaseRetrieverAdapter",
    "ArxivAdapter",
    "SemanticScholarAdapter",
    "PubMedAdapter",
    "WikipediaAdapter",
    "GoogleCSEAdapter",
]
