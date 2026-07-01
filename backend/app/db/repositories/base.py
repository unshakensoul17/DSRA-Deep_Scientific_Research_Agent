"""
DSRA V2 — Base Repository Pattern
==================================
Defines generic CRUD operations for database access.
Allows testing by swapping out implementations with a mock layer.
"""

from typing import Any, Generic, Optional, Type, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """
    Abstract Base Repository encapsulating common SQLAlchemy queries.
    Uses async session operations.
    """

    def __init__(self, model: Type[ModelT], db_session: AsyncSession):
        self.model = model
        self.db_session = db_session

    async def get_by_id(self, id: Any) -> Optional[ModelT]:
        """Fetch a single record by its primary key ID."""
        return await self.db_session.get(self.model, id)

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[ModelT]:
        """Fetch all records with optional offset pagination."""
        query = select(self.model).offset(skip).limit(limit)
        result = await self.db_session.execute(query)
        return list(result.scalars().all())

    async def create(self, obj_in: ModelT) -> ModelT:
        """Add a new model instance to the session."""
        self.db_session.add(obj_in)
        return obj_in

    async def delete(self, id: Any) -> bool:
        """Delete a record by its primary key ID."""
        obj = await self.get_by_id(id)
        if obj:
            await self.db_session.delete(obj)
            return True
        return False
