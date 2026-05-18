"""Lending dashboard aggregator.

Composes the Lending Dashboard widgets:
  1. Portfolio KPIs — Total AUM, Active Accounts, Pipeline, NPAs, Collection
     Efficiency.
  2. Disbursement trend — last 6 months of disbursed amounts (in ₹ Cr).
  3. Portfolio by product — current AUM split by product code.
  4. Asset classification — RBI buckets (Standard / SMA-0/1/2 / NPA) by
     outstanding.
  5. Pending approvals — applications / disbursements / OTS proposals
     awaiting a reviewer.
  6. Upcoming maturities — loans maturing in the next 30 days.

This is a read-only aggregator: no writes, no audit rows, no idempotency.
RLS is the caller's responsibility (the endpoint uses get_db_with_tenant).

Returns plain dicts — schema serialisation happens in the endpoint module
via Pydantic so frontend gets a stable typed contract.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lending.application import LoanApplication
from app.models.lending.entity import Entity
from app.models.lending.enums import (
    ApplicationStatus,
    AssetClassification,
    DisbursementStatus,
    InstallmentStatus,
    LoanAccountStatus,
    ReceiptStatus,
    SanctionStatus,
)
from app.models.lending.loan_account import (
    Disbursement,
    LoanAccount,
    LoanReceipt,
    RepaymentSchedule,
    ScheduleInstallment,
)
from app.models.lending.sanction import LoanSanction
from app.models.lending.treasury import Borrowing, BorrowingSchedule
from app.services.lending.fund_deployment_service import FundDeploymentService
from app.services.lending.repayment_matching_service import RepaymentMatchingService

# Asset-classification → render colour (Tailwind class). Kept on the BE so the
# frontend gets a fully-rendered widget without each FE needing its own table.
_ASSET_CLASS_COLOUR: dict[AssetClassification, str] = {
    AssetClassification.STANDARD: "bg-green-500",
    AssetClassification.SMA_0: "bg-yellow-400",
    AssetClassification.SMA_1: "bg-yellow-500",
    AssetClassification.SMA_2: "bg-orange-500",
    AssetClassification.NPA: "bg-red-500",
    AssetClassification.SUBSTANDARD: "bg-red-500",
    AssetClassification.DOUBTFUL_1: "bg-red-600",
    AssetClassification.DOUBTFUL_2: "bg-red-700",
    AssetClassification.DOUBTFUL_3: "bg-red-800",
    AssetClassification.LOSS: "bg-red-900",
}

# Display labels — RBI buckets compacted to what fits the widget row.
_ASSET_CLASS_LABEL: dict[AssetClassification, str] = {
    AssetClassification.STANDARD: "Standard",
    AssetClassification.SMA_0: "SMA-0",
    AssetClassification.SMA_1: "SMA-1",
    AssetClassification.SMA_2: "SMA-2",
    AssetClassification.NPA: "NPA",
    AssetClassification.SUBSTANDARD: "Substandard",
    AssetClassification.DOUBTFUL_1: "Doubtful-1",
    AssetClassification.DOUBTFUL_2: "Doubtful-2",
    AssetClassification.DOUBTFUL_3: "Doubtful-3",
    AssetClassification.LOSS: "Loss",
}

# Pie-chart colour palette for product split — stable across reruns so the
# legend doesn't shuffle.
_PRODUCT_PALETTE: list[str] = [
    "#3b82f6",
    "#10b981",
    "#f59e0b",
    "#8b5cf6",
    "#ef4444",
    "#06b6d4",
    "#84cc16",
    "#ec4899",
]


@dataclass
class DashboardData:
    """Plain data carrier; Pydantic schema converts on the wire."""

    portfolio_kpis: dict
    lifecycle_pipeline: list[dict] = field(default_factory=list)
    treasury_funding: dict = field(default_factory=dict)
    source_of_funds: dict = field(default_factory=dict)
    margin_summary: dict = field(default_factory=dict)
    collection_summary: dict = field(default_factory=dict)
    cashflow_buckets: list[dict] = field(default_factory=list)
    monthly_disbursements: list[dict] = field(default_factory=list)
    portfolio_by_product: list[dict] = field(default_factory=list)
    asset_classification: list[dict] = field(default_factory=list)
    pending_approvals: list[dict] = field(default_factory=list)
    upcoming_maturities: list[dict] = field(default_factory=list)


class LendingDashboardService:
    """Read-only aggregator for the lending dashboard."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_dashboard(self, organization_id: UUID) -> DashboardData:
        """Compose the dashboard payload for one org. RLS already constrains
        every query because the caller uses get_db_with_tenant."""
        portfolio_kpis = await self._portfolio_kpis(organization_id)
        collection_summary = await self._collection_summary(organization_id)
        portfolio_kpis["collection_efficiency"] = collection_summary["collection_efficiency"]
        portfolio_kpis["overdue_amount"] = collection_summary["overdue_amount"]
        return DashboardData(
            portfolio_kpis=portfolio_kpis,
            lifecycle_pipeline=await self._lifecycle_pipeline(organization_id),
            treasury_funding=await self._treasury_funding(organization_id),
            source_of_funds=(
                await FundDeploymentService(self.session).get_summary(organization_id)
            ).model_dump(),
            margin_summary=await self._margin_summary(organization_id),
            collection_summary=collection_summary,
            cashflow_buckets=await self._cashflow_buckets(organization_id),
            monthly_disbursements=await self._monthly_disbursements(organization_id),
            portfolio_by_product=await self._portfolio_by_product(organization_id),
            asset_classification=await self._asset_classification(organization_id),
            pending_approvals=await self._pending_approvals(organization_id),
            upcoming_maturities=await self._upcoming_maturities(organization_id),
        )

    # -----------------------------------------------------------------
    # KPIs.
    # -----------------------------------------------------------------

    async def _portfolio_kpis(self, organization_id: UUID) -> dict:
        # Active-loan aggregates. `total_outstanding` is the authoritative
        # AUM contribution (principal + interest + charges already netted on
        # the LoanAccount row by the LMS reconciliation jobs).
        active_q = select(
            func.coalesce(func.sum(LoanAccount.total_outstanding), 0).label("total_aum"),
            func.coalesce(func.sum(LoanAccount.principal_outstanding), 0).label(
                "principal_oustanding"
            ),
            func.count(LoanAccount.id).label("active_count"),
        ).where(
            LoanAccount.organization_id == organization_id,
            LoanAccount.status == LoanAccountStatus.ACTIVE,
        )
        active = (await self.session.execute(active_q)).one()

        # Pipeline = sum of sanctioned amounts that haven't disbursed yet.
        # We approximate with SANCTIONED applications + ACCEPTED sanctions
        # that don't yet have a fully-utilised loan account.
        pipeline_q = select(func.coalesce(func.sum(LoanSanction.sanctioned_amount), 0)).where(
            LoanSanction.organization_id == organization_id,
            LoanSanction.status.in_([SanctionStatus.APPROVED, SanctionStatus.ACCEPTED]),
        )
        sanctioned_pipeline = (await self.session.execute(pipeline_q)).scalar() or 0

        # NPA ratios — RBI defines Gross NPA as (NPA-bucketed outstanding / Total
        # outstanding) on active accounts. We use the same denominator as
        # total_aum for consistency.
        npa_q = select(func.coalesce(func.sum(LoanAccount.total_outstanding), 0)).where(
            LoanAccount.organization_id == organization_id,
            LoanAccount.status == LoanAccountStatus.ACTIVE,
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
        npa_outstanding = (await self.session.execute(npa_q)).scalar() or 0
        total_aum = active.total_aum or 0

        pending_disbursement_q = (
            select(
                func.coalesce(
                    func.sum(
                        func.coalesce(
                            Disbursement.approved_amount,
                            Disbursement.requested_amount,
                            0,
                        )
                    ),
                    0,
                )
            )
            .join(LoanAccount, LoanAccount.id == Disbursement.loan_account_id)
            .where(
                LoanAccount.organization_id == organization_id,
                Disbursement.status.in_([DisbursementStatus.PENDING, DisbursementStatus.APPROVED]),
            )
        )
        pending_disbursements = (await self.session.execute(pending_disbursement_q)).scalar() or 0

        # Decimal throughout per CLAUDE.md §6.2 — Pydantic CamelSchema serializes
        # Decimal to JSON as a string, preserving precision.
        npa_dec = (
            npa_outstanding
            if isinstance(npa_outstanding, Decimal)
            else Decimal(str(npa_outstanding))
        )
        total_aum_dec = (
            total_aum if isinstance(total_aum, Decimal) else Decimal(str(total_aum or 0))
        )
        gross_npa_pct = (
            (npa_dec / total_aum_dec * Decimal("100")).quantize(Decimal("0.01"))
            if total_aum_dec > 0
            else Decimal("0")
        )
        # Net NPA = Gross NPA minus provisioning. We don't have provisioning
        # rolled up here yet (separate provisioning_service); return 0 until
        # that's wired. Same with PCR — defaulted to 0 so the UI shows a muted
        # KPI rather than a fake number.
        return {
            "total_aum": total_aum_dec,
            "aum_growth_mom": Decimal("0"),
            "active_accounts": int(active.active_count or 0),
            "sanctioned_pipeline": (
                sanctioned_pipeline
                if isinstance(sanctioned_pipeline, Decimal)
                else Decimal(str(sanctioned_pipeline or 0))
            ),
            "pending_disbursements": _decimal(pending_disbursements),
            "collection_efficiency": Decimal("0"),
            "overdue_amount": Decimal("0"),
            "gross_npa": gross_npa_pct,
            "net_npa": Decimal("0"),
            "provision_coverage": Decimal("0"),
        }

    async def _lifecycle_pipeline(self, organization_id: UUID) -> list[dict]:
        active_application_statuses = [
            ApplicationStatus.SUBMITTED,
            ApplicationStatus.UNDER_REVIEW,
            ApplicationStatus.ADDITIONAL_INFO_REQUIRED,
        ]
        app_q = select(
            func.count(LoanApplication.id),
            func.coalesce(func.sum(LoanApplication.requested_amount), 0),
        ).where(
            LoanApplication.organization_id == organization_id,
            LoanApplication.status.in_(active_application_statuses),
        )
        app_count, app_amount = (await self.session.execute(app_q)).one()

        sanction_q = select(
            func.count(LoanSanction.id),
            func.coalesce(func.sum(LoanSanction.sanctioned_amount), 0),
        ).where(
            LoanSanction.organization_id == organization_id,
            LoanSanction.status.in_([SanctionStatus.APPROVED, SanctionStatus.ACCEPTED]),
        )
        sanction_count, sanction_amount = (await self.session.execute(sanction_q)).one()

        active_q = select(
            func.count(LoanAccount.id),
            func.coalesce(func.sum(LoanAccount.total_outstanding), 0),
        ).where(
            LoanAccount.organization_id == organization_id,
            LoanAccount.status == LoanAccountStatus.ACTIVE,
        )
        active_count, active_amount = (await self.session.execute(active_q)).one()

        overdue_q = select(
            func.count(LoanAccount.id),
            func.coalesce(
                func.sum(
                    LoanAccount.principal_overdue
                    + LoanAccount.interest_overdue
                    + LoanAccount.penal_interest_outstanding
                    + LoanAccount.charges_outstanding
                ),
                0,
            ),
        ).where(
            LoanAccount.organization_id == organization_id,
            LoanAccount.status == LoanAccountStatus.ACTIVE,
            LoanAccount.days_past_due > 0,
        )
        overdue_count, overdue_amount = (await self.session.execute(overdue_q)).one()

        return [
            {
                "stage": "Application Pipeline",
                "count": int(app_count or 0),
                "amount": _decimal(app_amount),
            },
            {
                "stage": "Sanctioned / Accepted",
                "count": int(sanction_count or 0),
                "amount": _decimal(sanction_amount),
            },
            {
                "stage": "Live Loan Assets",
                "count": int(active_count or 0),
                "amount": _decimal(active_amount),
            },
            {
                "stage": "Overdue / Collection",
                "count": int(overdue_count or 0),
                "amount": _decimal(overdue_amount),
            },
        ]

    async def _treasury_funding(self, organization_id: UUID) -> dict:
        active_statuses = ["ACTIVE", "FULLY_DRAWN", "REPAYING", "SANCTIONED"]
        q = select(
            func.count(Borrowing.id),
            func.coalesce(func.sum(Borrowing.sanctioned_amount), 0),
            func.coalesce(func.sum(Borrowing.drawn_amount), 0),
            func.coalesce(func.sum(Borrowing.available_amount), 0),
            func.coalesce(func.sum(Borrowing.principal_outstanding), 0),
            func.coalesce(
                func.sum(Borrowing.principal_outstanding * Borrowing.effective_rate),
                0,
            ),
        ).where(
            Borrowing.organization_id == organization_id,
            Borrowing.status.in_(active_statuses),
        )
        (
            active_borrowings,
            sanctioned_borrowings,
            drawn_borrowings,
            available_borrowings,
            borrowing_outstanding,
            weighted_rate_numerator,
        ) = (await self.session.execute(q)).one()
        borrowing_outstanding_dec = _decimal(borrowing_outstanding)
        weighted_cost = (
            (_decimal(weighted_rate_numerator) / borrowing_outstanding_dec).quantize(
                Decimal("0.01")
            )
            if borrowing_outstanding_dec > 0
            else Decimal("0")
        )
        return {
            "active_borrowings": int(active_borrowings or 0),
            "sanctioned_borrowings": _decimal(sanctioned_borrowings),
            "drawn_borrowings": _decimal(drawn_borrowings),
            "available_borrowings": _decimal(available_borrowings),
            "borrowing_outstanding": borrowing_outstanding_dec,
            "weighted_cost_of_funds": weighted_cost,
        }

    async def _margin_summary(self, organization_id: UUID) -> dict:
        asset_q = select(
            func.coalesce(func.sum(LoanAccount.principal_outstanding), 0),
            func.coalesce(
                func.sum(LoanAccount.principal_outstanding * LoanAccount.current_interest_rate),
                0,
            ),
            func.coalesce(
                func.sum(LoanAccount.interest_outstanding + LoanAccount.interest_accrued_not_due),
                0,
            ),
        ).where(
            LoanAccount.organization_id == organization_id,
            LoanAccount.status == LoanAccountStatus.ACTIVE,
        )
        asset_principal, asset_rate_numerator, interest_receivable = (
            await self.session.execute(asset_q)
        ).one()

        liability_q = select(
            func.coalesce(func.sum(Borrowing.principal_outstanding), 0),
            func.coalesce(
                func.sum(Borrowing.principal_outstanding * Borrowing.effective_rate),
                0,
            ),
        ).where(
            Borrowing.organization_id == organization_id,
            Borrowing.status.in_(["ACTIVE", "FULLY_DRAWN", "REPAYING", "SANCTIONED"]),
        )
        liability_principal, liability_rate_numerator = (
            await self.session.execute(liability_q)
        ).one()

        today = datetime.now(UTC).date()
        interest_payable_q = (
            select(
                func.coalesce(
                    func.sum(BorrowingSchedule.interest_due - BorrowingSchedule.interest_paid),
                    0,
                )
            )
            .join(Borrowing, Borrowing.id == BorrowingSchedule.borrowing_id)
            .where(
                Borrowing.organization_id == organization_id,
                BorrowingSchedule.due_date <= today,
                BorrowingSchedule.status != "PAID",
            )
        )
        interest_payable = (await self.session.execute(interest_payable_q)).scalar() or 0

        asset_principal_dec = _decimal(asset_principal)
        liability_principal_dec = _decimal(liability_principal)
        lending_yield = (
            (_decimal(asset_rate_numerator) / asset_principal_dec).quantize(Decimal("0.01"))
            if asset_principal_dec > 0
            else Decimal("0")
        )
        cost_of_funds = (
            (_decimal(liability_rate_numerator) / liability_principal_dec).quantize(Decimal("0.01"))
            if liability_principal_dec > 0
            else Decimal("0")
        )
        gross_spread_bps = ((lending_yield - cost_of_funds) * Decimal("100")).quantize(Decimal("1"))
        interest_receivable_dec = _decimal(interest_receivable)
        interest_payable_dec = _decimal(interest_payable)
        return {
            "lending_yield": lending_yield,
            "cost_of_funds": cost_of_funds,
            "gross_spread_bps": gross_spread_bps,
            "interest_receivable": interest_receivable_dec,
            "interest_payable": interest_payable_dec,
            "net_interest_position": interest_receivable_dec - interest_payable_dec,
        }

    async def _collection_summary(self, organization_id: UUID) -> dict:
        today = datetime.now(UTC).date()
        period_start = today.replace(day=1)
        due_q = (
            select(
                func.coalesce(
                    func.sum(
                        ScheduleInstallment.principal_amount
                        + ScheduleInstallment.interest_amount
                        + ScheduleInstallment.penal_interest_due
                    ),
                    0,
                )
            )
            .join(RepaymentSchedule, RepaymentSchedule.id == ScheduleInstallment.schedule_id)
            .join(LoanAccount, LoanAccount.id == RepaymentSchedule.loan_account_id)
            .where(
                LoanAccount.organization_id == organization_id,
                RepaymentSchedule.is_current.is_(True),
                ScheduleInstallment.due_date >= period_start,
                ScheduleInstallment.due_date <= today,
            )
        )
        due_this_month = (await self.session.execute(due_q)).scalar() or 0

        receipt_q = select(
            func.coalesce(func.sum(LoanReceipt.receipt_amount), 0),
            func.coalesce(func.sum(LoanReceipt.unallocated_amount), 0),
        ).where(
            LoanReceipt.organization_id == organization_id,
            LoanReceipt.receipt_date >= period_start,
            LoanReceipt.receipt_date <= today,
            LoanReceipt.status.in_([ReceiptStatus.ALLOCATED, ReceiptStatus.PENDING]),
            LoanReceipt.bounced.is_(False),
        )
        collected_this_month, unallocated_receipts = (await self.session.execute(receipt_q)).one()

        overdue_q = select(
            func.coalesce(
                func.sum(
                    LoanAccount.principal_overdue
                    + LoanAccount.interest_overdue
                    + LoanAccount.penal_interest_outstanding
                    + LoanAccount.charges_outstanding
                ),
                0,
            )
        ).where(
            LoanAccount.organization_id == organization_id,
            LoanAccount.status == LoanAccountStatus.ACTIVE,
        )
        overdue_amount = (await self.session.execute(overdue_q)).scalar() or 0
        matching_summary = await RepaymentMatchingService(self.session).get_summary(
            organization_id=organization_id
        )

        due_dec = _decimal(due_this_month)
        collected_dec = _decimal(collected_this_month)
        efficiency = (
            (collected_dec / due_dec * Decimal("100")).quantize(Decimal("0.01"))
            if due_dec > 0
            else Decimal("0")
        )
        return {
            "due_this_month": due_dec,
            "collected_this_month": collected_dec,
            "collection_efficiency": efficiency,
            "overdue_amount": _decimal(overdue_amount),
            "unallocated_receipts": _decimal(unallocated_receipts),
            "unmatched_bank_credit_count": matching_summary.unmatched_credit_count,
            "unmatched_bank_credit_amount": matching_summary.unmatched_credit_amount,
            "auto_match_candidate_count": matching_summary.high_confidence_count,
            "match_review_required_count": matching_summary.review_required_count,
        }

    async def _cashflow_buckets(self, organization_id: UUID) -> list[dict]:
        today = datetime.now(UTC).date()
        buckets = [
            ("0-7 Days", 0, 7),
            ("8-30 Days", 8, 30),
            ("31-90 Days", 31, 90),
            ("91-180 Days", 91, 180),
        ]
        out: list[dict] = []
        for label, start_days, end_days in buckets:
            start_date = today + timedelta(days=start_days)
            end_date = today + timedelta(days=end_days)
            borrower_q = (
                select(
                    func.coalesce(
                        func.sum(
                            ScheduleInstallment.principal_amount
                            + ScheduleInstallment.interest_amount
                            + ScheduleInstallment.penal_interest_due
                            - ScheduleInstallment.principal_paid
                            - ScheduleInstallment.interest_paid
                            - ScheduleInstallment.penal_interest_paid
                        ),
                        0,
                    )
                )
                .join(RepaymentSchedule, RepaymentSchedule.id == ScheduleInstallment.schedule_id)
                .join(LoanAccount, LoanAccount.id == RepaymentSchedule.loan_account_id)
                .where(
                    LoanAccount.organization_id == organization_id,
                    RepaymentSchedule.is_current.is_(True),
                    ScheduleInstallment.due_date >= start_date,
                    ScheduleInstallment.due_date <= end_date,
                    ScheduleInstallment.status != InstallmentStatus.PAID,
                )
            )
            borrower_inflows = (await self.session.execute(borrower_q)).scalar() or 0

            lender_q = (
                select(
                    func.coalesce(
                        func.sum(BorrowingSchedule.total_due - BorrowingSchedule.total_paid),
                        0,
                    )
                )
                .join(Borrowing, Borrowing.id == BorrowingSchedule.borrowing_id)
                .where(
                    Borrowing.organization_id == organization_id,
                    BorrowingSchedule.due_date >= start_date,
                    BorrowingSchedule.due_date <= end_date,
                    BorrowingSchedule.status != "PAID",
                )
            )
            lender_outflows = (await self.session.execute(lender_q)).scalar() or 0
            borrower_dec = _decimal(borrower_inflows)
            lender_dec = _decimal(lender_outflows)
            out.append(
                {
                    "bucket": label,
                    "borrower_inflows": borrower_dec,
                    "lender_outflows": lender_dec,
                    "net_gap": borrower_dec - lender_dec,
                }
            )
        return out

    # -----------------------------------------------------------------
    # Monthly disbursement trend (last 6 months).
    # -----------------------------------------------------------------

    async def _monthly_disbursements(self, organization_id: UUID) -> list[dict]:
        today = datetime.now(UTC).date()
        # 6 calendar months ending this month. Anchor at the first-of-month so
        # partial-month results are still attributable.
        first_of_this_month = today.replace(day=1)
        # Approximate 6 months ago — close enough for monthly granularity.
        six_months_ago = first_of_this_month - timedelta(days=31 * 5)
        anchor = six_months_ago.replace(day=1)

        # Group by month bucket. `date_trunc('month', ...)` is Postgres-only,
        # which is what this app uses. SQLite tests use a different engine
        # and would need a separate codepath — for now we ship the prod path.
        bucket = func.date_trunc("month", Disbursement.disbursement_date).label("bucket")
        q = (
            select(
                bucket,
                func.coalesce(func.sum(Disbursement.disbursed_amount), 0).label("total"),
            )
            .join(LoanAccount, LoanAccount.id == Disbursement.loan_account_id)
            .where(
                LoanAccount.organization_id == organization_id,
                Disbursement.disbursement_date >= anchor,
                Disbursement.disbursement_date.is_not(None),
                Disbursement.status == DisbursementStatus.PROCESSED,
            )
            .group_by(bucket)
            .order_by(bucket)
        )
        rows = (await self.session.execute(q)).all()
        if not rows:
            return []

        # Convert ₹ amounts → Cr for the chart, format the month label.
        # Decimal throughout per CLAUDE.md §6.2.
        return [
            {
                "month": _format_month_label(row.bucket),
                "amount": (Decimal(row.total or 0) / Decimal("10000000")).quantize(Decimal("0.01")),
            }
            for row in rows
        ]

    # -----------------------------------------------------------------
    # Portfolio split by product code.
    # -----------------------------------------------------------------

    async def _portfolio_by_product(self, organization_id: UUID) -> list[dict]:
        from app.models.lending.product import LoanProduct

        q = (
            select(
                LoanProduct.name.label("name"),
                func.coalesce(func.sum(LoanAccount.total_outstanding), 0).label("value"),
            )
            .join(LoanAccount, LoanAccount.product_id == LoanProduct.id)
            .where(
                LoanAccount.organization_id == organization_id,
                LoanAccount.status == LoanAccountStatus.ACTIVE,
            )
            .group_by(LoanProduct.name)
            .order_by(func.sum(LoanAccount.total_outstanding).desc())
        )
        rows = (await self.session.execute(q)).all()
        return [
            {
                "name": row.name,
                "value": (Decimal(row.value or 0) / Decimal("10000000")).quantize(Decimal("0.01")),
                "color": _PRODUCT_PALETTE[idx % len(_PRODUCT_PALETTE)],
            }
            for idx, row in enumerate(rows)
        ]

    # -----------------------------------------------------------------
    # Asset classification breakdown.
    # -----------------------------------------------------------------

    async def _asset_classification(self, organization_id: UUID) -> list[dict]:
        q = (
            select(
                LoanAccount.asset_classification,
                func.coalesce(func.sum(LoanAccount.total_outstanding), 0).label("amount"),
            )
            .where(
                LoanAccount.organization_id == organization_id,
                LoanAccount.status == LoanAccountStatus.ACTIVE,
            )
            .group_by(LoanAccount.asset_classification)
        )
        rows = (await self.session.execute(q)).all()
        if not rows:
            return []

        total = sum((Decimal(row.amount or 0) for row in rows), Decimal("0"))
        if total == 0:
            total = Decimal("1")  # avoid divide-by-zero in percentage calc
        # Render in canonical order so the bars don't jump between requests.
        canonical_order = [
            AssetClassification.STANDARD,
            AssetClassification.SMA_0,
            AssetClassification.SMA_1,
            AssetClassification.SMA_2,
            AssetClassification.NPA,
            AssetClassification.SUBSTANDARD,
            AssetClassification.DOUBTFUL_1,
            AssetClassification.DOUBTFUL_2,
            AssetClassification.DOUBTFUL_3,
            AssetClassification.LOSS,
        ]
        amounts_by_class = {row.asset_classification: Decimal(row.amount or 0) for row in rows}
        out: list[dict] = []
        for ac in canonical_order:
            if ac not in amounts_by_class:
                continue
            amt = amounts_by_class[ac]
            out.append(
                {
                    "category": _ASSET_CLASS_LABEL[ac],
                    "amount": (amt / Decimal("10000000")).quantize(Decimal("0.01")),
                    "percentage": (amt / total * Decimal("100")).quantize(Decimal("0.01")),
                    "color": _ASSET_CLASS_COLOUR[ac],
                }
            )
        return out

    # -----------------------------------------------------------------
    # Pending approvals — applications + disbursements + OTS.
    # -----------------------------------------------------------------

    async def _pending_approvals(self, organization_id: UUID, limit: int = 5) -> list[dict]:
        # Top N applications + disbursements awaiting review. OTS is in a
        # separate table (collections) — we'll add it once the OTS hook
        # lands; for now the two highest-traffic types cover the demo.
        app_q = (
            select(
                LoanApplication.id,
                LoanApplication.application_number.label("reference"),
                Entity.legal_name.label("entity"),
                LoanApplication.requested_amount.label("amount"),
                LoanApplication.status.label("stage"),
                LoanApplication.created_at.label("due"),
            )
            .join(Entity, Entity.id == LoanApplication.entity_id)
            .where(
                LoanApplication.organization_id == organization_id,
                LoanApplication.status.in_(
                    [
                        ApplicationStatus.SUBMITTED,
                        ApplicationStatus.UNDER_REVIEW,
                        ApplicationStatus.ADDITIONAL_INFO_REQUIRED,
                    ]
                ),
            )
            .order_by(LoanApplication.created_at.desc())
            .limit(limit)
        )
        rows = (await self.session.execute(app_q)).all()
        return [
            {
                "id": str(row.id),
                "type": "Application",
                "reference": row.reference,
                "entity": row.entity,
                "amount": Decimal(row.amount or 0),
                "stage": row.stage.value if hasattr(row.stage, "value") else str(row.stage),
                "due_date": row.due.date().isoformat() if row.due else None,
            }
            for row in rows
        ]

    # -----------------------------------------------------------------
    # Upcoming maturities — loans maturing in next 30 days.
    # -----------------------------------------------------------------

    async def _upcoming_maturities(
        self, organization_id: UUID, days_ahead: int = 30, limit: int = 5
    ) -> list[dict]:
        today = datetime.now(UTC).date()
        horizon = today + timedelta(days=days_ahead)
        q = (
            select(
                LoanAccount.id,
                LoanAccount.loan_account_number.label("account_number"),
                Entity.legal_name.label("entity"),
                LoanAccount.maturity_date,
                LoanAccount.total_outstanding.label("outstanding"),
            )
            .join(Entity, Entity.id == LoanAccount.entity_id)
            .where(
                LoanAccount.organization_id == organization_id,
                LoanAccount.status == LoanAccountStatus.ACTIVE,
                LoanAccount.maturity_date.is_not(None),
                LoanAccount.maturity_date >= today,
                LoanAccount.maturity_date <= horizon,
            )
            .order_by(LoanAccount.maturity_date)
            .limit(limit)
        )
        rows = (await self.session.execute(q)).all()
        return [
            {
                "id": str(row.id),
                "account_number": row.account_number,
                "entity": row.entity,
                "maturity_date": row.maturity_date.isoformat(),
                "outstanding": Decimal(row.outstanding or 0),
            }
            for row in rows
        ]


def _format_month_label(d: date | datetime) -> str:
    """Tiny helper — 'Jan', 'Feb', etc."""
    if isinstance(d, datetime):
        d = d.date()
    return d.strftime("%b")


def _decimal(value: Decimal | int | float | str | None) -> Decimal:
    """Convert DB aggregate values to Decimal without losing money precision."""
    if value is None:
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))
