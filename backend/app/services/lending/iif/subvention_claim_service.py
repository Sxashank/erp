"""Subvention claim lifecycle + compute + report.

Owns ``txn_subvention_claim`` and is the workhorse of the IIF module.

Key responsibilities:

- ``compute_claim`` — sum of receipt-allocated interest in a period ×
  scheme rate, returning a Decimal pair without persisting.
- ``eligible_periods`` — for an enrolment, list the next claimable
  periods aligned to the Indian fiscal year (Apr–Mar).
- ``create_claim`` / ``submit_claim`` / ``verify_claim`` /
  ``initiate_release`` / ``mark_released`` / ``cancel_claim`` —
  lifecycle transitions.
- ``generate_claim_report`` — structured payload that can be rendered
  as PDF / Excel / JSON. The route layer is responsible for turning
  the structured dict into a binary; we expose the data shape here so
  the report stays a function of the data, not of the renderer.

All Decimal arithmetic — never float (CLAUDE.md §6.2). The service owns
the transaction boundary indirectly: route calls ``async with
db.begin()`` and we ``flush()`` within it.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    NotFoundException,
)
from app.models.auth.user import User
from app.models.lending.enums import (
    AllocationComponent,
    ClaimFrequency,
    ReceiptStatus,
    SubventionClaimStatus,
    SubventionEnrollmentStatus,
)
from app.models.lending.iif.loan_subvention_enrollment import (
    LoanSubventionEnrollment,
)
from app.models.lending.iif.subvention_claim import SubventionClaim
from app.models.lending.iif.subvention_fund_transaction import SubventionFundTransaction
from app.models.lending.iif.subvention_scheme import SubventionScheme
from app.models.lending.loan_account import (
    Disbursement,
    LoanAccount,
    LoanReceipt,
    ReceiptAllocation,
)
from app.models.lending.sanction import LoanSanction
from app.services.audit import record_financial_action
from app.schemas.lending.iif import (
    ClaimAccountStatus,
    ClaimReportFooter,
    ClaimReportHeader,
    ClaimReportResponse,
    EligibleClaimPeriod,
    EligibleClaimPeriodResponse,
    InterestCalculationLine,
    RepaymentRecordLine,
    SubventionClaimDocumentInput,
)
from app.core.iif_rules import (
    CALCULATION_PERCENT_OF_INTEREST_PAID,
    calculation_rules,
    eligibility_rules,
    fund_rules,
    missing_required_documents,
)

# ---------------------------------------------------------------------------
# Indian fiscal year helpers (Apr 1 → Mar 31)
# ---------------------------------------------------------------------------


def _fy_start_year(d: date) -> int:
    """Return the FY-start calendar year for date ``d``.

    Apr 2026 → 2026, Mar 2026 → 2025.
    """
    return d.year if d.month >= 4 else d.year - 1


def _quarter_of(d: date) -> int:
    """Quarter number 1..4 within the Indian FY for date ``d``."""
    m = d.month
    if m in (4, 5, 6):
        return 1
    if m in (7, 8, 9):
        return 2
    if m in (10, 11, 12):
        return 3
    return 4  # Jan, Feb, Mar


def _half_of(d: date) -> int:
    """Half-year number 1..2 within the Indian FY for date ``d``."""
    return 1 if d.month >= 4 and d.month <= 9 else 2


def _quarter_bounds(fy_start_year: int, q: int) -> tuple[date, date]:
    """Return (period_start, period_end) for a fiscal quarter."""
    starts = {
        1: date(fy_start_year, 4, 1),
        2: date(fy_start_year, 7, 1),
        3: date(fy_start_year, 10, 1),
        4: date(fy_start_year + 1, 1, 1),
    }
    ends = {
        1: date(fy_start_year, 6, 30),
        2: date(fy_start_year, 9, 30),
        3: date(fy_start_year, 12, 31),
        4: date(fy_start_year + 1, 3, 31),
    }
    return starts[q], ends[q]


def _half_bounds(fy_start_year: int, h: int) -> tuple[date, date]:
    if h == 1:
        return date(fy_start_year, 4, 1), date(fy_start_year, 9, 30)
    return date(fy_start_year, 10, 1), date(fy_start_year + 1, 3, 31)


def _year_bounds(fy_start_year: int) -> tuple[date, date]:
    return date(fy_start_year, 4, 1), date(fy_start_year + 1, 3, 31)


def _format_fy(fy_start_year: int) -> str:
    """`FY 2026-27` style label."""
    return f"FY {fy_start_year}-{(fy_start_year + 1) % 100:02d}"


_MONTH_SHORT = [
    "",
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
]


def _label_for_period(period_start: date, period_end: date, claim_frequency: str) -> str:
    fy = _fy_start_year(period_start)
    if claim_frequency == ClaimFrequency.QUARTERLY.value:
        q = _quarter_of(period_start)
        return (
            f"{_format_fy(fy)} Q{q} "
            f"({_MONTH_SHORT[period_start.month]}-{_MONTH_SHORT[period_end.month]} "
            f"{period_end.year})"
        )
    if claim_frequency == ClaimFrequency.HALF_YEARLY.value:
        h = _half_of(period_start)
        return (
            f"{_format_fy(fy)} H{h} "
            f"({_MONTH_SHORT[period_start.month]}-{_MONTH_SHORT[period_end.month]} "
            f"{period_end.year})"
        )
    return _format_fy(fy)


def _reference_suffix(period_start: date, claim_frequency: str) -> str:
    """`2026Q1`, `2026H1`, `2026` slice of the reference."""
    fy = _fy_start_year(period_start)
    if claim_frequency == ClaimFrequency.QUARTERLY.value:
        return f"{fy}Q{_quarter_of(period_start)}"
    if claim_frequency == ClaimFrequency.HALF_YEARLY.value:
        return f"{fy}H{_half_of(period_start)}"
    return f"{fy}"


_DECLARATION_TEXT = (
    "We hereby declare that the information furnished above is true and "
    "correct to the best of our knowledge, that the claimed interest "
    "amount has not been claimed under any other subvention / "
    "incentivisation scheme, and that the borrower account is in regular "
    "repayment status as on the period-end date. We further undertake to "
    "refund any over-claim with interest as per the scheme guidelines."
)


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class SubventionClaimService:
    """Service for the subvention-claim lifecycle."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # =========================================================================
    # Period helpers
    # =========================================================================

    async def eligible_periods(
        self,
        organization_id: UUID,
        enrollment_id: UUID,
        *,
        lookback_periods: int = 4,
    ) -> EligibleClaimPeriodResponse:
        """List the candidate periods that can be claimed next.

        Starts from the enrolment date and walks forward in the
        scheme's claim cadence. Periods entirely in the future are
        excluded; periods fully covered by an existing non-CANCELLED
        claim are flagged ``already_claimed=True``.
        """
        enrollment = await self._get_enrollment(organization_id, enrollment_id)
        scheme = enrollment.scheme
        today = date.today()

        periods: list[tuple[date, date]] = []
        if scheme.claim_frequency == ClaimFrequency.QUARTERLY.value:
            # Iterate fiscal quarters from enrolment date forward.
            fy = _fy_start_year(enrollment.enrolled_date)
            q = _quarter_of(enrollment.enrolled_date)
            while True:
                start, end = _quarter_bounds(fy, q)
                if end > today:
                    break
                periods.append((start, end))
                q += 1
                if q > 4:
                    q = 1
                    fy += 1
        elif scheme.claim_frequency == ClaimFrequency.HALF_YEARLY.value:
            fy = _fy_start_year(enrollment.enrolled_date)
            h = _half_of(enrollment.enrolled_date)
            while True:
                start, end = _half_bounds(fy, h)
                if end > today:
                    break
                periods.append((start, end))
                h += 1
                if h > 2:
                    h = 1
                    fy += 1
        else:  # YEARLY
            fy = _fy_start_year(enrollment.enrolled_date)
            while True:
                start, end = _year_bounds(fy)
                if end > today:
                    break
                periods.append((start, end))
                fy += 1

        # Optionally truncate to the last N periods so the UI's "next
        # claim" picker stays focused.
        periods = periods[-lookback_periods * 2 :] if periods else []

        # Look up existing claims for any of these periods.
        existing_stmt = select(SubventionClaim).where(
            SubventionClaim.enrollment_id == enrollment_id,
            SubventionClaim.organization_id == organization_id,
            SubventionClaim.deleted_at.is_(None),
        )
        existing = list((await self.session.execute(existing_stmt)).scalars().all())
        by_period: dict[tuple[date, date], SubventionClaim] = {
            (c.period_start, c.period_end): c for c in existing
        }

        out: list[EligibleClaimPeriod] = []
        for start, end in periods:
            existing_claim = by_period.get((start, end))
            already = (
                existing_claim is not None
                and existing_claim.status != SubventionClaimStatus.CANCELLED.value
            )
            out.append(
                EligibleClaimPeriod(
                    period_start=start,
                    period_end=end,
                    label=_label_for_period(start, end, scheme.claim_frequency),
                    claim_frequency=scheme.claim_frequency,
                    already_claimed=already,
                    existing_claim_id=existing_claim.id if existing_claim else None,
                    existing_status=existing_claim.status if existing_claim else None,
                )
            )

        return EligibleClaimPeriodResponse(
            enrollment_id=enrollment_id,
            claim_frequency=scheme.claim_frequency,
            periods=out,
        )

    # =========================================================================
    # Compute
    # =========================================================================

    async def compute_claim(
        self,
        organization_id: UUID,
        enrollment_id: UUID,
        period_start: date,
        period_end: date,
    ) -> tuple[Decimal, Decimal, Decimal, str, Decimal]:
        """Compute (interest_paid, rate, applicable_subvention, method, base).

        Sums ``ReceiptAllocation.allocated_amount`` where
        ``allocation_component == INTEREST`` over receipts whose
        ``value_date`` falls in ``[period_start, period_end]`` and the
        receipt belongs to the enrolment's loan account. Bounced /
        reversed receipts are excluded.

        The default IIF method applies a 3 percentage-point annual incentive
        on principal-days, capped by actual interest paid in the period. A
        legacy ``PERCENT_OF_INTEREST_PAID`` method remains configurable for
        non-IIF schemes.
        """
        if period_end < period_start:
            raise BadRequestException(
                "period_end must be on or after period_start",
                error_code="INVALID_PERIOD",
            )

        enrollment = await self._get_enrollment(organization_id, enrollment_id)
        scheme = enrollment.scheme
        loan_account_id = enrollment.loan_account_id
        loan = enrollment.loan_account

        stmt = (
            select(
                func.coalesce(
                    func.sum(ReceiptAllocation.allocated_amount),
                    Decimal("0"),
                )
            )
            .select_from(ReceiptAllocation)
            .join(LoanReceipt, LoanReceipt.id == ReceiptAllocation.receipt_id)
            .where(
                LoanReceipt.organization_id == organization_id,
                LoanReceipt.loan_account_id == loan_account_id,
                LoanReceipt.value_date >= period_start,
                LoanReceipt.value_date <= period_end,
                LoanReceipt.deleted_at.is_(None),
                LoanReceipt.bounced.is_(False),
                LoanReceipt.status != ReceiptStatus.REVERSED,
                ReceiptAllocation.allocation_component == AllocationComponent.INTEREST,
                ReceiptAllocation.deleted_at.is_(None),
            )
        )
        interest_paid_raw = (await self.session.execute(stmt)).scalar_one()
        interest_paid = Decimal(interest_paid_raw or 0)

        rate = scheme.subvention_rate_percent
        rules = calculation_rules(scheme)
        method = str(rules.get("method") or "")
        if method == CALCULATION_PERCENT_OF_INTEREST_PAID:
            eligible_base = interest_paid
            applicable = interest_paid * rate / Decimal("100")
        else:
            eligible_base = await self._eligible_principal_years(
                loan=loan,
                period_start=period_start,
                period_end=period_end,
            )
            applicable = eligible_base * rate / Decimal("100")
            if rules.get("cap_by_actual_interest_paid", True):
                applicable = min(applicable, interest_paid)

        applicable = applicable.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        interest_paid = interest_paid.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        eligible_base = eligible_base.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        return interest_paid, rate, applicable, method, eligible_base

    # =========================================================================
    # Lifecycle
    # =========================================================================

    async def create_claim(
        self,
        organization_id: UUID,
        enrollment_id: UUID,
        period_start: date,
        period_end: date,
        documents: list[SubventionClaimDocumentInput] | None,
        current_user: User,
    ) -> SubventionClaim:
        """Create a DRAFT claim. Idempotency is enforced upstream via
        the ``Idempotency-Key`` header + the unique (org,
        claim_reference) constraint."""
        enrollment = await self._get_enrollment(organization_id, enrollment_id)
        scheme = enrollment.scheme

        if enrollment.status != SubventionEnrollmentStatus.ENROLLED.value:
            raise BadRequestException(
                f"Enrollment must be ENROLLED to raise a claim; status is " f"{enrollment.status}",
                error_code="ENROLLMENT_NOT_ACTIVE",
            )

        if period_end < period_start:
            raise BadRequestException(
                "period_end must be on or after period_start",
                error_code="INVALID_PERIOD",
            )

        # Reject claims for the same period that already exist and are
        # not cancelled.
        dup_stmt = select(SubventionClaim).where(
            SubventionClaim.enrollment_id == enrollment_id,
            SubventionClaim.organization_id == organization_id,
            SubventionClaim.deleted_at.is_(None),
            SubventionClaim.period_start == period_start,
            SubventionClaim.period_end == period_end,
            SubventionClaim.status != SubventionClaimStatus.CANCELLED.value,
        )
        if (await self.session.execute(dup_stmt)).scalar_one_or_none():
            raise ConflictException(
                "A non-cancelled claim already exists for this period",
                error_code="CLAIM_EXISTS",
            )

        await self._validate_claim_account_eligibility(enrollment, stage="claim creation")

        interest_paid, _rate, applicable, _method, _base = await self.compute_claim(
            organization_id, enrollment_id, period_start, period_end
        )

        reference = await self._next_claim_reference(
            organization_id,
            scheme.scheme_code,
            scheme.claim_frequency,
            period_start,
        )

        documents_payload = [
            {
                "document_id": (str(d.document_id) if d.document_id is not None else None),
                "name": d.name,
                "file_name": d.file_name or d.name,
                "document_category": d.document_category,
                "path": d.path,
                "uploaded_at": (d.uploaded_at or datetime.now(UTC)).isoformat(),
            }
            for d in (documents or [])
        ]

        claim = SubventionClaim(
            organization_id=organization_id,
            enrollment_id=enrollment_id,
            claim_reference=reference,
            period_start=period_start,
            period_end=period_end,
            claim_frequency=scheme.claim_frequency,
            interest_paid_in_period=interest_paid,
            applicable_subvention_amount=applicable,
            status=SubventionClaimStatus.DRAFT.value,
            documents=documents_payload,
            created_by=current_user.id,
        )
        self.session.add(claim)
        await self.session.flush()
        await self.session.refresh(claim)
        return claim

    async def update_documents(
        self,
        organization_id: UUID,
        claim_id: UUID,
        documents: list[SubventionClaimDocumentInput],
        current_user: User,
    ) -> SubventionClaim:
        claim = await self.get(organization_id, claim_id)
        if claim.status != SubventionClaimStatus.DRAFT.value:
            raise BadRequestException(
                "Documents can only be edited on DRAFT claims",
                error_code="INVALID_TRANSITION",
            )
        claim.documents = [
            {
                "document_id": (str(d.document_id) if d.document_id is not None else None),
                "name": d.name,
                "file_name": d.file_name or d.name,
                "document_category": d.document_category,
                "path": d.path,
                "uploaded_at": (d.uploaded_at or datetime.now(UTC)).isoformat(),
            }
            for d in documents
        ]
        claim.updated_by = current_user.id
        claim.version = (claim.version or 1) + 1
        await self.session.flush()
        await self.session.refresh(claim)
        return claim

    async def submit_claim(
        self,
        organization_id: UUID,
        claim_id: UUID,
        declaration_signed_at: datetime | None,
        current_user: User,
    ) -> SubventionClaim:
        claim = await self.get(organization_id, claim_id)
        if claim.status != SubventionClaimStatus.DRAFT.value:
            raise BadRequestException(
                f"Cannot submit claim in status {claim.status}",
                error_code="INVALID_TRANSITION",
            )
        enrollment = await self._get_enrollment(organization_id, claim.enrollment_id)
        await self._validate_claim_account_eligibility(enrollment, stage="claim submission")
        missing_docs = missing_required_documents(
            enrollment.scheme,
            claim.documents or [],
            stage="CLAIM_SUBMISSION",
        )
        if missing_docs:
            raise BadRequestException(
                "Required IIF claim documents are missing: " + "; ".join(missing_docs),
                error_code="IIF_REQUIRED_DOCUMENTS_MISSING",
            )
        claim.status = SubventionClaimStatus.SUBMITTED.value
        claim.submitted_date = date.today()
        claim.declaration_signed_by = current_user.id
        claim.declaration_signed_at = declaration_signed_at or datetime.now(UTC)
        claim.updated_by = current_user.id
        claim.version = (claim.version or 1) + 1
        # Roll the enrolment's running total up.
        enrollment.total_claimed_to_date = (
            enrollment.total_claimed_to_date or Decimal("0")
        ) + claim.applicable_subvention_amount
        enrollment.updated_by = current_user.id
        enrollment.version = (enrollment.version or 1) + 1

        await self.session.flush()
        await self.session.refresh(claim)
        return claim

    async def verify_claim(
        self,
        organization_id: UUID,
        claim_id: UUID,
        decision: str,
        reason: str | None,
        current_user: User,
    ) -> SubventionClaim:
        claim = await self.get(organization_id, claim_id)
        if claim.status != SubventionClaimStatus.SUBMITTED.value:
            raise BadRequestException(
                f"Cannot verify claim in status {claim.status}",
                error_code="INVALID_TRANSITION",
            )
        if decision == "APPROVE":
            enrollment = await self._get_enrollment(organization_id, claim.enrollment_id)
            await self._validate_claim_account_eligibility(enrollment, stage="claim verification")
            claim.status = SubventionClaimStatus.VERIFIED.value
            claim.verified_date = date.today()
        elif decision == "REJECT":
            claim.status = SubventionClaimStatus.REJECTED.value
            claim.rejection_reason = reason
            # Undo the claimed-to-date contribution.
            enrollment = await self._get_enrollment(organization_id, claim.enrollment_id)
            enrollment.total_claimed_to_date = (
                enrollment.total_claimed_to_date or Decimal("0")
            ) - claim.applicable_subvention_amount
            if enrollment.total_claimed_to_date < Decimal("0"):
                enrollment.total_claimed_to_date = Decimal("0")
            enrollment.updated_by = current_user.id
            enrollment.version = (enrollment.version or 1) + 1
        else:
            raise BadRequestException(
                f"Unknown decision {decision!r}",
                error_code="INVALID_DECISION",
            )
        claim.updated_by = current_user.id
        claim.version = (claim.version or 1) + 1
        await self.session.flush()
        await self.session.refresh(claim)
        return claim

    async def initiate_release(
        self,
        organization_id: UUID,
        claim_id: UUID,
        release_instruction_reference: str,
        release_initiated_date: date | None,
        release_instruction_notes: str | None,
        current_user: User,
    ) -> SubventionClaim:
        claim = await self.get(organization_id, claim_id)
        if claim.status != SubventionClaimStatus.VERIFIED.value:
            raise BadRequestException(
                f"Cannot initiate release in status {claim.status}",
                error_code="INVALID_TRANSITION",
            )
        enrollment = await self._get_enrollment(organization_id, claim.enrollment_id)
        await self._validate_claim_account_eligibility(enrollment, stage="release initiation")
        claim.status = SubventionClaimStatus.RELEASE_IN_PROGRESS.value
        claim.release_initiated_date = release_initiated_date or date.today()
        claim.release_instruction_reference = release_instruction_reference.strip()
        claim.release_instruction_notes = (
            release_instruction_notes.strip() if release_instruction_notes else None
        )
        claim.updated_by = current_user.id
        claim.version = (claim.version or 1) + 1
        await self.session.flush()
        await self.session.refresh(claim)
        return claim

    async def mark_released(
        self,
        organization_id: UUID,
        claim_id: UUID,
        release_reference: str,
        released_date: date | None,
        current_user: User,
    ) -> SubventionClaim:
        claim = await self.get(organization_id, claim_id)
        if claim.status != SubventionClaimStatus.RELEASE_IN_PROGRESS.value:
            raise BadRequestException(
                f"Cannot mark released in status {claim.status}",
                error_code="INVALID_TRANSITION",
            )
        enrollment = await self._get_enrollment(organization_id, claim.enrollment_id)
        await self._validate_claim_account_eligibility(enrollment, stage="release")

        before_snapshot = {
            "status": claim.status,
            "paid_date": claim.paid_date,
            "utr_reference": claim.utr_reference,
            "applicable_subvention_amount": claim.applicable_subvention_amount,
        }

        claim.status = SubventionClaimStatus.RELEASED.value
        claim.paid_date = released_date or date.today()
        claim.utr_reference = release_reference.strip()
        claim.updated_by = current_user.id
        claim.version = (claim.version or 1) + 1
        enrollment.total_paid_to_date = (
            enrollment.total_paid_to_date or Decimal("0")
        ) + claim.applicable_subvention_amount
        enrollment.updated_by = current_user.id
        enrollment.version = (enrollment.version or 1) + 1
        await self.session.flush()
        await self.session.refresh(claim)

        if fund_rules(enrollment.scheme).get("dedicated_bank_account_required", True):
            self.session.add(
                SubventionFundTransaction(
                    organization_id=organization_id,
                    scheme_id=enrollment.scheme_id,
                    claim_id=claim.id,
                    transaction_type="CLAIM_RELEASE",
                    transaction_date=claim.paid_date or date.today(),
                    amount=-claim.applicable_subvention_amount,
                    reference_number=claim.utr_reference,
                    notes="Interest incentive released to borrower loan account",
                    created_by=current_user.id,
                )
            )
            await self.session.flush()

        # Domain audit: IIF subvention claim released — §8.5.
        # Captures the released amount + UTR + paid_date for the auditor trail.
        await record_financial_action(
            self.session,
            organization_id=organization_id,
            entity_type="SUBVENTION_CLAIM",
            entity_id=claim.id,
            entity_reference=claim.claim_reference,
            action="IIF_CLAIM_RELEASE",
            user_id=current_user.id,
            before=before_snapshot,
            after={
                "status": claim.status,
                "paid_date": claim.paid_date,
                "utr_reference": claim.utr_reference,
                "applicable_subvention_amount": claim.applicable_subvention_amount,
            },
            metadata={
                "transaction_type": "IIF_CLAIM_RELEASE",
                "enrollment_id": str(claim.enrollment_id),
                "released_amount": str(claim.applicable_subvention_amount),
                "utr_reference": claim.utr_reference,
                "paid_date": claim.paid_date.isoformat() if claim.paid_date else None,
                "enrollment_total_paid_to_date": str(enrollment.total_paid_to_date),
            },
            change_reason="IIF subvention claim released (UTR booked)",
        )

        return claim

    async def _eligible_principal_years(
        self,
        *,
        loan: LoanAccount,
        period_start: date,
        period_end: date,
    ) -> Decimal:
        """Return principal-years eligible for annual-rate incentive.

        Uses actual disbursement tranches when present. When legacy data lacks
        tranche rows, falls back to current outstanding for the period.
        """
        stmt = (
            select(Disbursement)
            .where(
                Disbursement.loan_account_id == loan.id,
                Disbursement.deleted_at.is_(None),
                Disbursement.disbursed_amount.is_not(None),
                Disbursement.disbursement_date.is_not(None),
            )
            .order_by(Disbursement.disbursement_number.asc())
        )
        disbursements = list((await self.session.execute(stmt)).scalars().all())
        principal_days = Decimal("0")
        for disbursement in disbursements:
            start = max(disbursement.disbursement_date, period_start)
            if start > period_end:
                continue
            days = (period_end - start).days + 1
            principal_days += (disbursement.disbursed_amount or Decimal("0")) * Decimal(days)

        if principal_days == 0:
            days = (period_end - period_start).days + 1
            principal_days = (loan.principal_outstanding or Decimal("0")) * Decimal(days)

        return principal_days / Decimal("365")

    async def _validate_claim_account_eligibility(
        self,
        enrollment: LoanSubventionEnrollment,
        *,
        stage: str,
    ) -> None:
        """Re-check continuous-assistance conditions at claim/release time."""
        scheme = enrollment.scheme
        loan = enrollment.loan_account
        rules = eligibility_rules(scheme)
        max_dpd = int(scheme.npa_disqualification_dpd_days or 30)
        reasons: list[str] = []

        if rules.get("exclude_overdue_or_npa", True):
            if int(loan.days_past_due or 0) > max_dpd:
                reasons.append(f"DPD {loan.days_past_due} exceeds allowed {max_dpd}")
            asset_class = (
                loan.asset_classification.value
                if hasattr(loan.asset_classification, "value")
                else str(loan.asset_classification)
            )
            if asset_class.upper() != "STANDARD":
                reasons.append(f"Loan asset classification is {asset_class}, not STANDARD")
            if (loan.principal_overdue or Decimal("0")) > 0 or (
                loan.interest_overdue or Decimal("0")
            ) > 0:
                reasons.append("Loan has principal or interest overdue")

        if rules.get("exclude_refinance_takeover_restructure", True):
            sanction = await self.session.get(LoanSanction, loan.sanction_id)
            extra = {}
            if sanction is not None:
                from app.models.lending.application import LoanApplication

                application = await self.session.get(LoanApplication, sanction.application_id)
                extra = dict(getattr(application, "extra_data", None) or {})
            for key in ("is_refinance", "is_takeover", "is_restructure", "is_restructured"):
                if extra.get(key) is True:
                    reasons.append(f"Loan application is flagged {key}=true")

        if reasons:
            raise BadRequestException(
                f"IIF {stage} is not allowed: " + "; ".join(reasons),
                error_code="IIF_CONTINUOUS_ASSISTANCE_BLOCKED",
            )

    async def mark_paid(
        self,
        organization_id: UUID,
        claim_id: UUID,
        utr_reference: str,
        paid_date: date | None,
        current_user: User,
    ) -> SubventionClaim:
        """Backward-compatible alias for the older mark-paid API."""

        return await self.mark_released(
            organization_id,
            claim_id,
            utr_reference,
            paid_date,
            current_user,
        )

    async def cancel_claim(
        self,
        organization_id: UUID,
        claim_id: UUID,
        reason: str,
        current_user: User,
    ) -> SubventionClaim:
        claim = await self.get(organization_id, claim_id)
        if claim.status in {
            SubventionClaimStatus.RELEASED.value,
            SubventionClaimStatus.CANCELLED.value,
        }:
            raise BadRequestException(
                f"Cannot cancel claim in status {claim.status}",
                error_code="INVALID_TRANSITION",
            )

        # If the claim had pushed totals, roll them back.
        if claim.status in {
            SubventionClaimStatus.SUBMITTED.value,
            SubventionClaimStatus.VERIFIED.value,
            SubventionClaimStatus.RELEASE_IN_PROGRESS.value,
        }:
            enrollment = await self._get_enrollment(organization_id, claim.enrollment_id)
            enrollment.total_claimed_to_date = (
                enrollment.total_claimed_to_date or Decimal("0")
            ) - claim.applicable_subvention_amount
            if enrollment.total_claimed_to_date < Decimal("0"):
                enrollment.total_claimed_to_date = Decimal("0")
            enrollment.updated_by = current_user.id
            enrollment.version = (enrollment.version or 1) + 1

        claim.status = SubventionClaimStatus.CANCELLED.value
        claim.rejection_reason = reason
        claim.updated_by = current_user.id
        claim.version = (claim.version or 1) + 1
        await self.session.flush()
        await self.session.refresh(claim)
        return claim

    # =========================================================================
    # Read
    # =========================================================================

    async def list_claims(
        self,
        organization_id: UUID,
        status: str | None = None,
        enrollment_id: UUID | None = None,
        loan_account_id: UUID | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[SubventionClaim], int]:
        where = [
            SubventionClaim.organization_id == organization_id,
            SubventionClaim.deleted_at.is_(None),
        ]
        if status is not None:
            where.append(SubventionClaim.status == status)
        if enrollment_id is not None:
            where.append(SubventionClaim.enrollment_id == enrollment_id)
        if loan_account_id is not None:
            where.append(
                SubventionClaim.enrollment_id.in_(
                    select(LoanSubventionEnrollment.id).where(
                        LoanSubventionEnrollment.loan_account_id == loan_account_id,
                    )
                )
            )

        count_stmt = select(func.count()).select_from(SubventionClaim).where(*where)
        total = (await self.session.execute(count_stmt)).scalar_one()

        stmt = (
            select(SubventionClaim)
            .options(
                selectinload(SubventionClaim.enrollment).selectinload(
                    LoanSubventionEnrollment.loan_account
                ),
                selectinload(SubventionClaim.enrollment).selectinload(
                    LoanSubventionEnrollment.scheme
                ),
            )
            .where(*where)
            .order_by(SubventionClaim.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        rows = list((await self.session.execute(stmt)).scalars().all())
        return rows, int(total)

    async def get(
        self,
        organization_id: UUID,
        claim_id: UUID,
        *,
        with_relations: bool = True,
    ) -> SubventionClaim:
        if with_relations:
            stmt = (
                select(SubventionClaim)
                .options(
                    selectinload(SubventionClaim.enrollment).selectinload(
                        LoanSubventionEnrollment.loan_account
                    ),
                    selectinload(SubventionClaim.enrollment).selectinload(
                        LoanSubventionEnrollment.scheme
                    ),
                )
                .where(
                    SubventionClaim.id == claim_id,
                    SubventionClaim.organization_id == organization_id,
                    SubventionClaim.deleted_at.is_(None),
                )
            )
            claim = (await self.session.execute(stmt)).scalar_one_or_none()
        else:
            claim = await self.session.get(SubventionClaim, claim_id)
            if claim is not None and (
                claim.deleted_at is not None or claim.organization_id != organization_id
            ):
                claim = None
        if claim is None:
            raise NotFoundException("Claim not found", error_code="CLAIM_NOT_FOUND")
        return claim

    # =========================================================================
    # Eligible loans (enrolled loans with no claim for next period yet)
    # =========================================================================

    async def list_loans_due_for_claim(
        self,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[dict[str, Any]], int]:
        """List enrolments whose next due period has no live claim.

        Returned shape is intentionally a dict — the caller (route)
        adapts it into the response schema.
        """
        stmt = (
            select(LoanSubventionEnrollment)
            .options(
                selectinload(LoanSubventionEnrollment.loan_account),
                selectinload(LoanSubventionEnrollment.scheme),
            )
            .where(
                LoanSubventionEnrollment.organization_id == organization_id,
                LoanSubventionEnrollment.deleted_at.is_(None),
                LoanSubventionEnrollment.status == SubventionEnrollmentStatus.ENROLLED.value,
            )
            .order_by(LoanSubventionEnrollment.enrolled_date.asc())
        )
        rows = list((await self.session.execute(stmt)).scalars().all())

        eligible: list[dict[str, Any]] = []
        for enrollment in rows:
            periods = await self.eligible_periods(organization_id, enrollment.id)
            # The "next due" period is the latest fully-elapsed period
            # that has not yet been claimed.
            for p in reversed(periods.periods):
                if not p.already_claimed:
                    eligible.append(
                        {
                            "enrollment_id": enrollment.id,
                            "loan_account_id": enrollment.loan_account_id,
                            "loan_account_number": enrollment.loan_account.loan_account_number,
                            "scheme_id": enrollment.scheme_id,
                            "scheme_code": enrollment.scheme.scheme_code,
                            "claim_frequency": enrollment.scheme.claim_frequency,
                            "period_start": p.period_start,
                            "period_end": p.period_end,
                            "label": p.label,
                        }
                    )
                    break

        total = len(eligible)
        return eligible[skip : skip + limit], total

    # =========================================================================
    # Report
    # =========================================================================

    async def generate_claim_report(
        self,
        organization_id: UUID,
        claim_id: UUID,
    ) -> ClaimReportResponse:
        """Build the structured claim report payload.

        The route layer is responsible for converting this into PDF /
        XLSX / CSV when those file types are requested.
        """
        claim = await self.get(organization_id, claim_id)
        enrollment: LoanSubventionEnrollment = claim.enrollment
        loan: LoanAccount = enrollment.loan_account
        scheme: SubventionScheme = enrollment.scheme

        # Entity + sanction look-ups via session.get keep the query
        # surface small.
        entity = None
        if loan is not None:
            entity = await self.session.get(
                __import__("app.models.lending.entity", fromlist=["Entity"]).Entity,
                loan.entity_id,
            )

        sanction = None
        if loan is not None and loan.sanction_id is not None:
            from app.models.lending.sanction import LoanSanction

            sanction = await self.session.get(LoanSanction, loan.sanction_id)

        header = ClaimReportHeader(
            scheme_code=scheme.scheme_code,
            scheme_name=scheme.scheme_name,
            implementing_agency=scheme.implementing_agency,
            administering_ministry=scheme.administering_ministry,
            borrower_entity_id=getattr(entity, "id", None),
            borrower_entity_name=getattr(entity, "legal_name", None),
            loan_account_id=loan.id if loan else None,
            loan_account_number=loan.loan_account_number if loan else None,
            sanction_date=sanction.sanction_date if sanction else None,
            tenure_months=loan.tenure_months if loan else None,
            period_start=claim.period_start,
            period_end=claim.period_end,
            claim_frequency=claim.claim_frequency,
        )

        # ---- Interest calculation (tranche-wise) ----
        from app.models.lending.loan_account import Disbursement

        disb_stmt = (
            select(Disbursement)
            .where(
                Disbursement.loan_account_id == loan.id,
                Disbursement.deleted_at.is_(None),
            )
            .order_by(Disbursement.disbursement_number.asc())
        )
        disbursements = list((await self.session.execute(disb_stmt)).scalars().all())

        # Total interest in the claim period — used to apportion per
        # tranche when we don't have a tranche-level interest accrual
        # source. The IIF incentive itself is computed on principal-days
        # by default, not as a percentage of interest paid.
        total_interest = claim.interest_paid_in_period
        rate = scheme.subvention_rate_percent
        rules = calculation_rules(scheme)
        method = str(rules.get("method") or "")

        weights: list[Decimal] = []
        for d in disbursements:
            if d.disbursement_date is None or d.disbursed_amount is None:
                weights.append(Decimal("0"))
                continue
            start = max(d.disbursement_date, claim.period_start)
            end = claim.period_end
            if start > end:
                weights.append(Decimal("0"))
                continue
            days = (end - start).days + 1
            weights.append(d.disbursed_amount * Decimal(days))
        weight_sum = sum(weights, start=Decimal("0"))
        uncapped_subventions: list[Decimal] = []
        for w in weights:
            if method == CALCULATION_PERCENT_OF_INTEREST_PAID:
                if weight_sum > 0 and w > 0:
                    tranche_interest = total_interest * w / weight_sum
                    uncapped_subventions.append(tranche_interest * rate / Decimal("100"))
                else:
                    uncapped_subventions.append(Decimal("0"))
            else:
                principal_years = w / Decimal("365")
                uncapped_subventions.append(principal_years * rate / Decimal("100"))
        uncapped_total = sum(uncapped_subventions, start=Decimal("0"))
        cap_factor = Decimal("1")
        if (
            method != CALCULATION_PERCENT_OF_INTEREST_PAID
            and rules.get("cap_by_actual_interest_paid", True)
            and uncapped_total > 0
            and uncapped_total > total_interest
        ):
            cap_factor = total_interest / uncapped_total

        calc_lines: list[InterestCalculationLine] = []
        for d, w, raw_subv in zip(disbursements, weights, uncapped_subventions):
            if weight_sum > 0 and w > 0:
                tranche_interest = (total_interest * w / weight_sum).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )
            else:
                tranche_interest = Decimal("0.00")
            tranche_subv = (raw_subv * cap_factor).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            calc_lines.append(
                InterestCalculationLine(
                    tranche_number=d.disbursement_number,
                    disbursement_reference=d.disbursement_reference,
                    disbursed_amount=d.disbursed_amount or Decimal("0"),
                    disbursement_date=d.disbursement_date,
                    opening_balance=d.disbursed_amount or Decimal("0"),
                    interest_rate=loan.current_interest_rate if loan is not None else Decimal("0"),
                    interest_for_period=tranche_interest,
                    eligible_subvention=tranche_subv,
                )
            )

        # ---- Repayment record (installment-wise) ----
        rec_stmt = (
            select(LoanReceipt)
            .where(
                LoanReceipt.loan_account_id == loan.id,
                LoanReceipt.organization_id == organization_id,
                LoanReceipt.value_date >= claim.period_start,
                LoanReceipt.value_date <= claim.period_end,
                LoanReceipt.deleted_at.is_(None),
                LoanReceipt.bounced.is_(False),
                LoanReceipt.status != ReceiptStatus.REVERSED,
            )
            .order_by(LoanReceipt.value_date.asc())
        )
        receipts = list((await self.session.execute(rec_stmt)).scalars().all())

        repayment_lines: list[RepaymentRecordLine] = []
        for r in receipts:
            repayment_lines.append(
                RepaymentRecordLine(
                    receipt_number=r.receipt_number,
                    value_date=r.value_date,
                    receipt_amount=r.receipt_amount,
                    allocated_to_interest=r.interest_allocated or Decimal("0"),
                    allocated_to_principal=r.principal_allocated or Decimal("0"),
                    allocated_to_penal=r.penal_interest_allocated or Decimal("0"),
                    allocated_to_charges=r.charges_allocated or Decimal("0"),
                )
            )

        # ---- Account status ----
        account_status = ClaimAccountStatus(
            asset_classification=(
                loan.asset_classification.value
                if loan and hasattr(loan.asset_classification, "value")
                else (loan.asset_classification if loan else None)
            ),
            days_past_due=loan.days_past_due if loan else None,
            last_emi_status=None,  # Filled in once installment status is rolled up.
        )

        # ---- Summary (auto-generated tail) ----
        total_tranche_interest = sum(
            (line.interest_for_period for line in calc_lines),
            start=Decimal("0"),
        )
        total_eligible = sum(
            (line.eligible_subvention for line in calc_lines),
            start=Decimal("0"),
        )
        summary: dict[str, Any] = {
            "total_interest_paid": str(claim.interest_paid_in_period),
            "subvention_rate_percent": str(rate),
            "calculation_method": method,
            "eligible_base_amount": str(
                (uncapped_total * Decimal("100") / rate).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )
                if rate > 0
                else Decimal("0.00")
            ),
            "applicable_subvention_amount": str(claim.applicable_subvention_amount),
            "tranche_interest_check": str(total_tranche_interest),
            "tranche_subvention_check": str(total_eligible),
            "receipt_count": len(repayment_lines),
            "tranche_count": len(calc_lines),
        }

        footer = ClaimReportFooter(
            claim_reference=claim.claim_reference,
            generated_at=datetime.now(UTC),
            version="1.0",
        )

        return ClaimReportResponse(
            header=header,
            interest_calculation=calc_lines,
            repayment_record=repayment_lines,
            account_status=account_status,
            declaration_text=_DECLARATION_TEXT,
            declaration_signed_by=claim.declaration_signed_by,
            declaration_signed_at=claim.declaration_signed_at,
            summary=summary,
            footer=footer,
        )

    # =========================================================================
    # Helpers
    # =========================================================================

    async def _get_enrollment(
        self, organization_id: UUID, enrollment_id: UUID
    ) -> LoanSubventionEnrollment:
        stmt = (
            select(LoanSubventionEnrollment)
            .options(
                selectinload(LoanSubventionEnrollment.loan_account),
                selectinload(LoanSubventionEnrollment.scheme),
            )
            .where(
                LoanSubventionEnrollment.id == enrollment_id,
                LoanSubventionEnrollment.organization_id == organization_id,
                LoanSubventionEnrollment.deleted_at.is_(None),
            )
        )
        enrollment = (await self.session.execute(stmt)).scalar_one_or_none()
        if enrollment is None:
            raise NotFoundException("Enrollment not found", error_code="ENROLLMENT_NOT_FOUND")
        return enrollment

    async def _next_claim_reference(
        self,
        organization_id: UUID,
        scheme_code: str,
        claim_frequency: str,
        period_start: date,
    ) -> str:
        """Generate a per-(org, scheme, period-suffix) sequence number."""
        suffix = _reference_suffix(period_start, claim_frequency)
        prefix = f"{scheme_code}/{suffix}/"

        # Count existing claims for that prefix in this org (including
        # cancelled ones — the reference is a permanent ID, not a slot).
        count_stmt = (
            select(func.count())
            .select_from(SubventionClaim)
            .where(
                SubventionClaim.organization_id == organization_id,
                SubventionClaim.claim_reference.like(prefix + "%"),
            )
        )
        seq = int((await self.session.execute(count_stmt)).scalar_one() or 0) + 1
        return f"{prefix}{seq:05d}"
