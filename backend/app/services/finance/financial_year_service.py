"""Financial Year service."""

from calendar import monthrange
from datetime import date, datetime, timezone
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException, ConflictException, BadRequestException
from app.models.finance.financial_year import FinancialYear, FinancialPeriod
from app.repositories.finance.financial_year_repo import (
    FinancialYearRepository,
    FinancialPeriodRepository,
)
from app.repositories.masters.organization_repo import OrganizationRepository
from app.schemas.finance.financial_year import FinancialYearCreate, FinancialYearUpdate


class FinancialYearService:
    """Service for financial year management."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = FinancialYearRepository(session)
        self.period_repo = FinancialPeriodRepository(session)
        self.org_repo = OrganizationRepository(session)

    async def create(
        self,
        data: FinancialYearCreate,
        created_by: Optional[UUID] = None,
    ) -> FinancialYear:
        """Create a new financial year with periods."""
        # Check if code exists
        if await self.repo.code_exists(data.code):
            raise ConflictException(f"Financial year code '{data.code}' already exists")

        # Verify organization exists
        org = await self.org_repo.get(data.organization_id)
        if not org:
            raise NotFoundException("Organization not found")

        # Validate dates
        if data.end_date <= data.start_date:
            raise BadRequestException("End date must be after start date")

        # If this is set as current, clear other current flags
        if data.is_current:
            await self.repo.clear_current(data.organization_id)

        # Create financial year
        fy_data = data.model_dump()
        fy_data["created_by"] = created_by
        fy = await self.repo.create(fy_data)

        # Generate periods (monthly)
        await self._generate_periods(fy, created_by)

        return fy

    async def _generate_periods(
        self,
        fy: FinancialYear,
        created_by: Optional[UUID] = None,
    ) -> None:
        """Generate monthly periods for a financial year."""
        current_date = fy.start_date
        period_number = 1

        while current_date <= fy.end_date:
            # Get the last day of the current month
            _, last_day = monthrange(current_date.year, current_date.month)
            period_end = date(current_date.year, current_date.month, last_day)

            # Don't go past the financial year end
            if period_end > fy.end_date:
                period_end = fy.end_date

            period_name = current_date.strftime("%B %Y")  # e.g., "April 2024"

            period_data = {
                "financial_year_id": fy.id,
                "period_number": period_number,
                "name": period_name,
                "start_date": current_date,
                "end_date": period_end,
                "is_closed": False,
                "is_adjustment_period": False,
                "created_by": created_by,
            }
            await self.period_repo.create(period_data)

            # Move to next month
            if period_end.month == 12:
                current_date = date(period_end.year + 1, 1, 1)
            else:
                current_date = date(period_end.year, period_end.month + 1, 1)
            period_number += 1

    async def update(
        self,
        id: UUID,
        data: FinancialYearUpdate,
        updated_by: Optional[UUID] = None,
    ) -> FinancialYear:
        """Update a financial year."""
        fy = await self.repo.get(id)
        if not fy:
            raise NotFoundException("Financial year not found")

        if fy.is_closed:
            raise BadRequestException("Cannot update a closed financial year")

        # Check code uniqueness if being updated
        if data.code and data.code != fy.code:
            if await self.repo.code_exists(data.code, exclude_id=id):
                raise ConflictException(f"Financial year code '{data.code}' already exists")

        # If setting as current, clear other current flags
        if data.is_current and not fy.is_current:
            await self.repo.clear_current(fy.organization_id)

        update_data = data.model_dump(exclude_unset=True)
        update_data["updated_by"] = updated_by

        return await self.repo.update(fy, update_data)

    async def get(self, id: UUID) -> FinancialYear:
        """Get financial year by ID."""
        fy = await self.repo.get_with_periods(id)
        if not fy:
            raise NotFoundException("Financial year not found")
        return fy

    async def get_all(
        self,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False,
    ) -> Tuple[List[FinancialYear], int]:
        """Get all financial years for an organization."""
        fys = await self.repo.get_by_organization(organization_id, include_inactive)
        total = len(fys)
        return fys[skip:skip + limit], total

    async def get_current(self, organization_id: UUID) -> Optional[FinancialYear]:
        """Get the current financial year."""
        return await self.repo.get_current(organization_id)

    async def get_by_date(
        self,
        organization_id: UUID,
        check_date: date,
    ) -> Optional[FinancialYear]:
        """Get financial year containing a specific date."""
        return await self.repo.get_by_date(organization_id, check_date)

    async def close_period(
        self,
        period_id: UUID,
        closed_by: Optional[UUID] = None,
    ) -> FinancialPeriod:
        """Close a financial period."""
        period = await self.period_repo.get(period_id)
        if not period:
            raise NotFoundException("Financial period not found")

        if period.is_closed:
            raise BadRequestException("Period is already closed")

        # Check that previous periods are closed
        periods = await self.period_repo.get_by_financial_year(period.financial_year_id)
        for p in periods:
            if p.period_number < period.period_number and not p.is_closed:
                raise BadRequestException(
                    f"Cannot close period. Previous period '{p.name}' is still open."
                )

        period.is_closed = True
        period.closed_at = datetime.now(timezone.utc)
        period.closed_by = closed_by
        await self.session.flush()
        await self.session.refresh(period)

        return period

    async def close_year(
        self,
        id: UUID,
        closed_by: Optional[UUID] = None,
    ) -> FinancialYear:
        """Close a financial year."""
        fy = await self.repo.get_with_periods(id)
        if not fy:
            raise NotFoundException("Financial year not found")

        if fy.is_closed:
            raise BadRequestException("Financial year is already closed")

        # Check all periods are closed
        for period in fy.periods:
            if not period.is_closed:
                raise BadRequestException(
                    f"Cannot close year. Period '{period.name}' is still open."
                )

        fy.is_closed = True
        fy.is_current = False
        fy.closed_at = datetime.now(timezone.utc)
        fy.closed_by = closed_by
        await self.session.flush()
        await self.session.refresh(fy)

        return fy

    async def delete(
        self,
        id: UUID,
        deleted_by: Optional[UUID] = None,
    ) -> FinancialYear:
        """Soft delete a financial year."""
        fy = await self.repo.get(id)
        if not fy:
            raise NotFoundException("Financial year not found")

        if fy.is_closed:
            raise BadRequestException("Cannot delete a closed financial year")

        # TODO: Check for vouchers in this financial year

        return await self.repo.soft_delete(id, deleted_by)
