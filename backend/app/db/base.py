"""
DSRA V2 — Database Base Declaration
====================================
Configures declarative base and shared registry for all SQL models.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    Unified base class for all SQLAlchemy ORM models.
    Supports modern type annotations.
    """
    pass
