"""
DSRA V2 — Database Session Factory
====================================
Manages the lifetime of the async engine and session makers.
Includes health check capability.
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config.settings import get_settings
from app.core.logging import get_logger

log = get_logger(__name__)
settings = get_settings()

# Create async engine with pooling options
async_engine = create_async_engine(
    settings.database_url,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    pool_pre_ping=True,  # Check connection health before checkout
    echo=False,
)

# Async session maker
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Prevent issues accessing attributes after commit
    autocommit=False,
    autoflush=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency helper for FastAPI endpoints.
    Ensures session is closed properly even on exceptions.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def check_db_health() -> bool:
    """Run a simple SELECT 1 query to verify database connectivity."""
    from sqlalchemy import text
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        return True
    except Exception as e:
        log.error("db_health_check_failed", error=str(e))
        return False
