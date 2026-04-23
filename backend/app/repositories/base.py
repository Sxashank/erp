"""Base repository with generic CRUD operations."""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar
from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import BaseModel

ModelType = TypeVar("ModelType", bound=BaseModel)


class BaseRepository(Generic[ModelType]):
    """Base repository providing generic CRUD operations."""

    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    async def get(self, id: UUID) -> Optional[ModelType]:
        """Get a record by ID."""
        query = select(self.model).where(
            and_(
                self.model.id == id,
                self.model.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_id(self, id: UUID, include_inactive: bool = False) -> Optional[ModelType]:
        """Get a record by ID with option to include inactive."""
        query = select(self.model).where(self.model.id == id)
        if not include_inactive:
            query = query.where(self.model.is_active == True)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False,
    ) -> List[ModelType]:
        """Get all records with pagination."""
        query = select(self.model)
        if not include_inactive:
            query = query.where(self.model.is_active == True)
        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count(self, include_inactive: bool = False) -> int:
        """Count all records."""
        query = select(func.count(self.model.id))
        if not include_inactive:
            query = query.where(self.model.is_active == True)
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def create(self, obj_in: Dict[str, Any]) -> ModelType:
        """Create a new record."""
        db_obj = self.model(**obj_in)
        self.session.add(db_obj)
        await self.session.flush()
        await self.session.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db_obj: ModelType,
        obj_in: Dict[str, Any],
    ) -> ModelType:
        """Update an existing record."""
        for field, value in obj_in.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        await self.session.flush()
        await self.session.refresh(db_obj)
        return db_obj

    async def delete(self, id: UUID) -> bool:
        """Hard delete a record."""
        db_obj = await self.get_by_id(id, include_inactive=True)
        if db_obj:
            await self.session.delete(db_obj)
            await self.session.flush()
            return True
        return False

    async def soft_delete(
        self,
        id: UUID,
        deleted_by: Optional[UUID] = None,
    ) -> Optional[ModelType]:
        """Soft delete a record."""
        db_obj = await self.get(id)
        if db_obj:
            db_obj.soft_delete(deleted_by)
            await self.session.flush()
            await self.session.refresh(db_obj)
            return db_obj
        return None

    async def restore(self, id: UUID) -> Optional[ModelType]:
        """Restore a soft-deleted record."""
        db_obj = await self.get_by_id(id, include_inactive=True)
        if db_obj and not db_obj.is_active:
            db_obj.restore()
            await self.session.flush()
            await self.session.refresh(db_obj)
            return db_obj
        return None

    async def exists(self, id: UUID) -> bool:
        """Check if a record exists."""
        query = select(func.count(self.model.id)).where(
            and_(
                self.model.id == id,
                self.model.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return (result.scalar() or 0) > 0

    async def get_by_field(
        self,
        field: str,
        value: Any,
        include_inactive: bool = False,
    ) -> Optional[ModelType]:
        """Get a record by a specific field."""
        query = select(self.model).where(getattr(self.model, field) == value)
        if not include_inactive:
            query = query.where(self.model.is_active == True)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_many_by_field(
        self,
        field: str,
        value: Any,
        include_inactive: bool = False,
    ) -> List[ModelType]:
        """Get multiple records by a specific field."""
        query = select(self.model).where(getattr(self.model, field) == value)
        if not include_inactive:
            query = query.where(self.model.is_active == True)
        result = await self.session.execute(query)
        return list(result.scalars().all())
