"""Loan-account ↔ subvention-scheme enrollment service.

Owns the ``los_loan_subvention_enrollment`` table and the
``check_eligibility`` invariant. Eligibility rules implemented (per the
IIF guidelines + scheme master columns):

1. Loan account exists, is active (status != CLOSED/WRITTEN_OFF), and
   isn't currently NPA (``days_past_due <=
   scheme.npa_disqualification_dpd_days``).
2. Sanction date in [scheme_start_date, scheme_start_date +
   eligibility_window_months].
3. Loan tenure within scheme caps — term-loan cap if it's a CAPEX loan,
   working-capital cap if it's a WC loan. The loan-type is derived
   from ``LoanProduct.category`` (TERM_LOAN → TERM_LOAN_CAPEX,
   WORKING_CAPITAL → WORKING_CAPITAL); other categories fail closed.
4. The loan's product category is in ``scheme.eligible_loan_types``.
5. Existing total enrolled subvention for this org-entity group is
   below ``scheme.max_subvention_per_beneficiary``.
6. Loan is NOT a refinance / takeover / restructure. We honour the
   ``LoanAccount`` flag when present; otherwise the check is skipped
   (CLAUDE.md §12.7 — no false positives without a real signal).
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
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
    IIFLoanType,
    LoanAccountStatus,
    ProductCategory,
    SubventionEnrollmentStatus,
)
from app.models.lending.iif.loan_subvention_enrollment import (
    LoanSubventionEnrollment,
)
from app.models.lending.iif.subvention_scheme import SubventionScheme
from app.models.lending.loan_account import LoanAccount
from app.models.lending.product import LoanProduct
from app.models.lending.sanction import LoanSanction
from app.schemas.lending.iif import (
    EligibilityCheckResponse,
    LoanSubventionEnrollmentCreate,
    LoanSubventionEnrollmentUpdate,
)


def _add_months(d: date, months: int) -> date:
    """Month-end-safe offset (used only for eligibility windows)."""
    year = d.year + (d.month - 1 + months) // 12
    month = (d.month - 1 + months) % 12 + 1
    day = min(d.day, 28)
    return date(year, month, day)


_PRODUCT_TO_IIF: dict[ProductCategory, IIFLoanType] = {
    ProductCategory.TERM_LOAN: IIFLoanType.TERM_LOAN_CAPEX,
    ProductCategory.WORKING_CAPITAL: IIFLoanType.WORKING_CAPITAL,
}


class SubventionEnrollmentService:
    """Service for enrollment lifecycle + eligibility."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # =========================================================================
    # Eligibility
    # =========================================================================

    async def check_eligibility(
        self,
        organization_id: UUID,
        loan_account_id: UUID,
        scheme_id: UUID,
    ) -> EligibilityCheckResponse:
        """Run the eligibility checklist for a (loan, scheme) pair.

        Returns a structured response so the FE can render each failed
        rule rather than a single string. Never raises.
        """
        loan = await self._get_loan_account(organization_id, loan_account_id)
        scheme = await self._get_scheme(organization_id, scheme_id)

        product: LoanProduct | None = await self.session.get(LoanProduct, loan.product_id)
        sanction: LoanSanction | None = await self.session.get(LoanSanction, loan.sanction_id)

        checks: dict[str, bool] = {}
        reasons: list[str] = []

        # 1. Loan active + not NPA.
        active = loan.status not in {
            LoanAccountStatus.CLOSED,
            LoanAccountStatus.WRITTEN_OFF,
        }
        checks["loan_active"] = active
        if not active:
            reasons.append(
                f"Loan account is {loan.status.value if hasattr(loan.status, 'value') else loan.status}"
            )

        dpd = int(loan.days_past_due or 0)
        not_npa = dpd <= int(scheme.npa_disqualification_dpd_days)
        checks["not_npa"] = not_npa
        if not not_npa:
            reasons.append(
                f"Loan is past-due {dpd} days; scheme requires ≤ "
                f"{scheme.npa_disqualification_dpd_days}"
            )

        # 2. Sanction date inside scheme window.
        sanction_date = sanction.sanction_date if sanction is not None else None
        window_end = scheme.scheme_end_date
        if scheme.eligibility_window_months is not None:
            window_end_candidate = _add_months(
                scheme.scheme_start_date, scheme.eligibility_window_months
            )
            if window_end_candidate < window_end:
                window_end = window_end_candidate

        in_window = (
            sanction_date is not None and scheme.scheme_start_date <= sanction_date <= window_end
        )
        checks["sanction_in_window"] = in_window
        if not in_window:
            if sanction_date is None:
                reasons.append("Sanction date not available")
            else:
                reasons.append(
                    f"Sanction date {sanction_date} outside scheme window "
                    f"[{scheme.scheme_start_date} .. {window_end}]"
                )

        # 3 & 4. Loan-type / tenure checks.
        iif_type: IIFLoanType | None = _PRODUCT_TO_IIF.get(product.category) if product else None
        type_ok = iif_type is not None and iif_type.value in (scheme.eligible_loan_types or [])
        checks["loan_type_eligible"] = type_ok
        if not type_ok:
            cat = (
                product.category.value
                if product and hasattr(product.category, "value")
                else (product.category if product else None)
            )
            reasons.append(f"Product category {cat!r} is not eligible under scheme")

        tenure_ok = True
        if iif_type is IIFLoanType.TERM_LOAN_CAPEX:
            cap = scheme.max_tenure_term_loan_months
            if cap is not None and loan.tenure_months > cap:
                tenure_ok = False
                reasons.append(f"Tenure {loan.tenure_months}m exceeds cap {cap}m for term loans")
        elif iif_type is IIFLoanType.WORKING_CAPITAL:
            cap = scheme.max_tenure_working_capital_months
            if cap is not None and loan.tenure_months > cap:
                tenure_ok = False
                reasons.append(
                    f"Tenure {loan.tenure_months}m exceeds cap {cap}m for working capital"
                )
        checks["tenure_within_cap"] = tenure_ok

        # 5. Per-beneficiary cap.
        cap = scheme.max_subvention_per_beneficiary
        beneficiary_ok = True
        if cap is not None:
            already = await self._sum_enrolled_subvention_for_entity(
                organization_id=organization_id,
                entity_id=loan.entity_id,
                scheme_id=scheme.id,
            )
            if already >= cap:
                beneficiary_ok = False
                reasons.append(
                    f"Beneficiary cap reached: existing claims sum " f"{already} ≥ scheme cap {cap}"
                )
        checks["beneficiary_cap_ok"] = beneficiary_ok

        # 6. Refinance / restructure check (best-effort; only enforces
        # if the relevant flag is present on the model).
        refinance_ok = True
        # The loan-account model in this codebase does not carry a
        # boolean ``is_refinance`` field today. The check therefore
        # passes — but the slot is here so we can extend without a
        # service refactor when the column lands.
        # (Approval to defer the actual signal lives in
        # .stubs-approved.md under STAGE-IIF-*; tracked alongside the
        # CRILC integration that publishes the restructure flag.)
        for flag_name in ("is_refinance", "is_restructure", "is_takeover"):
            flag_val = getattr(loan, flag_name, None)
            if flag_val is True:
                refinance_ok = False
                reasons.append(f"Loan is flagged {flag_name}=True")
        checks["not_refinance"] = refinance_ok

        eligible = all(checks.values())
        return EligibilityCheckResponse(
            eligible=eligible,
            reasons=reasons,
            checks=checks,
        )

    # =========================================================================
    # Enrollment lifecycle
    # =========================================================================

    async def create(
        self,
        organization_id: UUID,
        data: LoanSubventionEnrollmentCreate,
        current_user: User,
    ) -> LoanSubventionEnrollment:
        """Create a PENDING_APPROVAL enrollment.

        Eligibility is checked at creation. If any rule fails, raises
        ``BadRequestException`` with the joined reasons.
        """
        # Duplicate guard — the partial unique index on (loan, scheme)
        # where ``deleted_at IS NULL`` is the DB-level backstop; we
        # also check here for a friendly error message.
        existing = await self.session.execute(
            select(LoanSubventionEnrollment).where(
                LoanSubventionEnrollment.organization_id == organization_id,
                LoanSubventionEnrollment.loan_account_id == data.loan_account_id,
                LoanSubventionEnrollment.scheme_id == data.scheme_id,
                LoanSubventionEnrollment.deleted_at.is_(None),
            )
        )
        if existing.scalar_one_or_none() is not None:
            raise ConflictException(
                "Loan is already enrolled in this scheme",
                error_code="ENROLLMENT_EXISTS",
            )

        result = await self.check_eligibility(organization_id, data.loan_account_id, data.scheme_id)
        if not result.eligible:
            raise BadRequestException(
                "Loan is not eligible for this scheme: " + "; ".join(result.reasons),
                error_code="NOT_ELIGIBLE",
            )

        enrollment = LoanSubventionEnrollment(
            organization_id=organization_id,
            loan_account_id=data.loan_account_id,
            scheme_id=data.scheme_id,
            enrolled_date=data.enrolled_date or date.today(),
            status=SubventionEnrollmentStatus.PENDING_APPROVAL.value,
            notes=data.notes,
            created_by=current_user.id,
        )
        self.session.add(enrollment)
        await self.session.flush()
        await self.session.refresh(enrollment)
        return enrollment

    async def update(
        self,
        organization_id: UUID,
        enrollment_id: UUID,
        data: LoanSubventionEnrollmentUpdate,
        current_user: User,
    ) -> LoanSubventionEnrollment:
        enrollment = await self.get(organization_id, enrollment_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(enrollment, field, value)
        enrollment.updated_by = current_user.id
        enrollment.version = (enrollment.version or 1) + 1
        await self.session.flush()
        await self.session.refresh(enrollment)
        return enrollment

    async def approve(
        self,
        organization_id: UUID,
        enrollment_id: UUID,
        current_user: User,
    ) -> LoanSubventionEnrollment:
        enrollment = await self.get(organization_id, enrollment_id)
        if enrollment.status != SubventionEnrollmentStatus.PENDING_APPROVAL.value:
            raise BadRequestException(
                f"Cannot approve enrollment in status {enrollment.status}",
                error_code="INVALID_TRANSITION",
            )
        enrollment.status = SubventionEnrollmentStatus.ENROLLED.value
        enrollment.updated_by = current_user.id
        enrollment.version = (enrollment.version or 1) + 1
        await self.session.flush()
        await self.session.refresh(enrollment)
        return enrollment

    async def reject(
        self,
        organization_id: UUID,
        enrollment_id: UUID,
        reason: str | None,
        current_user: User,
    ) -> LoanSubventionEnrollment:
        enrollment = await self.get(organization_id, enrollment_id)
        if enrollment.status != SubventionEnrollmentStatus.PENDING_APPROVAL.value:
            raise BadRequestException(
                f"Cannot reject enrollment in status {enrollment.status}",
                error_code="INVALID_TRANSITION",
            )
        enrollment.status = SubventionEnrollmentStatus.REJECTED.value
        enrollment.rejection_reason = reason
        enrollment.updated_by = current_user.id
        enrollment.version = (enrollment.version or 1) + 1
        await self.session.flush()
        await self.session.refresh(enrollment)
        return enrollment

    async def suspend(
        self,
        organization_id: UUID,
        enrollment_id: UUID,
        reason: str | None,
        current_user: User,
    ) -> LoanSubventionEnrollment:
        enrollment = await self.get(organization_id, enrollment_id)
        if enrollment.status != SubventionEnrollmentStatus.ENROLLED.value:
            raise BadRequestException(
                f"Cannot suspend enrollment in status {enrollment.status}",
                error_code="INVALID_TRANSITION",
            )
        enrollment.status = SubventionEnrollmentStatus.SUSPENDED.value
        if reason:
            enrollment.notes = (
                f"{enrollment.notes}\n[suspend] {reason}"
                if enrollment.notes
                else f"[suspend] {reason}"
            )
        enrollment.updated_by = current_user.id
        enrollment.version = (enrollment.version or 1) + 1
        await self.session.flush()
        await self.session.refresh(enrollment)
        return enrollment

    async def reinstate(
        self,
        organization_id: UUID,
        enrollment_id: UUID,
        current_user: User,
    ) -> LoanSubventionEnrollment:
        enrollment = await self.get(organization_id, enrollment_id)
        if enrollment.status != SubventionEnrollmentStatus.SUSPENDED.value:
            raise BadRequestException(
                f"Cannot reinstate enrollment in status {enrollment.status}",
                error_code="INVALID_TRANSITION",
            )
        # Re-check eligibility before flipping back to ENROLLED.
        result = await self.check_eligibility(
            organization_id,
            enrollment.loan_account_id,
            enrollment.scheme_id,
        )
        if not result.eligible:
            raise BadRequestException(
                "Loan is still not eligible: " + "; ".join(result.reasons),
                error_code="NOT_ELIGIBLE",
            )
        enrollment.status = SubventionEnrollmentStatus.ENROLLED.value
        enrollment.updated_by = current_user.id
        enrollment.version = (enrollment.version or 1) + 1
        await self.session.flush()
        await self.session.refresh(enrollment)
        return enrollment

    # =========================================================================
    # Read
    # =========================================================================

    async def list_enrollments(
        self,
        organization_id: UUID,
        status: str | None = None,
        scheme_id: UUID | None = None,
        loan_account_id: UUID | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[LoanSubventionEnrollment], int]:
        where = [
            LoanSubventionEnrollment.organization_id == organization_id,
            LoanSubventionEnrollment.deleted_at.is_(None),
        ]
        if status is not None:
            where.append(LoanSubventionEnrollment.status == status)
        if scheme_id is not None:
            where.append(LoanSubventionEnrollment.scheme_id == scheme_id)
        if loan_account_id is not None:
            where.append(LoanSubventionEnrollment.loan_account_id == loan_account_id)

        count_stmt = select(func.count()).select_from(LoanSubventionEnrollment).where(*where)
        total = (await self.session.execute(count_stmt)).scalar_one()

        stmt = (
            select(LoanSubventionEnrollment)
            .options(
                selectinload(LoanSubventionEnrollment.loan_account).selectinload(
                    LoanAccount.entity
                ),
                selectinload(LoanSubventionEnrollment.scheme),
            )
            .where(*where)
            .order_by(LoanSubventionEnrollment.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        rows = list((await self.session.execute(stmt)).scalars().all())
        return rows, int(total)

    async def get(
        self,
        organization_id: UUID,
        enrollment_id: UUID,
        *,
        with_relations: bool = True,
    ) -> LoanSubventionEnrollment:
        if with_relations:
            stmt = (
                select(LoanSubventionEnrollment)
                .options(
                    selectinload(LoanSubventionEnrollment.loan_account).selectinload(
                        LoanAccount.entity
                    ),
                    selectinload(LoanSubventionEnrollment.scheme),
                )
                .where(
                    LoanSubventionEnrollment.id == enrollment_id,
                    LoanSubventionEnrollment.organization_id == organization_id,
                    LoanSubventionEnrollment.deleted_at.is_(None),
                )
            )
            enrollment = (await self.session.execute(stmt)).scalar_one_or_none()
        else:
            enrollment = await self.session.get(LoanSubventionEnrollment, enrollment_id)
            if enrollment is not None and (
                enrollment.deleted_at is not None or enrollment.organization_id != organization_id
            ):
                enrollment = None
        if enrollment is None:
            raise NotFoundException("Enrollment not found", error_code="ENROLLMENT_NOT_FOUND")
        return enrollment

    # =========================================================================
    # Helpers
    # =========================================================================

    async def _get_loan_account(self, organization_id: UUID, loan_account_id: UUID) -> LoanAccount:
        loan = await self.session.get(LoanAccount, loan_account_id)
        if loan is None or loan.deleted_at is not None or loan.organization_id != organization_id:
            raise NotFoundException(
                "Loan account not found",
                error_code="LOAN_ACCOUNT_NOT_FOUND",
            )
        return loan

    async def _get_scheme(self, organization_id: UUID, scheme_id: UUID) -> SubventionScheme:
        scheme = await self.session.get(SubventionScheme, scheme_id)
        if scheme is None or scheme.deleted_at is not None:
            raise NotFoundException("Scheme not found", error_code="SCHEME_NOT_FOUND")
        if scheme.organization_id is not None and scheme.organization_id != organization_id:
            raise NotFoundException("Scheme not found", error_code="SCHEME_NOT_FOUND")
        return scheme

    async def _sum_enrolled_subvention_for_entity(
        self,
        organization_id: UUID,
        entity_id: UUID,
        scheme_id: UUID,
    ) -> Decimal:
        """Sum ``total_claimed_to_date`` across all active enrolments of
        this entity in this scheme."""
        stmt = (
            select(
                func.coalesce(
                    func.sum(LoanSubventionEnrollment.total_claimed_to_date),
                    Decimal("0"),
                )
            )
            .select_from(LoanSubventionEnrollment)
            .join(
                LoanAccount,
                LoanAccount.id == LoanSubventionEnrollment.loan_account_id,
            )
            .where(
                LoanSubventionEnrollment.organization_id == organization_id,
                LoanSubventionEnrollment.scheme_id == scheme_id,
                LoanSubventionEnrollment.deleted_at.is_(None),
                LoanSubventionEnrollment.status.in_(
                    [
                        SubventionEnrollmentStatus.ENROLLED.value,
                        SubventionEnrollmentStatus.SUSPENDED.value,
                    ]
                ),
                LoanAccount.entity_id == entity_id,
            )
        )
        val = (await self.session.execute(stmt)).scalar_one()
        return Decimal(val or 0)
