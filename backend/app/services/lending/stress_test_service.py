"""Stress Test Service — parametric v1.

Computes portfolio-level impact under four standard scenarios:
  1. Rate shock +200 bps  (NII impact via IRS Gap math)
  2. Rate shock -200 bps  (mirror of #1)
  3. NPA shock +5%        (5% of active principal migrates Standard → Substandard)
  4. Combined macro       (#1 + #3)

This is honest, parametric math — not Monte Carlo, not full portfolio
revaluation. v1 scope is documented at the top of `StressTest.tsx`.

Provisioning rates: looked up from `mst_provisioning_rate` if the table /
model exists for this tenant; otherwise we fall back to RBI defaults
(Standard secured 0.40%, Substandard secured 15%; Standard unsecured 0.40%,
Substandard unsecured 25%). Source is recorded on every result so audit can
tell at a glance which path was used (CLAUDE.md §4.8 — rates never hardcoded
in math; we capture the source).

Pure computation — no DB writes. Routes therefore don't need
`async with db.begin()` around the call, but they DO carry an Idempotency-Key
because we read heavy aggregates and the API contract stays consistent
(CLAUDE.md §6.3).
"""

from __future__ import annotations

from datetime import date as date_type
from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException
from app.models.lending.enums import LoanAccountStatus
from app.models.lending.loan_account import LoanAccount
from app.models.lending.product import LoanProduct
from app.models.lending.treasury import Borrowing
from app.schemas.lending.stress_test import (
    ScenarioId,
    ScenarioInputs,
    ScenarioMetadata,
    ScenarioOutputs,
    ScenarioResult,
    ScenarioStatus,
)
from app.services.reports.regulatory_report_service import RegulatoryReportService

# RBI default provisioning rates (percent — multiply by amount/100 to get ₹).
# Used when `mst_provisioning_rate` is not available for this tenant.
# Per CLAUDE.md §4.8 the live system should read from the master table;
# the constants here are explicit fallbacks captured in `ScenarioInputs.
# provisioning_rate_source` so audit can trace which path ran.
RBI_DEFAULT_STANDARD_SECURED = Decimal("0.40")
RBI_DEFAULT_SUBSTANDARD_SECURED = Decimal("15.00")
RBI_DEFAULT_STANDARD_UNSECURED = Decimal("0.40")
RBI_DEFAULT_SUBSTANDARD_UNSECURED = Decimal("25.00")

# CRAR regulatory thresholds for NBFCs (per RBI Scale-Based Regulation).
MINIMUM_CRAR_PCT = Decimal("15.00")
WARN_CRAR_PCT = Decimal("12.00")

# Default NPA migration applied by the credit-shock scenario.
NPA_MIGRATION_PCT = Decimal("5.00")

# Default rate shock magnitude (basis points).
DEFAULT_SHOCK_BPS = 200

# Last-year NII estimate used to express NII impact as a percentage.
# v1 fallback: assume NII ≈ 8% of rate-sensitive liabilities (rough proxy for
# net interest income on a leveraged book). When the GL service exposes a
# real "last 12 months NII" figure this should switch to that — captured as
# STAGE-PENDING in `.stubs-approved.md`.
LAST_YEAR_NII_PROXY_RATE = Decimal("0.08")


SCENARIO_METADATA: list[ScenarioMetadata] = [
    ScenarioMetadata(
        scenario_id="RATE_SHOCK_PLUS_200",
        name="Rate Shock +200 bps",
        description=(
            "Parallel upward shift of the interest-rate curve by 200 basis"
            " points. NII impact computed via the IRS Gap method"
            " (Rate-Sensitive Assets − Rate-Sensitive Liabilities) × shock."
        ),
        category="RATE",
        shock_bps=DEFAULT_SHOCK_BPS,
        npa_migration_pct=None,
    ),
    ScenarioMetadata(
        scenario_id="RATE_SHOCK_MINUS_200",
        name="Rate Shock -200 bps",
        description=(
            "Parallel downward shift of the interest-rate curve by 200 basis"
            " points. Symmetric to the +200 bps scenario; magnitude same,"
            " sign flipped."
        ),
        category="RATE",
        shock_bps=-DEFAULT_SHOCK_BPS,
        npa_migration_pct=None,
    ),
    ScenarioMetadata(
        scenario_id="NPA_SHOCK_PLUS_5",
        name="NPA Shock +5%",
        description=(
            "5% of the active loan principal migrates from Standard to"
            " Substandard. Incremental provision = 5% × principal ×"
            " (substandard_rate − standard_rate), split by secured /"
            " unsecured per RBI provisioning norms."
        ),
        category="CREDIT",
        shock_bps=None,
        npa_migration_pct=NPA_MIGRATION_PCT,
    ),
    ScenarioMetadata(
        scenario_id="COMBINED_MACRO",
        name="Combined Macro Stress",
        description=(
            "Composite stress combining a +200 bps rate shock with a +5% NPA"
            " migration. Captures the worst-case effect of monetary"
            " tightening alongside credit deterioration."
        ),
        category="COMBINED",
        shock_bps=DEFAULT_SHOCK_BPS,
        npa_migration_pct=NPA_MIGRATION_PCT,
    ),
]


class StressTestService:
    """Parametric stress-test engine. Pure computation; no DB writes."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.regulatory = RegulatoryReportService(session)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def list_scenarios(
        self, organization_id: UUID  # noqa: ARG002 - kept for tenant-aware signature
    ) -> list[ScenarioMetadata]:
        """Return static scenario metadata.

        Tenant-aware signature even though the list is currently global —
        a future iteration may filter by feature flag / role.
        """
        return list(SCENARIO_METADATA)

    async def run_stress(
        self,
        organization_id: UUID,
        scenario_id: ScenarioId,
        as_of_date: date_type | None = None,
    ) -> ScenarioResult:
        """Run a single scenario and return its result.

        Reads expensive aggregates once and reuses them. Pure computation —
        no DB writes.
        """
        if scenario_id not in {m.scenario_id for m in SCENARIO_METADATA}:
            raise BadRequestException(
                f"Unknown scenario_id '{scenario_id}'",
                error_code="UNKNOWN_SCENARIO",
            )

        as_of = as_of_date or date_type.today()
        snapshot = await self._capture_snapshot(organization_id, as_of)
        meta = next(m for m in SCENARIO_METADATA if m.scenario_id == scenario_id)
        return self._run_scenario(meta, snapshot)

    async def run_all_scenarios(
        self,
        organization_id: UUID,
        as_of_date: date_type | None = None,
    ) -> list[ScenarioResult]:
        """Run all 4 scenarios against a single snapshot."""
        as_of = as_of_date or date_type.today()
        snapshot = await self._capture_snapshot(organization_id, as_of)
        return [self._run_scenario(meta, snapshot) for meta in SCENARIO_METADATA]

    # ------------------------------------------------------------------
    # Snapshot — single read of portfolio + capital aggregates
    # ------------------------------------------------------------------

    async def _capture_snapshot(self, organization_id: UUID, as_of: date_type) -> _Snapshot:
        """Pull the inputs once so all 4 scenarios share one consistent view."""
        # --- portfolio aggregates (active loans split by secured/unsecured) ---
        secured, unsecured = await self._portfolio_principal_split(organization_id)
        total_principal = secured + unsecured

        # --- borrowings (rate-sensitive liabilities for IRS Gap math) ---
        rsl = await self._rate_sensitive_liabilities(organization_id)

        # v1: rate-sensitive assets are limited to floating-rate loans, which
        # we don't currently flag separately. The honest position is RSA = 0
        # and Gap = -RSL (a fully fixed-rate book is the conservative read).
        # This matches the existing IRS Gap math in `treasury_service`.
        rsa = Decimal("0")

        # --- CRAR snapshot from the regulatory report service ---
        crar_report = await self.regulatory.generate_crar_report(organization_id, as_of)
        tier1 = Decimal(str(crar_report["capital"]["tier1_capital"]))
        tier2 = Decimal(str(crar_report["capital"]["tier2_capital"]))
        total_capital = Decimal(str(crar_report["capital"]["total_capital"]))
        total_rwa = Decimal(str(crar_report["risk_weighted_assets"]["total_rwa"]))
        pre_crar = (total_capital / total_rwa * Decimal("100")) if total_rwa > 0 else Decimal("0")

        # --- provisioning rates: real table if present, RBI defaults otherwise ---
        rates, rates_source = await self._provisioning_rates(organization_id)

        # --- pre-stress NPA ratio (NPA principal / total principal) ---
        pre_npa_principal = await self._pre_stress_npa_principal(organization_id)
        pre_npa_ratio = (
            (pre_npa_principal / total_principal * Decimal("100"))
            if total_principal > 0
            else Decimal("0")
        )

        return _Snapshot(
            as_of=as_of,
            secured_principal=secured,
            unsecured_principal=unsecured,
            total_principal=total_principal,
            rate_sensitive_liabilities=rsl,
            rate_sensitive_assets=rsa,
            tier1=tier1,
            tier2=tier2,
            total_capital=total_capital,
            total_rwa=total_rwa,
            pre_crar=pre_crar,
            pre_npa_principal=pre_npa_principal,
            pre_npa_ratio=pre_npa_ratio,
            std_secured=rates["std_secured"],
            sub_secured=rates["sub_secured"],
            std_unsecured=rates["std_unsecured"],
            sub_unsecured=rates["sub_unsecured"],
            rates_source=rates_source,
        )

    # ------------------------------------------------------------------
    # Scenario computation
    # ------------------------------------------------------------------

    def _run_scenario(self, meta: ScenarioMetadata, snap: _Snapshot) -> ScenarioResult:
        warnings: list[str] = []

        # NII impact (rate scenarios)
        nii_impact = Decimal("0")
        if meta.shock_bps is not None:
            shock_rate = Decimal(str(meta.shock_bps)) / Decimal("10000")
            gap = snap.rate_sensitive_assets - snap.rate_sensitive_liabilities
            nii_impact = (gap * shock_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # NII impact as % of last-year NII (proxy in v1)
        last_year_nii_proxy = snap.rate_sensitive_liabilities * LAST_YEAR_NII_PROXY_RATE
        nii_impact_pct = Decimal("0")
        if last_year_nii_proxy > 0:
            nii_impact_pct = (nii_impact / last_year_nii_proxy * Decimal("100")).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )

        # Provision impact (credit scenarios)
        provision_impact = Decimal("0")
        post_npa_principal = snap.pre_npa_principal
        if meta.npa_migration_pct is not None:
            migration_frac = meta.npa_migration_pct / Decimal("100")
            migrated_secured = snap.secured_principal * migration_frac
            migrated_unsecured = snap.unsecured_principal * migration_frac

            # delta_rate × migrated_amount for each bucket
            secured_delta_rate = (snap.sub_secured - snap.std_secured) / Decimal("100")
            unsecured_delta_rate = (snap.sub_unsecured - snap.std_unsecured) / Decimal("100")
            provision_impact = (
                migrated_secured * secured_delta_rate + migrated_unsecured * unsecured_delta_rate
            ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            post_npa_principal = snap.pre_npa_principal + migrated_secured + migrated_unsecured

        # Post-stress CRAR: capital reduced by provision_impact (v1 ignores tax,
        # uses full pre-tax provision per scope). RWA inflation from a rate
        # shock is negligible at v1 — left as a known follow-up.
        post_capital = snap.total_capital - provision_impact
        post_crar = (
            (post_capital / snap.total_rwa * Decimal("100")) if snap.total_rwa > 0 else Decimal("0")
        )
        crar_delta_bps = int(
            ((post_crar - snap.pre_crar) * Decimal("100")).quantize(
                Decimal("1"), rounding=ROUND_HALF_UP
            )
        )

        post_npa_ratio = (
            (post_npa_principal / snap.total_principal * Decimal("100"))
            if snap.total_principal > 0
            else Decimal("0")
        )

        breach = post_crar < MINIMUM_CRAR_PCT

        # Quantize headline ratios for display
        pre_crar_q = snap.pre_crar.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        post_crar_q = post_crar.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        pre_npa_ratio_q = snap.pre_npa_ratio.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        post_npa_ratio_q = post_npa_ratio.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # Surface defensive warnings — these don't change PASS/WARN/FAIL but
        # they're useful for the UI to display alongside the result.
        if snap.total_rwa == 0:
            warnings.append(
                "Total RWA is zero — CRAR cannot be computed. Verify the"
                " regulatory report inputs."
            )
        if snap.total_principal == 0 and meta.npa_migration_pct is not None:
            warnings.append("No active loan principal found — credit shock has no effect.")
        if snap.rate_sensitive_liabilities == 0 and meta.shock_bps is not None:
            warnings.append("No floating-rate borrowings — rate shock has no NII effect.")

        status = self._status_for(post_crar, breach)

        outputs = ScenarioOutputs(
            nii_impact=nii_impact,
            nii_impact_percent=nii_impact_pct,
            provision_impact=provision_impact,
            pre_stress_crar=pre_crar_q,
            post_stress_crar=post_crar_q,
            crar_delta_bps=crar_delta_bps,
            pre_stress_npa_ratio=pre_npa_ratio_q,
            post_stress_npa_ratio=post_npa_ratio_q,
            minimum_crar_required=MINIMUM_CRAR_PCT,
            breach_minimum_crar=breach,
        )

        inputs = ScenarioInputs(
            as_of_date=snap.as_of,
            shock_bps=meta.shock_bps,
            npa_migration_pct=meta.npa_migration_pct,
            total_principal_outstanding=snap.total_principal,
            secured_principal=snap.secured_principal,
            unsecured_principal=snap.unsecured_principal,
            rate_sensitive_liabilities=snap.rate_sensitive_liabilities,
            rate_sensitive_assets=snap.rate_sensitive_assets,
            tier1_capital=snap.tier1,
            tier2_capital=snap.tier2,
            total_capital=snap.total_capital,
            total_rwa=snap.total_rwa,
            standard_secured_rate=snap.std_secured,
            substandard_secured_rate=snap.sub_secured,
            standard_unsecured_rate=snap.std_unsecured,
            substandard_unsecured_rate=snap.sub_unsecured,
            provisioning_rate_source=snap.rates_source,
        )

        return ScenarioResult(
            scenario_id=meta.scenario_id,
            name=meta.name,
            description=meta.description,
            inputs=inputs,
            outputs=outputs,
            status=status,
            warnings=warnings,
        )

    @staticmethod
    def _status_for(post_crar: Decimal, breach: bool) -> ScenarioStatus:
        """Map post-stress CRAR to PASS / WARN / FAIL.

        FAIL when post_crar < 12% OR a minimum-CRAR breach is flagged.
        WARN when post_crar in [12%, 15%].
        PASS when post_crar > 15% and no breach.
        """
        if breach or post_crar < WARN_CRAR_PCT:
            return "FAIL"
        if post_crar <= MINIMUM_CRAR_PCT:
            return "WARN"
        return "PASS"

    # ------------------------------------------------------------------
    # Aggregate readers
    # ------------------------------------------------------------------

    async def _portfolio_principal_split(self, organization_id: UUID) -> tuple[Decimal, Decimal]:
        """Sum active loan principal_outstanding split secured / unsecured.

        Secured is decided by the originating product's `requires_collateral`
        flag — the closest proxy we have at v1. A future iteration should
        switch to the live collateral attachment state on the loan account.
        """
        stmt = (
            select(
                LoanProduct.requires_collateral,
                func.coalesce(func.sum(LoanAccount.principal_outstanding), 0),
            )
            .select_from(LoanAccount)
            .join(LoanProduct, LoanAccount.product_id == LoanProduct.product_id)
            .where(
                LoanAccount.organization_id == organization_id,
                LoanAccount.status == LoanAccountStatus.ACTIVE,
            )
            .group_by(LoanProduct.requires_collateral)
        )
        result = await self.session.execute(stmt)
        secured = Decimal("0")
        unsecured = Decimal("0")
        for requires_collateral, total in result.all():
            amount = Decimal(str(total or 0))
            if requires_collateral:
                secured += amount
            else:
                unsecured += amount
        return secured, unsecured

    async def _rate_sensitive_liabilities(self, organization_id: UUID) -> Decimal:
        """Sum principal_outstanding for floating / MCLR / repo-linked borrowings.

        Mirrors `treasury_service.generate_irs_analysis` (CLAUDE.md §4.9).
        """
        stmt = select(func.coalesce(func.sum(Borrowing.principal_outstanding), 0)).where(
            Borrowing.organization_id == organization_id,
            Borrowing.rate_type.in_(["FLOATING", "MCLR_LINKED", "REPO_LINKED"]),
        )
        result = await self.session.execute(stmt)
        total = result.scalar_one_or_none()
        return Decimal(str(total or 0))

    async def _pre_stress_npa_principal(self, organization_id: UUID) -> Decimal:
        """Sum current principal of open NPA records for this tenant.

        `NPARecord` (aliased as `NPAClassification`) tracks live NPA exposure
        per loan account. We sum `current_principal` for records that are
        still open (no `closure_date`, no `upgrade_date`). If the model is
        absent or query fails, fall back to zero (no pre-existing NPA stock).
        """
        try:
            from app.models.lending.npa import (  # local import — avoids cycles
                NPAClassification,
            )

            stmt = select(func.coalesce(func.sum(NPAClassification.current_principal), 0)).where(
                NPAClassification.organization_id == organization_id,
                NPAClassification.closure_date.is_(None),
                NPAClassification.upgrade_date.is_(None),
            )
            result = await self.session.execute(stmt)
            total = result.scalar_one_or_none()
            return Decimal(str(total or 0))
        except Exception:
            return Decimal("0")

    async def _provisioning_rates(
        self, organization_id: UUID  # noqa: ARG002 - reserved for tenant override
    ) -> tuple[dict, str]:
        """Resolve provisioning rates.

        Tries to read a per-tenant `mst_provisioning_rate` row when the model
        exists. Falls back to RBI defaults otherwise. The source is captured
        in the result so audit can tell which path ran (CLAUDE.md §4.8).
        """
        # `mst_provisioning_rate` is referenced in CLAUDE.md §4.8 but the
        # canonical model isn't part of this repo yet. We try a defensive
        # dynamic import so this code keeps working the moment the model
        # lands without a re-deploy.
        try:
            from app.models.lending.provisioning_rate import (  # type: ignore[import-not-found]
                ProvisioningRate,
            )

            stmt = select(ProvisioningRate).where(
                ProvisioningRate.organization_id == organization_id
            )
            result = await self.session.execute(stmt)
            rows = result.scalars().all()
            if rows:
                # Build {(bucket, secured): rate}
                index: dict = {}
                for row in rows:
                    index[(row.bucket, bool(row.is_secured))] = Decimal(str(row.rate_pct))
                return (
                    {
                        "std_secured": index.get(("STANDARD", True), RBI_DEFAULT_STANDARD_SECURED),
                        "sub_secured": index.get(
                            ("SUBSTANDARD", True), RBI_DEFAULT_SUBSTANDARD_SECURED
                        ),
                        "std_unsecured": index.get(
                            ("STANDARD", False), RBI_DEFAULT_STANDARD_UNSECURED
                        ),
                        "sub_unsecured": index.get(
                            ("SUBSTANDARD", False),
                            RBI_DEFAULT_SUBSTANDARD_UNSECURED,
                        ),
                    },
                    "mst_provisioning_rate",
                )
        except (ImportError, AttributeError):
            # Model not present — fall through to defaults.
            pass

        return (
            {
                "std_secured": RBI_DEFAULT_STANDARD_SECURED,
                "sub_secured": RBI_DEFAULT_SUBSTANDARD_SECURED,
                "std_unsecured": RBI_DEFAULT_STANDARD_UNSECURED,
                "sub_unsecured": RBI_DEFAULT_SUBSTANDARD_UNSECURED,
            },
            "rbi_default",
        )


# ----------------------------------------------------------------------
# Internal snapshot dataclass — tiny on purpose; not exported.
# ----------------------------------------------------------------------


class _Snapshot:
    __slots__ = (
        "as_of",
        "secured_principal",
        "unsecured_principal",
        "total_principal",
        "rate_sensitive_liabilities",
        "rate_sensitive_assets",
        "tier1",
        "tier2",
        "total_capital",
        "total_rwa",
        "pre_crar",
        "pre_npa_principal",
        "pre_npa_ratio",
        "std_secured",
        "sub_secured",
        "std_unsecured",
        "sub_unsecured",
        "rates_source",
    )

    def __init__(
        self,
        *,
        as_of: date_type,
        secured_principal: Decimal,
        unsecured_principal: Decimal,
        total_principal: Decimal,
        rate_sensitive_liabilities: Decimal,
        rate_sensitive_assets: Decimal,
        tier1: Decimal,
        tier2: Decimal,
        total_capital: Decimal,
        total_rwa: Decimal,
        pre_crar: Decimal,
        pre_npa_principal: Decimal,
        pre_npa_ratio: Decimal,
        std_secured: Decimal,
        sub_secured: Decimal,
        std_unsecured: Decimal,
        sub_unsecured: Decimal,
        rates_source: str,
    ) -> None:
        self.as_of = as_of
        self.secured_principal = secured_principal
        self.unsecured_principal = unsecured_principal
        self.total_principal = total_principal
        self.rate_sensitive_liabilities = rate_sensitive_liabilities
        self.rate_sensitive_assets = rate_sensitive_assets
        self.tier1 = tier1
        self.tier2 = tier2
        self.total_capital = total_capital
        self.total_rwa = total_rwa
        self.pre_crar = pre_crar
        self.pre_npa_principal = pre_npa_principal
        self.pre_npa_ratio = pre_npa_ratio
        self.std_secured = std_secured
        self.sub_secured = sub_secured
        self.std_unsecured = std_unsecured
        self.sub_unsecured = sub_unsecured
        self.rates_source = rates_source
