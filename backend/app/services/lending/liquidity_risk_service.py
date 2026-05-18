"""Liquidity Risk service — LCR, NSFR, cash-flow ladder, funding concentration.

This is a simplified RBI NBFC-SBR variant of Basel III LCR / NSFR. Read-only,
computed on demand; no persistence in v1 (snapshots will land with the
``trs_lcr_snapshot`` / ``trs_nsfr_snapshot`` tables — see roadmap).

Inputs are pulled from existing models:
  - GL ``mst_account`` (joined to ``mst_account_group``) for HQLA Level-1
    (cash + RBI balances + Government Securities) using account-name heuristics.
  - ``trs_investment`` (TreasuryInvestment) for HQLA Level-2A — all CORP_BOND
    / NCD positions in HTM or AFS are treated as L2A in v1 (rating not yet
    tracked per CLAUDE.md §4.7 v1 scope).
  - ``trs_borrowing`` (Borrowing) + ``trs_borrowing_schedule`` for outflows
    (wholesale unsecured / secured), funding concentration and NSFR ASF.
  - ``lms_loan_account`` + ``lms_schedule_installment`` for inflows and NSFR
    RSF (performing loan classification by remaining tenure).
  - ``fd_fixed_deposit`` for retail deposit outflows when the FD module is
    populated; otherwise the line contributes 0.
  - ``fin_capital_snapshot`` for the most-recent Tier-1 + Tier-2 capital.

All runoff / haircut / ASF / RSF factors are sourced from RBI master
direction. They are coded as ``Decimal`` constants on the service so a future
table-driven version (``mst_lcr_runoff_factor`` etc.) can swap them in
without changing call sites.

Multi-tenant per CLAUDE.md §3.4 — every query filters by ``organization_id``;
RLS at the DB layer is the defence-in-depth.
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import AccountNature
from app.models.finance.account import Account
from app.models.finance.account_group import AccountGroup
from app.models.finance.capital_snapshot import CapitalSnapshot
from app.models.lending.loan_account import (
    LoanAccount,
    RepaymentSchedule,
    ScheduleInstallment,
)
from app.models.lending.treasury import Borrowing, BorrowingSchedule, Lender
from app.models.lending.treasury_investment import TreasuryInvestment
from app.schemas.lending.liquidity_risk import (
    CashflowBucket,
    CashflowLadderSnapshot,
    FundingConcentrationItem,
    FundingConcentrationSnapshot,
    LCRComponent,
    LCRSnapshot,
    NSFRComponent,
    NSFRSnapshot,
)

# Optional import — FD module may not have been migrated in every environment;
# fall back to "no retail deposits" rather than crashing.
try:
    from app.models.fixed_deposits.fixed_deposit import FDStatus, FixedDeposit

    _FD_AVAILABLE = True
except ImportError:  # pragma: no cover - defensive
    FixedDeposit = None  # type: ignore[assignment]
    FDStatus = None  # type: ignore[assignment]
    _FD_AVAILABLE = False


# =============================================================================
# RBI factors (NBFC-SBR variant of Basel III)
# =============================================================================

# HQLA haircuts (Level-2A is 85%; Level-2B 50% — Level-2B skipped in v1).
HQLA_LEVEL_1_WEIGHT = Decimal("1.00")
HQLA_LEVEL_2A_WEIGHT = Decimal("0.85")
HQLA_LEVEL_2B_WEIGHT = Decimal("0.50")

# 30-day runoff factors.
RUNOFF_RETAIL_LESS_STABLE = Decimal("0.10")  # FDs — less-stable proxy.
RUNOFF_WHOLESALE_UNSECURED = Decimal("0.40")
RUNOFF_WHOLESALE_SECURED = Decimal("0.25")

# 30-day inflow factor for performing loans.
INFLOW_PERFORMING_LOANS = Decimal("0.50")

# Basel cap on inflow recognition.
INFLOW_CAP_RATIO = Decimal("0.75")
NET_OUTFLOW_FLOOR_RATIO = Decimal("0.25")

# NSFR factors.
ASF_CAPITAL = Decimal("1.00")
ASF_BORROWING_OVER_1Y = Decimal("1.00")
ASF_BORROWING_6M_TO_1Y = Decimal("0.50")
ASF_BORROWING_UNDER_6M = Decimal("0.00")

RSF_LOAN_OVER_1Y = Decimal("0.85")
RSF_LOAN_UNDER_1Y = Decimal("0.50")
RSF_HQLA_L1 = Decimal("0.05")
RSF_HQLA_L2A = Decimal("0.15")

# Regulatory minimums (used for the colour-coded status).
LCR_MINIMUM_PERCENT = Decimal("100.00")
NSFR_MINIMUM_PERCENT = Decimal("100.00")

# Heuristic patterns for HQLA Level-1 lookup against the chart of accounts.
# We match by account_group.code OR account_group.name OR account.name —
# case-insensitive, substring. Keep these as wide as needed for the v1; once
# we ship a ``hqla_category`` column on ``mst_account``, replace this with an
# explicit join.
_HQLA_L1_KEYWORDS = (
    "cash in hand",
    "cash on hand",
    "petty cash",
    "balances with rbi",
    "balance with rbi",
    "reserve bank",
    "government securit",  # 'government securities', 'government security'
    "g-sec",
    "g sec",
    "treasury bill",
    "t-bill",
)

# Loan account statuses considered "performing" for inflow + RSF.
_PERFORMING_LOAN_STATUSES = ("CREATED", "ACTIVE")

# Borrowing statuses considered "active" for outflow / NSFR ASF.
_ACTIVE_BORROWING_STATUSES = ("SANCTIONED", "DISBURSED", "PARTIALLY_DISBURSED", "ACTIVE")

# Borrowing security types treated as secured for the wholesale outflow split.
_SECURED_BORROWING_TYPES = ("SECURED", "COLLATERALIZED")


# =============================================================================
# Bucket definitions for the cash-flow ladder (RBI ALM).
# =============================================================================

# Each tuple is (label, days_from, days_to_inclusive). Final bucket sets
# days_to_inclusive to None on the schema side.
_LADDER_BUCKETS: list[tuple[str, int, int | None]] = [
    ("Day 1", 0, 1),
    ("2-7 days", 2, 7),
    ("8-14 days", 8, 14),
    ("15-30 days", 15, 30),
    ("31-60 days", 31, 60),
    ("61-90 days", 61, 90),
    ("91-180 days", 91, 180),
    ("181-365 days", 181, 365),
    ("1-3 years", 366, 1095),
    ("3-5 years", 1096, 1825),
    (">5 years", 1826, None),
]


class LiquidityRiskService:
    """Read-only liquidity risk analytics."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # ------------------------------------------------------------------ utils

    @staticmethod
    def _round_money(value: Decimal) -> Decimal:
        return value.quantize(Decimal("0.01"))

    @staticmethod
    def _round_percent(value: Decimal) -> Decimal:
        return value.quantize(Decimal("0.01"))

    @staticmethod
    def _status_from_ratio(ratio: Decimal, minimum: Decimal) -> str:
        if ratio <= 0:
            return "NO_DATA"
        if ratio >= minimum:
            return "ADEQUATE"
        if ratio >= minimum * Decimal("0.80"):
            return "WATCH"
        return "BREACH"

    @staticmethod
    def _resolve_as_of(as_of_date: date | None) -> date:
        return as_of_date or date.today()

    # =====================================================================
    # HQLA
    # =====================================================================

    async def _hqla_level_1_from_gl(self, organization_id: UUID) -> list[LCRComponent]:
        """Level-1 HQLA from the chart of accounts.

        Heuristic — match account.name / account_group.name / account_group.code
        against ``_HQLA_L1_KEYWORDS`` and require the account_group.nature to be
        ASSETS. Caller balance is read from ``current_balance`` (we don't try
        to re-derive from the journal in v1; the GL service maintains it).
        """
        components: list[LCRComponent] = []

        if not _HQLA_L1_KEYWORDS:
            return components

        like_clauses = []
        for kw in _HQLA_L1_KEYWORDS:
            pattern = f"%{kw}%"
            like_clauses.extend(
                [
                    Account.name.ilike(pattern),
                    AccountGroup.name.ilike(pattern),
                    AccountGroup.code.ilike(pattern),
                ]
            )

        stmt = (
            select(
                Account.id,
                Account.name,
                Account.current_balance,
            )
            .join(AccountGroup, AccountGroup.id == Account.account_group_id)
            .where(
                Account.organization_id == organization_id,
                AccountGroup.nature == AccountNature.ASSETS,
                or_(*like_clauses),
            )
        )
        result = await self.session.execute(stmt)
        rows = result.all()

        # Aggregate by display label so we don't list every per-branch cash GL.
        # Bucket by which keyword group matched ("Cash & balances with RBI" vs
        # "Government securities"). Simple lexical pass — keep the heuristic
        # transparent.
        cash_total = Decimal("0")
        gsec_total = Decimal("0")
        for _account_id, name, balance in rows:
            lower = (name or "").lower()
            if "rbi" in lower or "reserve bank" in lower:
                cash_total += balance or Decimal("0")
            elif (
                "government" in lower
                or "g-sec" in lower
                or "g sec" in lower
                or "treasury bill" in lower
                or "t-bill" in lower
            ):
                gsec_total += balance or Decimal("0")
            else:
                # cash in hand / petty cash / generic
                cash_total += balance or Decimal("0")

        if cash_total > 0:
            components.append(
                LCRComponent(
                    label="Cash & balances with RBI",
                    amount=self._round_money(cash_total),
                    weight=HQLA_LEVEL_1_WEIGHT,
                    weighted_amount=self._round_money(cash_total * HQLA_LEVEL_1_WEIGHT),
                )
            )
        if gsec_total > 0:
            components.append(
                LCRComponent(
                    label="Government Securities / T-Bills",
                    amount=self._round_money(gsec_total),
                    weight=HQLA_LEVEL_1_WEIGHT,
                    weighted_amount=self._round_money(gsec_total * HQLA_LEVEL_1_WEIGHT),
                )
            )

        return components

    async def _hqla_level_2a_from_investments(self, organization_id: UUID) -> list[LCRComponent]:
        """Level-2A HQLA from the investment portfolio.

        v1 heuristic: ``type IN ('CORP_BOND', 'NCD')`` AND
        ``category IN ('HTM', 'AFS')`` AND ``status = 'ACTIVE'``. Once the
        portfolio carries an instrument-level credit rating we will gate on
        ``rating >= 'AA-'``.
        """
        stmt = select(func.coalesce(func.sum(TreasuryInvestment.face_value), 0)).where(
            TreasuryInvestment.organization_id == organization_id,
            TreasuryInvestment.status == "ACTIVE",
            TreasuryInvestment.type.in_(("CORP_BOND", "NCD")),
            TreasuryInvestment.category.in_(("HTM", "AFS")),
        )
        result = await self.session.execute(stmt)
        total = Decimal(str(result.scalar_one() or 0))

        if total <= 0:
            return []

        return [
            LCRComponent(
                label="AA-rated corporate bonds / NCDs (proxy)",
                amount=self._round_money(total),
                weight=HQLA_LEVEL_2A_WEIGHT,
                weighted_amount=self._round_money(total * HQLA_LEVEL_2A_WEIGHT),
            )
        ]

    # =====================================================================
    # LCR
    # =====================================================================

    async def compute_lcr(
        self,
        organization_id: UUID,
        as_of_date: date | None = None,
    ) -> LCRSnapshot:
        """Compute LCR snapshot."""
        as_of = self._resolve_as_of(as_of_date)
        window_end = as_of + timedelta(days=30)

        # ---- HQLA ----------------------------------------------------------
        l1 = await self._hqla_level_1_from_gl(organization_id)
        l2a = await self._hqla_level_2a_from_investments(organization_id)
        l2b: list[LCRComponent] = []  # v1: not tracked.

        total_hqla = sum(
            (c.weighted_amount for c in (*l1, *l2a, *l2b)),
            start=Decimal("0"),
        )

        # ---- Outflows ------------------------------------------------------
        outflows: list[LCRComponent] = []

        # Retail deposits (FD module). 10% blanket runoff (less-stable proxy).
        if _FD_AVAILABLE and FixedDeposit is not None and FDStatus is not None:
            fd_stmt = select(func.coalesce(func.sum(FixedDeposit.deposit_amount), 0)).where(
                FixedDeposit.organization_id == organization_id,
                FixedDeposit.status == FDStatus.ACTIVE,
            )
            fd_result = await self.session.execute(fd_stmt)
            retail_amt = Decimal(str(fd_result.scalar_one() or 0))
            if retail_amt > 0:
                outflows.append(
                    LCRComponent(
                        label="Retail deposits (FDs, less-stable)",
                        amount=self._round_money(retail_amt),
                        weight=RUNOFF_RETAIL_LESS_STABLE,
                        weighted_amount=self._round_money(retail_amt * RUNOFF_RETAIL_LESS_STABLE),
                    )
                )

        # Wholesale outflows: principal + interest on borrowing schedule due
        # within the next 30 days. Split by security type.
        bs_stmt = (
            select(
                Borrowing.security_type,
                func.coalesce(
                    func.sum(BorrowingSchedule.principal_due + BorrowingSchedule.interest_due),
                    0,
                ),
            )
            .join(Borrowing, Borrowing.borrowing_id == BorrowingSchedule.borrowing_id)
            .where(
                Borrowing.organization_id == organization_id,
                Borrowing.status.in_(_ACTIVE_BORROWING_STATUSES),
                BorrowingSchedule.due_date >= as_of,
                BorrowingSchedule.due_date <= window_end,
                BorrowingSchedule.status.in_(("NOT_DUE", "DUE", "PARTIALLY_PAID")),
            )
            .group_by(Borrowing.security_type)
        )
        bs_result = await self.session.execute(bs_stmt)
        wholesale_secured = Decimal("0")
        wholesale_unsecured = Decimal("0")
        for security_type, amount in bs_result.all():
            amt = Decimal(str(amount or 0))
            if (security_type or "UNSECURED").upper() in _SECURED_BORROWING_TYPES:
                wholesale_secured += amt
            else:
                wholesale_unsecured += amt

        if wholesale_unsecured > 0:
            outflows.append(
                LCRComponent(
                    label="Wholesale funding — unsecured (30d)",
                    amount=self._round_money(wholesale_unsecured),
                    weight=RUNOFF_WHOLESALE_UNSECURED,
                    weighted_amount=self._round_money(
                        wholesale_unsecured * RUNOFF_WHOLESALE_UNSECURED
                    ),
                )
            )
        if wholesale_secured > 0:
            outflows.append(
                LCRComponent(
                    label="Wholesale funding — secured (30d)",
                    amount=self._round_money(wholesale_secured),
                    weight=RUNOFF_WHOLESALE_SECURED,
                    weighted_amount=self._round_money(wholesale_secured * RUNOFF_WHOLESALE_SECURED),
                )
            )

        total_weighted_outflows = sum((c.weighted_amount for c in outflows), start=Decimal("0"))

        # ---- Inflows -------------------------------------------------------
        # Performing loan inflows: principal + interest scheduled due in 30d.
        inflow_stmt = (
            select(
                func.coalesce(
                    func.sum(
                        ScheduleInstallment.principal_amount + ScheduleInstallment.interest_amount
                    ),
                    0,
                )
            )
            .select_from(ScheduleInstallment)
            .join(RepaymentSchedule, RepaymentSchedule.id == ScheduleInstallment.schedule_id)
            .join(LoanAccount, LoanAccount.id == RepaymentSchedule.loan_account_id)
            .where(
                LoanAccount.organization_id == organization_id,
                LoanAccount.status.in_(_PERFORMING_LOAN_STATUSES),
                RepaymentSchedule.is_current.is_(True),
                ScheduleInstallment.due_date >= as_of,
                ScheduleInstallment.due_date <= window_end,
                ScheduleInstallment.status.in_(("NOT_DUE", "DUE", "PARTIALLY_PAID")),
            )
        )
        inflow_result = await self.session.execute(inflow_stmt)
        performing_inflow = Decimal(str(inflow_result.scalar_one() or 0))

        inflows: list[LCRComponent] = []
        if performing_inflow > 0:
            inflows.append(
                LCRComponent(
                    label="Performing loan inflows (30d)",
                    amount=self._round_money(performing_inflow),
                    weight=INFLOW_PERFORMING_LOANS,
                    weighted_amount=self._round_money(performing_inflow * INFLOW_PERFORMING_LOANS),
                )
            )

        total_weighted_inflows_raw = sum((c.weighted_amount for c in inflows), start=Decimal("0"))

        # ---- Net outflows (with Basel cap and floor) -----------------------
        inflow_cap = total_weighted_outflows * INFLOW_CAP_RATIO
        capped_inflows = min(total_weighted_inflows_raw, inflow_cap)
        inflow_cap_applied = total_weighted_inflows_raw > inflow_cap

        floor = total_weighted_outflows * NET_OUTFLOW_FLOOR_RATIO
        net_outflows = max(total_weighted_outflows - capped_inflows, floor)

        # ---- LCR -----------------------------------------------------------
        if net_outflows > 0:
            lcr_percent = (total_hqla / net_outflows) * Decimal("100")
        else:
            lcr_percent = Decimal("0")

        status = self._status_from_ratio(lcr_percent, LCR_MINIMUM_PERCENT)
        # If we literally have no inputs at all, flag NO_DATA explicitly.
        if total_hqla == 0 and total_weighted_outflows == 0:
            status = "NO_DATA"

        return LCRSnapshot(
            as_of_date=as_of,
            hqla_level_1=l1,
            hqla_level_2a=l2a,
            hqla_level_2b=l2b,
            total_hqla=self._round_money(total_hqla),
            outflows=outflows,
            total_weighted_outflows=self._round_money(total_weighted_outflows),
            inflows=inflows,
            total_weighted_inflows=self._round_money(capped_inflows),
            inflow_cap_applied=inflow_cap_applied,
            net_cash_outflows=self._round_money(net_outflows),
            lcr_percent=self._round_percent(lcr_percent),
            minimum_required_percent=LCR_MINIMUM_PERCENT,
            status=status,
        )

    # =====================================================================
    # NSFR
    # =====================================================================

    async def compute_nsfr(
        self,
        organization_id: UUID,
        as_of_date: date | None = None,
    ) -> NSFRSnapshot:
        """Compute NSFR snapshot."""
        as_of = self._resolve_as_of(as_of_date)

        asf: list[NSFRComponent] = []
        rsf: list[NSFRComponent] = []

        # ---- ASF: capital --------------------------------------------------
        cap_stmt = (
            select(CapitalSnapshot.tier_1_capital, CapitalSnapshot.tier_2_capital)
            .where(CapitalSnapshot.organization_id == organization_id)
            .order_by(CapitalSnapshot.snapshot_date.desc())
            .limit(1)
        )
        cap_result = await self.session.execute(cap_stmt)
        cap_row = cap_result.first()
        if cap_row:
            tier_1 = Decimal(str(cap_row[0] or 0))
            tier_2 = Decimal(str(cap_row[1] or 0))
            capital = tier_1 + tier_2
            if capital > 0:
                asf.append(
                    NSFRComponent(
                        label="Tier-1 + Tier-2 capital",
                        amount=self._round_money(capital),
                        weight=ASF_CAPITAL,
                        weighted_amount=self._round_money(capital * ASF_CAPITAL),
                    )
                )

        # ---- ASF: borrowings bucketed by residual maturity ----------------
        b_stmt = select(
            Borrowing.maturity_date,
            Borrowing.principal_outstanding,
        ).where(
            Borrowing.organization_id == organization_id,
            Borrowing.status.in_(_ACTIVE_BORROWING_STATUSES),
        )
        b_result = await self.session.execute(b_stmt)

        over_1y = Decimal("0")
        bucket_6m_1y = Decimal("0")
        under_6m = Decimal("0")
        for maturity_date, outstanding in b_result.all():
            amount = Decimal(str(outstanding or 0))
            if amount <= 0 or maturity_date is None:
                continue
            days = (maturity_date - as_of).days
            if days > 365:
                over_1y += amount
            elif days >= 180:
                bucket_6m_1y += amount
            else:
                under_6m += amount

        if over_1y > 0:
            asf.append(
                NSFRComponent(
                    label="Borrowings > 1 year residual",
                    amount=self._round_money(over_1y),
                    weight=ASF_BORROWING_OVER_1Y,
                    weighted_amount=self._round_money(over_1y * ASF_BORROWING_OVER_1Y),
                )
            )
        if bucket_6m_1y > 0:
            asf.append(
                NSFRComponent(
                    label="Borrowings 6m–1y residual",
                    amount=self._round_money(bucket_6m_1y),
                    weight=ASF_BORROWING_6M_TO_1Y,
                    weighted_amount=self._round_money(bucket_6m_1y * ASF_BORROWING_6M_TO_1Y),
                )
            )
        if under_6m > 0:
            asf.append(
                NSFRComponent(
                    label="Borrowings < 6m residual (no ASF credit)",
                    amount=self._round_money(under_6m),
                    weight=ASF_BORROWING_UNDER_6M,
                    weighted_amount=Decimal("0.00"),
                )
            )

        total_asf = sum((c.weighted_amount for c in asf), start=Decimal("0"))

        # ---- RSF: performing loans bucketed by residual maturity ----------
        la_stmt = select(
            LoanAccount.maturity_date,
            LoanAccount.principal_outstanding,
        ).where(
            LoanAccount.organization_id == organization_id,
            LoanAccount.status.in_(_PERFORMING_LOAN_STATUSES),
        )
        la_result = await self.session.execute(la_stmt)

        loan_over_1y = Decimal("0")
        loan_under_1y = Decimal("0")
        for maturity_date, outstanding in la_result.all():
            amount = Decimal(str(outstanding or 0))
            if amount <= 0:
                continue
            if maturity_date is None:
                # Indeterminate maturity — conservatively treat as > 1y.
                loan_over_1y += amount
                continue
            days = (maturity_date - as_of).days
            if days > 365:
                loan_over_1y += amount
            else:
                loan_under_1y += amount

        if loan_over_1y > 0:
            rsf.append(
                NSFRComponent(
                    label="Performing loans > 1y residual",
                    amount=self._round_money(loan_over_1y),
                    weight=RSF_LOAN_OVER_1Y,
                    weighted_amount=self._round_money(loan_over_1y * RSF_LOAN_OVER_1Y),
                )
            )
        if loan_under_1y > 0:
            rsf.append(
                NSFRComponent(
                    label="Performing loans < 1y residual",
                    amount=self._round_money(loan_under_1y),
                    weight=RSF_LOAN_UNDER_1Y,
                    weighted_amount=self._round_money(loan_under_1y * RSF_LOAN_UNDER_1Y),
                )
            )

        # ---- RSF: HQLA credit ---------------------------------------------
        l1 = await self._hqla_level_1_from_gl(organization_id)
        l2a = await self._hqla_level_2a_from_investments(organization_id)
        l1_total = sum((c.amount for c in l1), start=Decimal("0"))
        l2a_total = sum((c.amount for c in l2a), start=Decimal("0"))

        if l1_total > 0:
            rsf.append(
                NSFRComponent(
                    label="HQLA Level-1 (RSF credit)",
                    amount=self._round_money(l1_total),
                    weight=RSF_HQLA_L1,
                    weighted_amount=self._round_money(l1_total * RSF_HQLA_L1),
                )
            )
        if l2a_total > 0:
            rsf.append(
                NSFRComponent(
                    label="HQLA Level-2A (RSF credit)",
                    amount=self._round_money(l2a_total),
                    weight=RSF_HQLA_L2A,
                    weighted_amount=self._round_money(l2a_total * RSF_HQLA_L2A),
                )
            )

        total_rsf = sum((c.weighted_amount for c in rsf), start=Decimal("0"))

        if total_rsf > 0:
            nsfr_percent = (total_asf / total_rsf) * Decimal("100")
        else:
            nsfr_percent = Decimal("0")

        status = self._status_from_ratio(nsfr_percent, NSFR_MINIMUM_PERCENT)
        if total_asf == 0 and total_rsf == 0:
            status = "NO_DATA"

        return NSFRSnapshot(
            as_of_date=as_of,
            asf_components=asf,
            total_asf=self._round_money(total_asf),
            rsf_components=rsf,
            total_rsf=self._round_money(total_rsf),
            nsfr_percent=self._round_percent(nsfr_percent),
            minimum_required_percent=NSFR_MINIMUM_PERCENT,
            status=status,
        )

    # =====================================================================
    # Cash-flow ladder
    # =====================================================================

    async def get_cashflow_ladder(
        self,
        organization_id: UUID,
        as_of_date: date | None = None,
    ) -> CashflowLadderSnapshot:
        """Compute the cash-flow ladder across RBI ALM buckets.

        Inflows: scheduled principal + interest from performing loan accounts.
        Outflows: scheduled principal + interest from active borrowings.
        Both are aggregated by the residual days-to-due bucket and the
        cumulative gap is rolled oldest → newest.
        """
        as_of = self._resolve_as_of(as_of_date)

        # ----- Inflows by day ----------------------------------------------
        in_stmt = (
            select(
                ScheduleInstallment.due_date,
                func.coalesce(
                    func.sum(
                        ScheduleInstallment.principal_amount + ScheduleInstallment.interest_amount
                    ),
                    0,
                ),
            )
            .select_from(ScheduleInstallment)
            .join(RepaymentSchedule, RepaymentSchedule.id == ScheduleInstallment.schedule_id)
            .join(LoanAccount, LoanAccount.id == RepaymentSchedule.loan_account_id)
            .where(
                LoanAccount.organization_id == organization_id,
                LoanAccount.status.in_(_PERFORMING_LOAN_STATUSES),
                RepaymentSchedule.is_current.is_(True),
                ScheduleInstallment.due_date >= as_of,
                ScheduleInstallment.status.in_(("NOT_DUE", "DUE", "PARTIALLY_PAID")),
            )
            .group_by(ScheduleInstallment.due_date)
        )
        in_result = await self.session.execute(in_stmt)
        inflow_rows: list[tuple[date, Decimal]] = [
            (d, Decimal(str(a or 0))) for d, a in in_result.all()
        ]

        # ----- Outflows by day ---------------------------------------------
        out_stmt = (
            select(
                BorrowingSchedule.due_date,
                func.coalesce(
                    func.sum(BorrowingSchedule.principal_due + BorrowingSchedule.interest_due),
                    0,
                ),
            )
            .select_from(BorrowingSchedule)
            .join(Borrowing, Borrowing.borrowing_id == BorrowingSchedule.borrowing_id)
            .where(
                Borrowing.organization_id == organization_id,
                Borrowing.status.in_(_ACTIVE_BORROWING_STATUSES),
                BorrowingSchedule.due_date >= as_of,
                BorrowingSchedule.status.in_(("NOT_DUE", "DUE", "PARTIALLY_PAID")),
            )
            .group_by(BorrowingSchedule.due_date)
        )
        out_result = await self.session.execute(out_stmt)
        outflow_rows: list[tuple[date, Decimal]] = [
            (d, Decimal(str(a or 0))) for d, a in out_result.all()
        ]

        # ----- Bucketise ----------------------------------------------------
        bucket_inflows = [Decimal("0") for _ in _LADDER_BUCKETS]
        bucket_outflows = [Decimal("0") for _ in _LADDER_BUCKETS]

        def _index_for_days(days: int) -> int:
            for idx, (_label, dfrom, dto) in enumerate(_LADDER_BUCKETS):
                if dto is None and days >= dfrom:
                    return idx
                if dto is not None and dfrom <= days <= dto:
                    return idx
            return len(_LADDER_BUCKETS) - 1  # safety net

        for due_date, amount in inflow_rows:
            days = (due_date - as_of).days
            if days < 0:
                continue
            bucket_inflows[_index_for_days(days)] += amount

        for due_date, amount in outflow_rows:
            days = (due_date - as_of).days
            if days < 0:
                continue
            bucket_outflows[_index_for_days(days)] += amount

        buckets: list[CashflowBucket] = []
        cumulative = Decimal("0")
        for idx, (label, dfrom, dto) in enumerate(_LADDER_BUCKETS):
            inflows_i = bucket_inflows[idx]
            outflows_i = bucket_outflows[idx]
            gap = inflows_i - outflows_i
            cumulative += gap
            buckets.append(
                CashflowBucket(
                    bucket_label=label,
                    days_from=dfrom,
                    days_to=dto,
                    inflows=self._round_money(inflows_i),
                    outflows=self._round_money(outflows_i),
                    gap=self._round_money(gap),
                    cumulative_gap=self._round_money(cumulative),
                )
            )

        total_inflows = sum(bucket_inflows, Decimal("0"))
        total_outflows = sum(bucket_outflows, Decimal("0"))

        return CashflowLadderSnapshot(
            as_of_date=as_of,
            buckets=buckets,
            total_inflows=self._round_money(total_inflows),
            total_outflows=self._round_money(total_outflows),
            net_position=self._round_money(total_inflows - total_outflows),
        )

    # =====================================================================
    # Funding Concentration
    # =====================================================================

    async def get_funding_concentration(
        self,
        organization_id: UUID,
        top_n: int = 10,
        as_of_date: date | None = None,
    ) -> FundingConcentrationSnapshot:
        """Top-N lenders by outstanding borrowing."""
        as_of = self._resolve_as_of(as_of_date)

        # Aggregate outstanding by lender. Limit on top_n is applied post-sort
        # so we still know the grand total + lender count.
        stmt = (
            select(
                Lender.lender_id,
                Lender.lender_name,
                Lender.lender_type,
                func.coalesce(func.sum(Borrowing.principal_outstanding), 0).label("outstanding"),
            )
            .join(Borrowing, Borrowing.lender_id == Lender.lender_id)
            .where(
                Lender.organization_id == organization_id,
                Borrowing.organization_id == organization_id,
                Borrowing.status.in_(_ACTIVE_BORROWING_STATUSES),
            )
            .group_by(Lender.lender_id, Lender.lender_name, Lender.lender_type)
        )
        result = await self.session.execute(stmt)
        rows = [
            (lid, name, ltype, Decimal(str(amount or 0)))
            for lid, name, ltype, amount in result.all()
            if Decimal(str(amount or 0)) > 0
        ]
        rows.sort(key=lambda r: r[3], reverse=True)

        total_outstanding = sum((r[3] for r in rows), Decimal("0"))
        top_n_safe = max(1, int(top_n))
        top_rows = rows[:top_n_safe]

        items: list[FundingConcentrationItem] = []
        high_count = 0
        for lender_id, lender_name, lender_type, outstanding in top_rows:
            if total_outstanding > 0:
                pct = (outstanding / total_outstanding) * Decimal("100")
            else:
                pct = Decimal("0")
            if pct > Decimal("20"):
                flag = "HIGH"
                high_count += 1
            elif pct > Decimal("10"):
                flag = "MEDIUM"
            else:
                flag = "LOW"
            items.append(
                FundingConcentrationItem(
                    lender_id=lender_id,
                    lender_name=lender_name,
                    lender_type=lender_type,
                    outstanding=self._round_money(outstanding),
                    percent_of_total=self._round_percent(pct),
                    risk_flag=flag,
                )
            )

        return FundingConcentrationSnapshot(
            as_of_date=as_of,
            items=items,
            total_outstanding=self._round_money(total_outstanding),
            total_lenders=len(rows),
            high_concentration_count=high_count,
        )
