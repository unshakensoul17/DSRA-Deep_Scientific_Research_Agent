"""
Exposes all database repositories for clean access.
"""

from app.db.repositories.base import BaseRepository
from app.db.repositories.research_session import ResearchSessionRepository
from app.db.repositories.source import SourceRepository
from app.db.repositories.claim import ClaimRepository
from app.db.repositories.report import ReportRepository
from app.db.repositories.user import UserRepository

__all__ = [
    "BaseRepository",
    "ResearchSessionRepository",
    "SourceRepository",
    "ClaimRepository",
    "ReportRepository",
    "UserRepository",
]
"""
Initial package file.
"""
