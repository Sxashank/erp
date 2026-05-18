"""Treasury and ALM repositories for the lending module."""

from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.lending.treasury import (
    ALMAsset,
    ALMLiability,
    ALMPosition,
    Borrowing,
    BorrowingCovenant,
    BorrowingPayment,
    BorrowingSchedule,
    BorrowingTranche,
    ExposureLimit,
    ExposureTracking,
    IRSAnalysis,
    Lender,
)
from app.repositories.base import BaseRepository


class LenderRepository(BaseRepository[Lender]):
    """Repository for Lender model."""

    def __init__(self, session: AsyncSession):
        super().__init__(Lender, session)

    async def get_by_code(self, organization_id: UUID, lender_code: str) -> Lender | None:
        """Get lender by code."""
        query = select(Lender).where(
            and_(
                Lender.organization_id == organization_id,
                Lender.lender_code == lender_code,
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_type(
        self,
        organization_id: UUID,
        lender_type: str,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[Lender], int]:
        """Get lenders by type."""
        query = select(Lender).where(
            and_(
                Lender.organization_id == organization_id,
                Lender.lender_type == lender_type,
                Lender.status == "ACTIVE",
            )
        )
        return await self._paginate(query, skip, limit)

    async def get_active_lenders(
        self,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[Lender], int]:
        """Get all active lenders."""
        base = select(Lender).where(
            and_(
                Lender.organization_id == organization_id,
                Lender.status == "ACTIVE",
            )
        )
        count_q = select(func.count()).select_from(base.subquery())
        total = (await self.session.execute(count_q)).scalar() or 0
        result = await self.session.execute(
            base.order_by(Lender.lender_name).offset(skip).limit(limit)
        )
        return list(result.scalars().all()), total

    async def generate_lender_code(self, organization_id: UUID) -> str:
        """Generate next lender code."""
        query = (
            select(func.count())
            .select_from(Lender)
            .where(Lender.organization_id == organization_id)
        )
        result = await self.session.execute(query)
        count = result.scalar() or 0
        return f"LND/{count + 1:05d}"


class BorrowingRepository(BaseRepository[Borrowing]):
    """Repository for Borrowing model."""

    def __init__(self, session: AsyncSession):
        super().__init__(Borrowing, session)

    async def get_by_number(self, organization_id: UUID, borrowing_number: str) -> Borrowing | None:
        """Get borrowing by number."""
        query = select(Borrowing).where(
            and_(
                Borrowing.organization_id == organization_id,
                Borrowing.borrowing_number == borrowing_number,
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_lender(
        self,
        organization_id: UUID,
        lender_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[Borrowing], int]:
        """Get borrowings by lender."""
        query = (
            select(Borrowing)
            .where(
                and_(
                    Borrowing.organization_id == organization_id,
                    Borrowing.lender_id == lender_id,
                )
            )
            .options(selectinload(Borrowing.lender))
            .order_by(Borrowing.sanction_date.desc())
        )
        return await self._paginate(query, skip, limit)

    async def get_active_borrowings(
        self,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[Borrowing], int]:
        """Get all active borrowings."""
        query = (
            select(Borrowing)
            .where(
                and_(
                    Borrowing.organization_id == organization_id,
                    Borrowing.status.in_(["ACTIVE", "FULLY_DRAWN", "REPAYING"]),
                )
            )
            .options(selectinload(Borrowing.lender))
            .order_by(Borrowing.maturity_date)
        )
        return await self._paginate(query, skip, limit)

    async def list_for_org(
        self,
        organization_id: UUID,
        lender_id: UUID | None = None,
        status: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[Borrowing], int]:
        """Paginated list of all borrowings (regardless of status)."""
        conditions = [Borrowing.organization_id == organization_id]
        if lender_id is not None:
            conditions.append(Borrowing.lender_id == lender_id)
        if status:
            conditions.append(Borrowing.status == status)
        base = select(Borrowing).where(and_(*conditions))
        count_q = select(func.count()).select_from(base.subquery())
        total = (await self.session.execute(count_q)).scalar() or 0
        result = await self.session.execute(
            base.options(selectinload(Borrowing.lender))
            .order_by(Borrowing.sanction_date.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all()), total

    async def get_maturing_borrowings(
        self,
        organization_id: UUID,
        days: int = 90,
    ) -> list[Borrowing]:
        """Get borrowings maturing within specified days."""
        today = date.today()
        end_date = date.today()
        # Calculate end date
        from datetime import timedelta

        end_date = today + timedelta(days=days)

        query = (
            select(Borrowing)
            .where(
                and_(
                    Borrowing.organization_id == organization_id,
                    Borrowing.status.in_(["ACTIVE", "FULLY_DRAWN", "REPAYING"]),
                    Borrowing.maturity_date <= end_date,
                    Borrowing.maturity_date >= today,
                )
            )
            .order_by(Borrowing.maturity_date)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_with_details(self, borrowing_id: UUID) -> Borrowing | None:
        """Get borrowing with related data."""
        query = (
            select(Borrowing)
            .options(
                selectinload(Borrowing.lender),
                selectinload(Borrowing.tranches),
                selectinload(Borrowing.schedule),
                selectinload(Borrowing.covenants),
            )
            .where(Borrowing.borrowing_id == borrowing_id)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def generate_borrowing_number(self, organization_id: UUID, borrowing_type: str) -> str:
        """Generate next borrowing number."""
        year = date.today().year
        query = (
            select(func.count())
            .select_from(Borrowing)
            .where(
                and_(
                    Borrowing.organization_id == organization_id,
                    func.extract("year", Borrowing.created_at) == year,
                )
            )
        )
        result = await self.session.execute(query)
        count = result.scalar() or 0
        type_code = borrowing_type[:2].upper()
        return f"BRW/{type_code}/{year}/{count + 1:05d}"

    async def get_total_outstanding(self, organization_id: UUID) -> Decimal:
        """Get total outstanding across all borrowings."""
        query = select(func.coalesce(func.sum(Borrowing.principal_outstanding), 0)).where(
            and_(
                Borrowing.organization_id == organization_id,
                Borrowing.status.in_(["ACTIVE", "FULLY_DRAWN", "REPAYING"]),
            )
        )
        result = await self.session.execute(query)
        return result.scalar() or Decimal("0")


class BorrowingTrancheRepository(BaseRepository[BorrowingTranche]):
    """Repository for BorrowingTranche model."""

    def __init__(self, session: AsyncSession):
        super().__init__(BorrowingTranche, session)

    async def get_by_borrowing(
        self,
        borrowing_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[BorrowingTranche], int]:
        """Get tranches by borrowing."""
        query = (
            select(BorrowingTranche)
            .where(BorrowingTranche.borrowing_id == borrowing_id)
            .order_by(BorrowingTranche.tranche_number)
        )
        return await self._paginate(query, skip, limit)

    async def get_next_tranche_number(self, borrowing_id: UUID) -> int:
        """Get next tranche number."""
        query = select(func.coalesce(func.max(BorrowingTranche.tranche_number), 0)).where(
            BorrowingTranche.borrowing_id == borrowing_id
        )
        result = await self.session.execute(query)
        return (result.scalar() or 0) + 1


class BorrowingScheduleRepository(BaseRepository[BorrowingSchedule]):
    """Repository for BorrowingSchedule model."""

    def __init__(self, session: AsyncSession):
        super().__init__(BorrowingSchedule, session)

    async def get_by_borrowing(
        self,
        borrowing_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[BorrowingSchedule], int]:
        """Get schedules by borrowing."""
        query = (
            select(BorrowingSchedule)
            .where(BorrowingSchedule.borrowing_id == borrowing_id)
            .order_by(BorrowingSchedule.due_date)
        )
        return await self._paginate(query, skip, limit)

    async def get_upcoming_payments(
        self,
        organization_id: UUID,
        days: int = 30,
    ) -> list[BorrowingSchedule]:
        """Get upcoming borrowing payments."""
        today = date.today()
        from datetime import timedelta

        end_date = today + timedelta(days=days)

        query = (
            select(BorrowingSchedule)
            .join(Borrowing)
            .where(
                and_(
                    Borrowing.organization_id == organization_id,
                    BorrowingSchedule.status.in_(["NOT_DUE", "DUE"]),
                    BorrowingSchedule.due_date >= today,
                    BorrowingSchedule.due_date <= end_date,
                )
            )
            .order_by(BorrowingSchedule.due_date)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_overdue_schedules(self, borrowing_id: UUID) -> list[BorrowingSchedule]:
        """Get overdue schedules for a borrowing."""
        today = date.today()
        query = (
            select(BorrowingSchedule)
            .where(
                and_(
                    BorrowingSchedule.borrowing_id == borrowing_id,
                    BorrowingSchedule.status.in_(["DUE", "NOT_DUE"]),
                    BorrowingSchedule.due_date < today,
                )
            )
            .order_by(BorrowingSchedule.due_date)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())


class BorrowingPaymentRepository(BaseRepository[BorrowingPayment]):
    """Repository for BorrowingPayment model."""

    def __init__(self, session: AsyncSession):
        super().__init__(BorrowingPayment, session)

    async def get_by_borrowing(
        self,
        borrowing_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[BorrowingPayment], int]:
        """Get payments by borrowing."""
        query = (
            select(BorrowingPayment)
            .where(BorrowingPayment.borrowing_id == borrowing_id)
            .order_by(BorrowingPayment.payment_date.desc())
        )
        return await self._paginate(query, skip, limit)

    async def get_total_paid(self, borrowing_id: UUID, payment_type: str | None = None) -> Decimal:
        """Get total amount paid for a borrowing."""
        conditions = [BorrowingPayment.borrowing_id == borrowing_id]
        if payment_type:
            conditions.append(BorrowingPayment.payment_type == payment_type)

        query = select(func.coalesce(func.sum(BorrowingPayment.total_amount), 0)).where(
            and_(*conditions)
        )
        result = await self.session.execute(query)
        return result.scalar() or Decimal("0")


class BorrowingCovenantRepository(BaseRepository[BorrowingCovenant]):
    """Repository for BorrowingCovenant model."""

    def __init__(self, session: AsyncSession):
        super().__init__(BorrowingCovenant, session)

    async def get_by_borrowing(
        self,
        borrowing_id: UUID,
        active_only: bool = True,
    ) -> list[BorrowingCovenant]:
        """Get covenants by borrowing."""
        conditions = [BorrowingCovenant.borrowing_id == borrowing_id]
        if active_only:
            conditions.append(BorrowingCovenant.is_active == True)

        query = select(BorrowingCovenant).where(and_(*conditions))
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_non_compliant(self, organization_id: UUID) -> list[BorrowingCovenant]:
        """Get all non-compliant covenants."""
        query = (
            select(BorrowingCovenant)
            .join(Borrowing)
            .where(
                and_(
                    Borrowing.organization_id == organization_id,
                    BorrowingCovenant.is_active == True,
                    BorrowingCovenant.status == "NON_COMPLIANT",
                )
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())


class ALMPositionRepository(BaseRepository[ALMPosition]):
    """Repository for ALMPosition model."""

    def __init__(self, session: AsyncSession):
        super().__init__(ALMPosition, session)

    async def get_by_date(self, organization_id: UUID, position_date: date) -> ALMPosition | None:
        """Get ALM position by date."""
        query = select(ALMPosition).where(
            and_(
                ALMPosition.organization_id == organization_id,
                ALMPosition.position_date == position_date,
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_latest(self, organization_id: UUID) -> ALMPosition | None:
        """Get latest ALM position."""
        query = (
            select(ALMPosition)
            .where(ALMPosition.organization_id == organization_id)
            .order_by(ALMPosition.position_date.desc())
            .limit(1)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_with_details(self, position_id: UUID) -> ALMPosition | None:
        """Get ALM position with assets and liabilities."""
        query = (
            select(ALMPosition)
            .options(
                selectinload(ALMPosition.assets),
                selectinload(ALMPosition.liabilities),
            )
            .where(ALMPosition.position_id == position_id)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_history(
        self,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 12,
    ) -> tuple[list[ALMPosition], int]:
        """Get ALM position history."""
        query = (
            select(ALMPosition)
            .where(ALMPosition.organization_id == organization_id)
            .order_by(ALMPosition.position_date.desc())
        )
        return await self._paginate(query, skip, limit)


class ALMAssetRepository(BaseRepository[ALMAsset]):
    """Repository for ALMAsset model."""

    def __init__(self, session: AsyncSession):
        super().__init__(ALMAsset, session)

    async def get_by_position(self, position_id: UUID) -> list[ALMAsset]:
        """Get assets by position."""
        query = (
            select(ALMAsset)
            .where(ALMAsset.position_id == position_id)
            .order_by(ALMAsset.alm_bucket)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def delete_by_position(self, position_id: UUID) -> None:
        """Delete all assets for a position."""
        query = select(ALMAsset).where(ALMAsset.position_id == position_id)
        result = await self.session.execute(query)
        for asset in result.scalars().all():
            await self.session.delete(asset)


class ALMLiabilityRepository(BaseRepository[ALMLiability]):
    """Repository for ALMLiability model."""

    def __init__(self, session: AsyncSession):
        super().__init__(ALMLiability, session)

    async def get_by_position(self, position_id: UUID) -> list[ALMLiability]:
        """Get liabilities by position."""
        query = (
            select(ALMLiability)
            .where(ALMLiability.position_id == position_id)
            .order_by(ALMLiability.alm_bucket)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def delete_by_position(self, position_id: UUID) -> None:
        """Delete all liabilities for a position."""
        query = select(ALMLiability).where(ALMLiability.position_id == position_id)
        result = await self.session.execute(query)
        for liability in result.scalars().all():
            await self.session.delete(liability)


class IRSAnalysisRepository(BaseRepository[IRSAnalysis]):
    """Repository for IRSAnalysis model."""

    def __init__(self, session: AsyncSession):
        super().__init__(IRSAnalysis, session)

    async def get_by_date(
        self,
        organization_id: UUID,
        analysis_date: date,
        shock_type: str | None = None,
    ) -> list[IRSAnalysis]:
        """Get IRS analyses by date."""
        conditions = [
            IRSAnalysis.organization_id == organization_id,
            IRSAnalysis.analysis_date == analysis_date,
        ]
        if shock_type:
            conditions.append(IRSAnalysis.shock_type == shock_type)

        query = select(IRSAnalysis).where(and_(*conditions))
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_latest_by_shock(
        self, organization_id: UUID, shock_type: str
    ) -> IRSAnalysis | None:
        """Get latest analysis for a shock type."""
        query = (
            select(IRSAnalysis)
            .where(
                and_(
                    IRSAnalysis.organization_id == organization_id,
                    IRSAnalysis.shock_type == shock_type,
                )
            )
            .order_by(IRSAnalysis.analysis_date.desc())
            .limit(1)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()


class ExposureLimitRepository(BaseRepository[ExposureLimit]):
    """Repository for ExposureLimit model."""

    def __init__(self, session: AsyncSession):
        super().__init__(ExposureLimit, session)

    async def get_by_type_key(
        self,
        organization_id: UUID,
        limit_type: str,
        limit_key: str,
    ) -> ExposureLimit | None:
        """Get exposure limit by type and key."""
        query = select(ExposureLimit).where(
            and_(
                ExposureLimit.organization_id == organization_id,
                ExposureLimit.limit_type == limit_type,
                ExposureLimit.limit_key == limit_key,
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_type(
        self,
        organization_id: UUID,
        limit_type: str,
        active_only: bool = True,
    ) -> list[ExposureLimit]:
        """Get exposure limits by type."""
        conditions = [
            ExposureLimit.organization_id == organization_id,
            ExposureLimit.limit_type == limit_type,
        ]
        if active_only:
            conditions.append(ExposureLimit.is_active == True)

        query = select(ExposureLimit).where(and_(*conditions))
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_breached_limits(self, organization_id: UUID) -> list[ExposureLimit]:
        """Get all breached limits."""
        query = select(ExposureLimit).where(
            and_(
                ExposureLimit.organization_id == organization_id,
                ExposureLimit.is_active == True,
                ExposureLimit.status == "BREACH",
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_near_limit(self, organization_id: UUID) -> list[ExposureLimit]:
        """Get limits approaching threshold."""
        query = select(ExposureLimit).where(
            and_(
                ExposureLimit.organization_id == organization_id,
                ExposureLimit.is_active == True,
                ExposureLimit.status == "NEAR_LIMIT",
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())


class ExposureTrackingRepository(BaseRepository[ExposureTracking]):
    """Repository for ExposureTracking model."""

    def __init__(self, session: AsyncSession):
        super().__init__(ExposureTracking, session)

    async def get_by_limit(
        self,
        limit_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[ExposureTracking], int]:
        """Get exposure tracking records by limit."""
        query = (
            select(ExposureTracking)
            .where(ExposureTracking.limit_id == limit_id)
            .order_by(ExposureTracking.exposure_amount.desc())
        )
        return await self._paginate(query, skip, limit)

    async def get_by_entity(self, entity_id: UUID) -> list[ExposureTracking]:
        """Get exposure tracking records by entity."""
        query = select(ExposureTracking).where(ExposureTracking.entity_id == entity_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def delete_by_limit(self, limit_id: UUID) -> None:
        """Delete all tracking records for a limit."""
        query = select(ExposureTracking).where(ExposureTracking.limit_id == limit_id)
        result = await self.session.execute(query)
        for tracking in result.scalars().all():
            await self.session.delete(tracking)
