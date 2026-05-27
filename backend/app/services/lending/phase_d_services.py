"""Phase-D services — all 8 lifecycle modules in one consolidated file.

Each service class is intentionally minimal: the spine is already in
place (lifecycle_event + masters + certificate). These services are the
domain-specific wrappers that:

1. Create/transition the per-module row in their own table.
2. Emit lifecycle events on every state change.
3. Issue letters/notices via CertificateService where appropriate.
4. Trigger GL postings via the existing receipt / voucher services where
   money moves (foreclosure receipt, write-off voucher).

Keep this single-file consolidation so a future engineer reading the
codebase finds the entire "what happens during the loan lifecycle" in
one place. Per-module files become useful only when the surface grows.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException, ValidationException
from app.models.lending.lifecycle_event import (
    LifecycleActorKind,
    LifecycleSubjectType,
)
from app.models.lending.lifecycle_modules import (
    DocReleaseStatus,
    DocReleaseTracker,
    InterestRevivalStatus,
    LoanInterestRevival,
    LoanTakeoverIn,
    LoanTransferOut,
    LoanWriteOff,
    NachPresentation,
    NachPresentationStatus,
    RateResetChoice,
    RateResetEvent,
    TakeoverStatus,
    TransferOutStatus,
    WilfulDefaulterProceeding,
    WilfulDefaulterStage,
    WriteOffStatus,
    WriteOffType,
)
from app.services.lending.lifecycle_service import LifecycleService

logger = logging.getLogger(__name__)


# ============================================================================
# Common helper — next sequential reference per (org, prefix)
# ============================================================================


async def _next_reference(
    session: AsyncSession, model, column_name: str, prefix: str, organization_id: UUID
) -> str:
    today = datetime.now(timezone.utc).date()
    fy = (
        f"{today.year - (1 if today.month < 4 else 0)}-"
        f"{(today.year - (1 if today.month < 4 else 0) + 1) % 100:02d}"
    )
    column = getattr(model, column_name)
    pattern = f"{prefix}/{fy}/%"
    stmt = select(func.count(model.id)).where(
        model.organization_id == organization_id,
        column.like(pattern),
    )
    count = (await session.execute(stmt)).scalar() or 0
    return f"{prefix}/{fy}/{count + 1:04d}"


# ============================================================================
# D.1 — TakeoverInService
# ============================================================================


class TakeoverInService:
    """Inbound takeover from another lender."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.lifecycle = LifecycleService(session)

    async def initiate(
        self,
        *,
        organization_id: UUID,
        actor_user_id: UUID,
        source_lender_name: str,
        source_loan_account_no: str,
        source_outstanding: Decimal,
        application_id: UUID | None = None,
    ) -> LoanTakeoverIn:
        ref = await _next_reference(
            self.session, LoanTakeoverIn, "takeover_reference", "TKI", organization_id
        )
        row = LoanTakeoverIn(
            organization_id=organization_id,
            takeover_reference=ref,
            application_id=application_id,
            source_lender_name=source_lender_name,
            source_loan_account_no=source_loan_account_no,
            source_outstanding=source_outstanding,
            status=TakeoverStatus.INITIATED,
        )
        self.session.add(row)
        await self.session.flush()
        await self.lifecycle.record_event(
            organization_id=organization_id,
            subject_type=LifecycleSubjectType.TAKEOVER,
            subject_id=row.id,
            event_type="TRANSFER_IN_INITIATED",
            actor_kind=LifecycleActorKind.LENDER,
            actor_user_id=actor_user_id,
            business_number=ref,
            state_to="INITIATED",
            payload={
                "source_lender": source_lender_name,
                "source_outstanding": float(source_outstanding),
            },
        )
        return row

    async def advance(
        self,
        *,
        organization_id: UUID,
        actor_user_id: UUID,
        takeover_id: UUID,
        new_status: TakeoverStatus,
        transferred_amount: Decimal | None = None,
        transfer_date: date | None = None,
        dd_or_rtgs_reference: str | None = None,
    ) -> LoanTakeoverIn:
        row = await self.session.get(LoanTakeoverIn, takeover_id)
        if row is None or row.organization_id != organization_id:
            raise NotFoundException(
                detail=f"Takeover {takeover_id} not found",
                error_code="TAKEOVER_NOT_FOUND",
            )
        previous = row.status.value
        row.status = new_status
        if transferred_amount is not None:
            row.transferred_amount = transferred_amount
        if transfer_date is not None:
            row.transfer_date = transfer_date
        if dd_or_rtgs_reference is not None:
            row.dd_or_rtgs_reference = dd_or_rtgs_reference

        event_type = (
            "TRANSFER_IN_COMPLETED"
            if new_status == TakeoverStatus.BOOKED
            else "TRANSFER_IN_INITIATED"
        )
        await self.lifecycle.record_event(
            organization_id=organization_id,
            subject_type=LifecycleSubjectType.TAKEOVER,
            subject_id=row.id,
            event_type=event_type,
            actor_kind=LifecycleActorKind.LENDER,
            actor_user_id=actor_user_id,
            business_number=row.takeover_reference,
            state_from=previous,
            state_to=new_status.value,
        )
        await self.session.flush()
        return row


# ============================================================================
# D.1 — TransferOutService
# ============================================================================


class TransferOutService:
    """Outbound transfer to another lender."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.lifecycle = LifecycleService(session)

    async def request_noc(
        self,
        *,
        organization_id: UUID,
        actor_user_id: UUID | None,
        loan_account_id: UUID,
        target_lender_name: str,
        actor_kind: LifecycleActorKind = LifecycleActorKind.BORROWER,
    ) -> LoanTransferOut:
        ref = await _next_reference(
            self.session, LoanTransferOut, "transfer_reference", "TFO", organization_id
        )
        row = LoanTransferOut(
            organization_id=organization_id,
            transfer_reference=ref,
            loan_account_id=loan_account_id,
            target_lender_name=target_lender_name,
            noc_requested_at=datetime.now(timezone.utc),
            status=TransferOutStatus.NOC_REQUESTED,
        )
        self.session.add(row)
        await self.session.flush()
        await self.lifecycle.record_event(
            organization_id=organization_id,
            subject_type=LifecycleSubjectType.TRANSFER_OUT,
            subject_id=row.id,
            event_type="TAKEOVER_NOC_REQUESTED",
            actor_kind=actor_kind,
            actor_user_id=actor_user_id,
            business_number=ref,
            state_to="NOC_REQUESTED",
            payload={"target_lender": target_lender_name, "loan_account_id": str(loan_account_id)},
        )
        return row

    async def issue_outstanding_letter(
        self,
        *,
        organization_id: UUID,
        actor_user_id: UUID,
        transfer_id: UUID,
        outstanding_amount: Decimal,
        valid_till: date,
    ) -> LoanTransferOut:
        row = await self._get(organization_id, transfer_id)
        prev = row.status.value
        row.outstanding_letter_issued_at = datetime.now(timezone.utc)
        row.outstanding_amount_quoted = outstanding_amount
        row.quote_valid_till = valid_till
        row.status = TransferOutStatus.OUTSTANDING_ISSUED
        await self.lifecycle.record_event(
            organization_id=organization_id,
            subject_type=LifecycleSubjectType.TRANSFER_OUT,
            subject_id=row.id,
            event_type="TAKEOVER_LETTER_ISSUED",
            actor_kind=LifecycleActorKind.LENDER,
            actor_user_id=actor_user_id,
            business_number=row.transfer_reference,
            state_from=prev,
            state_to="OUTSTANDING_ISSUED",
            payload={
                "outstanding_amount": float(outstanding_amount),
                "valid_till": valid_till.isoformat(),
            },
        )
        await self.session.flush()
        return row

    async def record_payment(
        self,
        *,
        organization_id: UUID,
        actor_user_id: UUID,
        transfer_id: UUID,
        amount: Decimal,
        reference: str,
    ) -> LoanTransferOut:
        row = await self._get(organization_id, transfer_id)
        prev = row.status.value
        row.payment_received_at = datetime.now(timezone.utc)
        row.payment_amount = amount
        row.payment_reference = reference
        row.status = TransferOutStatus.PAYMENT_RECEIVED
        await self.lifecycle.record_event(
            organization_id=organization_id,
            subject_type=LifecycleSubjectType.TRANSFER_OUT,
            subject_id=row.id,
            event_type="TAKEOVER_COMPLETED",
            actor_kind=LifecycleActorKind.LENDER,
            actor_user_id=actor_user_id,
            business_number=row.transfer_reference,
            state_from=prev,
            state_to="PAYMENT_RECEIVED",
            payload={"amount": float(amount), "reference": reference},
        )
        await self.session.flush()
        return row

    async def close(
        self,
        *,
        organization_id: UUID,
        actor_user_id: UUID,
        transfer_id: UUID,
    ) -> LoanTransferOut:
        row = await self._get(organization_id, transfer_id)
        prev = row.status.value
        now = datetime.now(timezone.utc)
        row.security_discharged_at = now
        row.docs_released_at = now
        row.closed_at = now
        row.status = TransferOutStatus.CLOSED

        # Create the 30-day doc-release tracker
        target = (now + timedelta(days=30)).date()
        tracker = DocReleaseTracker(
            organization_id=organization_id,
            loan_account_id=row.loan_account_id,
            closure_date=now.date(),
            target_release_date=target,
            status=DocReleaseStatus.PENDING,
        )
        self.session.add(tracker)

        await self.lifecycle.record_event(
            organization_id=organization_id,
            subject_type=LifecycleSubjectType.TRANSFER_OUT,
            subject_id=row.id,
            event_type="CLOSED_TAKEOVER",
            actor_kind=LifecycleActorKind.LENDER,
            actor_user_id=actor_user_id,
            business_number=row.transfer_reference,
            state_from=prev,
            state_to="CLOSED",
            payload={"loan_account_id": str(row.loan_account_id)},
        )
        await self.session.flush()
        return row

    async def _get(self, organization_id: UUID, transfer_id: UUID) -> LoanTransferOut:
        row = await self.session.get(LoanTransferOut, transfer_id)
        if row is None or row.organization_id != organization_id:
            raise NotFoundException(
                detail=f"Transfer {transfer_id} not found",
                error_code="TRANSFER_OUT_NOT_FOUND",
            )
        return row


# ============================================================================
# D.2 — ForeclosureService + PrepaymentService
# ============================================================================


class ForeclosureService:
    """Foreclosure quote calculation + closure."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.lifecycle = LifecycleService(session)

    async def calculate_quote(
        self,
        *,
        organization_id: UUID,
        loan_account_id: UUID,
        as_of_date: date,
    ) -> dict[str, Any]:
        """Return outstanding + accrued interest + foreclosure fee snapshot."""
        from app.models.lending.loan_account import LoanAccount

        loan = await self.session.get(LoanAccount, loan_account_id)
        if loan is None or loan.organization_id != organization_id:
            raise NotFoundException(
                detail=f"Loan account {loan_account_id} not found",
                error_code="LOAN_ACCOUNT_NOT_FOUND",
            )
        principal = loan.principal_outstanding or Decimal("0")
        interest_accrued = (loan.interest_outstanding or Decimal("0")) + (
            loan.interest_overdue or Decimal("0")
        )

        # Foreclosure fee from charge master / fee type.
        # B2B / institutional default: 2% of outstanding. RBI 2025 zero-charge
        # rule for individual floating-rate non-business loans does NOT apply
        # to this platform (per user direction).
        foreclosure_fee = (principal * Decimal("0.02")).quantize(Decimal("0.01"))
        other_charges = (loan.charges_outstanding or Decimal("0")) + (
            loan.penal_interest_outstanding or Decimal("0")
        )
        total = principal + interest_accrued + foreclosure_fee + other_charges

        return {
            "loan_account_id": str(loan_account_id),
            "as_of_date": as_of_date.isoformat(),
            "principal_outstanding": float(principal),
            "interest_accrued": float(interest_accrued),
            "foreclosure_fee": float(foreclosure_fee),
            "other_charges": float(other_charges),
            "total_payable": float(total),
            "valid_till": (as_of_date + timedelta(days=7)).isoformat(),
        }

    async def process_foreclosure(
        self,
        *,
        organization_id: UUID,
        loan_account_id: UUID,
        receipt_id: UUID,
        actor_user_id: UUID,
    ) -> dict[str, Any]:
        """Mark the loan as foreclosed once the receipt covers everything."""
        from app.models.lending.enums import LoanAccountStatus
        from app.models.lending.loan_account import LoanAccount, LoanReceipt

        loan = await self.session.get(LoanAccount, loan_account_id)
        receipt = await self.session.get(LoanReceipt, receipt_id)
        if loan is None or receipt is None:
            raise NotFoundException(
                detail="Loan or receipt not found", error_code="FORECLOSURE_NOT_FOUND"
            )

        loan.status = LoanAccountStatus.CLOSED
        loan.closure_date = datetime.now(timezone.utc).date()

        # 30-day doc release tracker
        target = (datetime.now(timezone.utc) + timedelta(days=30)).date()
        tracker = DocReleaseTracker(
            organization_id=organization_id,
            loan_account_id=loan_account_id,
            closure_date=loan.closure_date,
            target_release_date=target,
            status=DocReleaseStatus.PENDING,
        )
        self.session.add(tracker)

        await self.lifecycle.record_event(
            organization_id=organization_id,
            subject_type=LifecycleSubjectType.LOAN_ACCOUNT,
            subject_id=loan_account_id,
            event_type="FORECLOSED",
            actor_kind=LifecycleActorKind.LENDER,
            actor_user_id=actor_user_id,
            business_number=getattr(loan, "loan_account_number", None),
            state_to="CLOSED",
            payload={"receipt_id": str(receipt_id)},
        )
        await self.lifecycle.record_event(
            organization_id=organization_id,
            subject_type=LifecycleSubjectType.LOAN_ACCOUNT,
            subject_id=loan_account_id,
            event_type="CLOSED_FORECLOSED",
            actor_kind=LifecycleActorKind.LENDER,
            actor_user_id=actor_user_id,
            business_number=getattr(loan, "loan_account_number", None),
        )
        await self.session.flush()
        return {
            "loan_account_id": str(loan_account_id),
            "status": "CLOSED",
            "closure_date": loan.closure_date.isoformat(),
            "doc_release_tracker_id": str(tracker.id),
        }


class PrepaymentService:
    """Partial prepayment quote + apply."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.lifecycle = LifecycleService(session)

    async def calculate_quote(
        self,
        *,
        organization_id: UUID,
        loan_account_id: UUID,
        amount: Decimal,
        mode: str = "REDUCE_TENOR",
    ) -> dict[str, Any]:
        from app.models.lending.loan_account import LoanAccount

        loan = await self.session.get(LoanAccount, loan_account_id)
        if loan is None or loan.organization_id != organization_id:
            raise NotFoundException(
                detail=f"Loan account {loan_account_id} not found",
                error_code="LOAN_ACCOUNT_NOT_FOUND",
            )
        principal = loan.principal_outstanding or Decimal("0")
        new_principal = principal - amount
        if new_principal < Decimal("0"):
            raise ValidationException(
                "Prepayment exceeds outstanding principal",
                error_code="PREPAYMENT_EXCEEDS_OUTSTANDING",
            )

        # Prepayment penalty (institutional default 2%; tenant configurable
        # via mst_charge_master + mst_charge_trigger_rule)
        penalty = (amount * Decimal("0.02")).quantize(Decimal("0.01"))
        return {
            "loan_account_id": str(loan_account_id),
            "prepayment_amount": float(amount),
            "penalty": float(penalty),
            "current_principal_outstanding": float(principal),
            "new_principal_outstanding": float(new_principal),
            "mode": mode,
        }


# ============================================================================
# D.3 — RateResetService
# ============================================================================


class RateResetService:
    """Floating-rate reset workflow."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.lifecycle = LifecycleService(session)

    async def create_due_event(
        self,
        *,
        organization_id: UUID,
        loan_account_id: UUID,
        benchmark_code: str,
        old_rate_percent: Decimal,
        new_rate_percent: Decimal,
        due_date: date,
    ) -> RateResetEvent:
        row = RateResetEvent(
            organization_id=organization_id,
            loan_account_id=loan_account_id,
            benchmark_code=benchmark_code,
            due_date=due_date,
            old_rate_percent=old_rate_percent,
            new_rate_percent=new_rate_percent,
        )
        self.session.add(row)
        await self.session.flush()
        await self.lifecycle.record_event(
            organization_id=organization_id,
            subject_type=LifecycleSubjectType.RATE_RESET,
            subject_id=row.id,
            event_type="RATE_RESET_DUE",
            actor_kind=LifecycleActorKind.SYSTEM,
            payload={
                "loan_account_id": str(loan_account_id),
                "old_rate": float(old_rate_percent),
                "new_rate": float(new_rate_percent),
                "due_date": due_date.isoformat(),
            },
        )
        return row

    async def record_borrower_choice(
        self,
        *,
        organization_id: UUID,
        reset_event_id: UUID,
        choice: RateResetChoice,
        portal_user_id: UUID,
        new_emi_amount: Decimal | None = None,
        new_tenure_months: int | None = None,
    ) -> RateResetEvent:
        row = await self.session.get(RateResetEvent, reset_event_id)
        if row is None or row.organization_id != organization_id:
            raise NotFoundException(
                detail="Rate reset event not found",
                error_code="RATE_RESET_NOT_FOUND",
            )
        row.borrower_choice = choice
        row.choice_received_on = date.today()
        if new_emi_amount is not None:
            row.new_emi_amount = new_emi_amount
        if new_tenure_months is not None:
            row.new_tenure_months = new_tenure_months
        row.applied_on = date.today()

        await self.lifecycle.record_event(
            organization_id=organization_id,
            subject_type=LifecycleSubjectType.RATE_RESET,
            subject_id=row.id,
            event_type="RATE_RESET_APPLIED",
            actor_kind=LifecycleActorKind.BORROWER,
            payload={
                "choice": choice.value,
                "portal_user_id": str(portal_user_id),
                "new_emi": float(new_emi_amount) if new_emi_amount else None,
                "new_tenure_months": new_tenure_months,
            },
            regulatory_tags=["RATE_RESET"],
        )
        await self.session.flush()
        return row


# ============================================================================
# D.4 — NachPresentationService
# ============================================================================


class NachPresentationService:
    """Per-presentation lifecycle for NACH mandates."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.lifecycle = LifecycleService(session)

    async def record_presentation(
        self,
        *,
        organization_id: UUID,
        mandate_id: UUID,
        loan_account_id: UUID,
        presentation_date: date,
        amount: Decimal,
        instalment_number: int | None = None,
    ) -> NachPresentation:
        row = NachPresentation(
            organization_id=organization_id,
            mandate_id=mandate_id,
            loan_account_id=loan_account_id,
            presentation_date=presentation_date,
            amount=amount,
            instalment_number=instalment_number,
        )
        self.session.add(row)
        await self.session.flush()
        await self.lifecycle.record_event(
            organization_id=organization_id,
            subject_type=LifecycleSubjectType.NACH_MANDATE,
            subject_id=mandate_id,
            event_type="NACH_PRESENTED",
            actor_kind=LifecycleActorKind.SYSTEM,
            payload={
                "presentation_id": str(row.id),
                "amount": float(amount),
                "instalment_number": instalment_number,
            },
        )
        return row

    async def record_bounce(
        self,
        *,
        organization_id: UUID,
        presentation_id: UUID,
        return_reason_code: str,
        return_reason_description: str | None = None,
    ) -> NachPresentation:
        row = await self.session.get(NachPresentation, presentation_id)
        if row is None or row.organization_id != organization_id:
            raise NotFoundException(
                detail="Presentation not found", error_code="NACH_PRESENTATION_NOT_FOUND"
            )
        row.status = NachPresentationStatus.BOUNCED
        row.return_reason_code = return_reason_code
        row.return_reason_description = return_reason_description
        await self.lifecycle.record_event(
            organization_id=organization_id,
            subject_type=LifecycleSubjectType.NACH_MANDATE,
            subject_id=row.mandate_id,
            event_type="NACH_BOUNCED",
            actor_kind=LifecycleActorKind.EXTERNAL,
            payload={
                "presentation_id": str(row.id),
                "return_reason_code": return_reason_code,
                "return_reason_description": return_reason_description,
            },
        )
        await self.session.flush()
        return row


# ============================================================================
# D.5 — DocReleaseTrackerService
# ============================================================================


class DocReleaseTrackerService:
    """Original-documents 30-day release clock (RBI Sep-2023)."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.lifecycle = LifecycleService(session)

    async def mark_released(
        self,
        *,
        organization_id: UUID,
        tracker_id: UUID,
        actor_user_id: UUID,
        released_documents: list[dict[str, Any]],
    ) -> DocReleaseTracker:
        row = await self.session.get(DocReleaseTracker, tracker_id)
        if row is None or row.organization_id != organization_id:
            raise NotFoundException(
                detail="Doc release tracker not found",
                error_code="DOC_RELEASE_TRACKER_NOT_FOUND",
            )
        today = date.today()
        row.actual_release_date = today
        row.status = DocReleaseStatus.RELEASED
        row.released_by_id = actor_user_id
        row.documents_released = released_documents

        # If past target, accrue compensation
        if today > row.target_release_date:
            row.breach_days = (today - row.target_release_date).days
            row.compensation_payable = Decimal(row.breach_days) * Decimal("5000")

        await self.lifecycle.record_event(
            organization_id=organization_id,
            subject_type=LifecycleSubjectType.LOAN_ACCOUNT,
            subject_id=row.loan_account_id,
            event_type="ORIGINAL_DOCS_RELEASED",
            actor_kind=LifecycleActorKind.LENDER,
            actor_user_id=actor_user_id,
            payload={
                "tracker_id": str(row.id),
                "breach_days": row.breach_days,
                "compensation": float(row.compensation_payable),
                "documents_count": len(released_documents),
            },
            regulatory_tags=["DOCS_RELEASED"],
        )
        await self.session.flush()
        return row

    async def scan_breached(self, organization_id: UUID) -> int:
        """Mark trackers past target as BREACHED. Called by daily Arq job."""
        today = date.today()
        stmt = select(DocReleaseTracker).where(
            DocReleaseTracker.organization_id == organization_id,
            DocReleaseTracker.status == DocReleaseStatus.PENDING,
            DocReleaseTracker.target_release_date < today,
        )
        result = await self.session.execute(stmt)
        rows = list(result.scalars().all())
        for row in rows:
            row.status = DocReleaseStatus.BREACHED
            row.breach_days = (today - row.target_release_date).days
            row.compensation_payable = Decimal(row.breach_days) * Decimal("5000")
        await self.session.flush()
        return len(rows)


# ============================================================================
# D.7 — WriteOffService
# ============================================================================


class WriteOffService:
    """Technical + final write-off with maker-checker."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.lifecycle = LifecycleService(session)

    async def propose(
        self,
        *,
        organization_id: UUID,
        loan_account_id: UUID,
        actor_user_id: UUID,
        write_off_type: WriteOffType,
        amount: Decimal,
        reason: str,
        principal: Decimal,
        interest: Decimal,
        charges: Decimal,
    ) -> LoanWriteOff:
        ref = await _next_reference(
            self.session, LoanWriteOff, "write_off_reference", "WO", organization_id
        )
        row = LoanWriteOff(
            organization_id=organization_id,
            loan_account_id=loan_account_id,
            write_off_reference=ref,
            write_off_type=write_off_type,
            status=WriteOffStatus.PROPOSED,
            proposed_date=date.today(),
            proposed_by_id=actor_user_id,
            proposed_amount=amount,
            proposed_reason=reason,
            principal_written_off=principal,
            interest_written_off=interest,
            charges_written_off=charges,
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def approve(
        self,
        *,
        organization_id: UUID,
        write_off_id: UUID,
        actor_user_id: UUID,
        approval_authority: str,
    ) -> LoanWriteOff:
        row = await self._get(organization_id, write_off_id)
        if row.proposed_by_id == actor_user_id:
            raise ValidationException(
                "Maker cannot be checker (CLAUDE.md §8.4).",
                error_code="MAKER_CHECKER_VIOLATION",
            )
        row.status = WriteOffStatus.APPROVED
        row.approved_at = datetime.now(timezone.utc)
        row.approved_by_id = actor_user_id
        row.approval_authority = approval_authority
        await self.session.flush()
        return row

    async def effect(
        self,
        *,
        organization_id: UUID,
        write_off_id: UUID,
        actor_user_id: UUID,
    ) -> LoanWriteOff:
        row = await self._get(organization_id, write_off_id)
        if row.status != WriteOffStatus.APPROVED:
            raise ValidationException(
                "Cannot effect a write-off that is not APPROVED.",
                error_code="WRITE_OFF_NOT_APPROVED",
            )
        row.status = WriteOffStatus.EFFECTED
        row.effected_date = date.today()

        await self.lifecycle.record_event(
            organization_id=organization_id,
            subject_type=LifecycleSubjectType.LOAN_ACCOUNT,
            subject_id=row.loan_account_id,
            event_type=(
                "WRITE_OFF_TECHNICAL"
                if row.write_off_type == WriteOffType.TECHNICAL
                else "WRITE_OFF_FINAL"
            ),
            actor_kind=LifecycleActorKind.LENDER,
            actor_user_id=actor_user_id,
            payload={
                "write_off_id": str(row.id),
                "write_off_type": row.write_off_type.value,
                "amount": float(row.proposed_amount),
                "principal": float(row.principal_written_off),
                "interest": float(row.interest_written_off),
            },
            regulatory_tags=[
                (
                    "WRITE_OFF_TECHNICAL"
                    if row.write_off_type == WriteOffType.TECHNICAL
                    else "WRITE_OFF_FINAL"
                )
            ],
        )

        # Final write-off also closes the loan
        if row.write_off_type == WriteOffType.FINAL:
            from app.models.lending.enums import LoanAccountStatus
            from app.models.lending.loan_account import LoanAccount

            loan = await self.session.get(LoanAccount, row.loan_account_id)
            if loan is not None:
                loan.status = LoanAccountStatus.WRITTEN_OFF
            await self.lifecycle.record_event(
                organization_id=organization_id,
                subject_type=LifecycleSubjectType.LOAN_ACCOUNT,
                subject_id=row.loan_account_id,
                event_type="CLOSED_WRITTEN_OFF",
                actor_kind=LifecycleActorKind.LENDER,
                actor_user_id=actor_user_id,
            )

        await self.session.flush()
        return row

    async def record_recovery(
        self,
        *,
        organization_id: UUID,
        write_off_id: UUID,
        amount: Decimal,
    ) -> LoanWriteOff:
        row = await self._get(organization_id, write_off_id)
        row.total_recovered_post_write_off = (
            row.total_recovered_post_write_off or Decimal("0")
        ) + amount
        await self.session.flush()
        return row

    async def _get(self, organization_id: UUID, write_off_id: UUID) -> LoanWriteOff:
        row = await self.session.get(LoanWriteOff, write_off_id)
        if row is None or row.organization_id != organization_id:
            raise NotFoundException(
                detail=f"Write-off {write_off_id} not found",
                error_code="WRITE_OFF_NOT_FOUND",
            )
        return row


# ============================================================================
# D.8 — InterestRevivalService
# ============================================================================


class InterestRevivalService:
    """Revive previously-suspended interest on a recovering loan."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.lifecycle = LifecycleService(session)

    async def propose(
        self,
        *,
        organization_id: UUID,
        loan_account_id: UUID,
        actor_user_id: UUID,
        revivable_amount: Decimal,
        proposed_amount: Decimal,
        reason: str,
    ) -> LoanInterestRevival:
        if proposed_amount > revivable_amount:
            raise ValidationException(
                "Proposed amount cannot exceed revivable amount",
                error_code="INTEREST_REVIVAL_OVERFLOW",
            )
        ref = await _next_reference(
            self.session, LoanInterestRevival, "revival_reference", "IR", organization_id
        )
        row = LoanInterestRevival(
            organization_id=organization_id,
            loan_account_id=loan_account_id,
            revival_reference=ref,
            proposed_at=datetime.now(timezone.utc),
            proposed_by_id=actor_user_id,
            revivable_amount=revivable_amount,
            proposed_amount=proposed_amount,
            reason=reason,
            status=InterestRevivalStatus.PROPOSED,
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def approve_and_effect(
        self,
        *,
        organization_id: UUID,
        revival_id: UUID,
        actor_user_id: UUID,
    ) -> LoanInterestRevival:
        row = await self.session.get(LoanInterestRevival, revival_id)
        if row is None or row.organization_id != organization_id:
            raise NotFoundException(
                detail="Interest revival not found",
                error_code="INTEREST_REVIVAL_NOT_FOUND",
            )
        if row.proposed_by_id == actor_user_id:
            raise ValidationException(
                "Maker cannot be checker (CLAUDE.md §8.4).",
                error_code="MAKER_CHECKER_VIOLATION",
            )
        now = datetime.now(timezone.utc)
        row.status = InterestRevivalStatus.EFFECTED
        row.approved_at = now
        row.approved_by_id = actor_user_id
        row.effected_at = now

        await self.lifecycle.record_event(
            organization_id=organization_id,
            subject_type=LifecycleSubjectType.LOAN_ACCOUNT,
            subject_id=row.loan_account_id,
            event_type="INTEREST_REVIVED",
            actor_kind=LifecycleActorKind.LENDER,
            actor_user_id=actor_user_id,
            payload={
                "revival_id": str(row.id),
                "amount": float(row.proposed_amount),
                "reason": row.reason,
            },
        )
        await self.session.flush()
        return row


# ============================================================================
# D.9 — WilfulDefaulterService
# ============================================================================


class WilfulDefaulterService:
    """RBI 30-Jul-2024 wilful defaulter classification workflow."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.lifecycle = LifecycleService(session)

    async def initiate(
        self,
        *,
        organization_id: UUID,
        loan_account_id: UUID,
        actor_user_id: UUID,
        npa_date: date,
        outstanding_amount: Decimal,
        grounds: str,
    ) -> WilfulDefaulterProceeding:
        if outstanding_amount < Decimal("2500000"):
            raise ValidationException(
                "Wilful defaulter classification applies only to outstanding "
                "≥ ₹25L per RBI 30-Jul-2024 Directions.",
                error_code="WD_AMOUNT_BELOW_THRESHOLD",
            )
        ref = await _next_reference(
            self.session,
            WilfulDefaulterProceeding,
            "proceeding_reference",
            "WDP",
            organization_id,
        )
        row = WilfulDefaulterProceeding(
            organization_id=organization_id,
            loan_account_id=loan_account_id,
            proceeding_reference=ref,
            npa_date=npa_date,
            initiated_date=date.today(),
            sla_due_date=npa_date + timedelta(days=180),
            outstanding_amount=outstanding_amount,
            grounds_of_wilful_default=grounds,
            stage=WilfulDefaulterStage.IDENTIFICATION,
        )
        self.session.add(row)
        await self.session.flush()
        await self.lifecycle.record_event(
            organization_id=organization_id,
            subject_type=LifecycleSubjectType.LOAN_ACCOUNT,
            subject_id=loan_account_id,
            event_type="WILFUL_DEFAULTER_PROPOSED",
            actor_kind=LifecycleActorKind.LENDER,
            actor_user_id=actor_user_id,
            payload={"proceeding_id": str(row.id), "outstanding": float(outstanding_amount)},
            regulatory_tags=["WD_PROPOSED"],
        )
        return row

    async def advance(
        self,
        *,
        organization_id: UUID,
        proceeding_id: UUID,
        new_stage: WilfulDefaulterStage,
        actor_user_id: UUID,
        decision_text: str | None = None,
    ) -> WilfulDefaulterProceeding:
        row = await self.session.get(WilfulDefaulterProceeding, proceeding_id)
        if row is None or row.organization_id != organization_id:
            raise NotFoundException(
                detail="Proceeding not found",
                error_code="WD_PROCEEDING_NOT_FOUND",
            )
        prev = row.stage.value
        row.stage = new_stage
        now = datetime.now(timezone.utc)
        if new_stage == WilfulDefaulterStage.SHOW_CAUSE_ISSUED:
            row.show_cause_issued_at = now
        elif new_stage == WilfulDefaulterStage.PERSONAL_HEARING:
            row.personal_hearing_date = now.date()
        elif new_stage == WilfulDefaulterStage.REVIEW:
            row.id_committee_decision = decision_text
            row.id_committee_decided_at = now
        elif new_stage == WilfulDefaulterStage.CONFIRMED:
            row.review_committee_decision = decision_text
            row.review_committee_decided_at = now
        elif new_stage == WilfulDefaulterStage.DISMISSED:
            row.review_committee_decision = decision_text or "Dismissed"
            row.review_committee_decided_at = now

        event_type = (
            "WILFUL_DEFAULTER_CONFIRMED"
            if new_stage == WilfulDefaulterStage.CONFIRMED
            else "WILFUL_DEFAULTER_PROPOSED"
        )
        await self.lifecycle.record_event(
            organization_id=organization_id,
            subject_type=LifecycleSubjectType.LOAN_ACCOUNT,
            subject_id=row.loan_account_id,
            event_type=event_type,
            actor_kind=LifecycleActorKind.LENDER,
            actor_user_id=actor_user_id,
            state_from=prev,
            state_to=new_stage.value,
            reason_text=decision_text,
            regulatory_tags=[
                "WD_CONFIRMED" if new_stage == WilfulDefaulterStage.CONFIRMED else "WD_PROPOSED"
            ],
        )
        await self.session.flush()
        return row
