"""Repositories for Phase 2 Loan Accounting."""

from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.lending.enums import (
    AccrualStatus,
    AssetClassification,
    DisbursementStatus,
    InstallmentStatus,
    LoanAccountStatus,
    MandateStatus,
    ReceiptStatus,
)
from app.models.lending.loan_account import (
    AssetClassificationHistory,
    Disbursement,
    LoanAccount,
    LoanAccrual,
    LoanAdjustment,
    LoanMandate,
    LoanProvision,
    LoanReceipt,
    ReceiptAllocation,
    RepaymentSchedule,
    ScheduleInstallment,
)
from app.repositories.base import BaseRepository


class LoanAccountRepository(BaseRepository[LoanAccount]):
    """Repository for loan accounts."""

    def __init__(self, db: AsyncSession):
        super().__init__(LoanAccount, db)

    async def get_by_account_number(self, account_number: str) -> LoanAccount | None:
        """Get loan account by account number."""
        query = select(LoanAccount).where(
            LoanAccount.loan_account_number == account_number,
            LoanAccount.is_active == True,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_sanction(self, sanction_id: UUID) -> LoanAccount | None:
        """Get loan account by sanction ID."""
        query = select(LoanAccount).where(
            LoanAccount.sanction_id == sanction_id,
            LoanAccount.is_active == True,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_entity_accounts(
        self,
        entity_id: UUID,
        include_closed: bool = False,
    ) -> list[LoanAccount]:
        """Get all loan accounts for an entity."""
        query = select(LoanAccount).where(
            LoanAccount.entity_id == entity_id,
            LoanAccount.is_active == True,
        )
        if not include_closed:
            query = query.where(LoanAccount.status != LoanAccountStatus.CLOSED)
        query = query.order_by(LoanAccount.account_open_date.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_with_details(self, loan_account_id: UUID) -> LoanAccount | None:
        """Get loan account with related data."""
        query = (
            select(LoanAccount)
            .options(
                selectinload(LoanAccount.entity),
                selectinload(LoanAccount.product),
                selectinload(LoanAccount.sanction),
                selectinload(LoanAccount.disbursements),
                selectinload(LoanAccount.schedules),
                selectinload(LoanAccount.mandates),
            )
            .where(LoanAccount.id == loan_account_id, LoanAccount.is_active == True)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_all_accounts(
        self,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 50,
        include_inactive: bool = False,
        search: str | None = None,
        entity_id: UUID | None = None,
        product_id: UUID | None = None,
        status: LoanAccountStatus | None = None,
        asset_classification: AssetClassification | None = None,
        min_dpd: int | None = None,
        max_dpd: int | None = None,
    ) -> tuple[list[LoanAccount], int]:
        """Get paginated list of loan accounts with filters."""
        query = (
            select(LoanAccount)
            .where(LoanAccount.organization_id == organization_id)
            .options(
                selectinload(LoanAccount.entity),
                selectinload(LoanAccount.product),
            )
        )

        if not include_inactive:
            query = query.where(LoanAccount.is_active == True)

        if search:
            query = query.where(
                or_(
                    LoanAccount.loan_account_number.ilike(f"%{search}%"),
                    LoanAccount.loan_reference_number.ilike(f"%{search}%"),
                )
            )

        if entity_id:
            query = query.where(LoanAccount.entity_id == entity_id)
        if product_id:
            query = query.where(LoanAccount.product_id == product_id)
        if status:
            query = query.where(LoanAccount.status == status)
        if asset_classification:
            query = query.where(LoanAccount.asset_classification == asset_classification)
        if min_dpd is not None:
            query = query.where(LoanAccount.days_past_due >= min_dpd)
        if max_dpd is not None:
            query = query.where(LoanAccount.days_past_due <= max_dpd)

        # Count
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.session.execute(count_query)
        total_count = total.scalar() or 0

        # Data
        query = query.order_by(LoanAccount.created_at.desc()).offset(skip).limit(limit)
        result = await self.session.execute(query)
        accounts = list(result.scalars().all())

        return accounts, total_count

    async def get_npa_accounts(
        self,
        organization_id: UUID,
    ) -> list[LoanAccount]:
        """Get all NPA accounts."""
        query = select(LoanAccount).where(
            LoanAccount.organization_id == organization_id,
            LoanAccount.is_active == True,
            LoanAccount.asset_classification.in_(
                [
                    AssetClassification.NPA,
                    AssetClassification.SUBSTANDARD,
                    AssetClassification.DOUBTFUL_1,
                    AssetClassification.DOUBTFUL_2,
                    AssetClassification.DOUBTFUL_3,
                    AssetClassification.LOSS,
                ]
            ),
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_accounts_for_accrual(
        self,
        organization_id: UUID,
        accrual_date: date,
    ) -> list[LoanAccount]:
        """Get accounts eligible for accrual on given date."""
        query = select(LoanAccount).where(
            LoanAccount.organization_id == organization_id,
            LoanAccount.is_active == True,
            LoanAccount.status == LoanAccountStatus.ACTIVE,
            LoanAccount.principal_outstanding > 0,
            or_(
                LoanAccount.last_accrual_date < accrual_date,
                LoanAccount.last_accrual_date.is_(None),
            ),
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_total_outstanding(
        self,
        organization_id: UUID,
    ) -> Decimal:
        """Get total outstanding for organization."""
        query = select(func.sum(LoanAccount.total_outstanding)).where(
            LoanAccount.organization_id == organization_id,
            LoanAccount.is_active == True,
            LoanAccount.status.in_([LoanAccountStatus.ACTIVE, LoanAccountStatus.DORMANT]),
        )
        result = await self.session.execute(query)
        return result.scalar() or Decimal("0")

    async def generate_account_number(
        self,
        organization_id: UUID,
        prefix: str = "LA",
    ) -> str:
        """Generate unique loan account number."""
        year = date.today().year
        query = select(func.count()).where(
            LoanAccount.organization_id == organization_id,
            LoanAccount.loan_account_number.like(f"%/{prefix}/{year}/%"),
        )
        result = await self.session.execute(query)
        count = (result.scalar() or 0) + 1
        return f"SMFC/{prefix}/{year}/{count:05d}"


class DisbursementRepository(BaseRepository[Disbursement]):
    """Repository for disbursements."""

    def __init__(self, db: AsyncSession):
        super().__init__(Disbursement, db)

    async def get_by_reference(self, reference: str) -> Disbursement | None:
        """Get disbursement by reference number."""
        query = select(Disbursement).where(
            Disbursement.disbursement_reference == reference,
            Disbursement.is_active == True,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_utr(self, utr_number: str) -> Disbursement | None:
        """Get disbursement by UTR number."""
        query = select(Disbursement).where(
            Disbursement.utr_number == utr_number,
            Disbursement.is_active == True,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_loan_disbursements(
        self,
        loan_account_id: UUID,
        include_inactive: bool = False,
    ) -> list[Disbursement]:
        """Get all disbursements for a loan account."""
        query = select(Disbursement).where(Disbursement.loan_account_id == loan_account_id)
        if not include_inactive:
            query = query.where(Disbursement.is_active == True)
        query = query.order_by(Disbursement.disbursement_number)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_pending_disbursements(
        self,
        loan_account_id: UUID,
    ) -> list[Disbursement]:
        """Get pending disbursements for a loan account."""
        query = select(Disbursement).where(
            Disbursement.loan_account_id == loan_account_id,
            Disbursement.is_active == True,
            Disbursement.status.in_([DisbursementStatus.PENDING, DisbursementStatus.APPROVED]),
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_next_disbursement_number(self, loan_account_id: UUID) -> int:
        """Get next disbursement number for a loan account."""
        query = select(func.max(Disbursement.disbursement_number)).where(
            Disbursement.loan_account_id == loan_account_id
        )
        result = await self.session.execute(query)
        max_num = result.scalar() or 0
        return max_num + 1

    async def get_total_disbursed(self, loan_account_id: UUID) -> Decimal:
        """Get total disbursed amount for a loan account."""
        query = select(func.sum(Disbursement.disbursed_amount)).where(
            Disbursement.loan_account_id == loan_account_id,
            Disbursement.is_active == True,
            Disbursement.status == DisbursementStatus.PROCESSED,
        )
        result = await self.session.execute(query)
        return result.scalar() or Decimal("0")


class RepaymentScheduleRepository(BaseRepository[RepaymentSchedule]):
    """Repository for repayment schedules."""

    def __init__(self, db: AsyncSession):
        super().__init__(RepaymentSchedule, db)

    async def get_current_schedule(
        self,
        loan_account_id: UUID,
    ) -> RepaymentSchedule | None:
        """Get current active schedule for a loan account."""
        query = (
            select(RepaymentSchedule)
            .options(selectinload(RepaymentSchedule.installments))
            .where(
                RepaymentSchedule.loan_account_id == loan_account_id,
                RepaymentSchedule.is_active == True,
                RepaymentSchedule.is_current == True,
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_all_schedules(
        self,
        loan_account_id: UUID,
    ) -> list[RepaymentSchedule]:
        """Get all schedules for a loan account."""
        query = (
            select(RepaymentSchedule)
            .where(
                RepaymentSchedule.loan_account_id == loan_account_id,
                RepaymentSchedule.is_active == True,
            )
            .order_by(RepaymentSchedule.schedule_number)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_next_schedule_number(self, loan_account_id: UUID) -> int:
        """Get next schedule number for a loan account."""
        query = select(func.max(RepaymentSchedule.schedule_number)).where(
            RepaymentSchedule.loan_account_id == loan_account_id
        )
        result = await self.session.execute(query)
        max_num = result.scalar() or 0
        return max_num + 1

    async def supersede_current_schedule(
        self,
        loan_account_id: UUID,
        new_schedule_id: UUID,
        supersede_date: date,
    ) -> None:
        """Mark current schedule as superseded."""
        stmt = (
            update(RepaymentSchedule)
            .where(
                RepaymentSchedule.loan_account_id == loan_account_id,
                RepaymentSchedule.is_current == True,
            )
            .values(
                is_current=False,
                superseded_date=supersede_date,
                superseded_by_id=new_schedule_id,
            )
        )
        await self.session.execute(stmt)


class ScheduleInstallmentRepository(BaseRepository[ScheduleInstallment]):
    """Repository for schedule installments."""

    def __init__(self, db: AsyncSession):
        super().__init__(ScheduleInstallment, db)

    async def get_schedule_installments(
        self,
        schedule_id: UUID,
    ) -> list[ScheduleInstallment]:
        """Get all installments for a schedule."""
        query = (
            select(ScheduleInstallment)
            .where(
                ScheduleInstallment.schedule_id == schedule_id,
                ScheduleInstallment.is_active == True,
            )
            .order_by(ScheduleInstallment.installment_number)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_due_installments(
        self,
        schedule_id: UUID,
        as_of_date: date,
    ) -> list[ScheduleInstallment]:
        """Get installments due as of a date."""
        query = (
            select(ScheduleInstallment)
            .where(
                ScheduleInstallment.schedule_id == schedule_id,
                ScheduleInstallment.is_active == True,
                ScheduleInstallment.due_date <= as_of_date,
                ScheduleInstallment.status.in_(
                    [
                        InstallmentStatus.DUE,
                        InstallmentStatus.PARTIALLY_PAID,
                        InstallmentStatus.OVERDUE,
                    ]
                ),
            )
            .order_by(ScheduleInstallment.due_date)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_overdue_installments(
        self,
        schedule_id: UUID,
    ) -> list[ScheduleInstallment]:
        """Get overdue installments for a schedule."""
        query = (
            select(ScheduleInstallment)
            .where(
                ScheduleInstallment.schedule_id == schedule_id,
                ScheduleInstallment.is_active == True,
                ScheduleInstallment.status == InstallmentStatus.OVERDUE,
            )
            .order_by(ScheduleInstallment.due_date)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_next_due_installment(
        self,
        schedule_id: UUID,
    ) -> ScheduleInstallment | None:
        """Get next unpaid installment."""
        query = (
            select(ScheduleInstallment)
            .where(
                ScheduleInstallment.schedule_id == schedule_id,
                ScheduleInstallment.is_active == True,
                ScheduleInstallment.status.in_(
                    [
                        InstallmentStatus.NOT_DUE,
                        InstallmentStatus.DUE,
                        InstallmentStatus.PARTIALLY_PAID,
                        InstallmentStatus.OVERDUE,
                    ]
                ),
            )
            .order_by(ScheduleInstallment.due_date)
            .limit(1)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_oldest_unpaid_date(
        self,
        schedule_id: UUID,
    ) -> date | None:
        """Get oldest unpaid installment date."""
        query = select(func.min(ScheduleInstallment.due_date)).where(
            ScheduleInstallment.schedule_id == schedule_id,
            ScheduleInstallment.is_active == True,
            ScheduleInstallment.status.in_(
                [
                    InstallmentStatus.DUE,
                    InstallmentStatus.PARTIALLY_PAID,
                    InstallmentStatus.OVERDUE,
                ]
            ),
        )
        result = await self.session.execute(query)
        return result.scalar()


class LoanAccrualRepository(BaseRepository[LoanAccrual]):
    """Repository for loan accruals."""

    def __init__(self, db: AsyncSession):
        super().__init__(LoanAccrual, db)

    async def get_loan_accruals(
        self,
        loan_account_id: UUID,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> list[LoanAccrual]:
        """Get accruals for a loan account."""
        query = select(LoanAccrual).where(
            LoanAccrual.loan_account_id == loan_account_id,
            LoanAccrual.is_active == True,
        )
        if from_date:
            query = query.where(LoanAccrual.accrual_date >= from_date)
        if to_date:
            query = query.where(LoanAccrual.accrual_date <= to_date)
        query = query.order_by(LoanAccrual.accrual_date)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_accrual_for_date(
        self,
        loan_account_id: UUID,
        accrual_date: date,
        category: str,
    ) -> LoanAccrual | None:
        """Get accrual for specific date and category."""
        query = select(LoanAccrual).where(
            LoanAccrual.loan_account_id == loan_account_id,
            LoanAccrual.accrual_date == accrual_date,
            LoanAccrual.accrual_category == category,
            LoanAccrual.is_active == True,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_total_accrued(
        self,
        loan_account_id: UUID,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> Decimal:
        """Get total accrued amount."""
        query = select(func.sum(LoanAccrual.accrued_amount)).where(
            LoanAccrual.loan_account_id == loan_account_id,
            LoanAccrual.is_active == True,
            LoanAccrual.status == AccrualStatus.ACCRUED,
        )
        if from_date:
            query = query.where(LoanAccrual.accrual_date >= from_date)
        if to_date:
            query = query.where(LoanAccrual.accrual_date <= to_date)
        result = await self.session.execute(query)
        return Decimal(str(result.scalar() or 0))


class LoanReceiptRepository(BaseRepository[LoanReceipt]):
    """Repository for loan receipts."""

    def __init__(self, db: AsyncSession):
        super().__init__(LoanReceipt, db)

    async def get_by_receipt_number(self, receipt_number: str) -> LoanReceipt | None:
        """Get receipt by receipt number."""
        query = select(LoanReceipt).where(
            LoanReceipt.receipt_number == receipt_number,
            LoanReceipt.is_active == True,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_loan_receipts(
        self,
        loan_account_id: UUID,
        include_inactive: bool = False,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> list[LoanReceipt]:
        """Get all receipts for a loan account."""
        query = select(LoanReceipt).where(LoanReceipt.loan_account_id == loan_account_id)
        if not include_inactive:
            query = query.where(LoanReceipt.is_active == True)
        if from_date:
            query = query.where(LoanReceipt.receipt_date >= from_date)
        if to_date:
            query = query.where(LoanReceipt.receipt_date <= to_date)
        query = query.order_by(LoanReceipt.receipt_date.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_with_allocations(self, receipt_id: UUID) -> LoanReceipt | None:
        """Get receipt with allocations."""
        query = (
            select(LoanReceipt)
            .options(selectinload(LoanReceipt.allocations))
            .where(LoanReceipt.id == receipt_id, LoanReceipt.is_active == True)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_total_collected(
        self,
        loan_account_id: UUID,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> Decimal:
        """Get total collected amount."""
        query = select(func.sum(LoanReceipt.receipt_amount)).where(
            LoanReceipt.loan_account_id == loan_account_id,
            LoanReceipt.is_active == True,
            LoanReceipt.status == ReceiptStatus.ALLOCATED,
            LoanReceipt.bounced == False,
        )
        if from_date:
            query = query.where(LoanReceipt.receipt_date >= from_date)
        if to_date:
            query = query.where(LoanReceipt.receipt_date <= to_date)
        result = await self.session.execute(query)
        return result.scalar() or Decimal("0")

    async def generate_receipt_number(
        self,
        organization_id: UUID,
    ) -> str:
        """Generate unique receipt number."""
        year = date.today().year
        query = select(func.count()).where(
            LoanReceipt.organization_id == organization_id,
            LoanReceipt.receipt_number.like(f"%/RCT/{year}/%"),
        )
        result = await self.session.execute(query)
        count = (result.scalar() or 0) + 1
        return f"SMFC/RCT/{year}/{count:06d}"


class ReceiptAllocationRepository(BaseRepository[ReceiptAllocation]):
    """Repository for receipt allocations."""

    def __init__(self, db: AsyncSession):
        super().__init__(ReceiptAllocation, db)

    async def get_receipt_allocations(
        self,
        receipt_id: UUID,
    ) -> list[ReceiptAllocation]:
        """Get all allocations for a receipt."""
        query = (
            select(ReceiptAllocation)
            .where(
                ReceiptAllocation.receipt_id == receipt_id,
                ReceiptAllocation.is_active == True,
            )
            .order_by(ReceiptAllocation.allocation_sequence)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_installment_allocations(
        self,
        installment_id: UUID,
    ) -> list[ReceiptAllocation]:
        """Get all allocations for an installment."""
        query = select(ReceiptAllocation).where(
            ReceiptAllocation.installment_id == installment_id,
            ReceiptAllocation.is_active == True,
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())


class LoanMandateRepository(BaseRepository[LoanMandate]):
    """Repository for loan mandates."""

    def __init__(self, db: AsyncSession):
        super().__init__(LoanMandate, db)

    async def get_by_reference(self, reference: str) -> LoanMandate | None:
        """Get mandate by reference."""
        query = select(LoanMandate).where(
            LoanMandate.mandate_reference == reference,
            LoanMandate.is_active == True,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_umrn(self, umrn: str) -> LoanMandate | None:
        """Get mandate by UMRN."""
        query = select(LoanMandate).where(
            LoanMandate.umrn == umrn,
            LoanMandate.is_active == True,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_loan_mandates(
        self,
        loan_account_id: UUID,
        include_inactive: bool = False,
    ) -> list[LoanMandate]:
        """Get all mandates for a loan account."""
        query = select(LoanMandate).where(LoanMandate.loan_account_id == loan_account_id)
        if not include_inactive:
            query = query.where(LoanMandate.is_active == True)
        query = query.order_by(LoanMandate.created_at.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_active_mandate(
        self,
        loan_account_id: UUID,
    ) -> LoanMandate | None:
        """Get active mandate for a loan account."""
        query = select(LoanMandate).where(
            LoanMandate.loan_account_id == loan_account_id,
            LoanMandate.is_active == True,
            LoanMandate.status == MandateStatus.ACTIVE,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()


class AssetClassificationHistoryRepository(BaseRepository[AssetClassificationHistory]):
    """Repository for asset classification history."""

    def __init__(self, db: AsyncSession):
        super().__init__(AssetClassificationHistory, db)

    async def get_loan_history(
        self,
        loan_account_id: UUID,
    ) -> list[AssetClassificationHistory]:
        """Get classification history for a loan account."""
        query = (
            select(AssetClassificationHistory)
            .where(
                AssetClassificationHistory.loan_account_id == loan_account_id,
                AssetClassificationHistory.is_active == True,
            )
            .order_by(AssetClassificationHistory.effective_date.desc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_latest_classification(
        self,
        loan_account_id: UUID,
    ) -> AssetClassificationHistory | None:
        """Get latest classification for a loan account."""
        query = (
            select(AssetClassificationHistory)
            .where(
                AssetClassificationHistory.loan_account_id == loan_account_id,
                AssetClassificationHistory.is_active == True,
            )
            .order_by(AssetClassificationHistory.effective_date.desc())
            .limit(1)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()


class LoanProvisionRepository(BaseRepository[LoanProvision]):
    """Repository for loan provisions."""

    def __init__(self, db: AsyncSession):
        super().__init__(LoanProvision, db)

    async def get_loan_provisions(
        self,
        loan_account_id: UUID,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> list[LoanProvision]:
        """Get provisions for a loan account."""
        query = select(LoanProvision).where(
            LoanProvision.loan_account_id == loan_account_id,
            LoanProvision.is_active == True,
        )
        if from_date:
            query = query.where(LoanProvision.provision_date >= from_date)
        if to_date:
            query = query.where(LoanProvision.provision_date <= to_date)
        query = query.order_by(LoanProvision.provision_date.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_latest_provision(
        self,
        loan_account_id: UUID,
    ) -> LoanProvision | None:
        """Get latest provision for a loan account."""
        query = (
            select(LoanProvision)
            .where(
                LoanProvision.loan_account_id == loan_account_id,
                LoanProvision.is_active == True,
            )
            .order_by(LoanProvision.provision_date.desc())
            .limit(1)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_total_provision(
        self,
        organization_id: UUID,
        provision_date: date,
    ) -> Decimal:
        """Get total provision for organization on a date."""
        query = select(func.sum(LoanProvision.provision_required)).where(
            LoanProvision.organization_id == organization_id,
            LoanProvision.provision_date == provision_date,
            LoanProvision.is_active == True,
        )
        result = await self.session.execute(query)
        return result.scalar() or Decimal("0")


class LoanAdjustmentRepository(BaseRepository[LoanAdjustment]):
    """Repository for loan adjustments."""

    def __init__(self, db: AsyncSession):
        super().__init__(LoanAdjustment, db)

    async def get_by_reference(self, reference: str) -> LoanAdjustment | None:
        """Get adjustment by reference."""
        query = select(LoanAdjustment).where(
            LoanAdjustment.adjustment_reference == reference,
            LoanAdjustment.is_active == True,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_loan_adjustments(
        self,
        loan_account_id: UUID,
        include_inactive: bool = False,
    ) -> list[LoanAdjustment]:
        """Get all adjustments for a loan account."""
        query = select(LoanAdjustment).where(LoanAdjustment.loan_account_id == loan_account_id)
        if not include_inactive:
            query = query.where(LoanAdjustment.is_active == True)
        query = query.order_by(LoanAdjustment.effective_date.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def generate_adjustment_reference(
        self,
        loan_account_id: UUID,
    ) -> str:
        """Generate unique adjustment reference."""
        year = date.today().year
        query = select(func.count()).where(
            LoanAdjustment.loan_account_id == loan_account_id,
        )
        result = await self.session.execute(query)
        count = (result.scalar() or 0) + 1
        return f"ADJ/{year}/{count:04d}"
