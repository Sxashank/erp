"""GST Rate service."""

from datetime import date
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.gst.gst_rate import GSTRate
from app.schemas.gst.gst_rate import GSTRateCreate, GSTRateUpdate
from app.repositories.gst.gst_rate_repo import GSTRateRepository
from app.core.exceptions import NotFoundException, ConflictException


class GSTRateService:
    """Service for GST Rate operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = GSTRateRepository(session)

    async def create(self, data: GSTRateCreate, created_by: UUID) -> GSTRate:
        """Create a new GST rate."""
        # Check for duplicate code
        existing = await self.repo.get_by_code(data.code)
        if existing:
            raise ConflictException(f"GST rate with code '{data.code}' already exists")

        rate = GSTRate(
            **data.model_dump(),
            created_by=created_by,
        )
        self.session.add(rate)
        await self.session.flush()
        await self.session.refresh(rate)
        return rate

    async def update(
        self,
        id: UUID,
        data: GSTRateUpdate,
        updated_by: UUID,
    ) -> GSTRate:
        """Update a GST rate."""
        rate = await self.repo.get(id)
        if not rate:
            raise NotFoundException("GST rate not found")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(rate, field, value)
        rate.updated_by = updated_by

        await self.session.flush()
        await self.session.refresh(rate)
        return rate

    async def get(self, id: UUID) -> GSTRate:
        """Get GST rate by ID."""
        rate = await self.repo.get(id)
        if not rate:
            raise NotFoundException("GST rate not found")
        return rate

    async def get_by_code(self, code: str) -> GSTRate:
        """Get GST rate by code."""
        rate = await self.repo.get_by_code(code)
        if not rate:
            raise NotFoundException(f"GST rate with code '{code}' not found")
        return rate

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False,
    ) -> Tuple[List[GSTRate], int]:
        """Get all GST rates."""
        return await self.repo.get_all_rates(skip, limit, include_inactive)

    async def get_active(
        self,
        as_of_date: Optional[date] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[GSTRate], int]:
        """Get active GST rates as of a date."""
        return await self.repo.get_active_rates(as_of_date, skip, limit)

    async def delete(self, id: UUID, deleted_by: UUID) -> None:
        """Soft delete a GST rate."""
        rate = await self.repo.get(id)
        if not rate:
            raise NotFoundException("GST rate not found")
        rate.soft_delete(deleted_by)
        await self.session.flush()
