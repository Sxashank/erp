"""Period Service for financial period locking and validation."""

from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.finance.financial_year import FinancialPeriod, FinancialYear
from app.core.exceptions import NotFoundException, ValidationException


@dataclass
class PeriodValidationResult:
    """Result of period validation."""
    allowed: bool
    period_id: Optional[UUID] = None
    period_name: Optional[str] = None
    reason: Optional[str] = None  # PERIOD_LOCKED, PERIOD_CLOSED, GST_FILED, OK


class PeriodLockedError(ValidationException):
    """Exception raised when trying to create entries in a locked period."""
    pass


class PeriodService:
    """Service for financial period operations including locking."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_period_for_date(
        self,
        organization_id: UUID,
        entry_date: date,
    ) -> Optional[FinancialPeriod]:
        """Get the financial period that contains the given date."""
        query = (
            select(FinancialPeriod)
            .join(FinancialYear)
            .where(
                and_(
                    FinancialYear.organization_id == organization_id,
                    FinancialPeriod.start_date <= entry_date,
                    FinancialPeriod.end_date >= entry_date,
                    FinancialPeriod.is_active == True,
                )
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_period(self, period_id: UUID) -> FinancialPeriod:
        """Get a financial period by ID."""
        query = select(FinancialPeriod).where(FinancialPeriod.id == period_id)
        result = await self.db.execute(query)
        period = result.scalar_one_or_none()
        if not period:
            raise NotFoundException("Financial period not found")
        return period

    async def validate_entry_date(
        self,
        organization_id: UUID,
        entry_date: date,
    ) -> PeriodValidationResult:
        """Check if entries are allowed for the given date.

        Returns validation result with details about why entries may be blocked.
        """
        period = await self.get_period_for_date(organization_id, entry_date)

        if not period:
            return PeriodValidationResult(
                allowed=False,
                reason="NO_PERIOD_FOUND",
            )

        # Check if period is closed (hard close)
        if period.is_closed:
            return PeriodValidationResult(
                allowed=False,
                period_id=period.id,
                period_name=period.name,
                reason="PERIOD_CLOSED",
            )

        # Check if period is locked (soft lock)
        if period.is_locked:
            return PeriodValidationResult(
                allowed=False,
                period_id=period.id,
                period_name=period.name,
                reason=f"PERIOD_LOCKED: {period.lock_reason or 'No reason provided'}",
            )

        # Check GST return filed date
        if period.gst_return_filed_date and entry_date <= period.gst_return_filed_date:
            return PeriodValidationResult(
                allowed=False,
                period_id=period.id,
                period_name=period.name,
                reason=f"GST_FILED: Return filed up to {period.gst_return_filed_date}",
            )

        return PeriodValidationResult(
            allowed=True,
            period_id=period.id,
            period_name=period.name,
            reason="OK",
        )

    async def require_entry_allowed(
        self,
        organization_id: UUID,
        entry_date: date,
    ) -> None:
        """Validate that entries are allowed for the date, raise exception if not.

        Use this method in transaction services before creating/updating entries.
        """
        result = await self.validate_entry_date(organization_id, entry_date)

        if not result.allowed:
            if result.reason and result.reason.startswith("PERIOD_LOCKED"):
                raise PeriodLockedError(
                    f"Period {result.period_name} is locked. {result.reason}"
                )
            elif result.reason == "PERIOD_CLOSED":
                raise PeriodLockedError(
                    f"Period {result.period_name} is closed. No entries allowed."
                )
            elif result.reason and result.reason.startswith("GST_FILED"):
                raise PeriodLockedError(
                    f"Cannot create entry on {entry_date}. {result.reason}"
                )
            elif result.reason == "NO_PERIOD_FOUND":
                raise ValidationException(
                    f"No financial period found for date {entry_date}"
                )
            else:
                raise PeriodLockedError(
                    f"Entries not allowed for {entry_date}. Reason: {result.reason}"
                )

    async def lock_period(
        self,
        period_id: UUID,
        reason: str,
        user_id: UUID,
    ) -> FinancialPeriod:
        """Lock a financial period (soft lock - prevents new entries).

        Args:
            period_id: The period to lock
            reason: Lock reason (GST_RETURN_FILED, PERIOD_CLOSE, AUDIT, etc.)
            user_id: User performing the lock
        """
        period = await self.get_period(period_id)

        if period.is_closed:
            raise ValidationException("Period is already closed")

        if period.is_locked:
            raise ValidationException(f"Period is already locked: {period.lock_reason}")

        period.is_locked = True
        period.locked_at = datetime.now(timezone.utc)
        period.locked_by = user_id
        period.lock_reason = reason

        await self.db.flush()
        await self.db.refresh(period)
        return period

    async def unlock_period(
        self,
        period_id: UUID,
        user_id: UUID,
        override_reason: str,
    ) -> FinancialPeriod:
        """Unlock a financial period.

        This should require elevated permissions (SUPER_ADMIN) in the API layer.

        Args:
            period_id: The period to unlock
            user_id: User performing the unlock
            override_reason: Reason for unlocking (for audit trail)
        """
        period = await self.get_period(period_id)

        if period.is_closed:
            raise ValidationException(
                "Cannot unlock a closed period. Contact administrator to reopen."
            )

        if not period.is_locked:
            raise ValidationException("Period is not locked")

        period.is_locked = False
        period.locked_at = None
        period.locked_by = None
        period.lock_reason = None
        # Note: In production, log the unlock reason to audit trail

        await self.db.flush()
        await self.db.refresh(period)
        return period

    async def set_gst_filed_date(
        self,
        period_id: UUID,
        filed_date: date,
        user_id: UUID,
    ) -> FinancialPeriod:
        """Set the GST return filed date for a period.

        Entries on or before this date will be blocked.

        Args:
            period_id: The period to update
            filed_date: Date until which GST return is filed
            user_id: User updating the date
        """
        period = await self.get_period(period_id)

        if filed_date > period.end_date:
            raise ValidationException(
                f"GST filed date cannot be after period end date ({period.end_date})"
            )

        if filed_date < period.start_date:
            raise ValidationException(
                f"GST filed date cannot be before period start date ({period.start_date})"
            )

        period.gst_return_filed_date = filed_date
        period.updated_by = user_id

        await self.db.flush()
        await self.db.refresh(period)
        return period

    async def close_period(
        self,
        period_id: UUID,
        user_id: UUID,
    ) -> FinancialPeriod:
        """Close a financial period (hard close).

        After closing, no modifications are allowed unless reopened by admin.
        """
        period = await self.get_period(period_id)

        if period.is_closed:
            raise ValidationException("Period is already closed")

        period.is_closed = True
        period.closed_at = datetime.now(timezone.utc)
        period.closed_by = user_id
        # Also lock if not already locked
        if not period.is_locked:
            period.is_locked = True
            period.locked_at = datetime.now(timezone.utc)
            period.locked_by = user_id
            period.lock_reason = "PERIOD_CLOSE"

        await self.db.flush()
        await self.db.refresh(period)
        return period

    async def reopen_period(
        self,
        period_id: UUID,
        user_id: UUID,
        reason: str,
    ) -> FinancialPeriod:
        """Reopen a closed period (requires SUPER_ADMIN).

        Args:
            period_id: The period to reopen
            user_id: User performing the reopen
            reason: Reason for reopening (for audit trail)
        """
        period = await self.get_period(period_id)

        if not period.is_closed:
            raise ValidationException("Period is not closed")

        period.is_closed = False
        period.closed_at = None
        period.closed_by = None
        # Keep lock status - admin may want to unlock separately
        # Note: In production, log the reopen reason to audit trail

        await self.db.flush()
        await self.db.refresh(period)
        return period
