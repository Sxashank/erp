"""Borrowing-to-loan fund deployment service."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lending.entity import Entity
from app.models.lending.enums import DisbursementStatus
from app.models.lending.loan_account import Disbursement, LoanAccount
from app.models.lending.treasury import Borrowing, BorrowingTranche, FundDeployment
from app.schemas.lending.treasury import (
    FundDeploymentCreate,
    FundDeploymentSummary,
    FundProfitabilityResponse,
    FundProfitabilityRow,
    FundProfitabilitySummary,
)


class FundDeploymentService:
    """Map borrowed money to deployed corporate loan assets."""

    ACTIVE_STATUSES = ["ACTIVE", "FULLY_DRAWN", "REPAYING", "SANCTIONED"]
    DEPLOYED_STATUS = "ACTIVE"

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_deployment(
        self,
        organization_id: UUID,
        data: FundDeploymentCreate,
        *,
        user_id: UUID | None = None,
    ) -> FundDeployment:
        borrowing = await self._get_borrowing(organization_id, data.borrowing_id)
        loan = await self._get_loan_account(organization_id, data.loan_account_id)
        tranche = await self._get_tranche(data.borrowing_tranche_id, borrowing.id)
        disbursement = await self._get_disbursement(
            data.disbursement_id,
            loan.id,
        )

        available = await self._available_for_borrowing(borrowing.id)
        if data.allocated_amount > available:
            raise ValueError("Deployment exceeds unallocated drawn borrowing amount")

        if disbursement:
            disbursement_available = await self._available_for_disbursement(
                disbursement.id,
                disbursement.disbursed_amount or Decimal("0"),
            )
            if data.allocated_amount > disbursement_available:
                raise ValueError("Deployment exceeds unallocated loan disbursement amount")

        cost_source = data.cost_rate
        if cost_source is None and tranche:
            cost_source = tranche.effective_rate
        cost_rate = _decimal(cost_source or borrowing.effective_rate)
        lending_rate = _decimal(data.lending_rate or loan.current_interest_rate)
        spread_bps = ((lending_rate - cost_rate) * Decimal("100")).quantize(Decimal("0.01"))

        deployment = FundDeployment(
            organization_id=organization_id,
            borrowing_id=borrowing.id,
            borrowing_tranche_id=tranche.id if tranche else None,
            loan_account_id=loan.id,
            disbursement_id=disbursement.id if disbursement else None,
            deployment_reference=await self._next_reference(organization_id),
            allocation_date=data.allocation_date,
            allocated_amount=data.allocated_amount,
            cost_rate=cost_rate,
            lending_rate=lending_rate,
            spread_bps=spread_bps,
            allocation_basis=data.allocation_basis
            or {
                "source": "treasury_fund_deployment",
                "basis": "manual_treasury_mapping",
            },
            status=self.DEPLOYED_STATUS,
            remarks=data.remarks,
            created_by=user_id,
        )
        self.session.add(deployment)
        await self.session.flush()
        return deployment

    async def list_deployments(
        self,
        organization_id: UUID,
        *,
        borrowing_id: UUID | None = None,
        loan_account_id: UUID | None = None,
        status: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[FundDeployment], int]:
        conditions = [FundDeployment.organization_id == organization_id]
        if borrowing_id:
            conditions.append(FundDeployment.borrowing_id == borrowing_id)
        if loan_account_id:
            conditions.append(FundDeployment.loan_account_id == loan_account_id)
        if status:
            conditions.append(FundDeployment.status == status)

        base = select(FundDeployment).where(and_(*conditions))
        total = (
            await self.session.execute(select(func.count()).select_from(base.subquery()))
        ).scalar_one()
        rows = (
            await self.session.execute(
                base.order_by(FundDeployment.allocation_date.desc()).offset(skip).limit(limit)
            )
        ).scalars()
        return list(rows.all()), int(total or 0)

    async def get_summary(self, organization_id: UUID) -> FundDeploymentSummary:
        active_drawn = await self._active_drawn_borrowings(organization_id)
        count, deployed, cost_num, lending_num = (
            await self.session.execute(
                select(
                    func.count(FundDeployment.id),
                    func.coalesce(func.sum(FundDeployment.allocated_amount), 0),
                    func.coalesce(
                        func.sum(FundDeployment.allocated_amount * FundDeployment.cost_rate),
                        0,
                    ),
                    func.coalesce(
                        func.sum(FundDeployment.allocated_amount * FundDeployment.lending_rate),
                        0,
                    ),
                ).where(
                    FundDeployment.organization_id == organization_id,
                    FundDeployment.status == self.DEPLOYED_STATUS,
                )
            )
        ).one()
        deployed_dec = _decimal(deployed)
        weighted_cost = (
            (_decimal(cost_num) / deployed_dec).quantize(Decimal("0.01"))
            if deployed_dec > 0
            else Decimal("0")
        )
        weighted_lending = (
            (_decimal(lending_num) / deployed_dec).quantize(Decimal("0.01"))
            if deployed_dec > 0
            else Decimal("0")
        )
        return FundDeploymentSummary(
            mapped_deployments=int(count or 0),
            deployed_amount=deployed_dec,
            active_drawn_borrowings=active_drawn,
            unmapped_drawn_borrowings=max(active_drawn - deployed_dec, Decimal("0")),
            weighted_cost_rate=weighted_cost,
            weighted_lending_rate=weighted_lending,
            weighted_spread_bps=((weighted_lending - weighted_cost) * Decimal("100")).quantize(
                Decimal("0.01")
            ),
        )

    async def get_profitability(
        self,
        organization_id: UUID,
        *,
        limit: int = 50,
    ) -> FundProfitabilityResponse:
        amount = func.coalesce(func.sum(FundDeployment.allocated_amount), 0)
        cost_num = func.coalesce(
            func.sum(FundDeployment.allocated_amount * FundDeployment.cost_rate),
            0,
        )
        lending_num = func.coalesce(
            func.sum(FundDeployment.allocated_amount * FundDeployment.lending_rate),
            0,
        )
        rows = (
            await self.session.execute(
                select(
                    LoanAccount.id,
                    LoanAccount.loan_account_number,
                    Entity.legal_name,
                    func.count(FundDeployment.id),
                    amount,
                    cost_num,
                    lending_num,
                )
                .join(LoanAccount, LoanAccount.id == FundDeployment.loan_account_id)
                .join(Entity, Entity.id == LoanAccount.entity_id)
                .where(
                    FundDeployment.organization_id == organization_id,
                    FundDeployment.status == self.DEPLOYED_STATUS,
                )
                .group_by(LoanAccount.id, LoanAccount.loan_account_number, Entity.legal_name)
                .order_by(amount.desc())
                .limit(limit)
            )
        ).all()

        items: list[FundProfitabilityRow] = []
        total_deployed = Decimal("0")
        total_cost_num = Decimal("0")
        total_lending_num = Decimal("0")
        for (
            loan_account_id,
            loan_account_number,
            entity_name,
            deployment_count,
            deployed,
            row_cost_num,
            row_lending_num,
        ) in rows:
            deployed_dec = _decimal(deployed)
            cost_rate = _weighted_rate(row_cost_num, deployed_dec)
            lending_rate = _weighted_rate(row_lending_num, deployed_dec)
            annual_income = _annual_interest(deployed_dec, lending_rate)
            annual_expense = _annual_interest(deployed_dec, cost_rate)
            items.append(
                FundProfitabilityRow(
                    loan_account_id=loan_account_id,
                    loan_account_number=loan_account_number,
                    entity_name=entity_name,
                    deployment_count=int(deployment_count or 0),
                    deployed_amount=deployed_dec,
                    weighted_cost_rate=cost_rate,
                    weighted_lending_rate=lending_rate,
                    spread_bps=_spread_bps(lending_rate, cost_rate),
                    estimated_annual_interest_income=annual_income,
                    estimated_annual_interest_expense=annual_expense,
                    estimated_annual_nii=annual_income - annual_expense,
                )
            )
            total_deployed += deployed_dec
            total_cost_num += _decimal(row_cost_num)
            total_lending_num += _decimal(row_lending_num)

        total_cost_rate = _weighted_rate(total_cost_num, total_deployed)
        total_lending_rate = _weighted_rate(total_lending_num, total_deployed)
        total_income = _annual_interest(total_deployed, total_lending_rate)
        total_expense = _annual_interest(total_deployed, total_cost_rate)
        return FundProfitabilityResponse(
            summary=FundProfitabilitySummary(
                mapped_loans=len(items),
                deployed_amount=total_deployed,
                weighted_cost_rate=total_cost_rate,
                weighted_lending_rate=total_lending_rate,
                weighted_spread_bps=_spread_bps(total_lending_rate, total_cost_rate),
                estimated_annual_interest_income=total_income,
                estimated_annual_interest_expense=total_expense,
                estimated_annual_nii=total_income - total_expense,
            ),
            rows=items,
        )

    async def _get_borrowing(self, organization_id: UUID, borrowing_id: UUID) -> Borrowing:
        borrowing = (
            await self.session.execute(
                select(Borrowing).where(
                    Borrowing.id == borrowing_id,
                    Borrowing.organization_id == organization_id,
                    Borrowing.status.in_(self.ACTIVE_STATUSES),
                )
            )
        ).scalar_one_or_none()
        if not borrowing:
            raise ValueError("Borrowing is not available for fund deployment")
        return borrowing

    async def _get_loan_account(
        self,
        organization_id: UUID,
        loan_account_id: UUID,
    ) -> LoanAccount:
        loan = (
            await self.session.execute(
                select(LoanAccount).where(
                    LoanAccount.id == loan_account_id,
                    LoanAccount.organization_id == organization_id,
                )
            )
        ).scalar_one_or_none()
        if not loan:
            raise ValueError("Loan account not found for this organization")
        return loan

    async def _get_tranche(
        self,
        tranche_id: UUID | None,
        borrowing_id: UUID,
    ) -> BorrowingTranche | None:
        if not tranche_id:
            return None
        tranche = (
            await self.session.execute(
                select(BorrowingTranche).where(
                    BorrowingTranche.id == tranche_id,
                    BorrowingTranche.borrowing_id == borrowing_id,
                    BorrowingTranche.status.in_(["DISBURSED", "ACTIVE", "APPROVED"]),
                )
            )
        ).scalar_one_or_none()
        if not tranche:
            raise ValueError("Borrowing tranche is not valid for deployment")
        return tranche

    async def _get_disbursement(
        self,
        disbursement_id: UUID | None,
        loan_account_id: UUID,
    ) -> Disbursement | None:
        if not disbursement_id:
            return None
        disbursement = (
            await self.session.execute(
                select(Disbursement).where(
                    Disbursement.id == disbursement_id,
                    Disbursement.loan_account_id == loan_account_id,
                    Disbursement.status == DisbursementStatus.PROCESSED,
                    Disbursement.disbursed_amount.is_not(None),
                )
            )
        ).scalar_one_or_none()
        if not disbursement:
            raise ValueError("Disbursement is not processed for this loan account")
        return disbursement

    async def _available_for_borrowing(self, borrowing_id: UUID) -> Decimal:
        borrowing = (
            await self.session.execute(select(Borrowing).where(Borrowing.id == borrowing_id))
        ).scalar_one()
        deployed = (
            await self.session.execute(
                select(func.coalesce(func.sum(FundDeployment.allocated_amount), 0)).where(
                    FundDeployment.borrowing_id == borrowing_id,
                    FundDeployment.status == self.DEPLOYED_STATUS,
                )
            )
        ).scalar_one()
        return max(_decimal(borrowing.drawn_amount) - _decimal(deployed), Decimal("0"))

    async def _available_for_disbursement(
        self,
        disbursement_id: UUID,
        disbursed_amount: Decimal,
    ) -> Decimal:
        deployed = (
            await self.session.execute(
                select(func.coalesce(func.sum(FundDeployment.allocated_amount), 0)).where(
                    FundDeployment.disbursement_id == disbursement_id,
                    FundDeployment.status == self.DEPLOYED_STATUS,
                )
            )
        ).scalar_one()
        return max(_decimal(disbursed_amount) - _decimal(deployed), Decimal("0"))

    async def _active_drawn_borrowings(self, organization_id: UUID) -> Decimal:
        amount = (
            await self.session.execute(
                select(func.coalesce(func.sum(Borrowing.drawn_amount), 0)).where(
                    Borrowing.organization_id == organization_id,
                    Borrowing.status.in_(self.ACTIVE_STATUSES),
                )
            )
        ).scalar_one()
        return _decimal(amount)

    async def _next_reference(self, organization_id: UUID) -> str:
        count = (
            await self.session.execute(
                select(func.count(FundDeployment.id)).where(
                    FundDeployment.organization_id == organization_id
                )
            )
        ).scalar_one()
        return f"FDM/{int(count or 0) + 1:06d}"


def _decimal(value: object) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value or "0"))


def _weighted_rate(numerator: object, amount: Decimal) -> Decimal:
    if amount <= 0:
        return Decimal("0")
    return (_decimal(numerator) / amount).quantize(Decimal("0.01"))


def _spread_bps(lending_rate: Decimal, cost_rate: Decimal) -> Decimal:
    return ((lending_rate - cost_rate) * Decimal("100")).quantize(Decimal("0.01"))


def _annual_interest(amount: Decimal, rate: Decimal) -> Decimal:
    return ((amount * rate) / Decimal("100")).quantize(Decimal("0.01"))
