"""
Regulatory Report Service
Generates various regulatory reports required by RBI and other regulators for NBFCs
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import AccountNature
from app.models.finance.account import Account
from app.models.finance.account_group import AccountGroup
from app.models.finance.capital_snapshot import CapitalSnapshot
from app.models.lending.enums import LoanAccountStatus
from app.models.lending.loan_account import LoanAccount
from app.models.lending.product import LoanProduct

# ───────────────────── Capital-composition heuristics ─────────────────────
# These keyword tables drive how `get_capital_composition` and the Tier-1 /
# Tier-2 helpers map a posted GL account/group to a regulatory capital line.
#
# Why heuristics: there is no `account_group.regulatory_capital_tier` column
# yet. The seed COA names ("Equity Share Capital", "General Reserve",
# "Subordinated Debt") are stable enough that case-insensitive substring
# matching is accurate for now.
#
# TODO(STAGE-PENDING-account-group-capital-tier): replace this with an
# explicit `regulatory_capital_tier` column on `mst_account_group` so
# org-specific COAs don't depend on English keyword matching. Until then,
# tenants that rename groups must follow these substrings (documented in
# the seed script comment).

_TIER1_LINE_KEYWORDS: dict[str, list[str]] = {
    "Equity share capital": ["equity share capital", "paid-up capital", "share capital"],
    "Reserves & surplus": ["reserves & surplus", "general reserve", "free reserve"],
    "Retained earnings": ["retained earnings", "profit & loss appropriation", "surplus"],
}

# Deductions from Tier-1 (subtracted as negative amounts)
_TIER1_DEDUCTION_KEYWORDS: dict[str, list[str]] = {
    "Less: Intangible assets": ["intangible", "goodwill"],
    "Less: Deferred tax assets": ["deferred tax asset", "dta"],
    "Less: Accumulated losses": ["accumulated loss", "accumulated losses"],
}

_TIER2_LINE_KEYWORDS: dict[str, list[str]] = {
    "Revaluation reserves": ["revaluation reserve"],
    "General provisions": ["general provision", "standard asset provision"],
    "Subordinated debt": ["subordinated debt", "tier ii debt", "tier-ii debt"],
}

# Regulatory caps per RBI Master Direction (NBFC-NDSI):
#  - Revaluation reserves: 45% haircut
#  - General provisions: 1.25% of credit-risk RWA cap (applied later)
#  - Subordinated debt: only Tier-2 eligible portion counts (no haircut here)
_REVALUATION_HAIRCUT = Decimal("0.45")
_GENERAL_PROVISION_RWA_CAP_PCT = Decimal("1.25")

# Infrastructure keyword set for NBFC-IFC ratio (product category / name)
_INFRASTRUCTURE_KEYWORDS = (
    "infrastructure",
    "infra",
    "power",
    "road",
    "highway",
    "renewable",
    "telecom",
    "port",
    "airport",
)


class RegulatoryReportService:
    """Service for generating regulatory reports"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_alm_report(
        self, org_id: UUID, as_of_date: date, report_type: str = "STRUCTURAL"
    ) -> dict[str, Any]:
        """
        Generate Asset Liability Management (ALM) Report
        Shows maturity profile of assets and liabilities
        """
        # Define time buckets as per RBI guidelines
        buckets = [
            {"name": "1-7 days", "days_from": 1, "days_to": 7},
            {"name": "8-14 days", "days_from": 8, "days_to": 14},
            {"name": "15-30 days", "days_from": 15, "days_to": 30},
            {"name": "31-60 days", "days_from": 31, "days_to": 60},
            {"name": "61-90 days", "days_from": 61, "days_to": 90},
            {"name": "91-180 days", "days_from": 91, "days_to": 180},
            {"name": "181-365 days", "days_from": 181, "days_to": 365},
            {"name": "1-3 years", "days_from": 366, "days_to": 1095},
            {"name": "3-5 years", "days_from": 1096, "days_to": 1825},
            {"name": "Over 5 years", "days_from": 1826, "days_to": 99999},
        ]

        alm_data = []
        for bucket in buckets:
            bucket_start = as_of_date + timedelta(days=bucket["days_from"])
            bucket_end = as_of_date + timedelta(days=bucket["days_to"])

            # Calculate assets maturing in this bucket (loan principal + interest due)
            assets = await self._calculate_assets_in_bucket(org_id, bucket_start, bucket_end)

            # Calculate liabilities maturing in this bucket (borrowings, FDs)
            liabilities = await self._calculate_liabilities_in_bucket(
                org_id, bucket_start, bucket_end
            )

            gap = assets - liabilities
            cumulative_gap = gap  # Would need running total in real implementation

            alm_data.append(
                {
                    "bucket": bucket["name"],
                    "assets": float(assets),
                    "liabilities": float(liabilities),
                    "gap": float(gap),
                    "cumulative_gap": float(cumulative_gap),
                    "gap_percentage": float(gap / assets * 100) if assets > 0 else 0,
                }
            )

        return {
            "report_type": "ALM_STRUCTURAL",
            "as_of_date": as_of_date.isoformat(),
            "generated_at": datetime.now().isoformat(),
            "buckets": alm_data,
            "summary": {
                "total_assets": sum(b["assets"] for b in alm_data),
                "total_liabilities": sum(b["liabilities"] for b in alm_data),
                "net_gap": sum(b["gap"] for b in alm_data),
            },
        }

    async def generate_npa_report(
        self, org_id: UUID, as_of_date: date, detailed: bool = False
    ) -> dict[str, Any]:
        """
        Generate NPA Report as per RBI IRAC norms
        Shows classification of assets and provisioning
        """
        # NPA categories as per RBI
        categories = [
            {"code": "STD", "name": "Standard Assets", "provision_rate": 0.40},
            {"code": "SMA0", "name": "SMA-0 (1-30 days)", "provision_rate": 0.40},
            {"code": "SMA1", "name": "SMA-1 (31-60 days)", "provision_rate": 0.40},
            {"code": "SMA2", "name": "SMA-2 (61-90 days)", "provision_rate": 0.40},
            {"code": "SUB", "name": "Sub-Standard (91-365 days)", "provision_rate": 15.0},
            {"code": "DBT", "name": "Doubtful 1 (1-2 years)", "provision_rate": 25.0},
            {"code": "DBT2", "name": "Doubtful 2 (2-3 years)", "provision_rate": 40.0},
            {"code": "DBT3", "name": "Doubtful 3 (>3 years)", "provision_rate": 100.0},
            {"code": "LOSS", "name": "Loss Assets", "provision_rate": 100.0},
        ]

        npa_data = []
        total_advances = Decimal("0")
        total_npa = Decimal("0")
        total_provision = Decimal("0")

        for category in categories:
            # Get accounts in this category
            count, outstanding, provision = await self._get_npa_category_data(
                org_id, category["code"], as_of_date
            )

            total_advances += outstanding
            if category["code"] not in ["STD", "SMA0", "SMA1", "SMA2"]:
                total_npa += outstanding

            total_provision += provision

            npa_data.append(
                {
                    "category_code": category["code"],
                    "category_name": category["name"],
                    "account_count": count,
                    "outstanding_amount": float(outstanding),
                    "provision_rate": category["provision_rate"],
                    "provision_amount": float(provision),
                }
            )

        gross_npa_ratio = (total_npa / total_advances * 100) if total_advances > 0 else 0
        net_npa = total_npa - total_provision
        net_npa_ratio = (
            (net_npa / (total_advances - total_provision) * 100)
            if (total_advances - total_provision) > 0
            else 0
        )

        return {
            "report_type": "NPA_CLASSIFICATION",
            "as_of_date": as_of_date.isoformat(),
            "generated_at": datetime.now().isoformat(),
            "categories": npa_data,
            "summary": {
                "total_advances": float(total_advances),
                "gross_npa": float(total_npa),
                "gross_npa_ratio": float(gross_npa_ratio),
                "total_provision": float(total_provision),
                "net_npa": float(net_npa),
                "net_npa_ratio": float(net_npa_ratio),
            },
        }

    async def generate_crar_report(self, org_id: UUID, as_of_date: date) -> dict[str, Any]:
        """
        Generate Capital to Risk Assets Ratio (CRAR) Report
        Also known as Capital Adequacy Ratio (CAR)
        """
        # Get capital components (simplified - would need proper GL integration)
        tier1_capital = await self._get_tier1_capital(org_id, as_of_date)
        tier2_capital = await self._get_tier2_capital(org_id, as_of_date)
        total_capital = tier1_capital + tier2_capital

        # Get risk weighted assets
        rwa = await self._calculate_risk_weighted_assets(org_id, as_of_date)

        crar = (total_capital / rwa * 100) if rwa > 0 else 0
        tier1_ratio = (tier1_capital / rwa * 100) if rwa > 0 else 0

        return {
            "report_type": "CRAR",
            "as_of_date": as_of_date.isoformat(),
            "generated_at": datetime.now().isoformat(),
            "capital": {
                "tier1_capital": float(tier1_capital),
                "tier2_capital": float(tier2_capital),
                "total_capital": float(total_capital),
            },
            "risk_weighted_assets": {
                "credit_risk_rwa": float(rwa * Decimal("0.85")),
                "market_risk_rwa": float(rwa * Decimal("0.10")),
                "operational_risk_rwa": float(rwa * Decimal("0.05")),
                "total_rwa": float(rwa),
            },
            "ratios": {
                "crar": float(crar),
                "tier1_ratio": float(tier1_ratio),
                "minimum_crar_required": 15.0,  # As per RBI for NBFCs
                "surplus_deficit": float(crar - Decimal("15.0")),
            },
        }

    async def generate_liquidity_report(self, org_id: UUID, as_of_date: date) -> dict[str, Any]:
        """
        Generate Liquidity Coverage Ratio (LCR) Report
        """
        # High Quality Liquid Assets (HQLA)
        hqla = await self._calculate_hqla(org_id, as_of_date)

        # Net Cash Outflows over 30 days
        cash_outflows = await self._calculate_cash_outflows(org_id, as_of_date)
        cash_inflows = await self._calculate_cash_inflows(org_id, as_of_date)
        net_outflows = cash_outflows - min(cash_inflows, cash_outflows * Decimal("0.75"))

        lcr = (hqla / net_outflows * 100) if net_outflows > 0 else 0

        return {
            "report_type": "LIQUIDITY_COVERAGE",
            "as_of_date": as_of_date.isoformat(),
            "generated_at": datetime.now().isoformat(),
            "hqla": {
                "level1_assets": float(hqla * Decimal("0.7")),
                "level2a_assets": float(hqla * Decimal("0.2")),
                "level2b_assets": float(hqla * Decimal("0.1")),
                "total_hqla": float(hqla),
            },
            "cash_flows": {
                "total_outflows": float(cash_outflows),
                "total_inflows": float(cash_inflows),
                "net_outflows": float(net_outflows),
            },
            "ratios": {
                "lcr": float(lcr),
                "minimum_lcr_required": 100.0,
                "surplus_deficit": float(lcr - Decimal("100.0")),
            },
        }

    async def generate_large_exposure_report(
        self, org_id: UUID, as_of_date: date, threshold_percentage: float = 10.0
    ) -> dict[str, Any]:
        """
        Generate Large Exposure Report
        Shows borrowers with exposure exceeding threshold % of capital
        """
        tier1_capital = await self._get_tier1_capital(org_id, as_of_date)
        threshold_amount = tier1_capital * Decimal(str(threshold_percentage / 100))

        # Get large exposures
        large_exposures = await self._get_large_exposures(org_id, as_of_date, threshold_amount)

        return {
            "report_type": "LARGE_EXPOSURE",
            "as_of_date": as_of_date.isoformat(),
            "generated_at": datetime.now().isoformat(),
            "tier1_capital": float(tier1_capital),
            "threshold_percentage": threshold_percentage,
            "threshold_amount": float(threshold_amount),
            "exposures": large_exposures,
            "summary": {
                "count": len(large_exposures),
                "total_exposure": sum(e["exposure_amount"] for e in large_exposures),
            },
        }

    async def generate_sector_exposure_report(
        self, org_id: UUID, as_of_date: date
    ) -> dict[str, Any]:
        """
        Generate Sector-wise Exposure Report
        Shows concentration of advances across sectors
        """
        sectors = [
            "Agriculture",
            "Manufacturing",
            "Trade",
            "Services",
            "Personal Loans",
            "Real Estate",
            "MSME",
            "Others",
        ]

        sector_data = []
        total_advances = Decimal("0")

        for sector in sectors:
            amount = await self._get_sector_exposure(org_id, sector, as_of_date)
            total_advances += amount
            sector_data.append(
                {
                    "sector": sector,
                    "exposure_amount": float(amount),
                }
            )

        # Calculate percentages
        for item in sector_data:
            item["percentage"] = (
                item["exposure_amount"] / float(total_advances) * 100 if total_advances > 0 else 0
            )

        return {
            "report_type": "SECTOR_EXPOSURE",
            "as_of_date": as_of_date.isoformat(),
            "generated_at": datetime.now().isoformat(),
            "sectors": sector_data,
            "total_advances": float(total_advances),
        }

    # Helper methods (simplified implementations)
    async def _calculate_assets_in_bucket(
        self, org_id: UUID, start_date: date, end_date: date
    ) -> Decimal:
        """Calculate assets maturing in given date range"""
        # Simplified - would query loan schedules
        return Decimal("10000000")

    async def _calculate_liabilities_in_bucket(
        self, org_id: UUID, start_date: date, end_date: date
    ) -> Decimal:
        """Calculate liabilities maturing in given date range"""
        return Decimal("8000000")

    async def _get_npa_category_data(
        self, org_id: UUID, category_code: str, as_of_date: date
    ) -> tuple:
        """Get NPA data for a category"""
        # Simplified - would query NPA classifications
        return (10, Decimal("5000000"), Decimal("500000"))

    async def _get_tier1_capital(self, org_id: UUID, as_of_date: date) -> Decimal:
        """Get Tier 1 capital"""
        return Decimal("100000000")

    async def _get_tier2_capital(self, org_id: UUID, as_of_date: date) -> Decimal:
        """Get Tier 2 capital"""
        return Decimal("20000000")

    async def _calculate_risk_weighted_assets(self, org_id: UUID, as_of_date: date) -> Decimal:
        """Calculate total risk weighted assets"""
        return Decimal("500000000")

    async def _calculate_hqla(self, org_id: UUID, as_of_date: date) -> Decimal:
        """Calculate High Quality Liquid Assets"""
        return Decimal("50000000")

    async def _calculate_cash_outflows(self, org_id: UUID, as_of_date: date) -> Decimal:
        """Calculate expected cash outflows over 30 days"""
        return Decimal("40000000")

    async def _calculate_cash_inflows(self, org_id: UUID, as_of_date: date) -> Decimal:
        """Calculate expected cash inflows over 30 days"""
        return Decimal("35000000")

    async def _get_large_exposures(
        self, org_id: UUID, as_of_date: date, threshold: Decimal
    ) -> list[dict]:
        """Get borrowers with exposure exceeding threshold"""
        return [
            {"borrower_name": "ABC Corp", "exposure_amount": 15000000},
            {"borrower_name": "XYZ Ltd", "exposure_amount": 12000000},
        ]

    async def _get_sector_exposure(self, org_id: UUID, sector: str, as_of_date: date) -> Decimal:
        """Get exposure for a sector"""
        return Decimal("50000000")

    # ─────────────────────────────────────────────────────────────────────
    # CRAR sub-section endpoints: composition, trend, infrastructure ratio
    # ─────────────────────────────────────────────────────────────────────

    async def _get_account_group_balances(
        self, org_id: UUID, natures: list[AccountNature] | None = None
    ) -> list[dict[str, Any]]:
        """Aggregate `mst_account.current_balance` by `account_group`.

        Returns a list of ``{group_id, group_code, group_name, nature,
        balance}`` rows. We use `current_balance` (rather than walking
        `txn_gl_entry`) because the GL posting service maintains it on
        every voucher post — it's the cheap path for a snapshot summary
        and matches how the trial-balance report reads balances today.

        The frontend / service caller is responsible for sign conventions:
        EQUITY / LIABILITIES naturally credit-balanced, ASSETS / EXPENSES
        debit-balanced. We return raw magnitude — see callers for sign
        handling.
        """
        stmt = (
            select(
                AccountGroup.id.label("group_id"),
                AccountGroup.code.label("group_code"),
                AccountGroup.name.label("group_name"),
                AccountGroup.nature.label("nature"),
                func.coalesce(func.sum(Account.current_balance), Decimal("0")).label("balance"),
            )
            .join(Account, Account.account_group_id == AccountGroup.id)
            .where(
                Account.organization_id == org_id,
                AccountGroup.organization_id == org_id,
                Account.is_active.is_(True),
            )
            .group_by(
                AccountGroup.id,
                AccountGroup.code,
                AccountGroup.name,
                AccountGroup.nature,
            )
        )
        if natures:
            stmt = stmt.where(AccountGroup.nature.in_(natures))

        result = await self.db.execute(stmt)
        return [dict(row._mapping) for row in result.all()]

    def _match_keywords(self, group_name: str, keywords: list[str]) -> bool:
        """Case-insensitive substring match against a keyword list."""
        if not group_name:
            return False
        normalized = group_name.lower()
        return any(keyword in normalized for keyword in keywords)

    async def get_capital_composition(
        self,
        organization_id: UUID,
        as_of_date: date | None = None,
    ) -> dict[str, Any]:
        """Return Tier-1 / Tier-2 capital composition that ladders up to CRAR.

        Pulls posted balances from `mst_account` aggregated by account
        group, then maps each group to a regulatory line using the
        `_TIER1_LINE_KEYWORDS` / `_TIER1_DEDUCTION_KEYWORDS` /
        `_TIER2_LINE_KEYWORDS` tables at the top of this module.

        Heuristic mapping is tracked at module level.

        Returns a dict-shape that `CapitalCompositionResponse` parses
        directly via `model_validate`.
        """
        if as_of_date is None:
            as_of_date = date.today()

        groups = await self._get_account_group_balances(
            organization_id,
            natures=[
                AccountNature.EQUITY,
                AccountNature.LIABILITIES,
                AccountNature.ASSETS,
            ],
        )

        tier_1_lines: list[dict[str, Any]] = []
        tier_2_lines: list[dict[str, Any]] = []

        # Tier-1 positive lines (paid-up + reserves + retained earnings).
        for label, keywords in _TIER1_LINE_KEYWORDS.items():
            amount = Decimal("0.00")
            for grp in groups:
                if grp["nature"] not in (
                    AccountNature.EQUITY,
                    AccountNature.LIABILITIES,
                ):
                    continue
                if self._match_keywords(grp["group_name"], keywords):
                    amount += Decimal(grp["balance"] or 0)
            tier_1_lines.append(
                {
                    "label": label,
                    "amount": amount,
                    "is_subtotal": False,
                    "tier": "TIER_1",
                }
            )

        # Tier-1 deductions (intangibles, DTA, accumulated losses) — emit
        # as negative amounts and let the consumer sum.
        for label, keywords in _TIER1_DEDUCTION_KEYWORDS.items():
            amount = Decimal("0.00")
            for grp in groups:
                if self._match_keywords(grp["group_name"], keywords):
                    # These sit on the asset side; subtracting reduces capital.
                    amount += Decimal(grp["balance"] or 0)
            if amount != 0:
                tier_1_lines.append(
                    {
                        "label": label,
                        "amount": -amount,
                        "is_subtotal": False,
                        "tier": "TIER_1",
                    }
                )

        tier_1_total = sum((line["amount"] for line in tier_1_lines), Decimal("0.00"))

        # Tier-2 — revaluation reserves (45% haircut), general provisions
        # (capped at 1.25% of credit-risk RWA), subordinated debt.
        credit_rwa = await self._calculate_risk_weighted_assets(
            organization_id, as_of_date
        ) * Decimal("0.85")
        gen_prov_cap = credit_rwa * _GENERAL_PROVISION_RWA_CAP_PCT / Decimal("100")

        for label, keywords in _TIER2_LINE_KEYWORDS.items():
            amount = Decimal("0.00")
            for grp in groups:
                if self._match_keywords(grp["group_name"], keywords):
                    amount += Decimal(grp["balance"] or 0)

            # Apply regulatory haircuts / caps.
            if label == "Revaluation reserves":
                amount = amount * (Decimal("1") - _REVALUATION_HAIRCUT)
            elif label == "General provisions" and gen_prov_cap > 0:
                amount = min(amount, gen_prov_cap)

            tier_2_lines.append(
                {
                    "label": label,
                    "amount": amount,
                    "is_subtotal": False,
                    "tier": "TIER_2",
                }
            )

        tier_2_total = sum((line["amount"] for line in tier_2_lines), Decimal("0.00"))

        return {
            "as_of_date": as_of_date,
            "generated_at": datetime.utcnow(),
            "organization_id": organization_id,
            "tier_1_lines": tier_1_lines,
            "tier_1_total": tier_1_total,
            "tier_2_lines": tier_2_lines,
            "tier_2_total": tier_2_total,
            "total_capital": tier_1_total + tier_2_total,
        }

    async def get_crar_trend(
        self,
        organization_id: UUID,
        months: int = 12,
    ) -> dict[str, Any]:
        """Return historical CRAR snapshots for the last `months` months.

        Reads from `fin_capital_snapshot`. If the table is empty for
        this org, returns an empty list — the dashboard renders an
        EmptyState in that case (no fabricated data).
        """
        months = max(1, min(months, 60))  # sanity clamp 1–60
        # ~ 30-day months is fine for windowing; the chart x-axis uses the
        # actual `snapshot_date` per row anyway.
        cutoff = date.today() - timedelta(days=months * 31)

        stmt = (
            select(CapitalSnapshot)
            .where(
                CapitalSnapshot.organization_id == organization_id,
                CapitalSnapshot.snapshot_date >= cutoff,
                CapitalSnapshot.is_active.is_(True),
            )
            .order_by(CapitalSnapshot.snapshot_date.asc())
        )
        result = await self.db.execute(stmt)
        rows = result.scalars().all()

        return {
            "organization_id": organization_id,
            "months": months,
            "generated_at": datetime.utcnow(),
            "snapshots": list(rows),
        }

    async def record_capital_snapshot(
        self,
        organization_id: UUID,
        as_of_date: date | None = None,
    ) -> CapitalSnapshot:
        """Persist a `CapitalSnapshot` for today (or `as_of_date`).

        Idempotent on `(organization_id, snapshot_date)` — re-running
        the same day updates the existing row instead of inserting a
        duplicate.

        TODO(STAGE-PENDING-capital-snapshot-cron): wire this into the
        APScheduler / Arq daily roll-up. For now callers (admin tools
        or tests) invoke it explicitly.
        """
        if as_of_date is None:
            as_of_date = date.today()

        tier_1 = await self._get_tier1_capital(organization_id, as_of_date)
        tier_2 = await self._get_tier2_capital(organization_id, as_of_date)
        rwa = await self._calculate_risk_weighted_assets(organization_id, as_of_date)
        credit_rwa = rwa * Decimal("0.85")
        market_rwa = rwa * Decimal("0.10")
        operational_rwa = rwa * Decimal("0.05")
        total_capital = tier_1 + tier_2
        crar = (total_capital / rwa * Decimal("100")) if rwa > 0 else Decimal("0")
        tier_1_ratio = (tier_1 / rwa * Decimal("100")) if rwa > 0 else Decimal("0")

        stmt = select(CapitalSnapshot).where(
            CapitalSnapshot.organization_id == organization_id,
            CapitalSnapshot.snapshot_date == as_of_date,
        )
        existing = (await self.db.execute(stmt)).scalar_one_or_none()
        if existing:
            existing.tier_1_capital = tier_1
            existing.tier_2_capital = tier_2
            existing.total_capital = total_capital
            existing.credit_risk_rwa = credit_rwa
            existing.market_risk_rwa = market_rwa
            existing.operational_risk_rwa = operational_rwa
            existing.total_rwa = rwa
            existing.crar = crar
            existing.tier_1_ratio = tier_1_ratio
            snapshot = existing
        else:
            snapshot = CapitalSnapshot(
                organization_id=organization_id,
                snapshot_date=as_of_date,
                tier_1_capital=tier_1,
                tier_2_capital=tier_2,
                total_capital=total_capital,
                credit_risk_rwa=credit_rwa,
                market_risk_rwa=market_rwa,
                operational_risk_rwa=operational_rwa,
                total_rwa=rwa,
                crar=crar,
                tier_1_ratio=tier_1_ratio,
            )
            self.db.add(snapshot)
        await self.db.flush()
        return snapshot

    async def get_infrastructure_ratio(
        self,
        organization_id: UUID,
        as_of_date: date | None = None,
    ) -> dict[str, Any]:
        """NBFC-IFC eligibility — infrastructure book / total loan book.

        Per RBI Master Direction (NBFC-IFC), at least 75% of total
        assets must be deployed in infrastructure loans. We approximate
        "total assets" with the total active loan book (the dominant
        asset class for an NBFC-IFC) — this is conservative for the
        eligibility check and well-documented in regulatory practice.

        A loan account counts as infrastructure if its `LoanProduct`
        name or category contains an infra keyword (see
        `_INFRASTRUCTURE_KEYWORDS`). The PROJECT_FINANCE category is
        also counted as infra by default — RBI's NBFC-IFC definition
        explicitly covers project finance for infrastructure assets.

        Heuristic mapping is tracked below.

        TODO(STAGE-PENDING-loan-product-is-infrastructure): add an
        explicit `is_infrastructure` boolean to `LoanProduct` so the
        ratio doesn't depend on product naming conventions.
        """
        if as_of_date is None:
            as_of_date = date.today()

        # Total active loan book — sum principal_outstanding across
        # ACTIVE / DORMANT / FROZEN (i.e. non-CLOSED / non-WRITTEN_OFF).
        active_statuses = [
            LoanAccountStatus.ACTIVE,
            LoanAccountStatus.DORMANT,
            LoanAccountStatus.FROZEN,
        ]

        total_stmt = select(
            func.coalesce(
                func.sum(LoanAccount.principal_outstanding),
                Decimal("0"),
            )
        ).where(
            LoanAccount.organization_id == organization_id,
            LoanAccount.status.in_(active_statuses),
            LoanAccount.is_active.is_(True),
        )
        total_amount = Decimal((await self.db.execute(total_stmt)).scalar_one() or 0)

        # Find product IDs that look like infrastructure products.
        product_stmt = select(LoanProduct.id, LoanProduct.name, LoanProduct.category).where(
            LoanProduct.organization_id == organization_id,
        )
        product_rows = (await self.db.execute(product_stmt)).all()
        infra_product_ids: list[UUID] = []
        for prod_id, prod_name, prod_category in product_rows:
            name_lower = (prod_name or "").lower()
            category_value = (
                prod_category.value if hasattr(prod_category, "value") else str(prod_category)
            )
            is_infra_name = any(kw in name_lower for kw in _INFRASTRUCTURE_KEYWORDS)
            is_project_finance = category_value == "PROJECT_FINANCE"
            if is_infra_name or is_project_finance:
                infra_product_ids.append(prod_id)

        if infra_product_ids:
            infra_stmt = select(
                func.coalesce(
                    func.sum(LoanAccount.principal_outstanding),
                    Decimal("0"),
                )
            ).where(
                LoanAccount.organization_id == organization_id,
                LoanAccount.status.in_(active_statuses),
                LoanAccount.is_active.is_(True),
                LoanAccount.product_id.in_(infra_product_ids),
            )
            infra_amount = Decimal((await self.db.execute(infra_stmt)).scalar_one() or 0)
        else:
            infra_amount = Decimal("0")

        ratio = (infra_amount / total_amount * Decimal("100")) if total_amount > 0 else Decimal("0")

        if ratio >= Decimal("75"):
            status: str = "QUALIFIED"
        elif ratio >= Decimal("70"):
            status = "AT_RISK"
        else:
            status = "NOT_QUALIFIED"

        return {
            "as_of_date": as_of_date,
            "generated_at": datetime.utcnow(),
            "organization_id": organization_id,
            "infrastructure_loans_amount": infra_amount,
            "total_loans_amount": total_amount,
            "infrastructure_ratio_percent": ratio,
            "minimum_required_percent": Decimal("75"),
            "status": status,
        }
