"""Credit-risk cockpit service for management visibility."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lending.entity import Entity
from app.models.lending.enums import AssetClassification, LoanAccountStatus
from app.models.lending.loan_account import LoanAccount
from app.schemas.lending.risk_cockpit import (
    OverdueBandMetric,
    RiskBucketMetric,
    RiskCockpitResponse,
    RiskCockpitSummary,
    TopRiskExposure,
)

MONEY = Decimal("0.01")
PERCENT = Decimal("0.01")

SMA_CLASSES = {
    AssetClassification.SMA_0,
    AssetClassification.SMA_1,
    AssetClassification.SMA_2,
}
NPA_CLASSES = {
    AssetClassification.NPA,
    AssetClassification.SUBSTANDARD,
    AssetClassification.DOUBTFUL_1,
    AssetClassification.DOUBTFUL_2,
    AssetClassification.DOUBTFUL_3,
    AssetClassification.LOSS,
}
OPEN_STATUSES = {
    LoanAccountStatus.CREATED,
    LoanAccountStatus.ACTIVE,
    LoanAccountStatus.DORMANT,
    LoanAccountStatus.FROZEN,
    LoanAccountStatus.RECALLED,
}
CLASSIFICATION_LABELS = {
    AssetClassification.STANDARD: "Standard",
    AssetClassification.SMA_0: "SMA-0 (1-30 DPD)",
    AssetClassification.SMA_1: "SMA-1 (31-60 DPD)",
    AssetClassification.SMA_2: "SMA-2 (61-90 DPD)",
    AssetClassification.NPA: "NPA",
    AssetClassification.SUBSTANDARD: "Substandard",
    AssetClassification.DOUBTFUL_1: "Doubtful 1",
    AssetClassification.DOUBTFUL_2: "Doubtful 2",
    AssetClassification.DOUBTFUL_3: "Doubtful 3",
    AssetClassification.LOSS: "Loss",
}
OVERDUE_BANDS = (
    ("current", "Current", 0, 0),
    ("dpd_1_30", "1-30 DPD", 1, 30),
    ("dpd_31_60", "31-60 DPD", 31, 60),
    ("dpd_61_90", "61-90 DPD", 61, 90),
    ("dpd_91_365", "91-365 DPD", 91, 365),
    ("dpd_365_plus", "365+ DPD", 366, None),
)


@dataclass
class BucketAccumulator:
    """Mutable accumulator for risk buckets."""

    count: int = 0
    outstanding: Decimal = Decimal("0")
    provision_required: Decimal = Decimal("0")
    provision_held: Decimal = Decimal("0")


@dataclass
class RiskAccumulator:
    """Mutable accumulator for one cockpit calculation."""

    total_accounts: int = 0
    total_outstanding: Decimal = Decimal("0")
    overdue_accounts: int = 0
    overdue_amount: Decimal = Decimal("0")
    sma_accounts: int = 0
    sma_amount: Decimal = Decimal("0")
    npa_accounts: int = 0
    npa_amount: Decimal = Decimal("0")
    provision_required: Decimal = Decimal("0")
    provision_held: Decimal = Decimal("0")
    classifications: dict[AssetClassification, BucketAccumulator] = field(
        default_factory=lambda: {
            classification: BucketAccumulator() for classification in AssetClassification
        }
    )
    overdue_bands: dict[str, BucketAccumulator] = field(
        default_factory=lambda: {band: BucketAccumulator() for band, _, _, _ in OVERDUE_BANDS}
    )


class RiskCockpitService:
    """Builds a corporate-loan risk cockpit from LMS account state."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_cockpit(
        self,
        organization_id: UUID,
        *,
        top_n: int = 10,
    ) -> RiskCockpitResponse:
        rows = await self._load_open_loans(organization_id)
        accumulator = RiskAccumulator()

        for loan, borrower_name in rows:
            self._add_loan(accumulator, loan)

        top_exposures = self._top_exposures(rows, top_n)
        return RiskCockpitResponse(
            summary=self._summary(accumulator),
            asset_classification=self._classification_rows(accumulator),
            overdue_bands=self._overdue_band_rows(accumulator),
            top_exposures=top_exposures,
        )

    async def _load_open_loans(
        self,
        organization_id: UUID,
    ) -> list[tuple[LoanAccount, str]]:
        result = await self.db.execute(
            select(LoanAccount, Entity.legal_name)
            .join(Entity, Entity.id == LoanAccount.entity_id)
            .where(
                LoanAccount.organization_id == organization_id,
                LoanAccount.status.in_(tuple(OPEN_STATUSES)),
                LoanAccount.is_active.is_(True),
            )
        )
        return [(loan, borrower_name) for loan, borrower_name in result.all()]

    def _add_loan(self, accumulator: RiskAccumulator, loan: LoanAccount) -> None:
        classification = loan.asset_classification or AssetClassification.STANDARD
        outstanding = self._money(loan.total_outstanding)
        overdue_amount = self._money(
            (loan.principal_overdue or Decimal("0"))
            + (loan.interest_overdue or Decimal("0"))
            + (loan.penal_interest_outstanding or Decimal("0"))
            + (loan.charges_outstanding or Decimal("0"))
        )
        provision_required = self._money(loan.provision_amount)
        provision_held = self._money(loan.provision_held)
        dpd = int(loan.days_past_due or 0)

        accumulator.total_accounts += 1
        accumulator.total_outstanding += outstanding
        accumulator.provision_required += provision_required
        accumulator.provision_held += provision_held

        if dpd > 0 or overdue_amount > 0:
            accumulator.overdue_accounts += 1
            accumulator.overdue_amount += overdue_amount

        if classification in SMA_CLASSES:
            accumulator.sma_accounts += 1
            accumulator.sma_amount += outstanding

        if classification in NPA_CLASSES:
            accumulator.npa_accounts += 1
            accumulator.npa_amount += outstanding

        classification_bucket = accumulator.classifications[classification]
        classification_bucket.count += 1
        classification_bucket.outstanding += outstanding
        classification_bucket.provision_required += provision_required
        classification_bucket.provision_held += provision_held

        overdue_bucket = accumulator.overdue_bands[self._dpd_band(dpd)]
        overdue_bucket.count += 1
        overdue_bucket.outstanding += outstanding

    def _summary(self, accumulator: RiskAccumulator) -> RiskCockpitSummary:
        provision_gap = max(
            accumulator.provision_required - accumulator.provision_held,
            Decimal("0"),
        )
        return RiskCockpitSummary(
            total_accounts=accumulator.total_accounts,
            total_outstanding=self._money(accumulator.total_outstanding),
            overdue_accounts=accumulator.overdue_accounts,
            overdue_amount=self._money(accumulator.overdue_amount),
            sma_accounts=accumulator.sma_accounts,
            sma_amount=self._money(accumulator.sma_amount),
            npa_accounts=accumulator.npa_accounts,
            npa_amount=self._money(accumulator.npa_amount),
            gross_npa_percent=self._percent(
                accumulator.npa_amount,
                accumulator.total_outstanding,
            ),
            provision_required=self._money(accumulator.provision_required),
            provision_held=self._money(accumulator.provision_held),
            provision_gap=self._money(provision_gap),
            provision_coverage_percent=self._percent(
                accumulator.provision_held,
                accumulator.npa_amount,
            ),
        )

    def _classification_rows(
        self,
        accumulator: RiskAccumulator,
    ) -> list[RiskBucketMetric]:
        rows: list[RiskBucketMetric] = []
        for classification in AssetClassification:
            bucket = accumulator.classifications[classification]
            provision_gap = max(
                bucket.provision_required - bucket.provision_held,
                Decimal("0"),
            )
            rows.append(
                RiskBucketMetric(
                    classification=classification.value,
                    label=CLASSIFICATION_LABELS[classification],
                    account_count=bucket.count,
                    outstanding=self._money(bucket.outstanding),
                    portfolio_percent=self._percent(
                        bucket.outstanding,
                        accumulator.total_outstanding,
                    ),
                    provision_required=self._money(bucket.provision_required),
                    provision_held=self._money(bucket.provision_held),
                    provision_gap=self._money(provision_gap),
                    provision_coverage_percent=self._percent(
                        bucket.provision_held,
                        bucket.provision_required,
                    ),
                )
            )
        return rows

    def _overdue_band_rows(
        self,
        accumulator: RiskAccumulator,
    ) -> list[OverdueBandMetric]:
        return [
            OverdueBandMetric(
                band=band,
                label=label,
                account_count=accumulator.overdue_bands[band].count,
                outstanding=self._money(accumulator.overdue_bands[band].outstanding),
                portfolio_percent=self._percent(
                    accumulator.overdue_bands[band].outstanding,
                    accumulator.total_outstanding,
                ),
            )
            for band, label, _, _ in OVERDUE_BANDS
        ]

    def _top_exposures(
        self,
        rows: list[tuple[LoanAccount, str]],
        top_n: int,
    ) -> list[TopRiskExposure]:
        risky_rows = [
            (loan, borrower_name)
            for loan, borrower_name in rows
            if (loan.days_past_due or 0) > 0
            or (loan.asset_classification or AssetClassification.STANDARD)
            != AssetClassification.STANDARD
        ]
        risky_rows.sort(
            key=lambda row: (
                self._money(row[0].total_outstanding),
                int(row[0].days_past_due or 0),
            ),
            reverse=True,
        )

        exposures: list[TopRiskExposure] = []
        for loan, borrower_name in risky_rows[:top_n]:
            provision_required = self._money(loan.provision_amount)
            provision_held = self._money(loan.provision_held)
            overdue_amount = self._money(
                (loan.principal_overdue or Decimal("0"))
                + (loan.interest_overdue or Decimal("0"))
                + (loan.penal_interest_outstanding or Decimal("0"))
                + (loan.charges_outstanding or Decimal("0"))
            )
            exposures.append(
                TopRiskExposure(
                    loan_account_id=loan.id,
                    loan_account_number=loan.loan_account_number,
                    borrower_name=borrower_name,
                    asset_classification=(
                        loan.asset_classification or AssetClassification.STANDARD
                    ).value,
                    days_past_due=int(loan.days_past_due or 0),
                    total_outstanding=self._money(loan.total_outstanding),
                    overdue_amount=overdue_amount,
                    provision_required=provision_required,
                    provision_held=provision_held,
                    provision_coverage_percent=self._percent(
                        provision_held,
                        provision_required,
                    ),
                    npa_date=loan.npa_date.isoformat() if loan.npa_date else None,
                    oldest_due_date=(
                        loan.oldest_due_date.isoformat() if loan.oldest_due_date else None
                    ),
                )
            )
        return exposures

    @staticmethod
    def _dpd_band(dpd: int) -> str:
        for band, _, start, end in OVERDUE_BANDS:
            if end is None and dpd >= start:
                return band
            if end is not None and start <= dpd <= end:
                return band
        return "current"

    @staticmethod
    def _money(value: Decimal | int | float | None) -> Decimal:
        return Decimal(str(value or 0)).quantize(MONEY, rounding=ROUND_HALF_UP)

    @staticmethod
    def _percent(numerator: Decimal, denominator: Decimal) -> Decimal:
        if not denominator:
            return Decimal("0.00")
        return ((numerator / denominator) * Decimal("100")).quantize(
            PERCENT,
            rounding=ROUND_HALF_UP,
        )
