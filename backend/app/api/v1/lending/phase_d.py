"""Phase-D API endpoints — all 8 lifecycle modules.

Slim REST surface: 1-3 endpoints per module, just enough to demonstrate
the workflow end-to-end. Heavy iteration happens after operators give
feedback on the spine.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RequirePermissions, get_current_user, get_db_with_tenant
from app.models.lending.lifecycle_event import LifecycleActorKind
from app.models.lending.lifecycle_modules import (
    RateResetChoice,
    TakeoverStatus,
    WilfulDefaulterStage,
    WriteOffType,
)
from app.schemas.base import CamelSchema
from app.services.lending.phase_d_services import (
    DocReleaseTrackerService,
    ForeclosureService,
    InterestRevivalService,
    NachPresentationService,
    PrepaymentService,
    RateResetService,
    TakeoverInService,
    TransferOutService,
    WilfulDefaulterService,
    WriteOffService,
)

router = APIRouter()


# ============================================================================
# Schemas
# ============================================================================


class _IdResponse(CamelSchema):
    id: UUID
    reference: Optional[str] = None
    status: Optional[str] = None


class TakeoverInitiateRequest(CamelSchema):
    source_lender_name: str
    source_loan_account_no: str
    source_outstanding: Decimal = Field(..., gt=0)
    application_id: Optional[UUID] = None


class TakeoverAdvanceRequest(CamelSchema):
    new_status: TakeoverStatus
    transferred_amount: Optional[Decimal] = None
    transfer_date: Optional[date] = None
    dd_or_rtgs_reference: Optional[str] = None


class TransferOutRequestNocRequest(CamelSchema):
    target_lender_name: str


class TransferOutOutstandingRequest(CamelSchema):
    outstanding_amount: Decimal = Field(..., ge=0)
    valid_till: date


class TransferOutPaymentRequest(CamelSchema):
    amount: Decimal = Field(..., gt=0)
    reference: str


class ForeclosureQuoteRequest(CamelSchema):
    as_of_date: date


class PrepaymentQuoteRequest(CamelSchema):
    amount: Decimal = Field(..., gt=0)
    mode: str = "REDUCE_TENOR"


class RateResetDueRequest(CamelSchema):
    benchmark_code: str
    old_rate_percent: Decimal
    new_rate_percent: Decimal
    due_date: date


class RateResetChoiceRequest(CamelSchema):
    choice: RateResetChoice
    new_emi_amount: Optional[Decimal] = None
    new_tenure_months: Optional[int] = None


class NachPresentationRequest(CamelSchema):
    mandate_id: UUID
    loan_account_id: UUID
    presentation_date: date
    amount: Decimal
    instalment_number: Optional[int] = None


class NachBounceRequest(CamelSchema):
    return_reason_code: str
    return_reason_description: Optional[str] = None


class DocReleaseMarkRequest(CamelSchema):
    released_documents: list[dict[str, Any]] = Field(default_factory=list)


class WriteOffProposeRequest(CamelSchema):
    loan_account_id: UUID
    write_off_type: WriteOffType
    amount: Decimal = Field(..., gt=0)
    reason: str
    principal: Decimal = Field(..., ge=0)
    interest: Decimal = Field(..., ge=0)
    charges: Decimal = Field(..., ge=0)


class WriteOffApproveRequest(CamelSchema):
    approval_authority: str


class InterestRevivalProposeRequest(CamelSchema):
    loan_account_id: UUID
    revivable_amount: Decimal = Field(..., gt=0)
    proposed_amount: Decimal = Field(..., gt=0)
    reason: str


class WilfulDefaulterInitiateRequest(CamelSchema):
    loan_account_id: UUID
    npa_date: date
    outstanding_amount: Decimal = Field(..., gt=0)
    grounds: str


class WilfulDefaulterAdvanceRequest(CamelSchema):
    new_stage: WilfulDefaulterStage
    decision_text: Optional[str] = None


# ============================================================================
# Takeover-in
# ============================================================================


@router.post(
    "/takeovers/in",
    response_model=_IdResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("LMS_WRITE"))],
)
async def initiate_takeover(
    data: TakeoverInitiateRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
) -> _IdResponse:
    async with db.begin():
        service = TakeoverInService(db)
        row = await service.initiate(
            organization_id=current_user.organization_id,
            actor_user_id=current_user.id,
            **data.model_dump(),
        )
    await db.refresh(row)
    return _IdResponse(id=row.id, reference=row.takeover_reference, status=row.status.value)


@router.post(
    "/takeovers/in/{takeover_id}/advance",
    response_model=_IdResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("LMS_WRITE"))],
)
async def advance_takeover(
    takeover_id: UUID,
    data: TakeoverAdvanceRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
) -> _IdResponse:
    async with db.begin():
        service = TakeoverInService(db)
        row = await service.advance(
            organization_id=current_user.organization_id,
            actor_user_id=current_user.id,
            takeover_id=takeover_id,
            **data.model_dump(),
        )
    await db.refresh(row)
    return _IdResponse(id=row.id, reference=row.takeover_reference, status=row.status.value)


# ============================================================================
# Transfer-out
# ============================================================================


@router.post(
    "/loan-accounts/{loan_account_id}/transfer-out",
    response_model=_IdResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("LMS_WRITE"))],
)
async def request_transfer_out_noc(
    loan_account_id: UUID,
    data: TransferOutRequestNocRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
) -> _IdResponse:
    async with db.begin():
        service = TransferOutService(db)
        row = await service.request_noc(
            organization_id=current_user.organization_id,
            actor_user_id=current_user.id,
            loan_account_id=loan_account_id,
            target_lender_name=data.target_lender_name,
            actor_kind=LifecycleActorKind.LENDER,
        )
    await db.refresh(row)
    return _IdResponse(id=row.id, reference=row.transfer_reference, status=row.status.value)


@router.post(
    "/transfers/{transfer_id}/issue-outstanding",
    response_model=_IdResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("LMS_WRITE"))],
)
async def issue_outstanding_letter(
    transfer_id: UUID,
    data: TransferOutOutstandingRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
) -> _IdResponse:
    async with db.begin():
        service = TransferOutService(db)
        row = await service.issue_outstanding_letter(
            organization_id=current_user.organization_id,
            actor_user_id=current_user.id,
            transfer_id=transfer_id,
            outstanding_amount=data.outstanding_amount,
            valid_till=data.valid_till,
        )
    await db.refresh(row)
    return _IdResponse(id=row.id, reference=row.transfer_reference, status=row.status.value)


@router.post(
    "/transfers/{transfer_id}/record-payment",
    response_model=_IdResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("LMS_WRITE"))],
)
async def record_transfer_payment(
    transfer_id: UUID,
    data: TransferOutPaymentRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
) -> _IdResponse:
    async with db.begin():
        service = TransferOutService(db)
        row = await service.record_payment(
            organization_id=current_user.organization_id,
            actor_user_id=current_user.id,
            transfer_id=transfer_id,
            amount=data.amount,
            reference=data.reference,
        )
    await db.refresh(row)
    return _IdResponse(id=row.id, reference=row.transfer_reference, status=row.status.value)


@router.post(
    "/transfers/{transfer_id}/close",
    response_model=_IdResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("LMS_WRITE"))],
)
async def close_transfer(
    transfer_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
) -> _IdResponse:
    async with db.begin():
        service = TransferOutService(db)
        row = await service.close(
            organization_id=current_user.organization_id,
            actor_user_id=current_user.id,
            transfer_id=transfer_id,
        )
    await db.refresh(row)
    return _IdResponse(id=row.id, reference=row.transfer_reference, status=row.status.value)


# ============================================================================
# Foreclosure + Prepayment
# ============================================================================


@router.post(
    "/loan-accounts/{loan_account_id}/foreclosure-quote",
    dependencies=[Depends(RequirePermissions("LMS_READ"))],
)
async def foreclosure_quote(
    loan_account_id: UUID,
    data: ForeclosureQuoteRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
):
    service = ForeclosureService(db)
    return await service.calculate_quote(
        organization_id=current_user.organization_id,
        loan_account_id=loan_account_id,
        as_of_date=data.as_of_date,
    )


@router.post(
    "/loan-accounts/{loan_account_id}/foreclose",
    dependencies=[Depends(RequirePermissions("LMS_WRITE"))],
)
async def foreclose_loan(
    loan_account_id: UUID,
    receipt_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
):
    async with db.begin():
        service = ForeclosureService(db)
        result = await service.process_foreclosure(
            organization_id=current_user.organization_id,
            loan_account_id=loan_account_id,
            receipt_id=receipt_id,
            actor_user_id=current_user.id,
        )
    return result


@router.post(
    "/loan-accounts/{loan_account_id}/prepayment-quote",
    dependencies=[Depends(RequirePermissions("LMS_READ"))],
)
async def prepayment_quote(
    loan_account_id: UUID,
    data: PrepaymentQuoteRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
):
    service = PrepaymentService(db)
    return await service.calculate_quote(
        organization_id=current_user.organization_id,
        loan_account_id=loan_account_id,
        amount=data.amount,
        mode=data.mode,
    )


# ============================================================================
# Rate reset
# ============================================================================


@router.post(
    "/loan-accounts/{loan_account_id}/rate-resets",
    response_model=_IdResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("LMS_WRITE"))],
)
async def create_rate_reset_due(
    loan_account_id: UUID,
    data: RateResetDueRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
) -> _IdResponse:
    async with db.begin():
        service = RateResetService(db)
        row = await service.create_due_event(
            organization_id=current_user.organization_id,
            loan_account_id=loan_account_id,
            **data.model_dump(),
        )
    await db.refresh(row)
    return _IdResponse(id=row.id, status="PENDING_CHOICE")


@router.post(
    "/rate-resets/{reset_id}/borrower-choice",
    response_model=_IdResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("LMS_WRITE"))],
)
async def record_rate_reset_choice(
    reset_id: UUID,
    data: RateResetChoiceRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
) -> _IdResponse:
    async with db.begin():
        service = RateResetService(db)
        row = await service.record_borrower_choice(
            organization_id=current_user.organization_id,
            reset_event_id=reset_id,
            choice=data.choice,
            portal_user_id=current_user.id,
            new_emi_amount=data.new_emi_amount,
            new_tenure_months=data.new_tenure_months,
        )
    await db.refresh(row)
    return _IdResponse(id=row.id, status="APPLIED")


# ============================================================================
# NACH presentations
# ============================================================================


@router.post(
    "/nach/presentations",
    response_model=_IdResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("LMS_WRITE"))],
)
async def record_nach_presentation(
    data: NachPresentationRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
) -> _IdResponse:
    async with db.begin():
        service = NachPresentationService(db)
        row = await service.record_presentation(
            organization_id=current_user.organization_id,
            **data.model_dump(),
        )
    await db.refresh(row)
    return _IdResponse(id=row.id, status=row.status.value)


@router.post(
    "/nach/presentations/{presentation_id}/bounce",
    response_model=_IdResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("LMS_WRITE"))],
)
async def record_nach_bounce(
    presentation_id: UUID,
    data: NachBounceRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
) -> _IdResponse:
    async with db.begin():
        service = NachPresentationService(db)
        row = await service.record_bounce(
            organization_id=current_user.organization_id,
            presentation_id=presentation_id,
            return_reason_code=data.return_reason_code,
            return_reason_description=data.return_reason_description,
        )
    await db.refresh(row)
    return _IdResponse(id=row.id, status=row.status.value)


# ============================================================================
# Doc release tracker
# ============================================================================


@router.post(
    "/doc-release-trackers/{tracker_id}/mark-released",
    response_model=_IdResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("LMS_WRITE"))],
)
async def mark_docs_released(
    tracker_id: UUID,
    data: DocReleaseMarkRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
) -> _IdResponse:
    async with db.begin():
        service = DocReleaseTrackerService(db)
        row = await service.mark_released(
            organization_id=current_user.organization_id,
            tracker_id=tracker_id,
            actor_user_id=current_user.id,
            released_documents=data.released_documents,
        )
    await db.refresh(row)
    return _IdResponse(id=row.id, status=row.status.value)


# ============================================================================
# Write-off (maker-checker)
# ============================================================================


@router.post(
    "/write-offs/propose",
    response_model=_IdResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("LMS_WRITE"))],
)
async def propose_write_off(
    data: WriteOffProposeRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
) -> _IdResponse:
    async with db.begin():
        service = WriteOffService(db)
        row = await service.propose(
            organization_id=current_user.organization_id,
            actor_user_id=current_user.id,
            **data.model_dump(),
        )
    await db.refresh(row)
    return _IdResponse(id=row.id, reference=row.write_off_reference, status=row.status.value)


@router.post(
    "/write-offs/{write_off_id}/approve",
    response_model=_IdResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("LMS_APPROVE"))],
)
async def approve_write_off(
    write_off_id: UUID,
    data: WriteOffApproveRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
) -> _IdResponse:
    async with db.begin():
        service = WriteOffService(db)
        row = await service.approve(
            organization_id=current_user.organization_id,
            write_off_id=write_off_id,
            actor_user_id=current_user.id,
            approval_authority=data.approval_authority,
        )
    await db.refresh(row)
    return _IdResponse(id=row.id, reference=row.write_off_reference, status=row.status.value)


@router.post(
    "/write-offs/{write_off_id}/effect",
    response_model=_IdResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("LMS_APPROVE"))],
)
async def effect_write_off(
    write_off_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
) -> _IdResponse:
    async with db.begin():
        service = WriteOffService(db)
        row = await service.effect(
            organization_id=current_user.organization_id,
            write_off_id=write_off_id,
            actor_user_id=current_user.id,
        )
    await db.refresh(row)
    return _IdResponse(id=row.id, reference=row.write_off_reference, status=row.status.value)


# ============================================================================
# Interest revival
# ============================================================================


@router.post(
    "/interest-revivals/propose",
    response_model=_IdResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("LMS_WRITE"))],
)
async def propose_interest_revival(
    data: InterestRevivalProposeRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
) -> _IdResponse:
    async with db.begin():
        service = InterestRevivalService(db)
        row = await service.propose(
            organization_id=current_user.organization_id,
            actor_user_id=current_user.id,
            **data.model_dump(),
        )
    await db.refresh(row)
    return _IdResponse(id=row.id, reference=row.revival_reference, status=row.status.value)


@router.post(
    "/interest-revivals/{revival_id}/approve",
    response_model=_IdResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("LMS_APPROVE"))],
)
async def approve_interest_revival(
    revival_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
) -> _IdResponse:
    async with db.begin():
        service = InterestRevivalService(db)
        row = await service.approve_and_effect(
            organization_id=current_user.organization_id,
            revival_id=revival_id,
            actor_user_id=current_user.id,
        )
    await db.refresh(row)
    return _IdResponse(id=row.id, reference=row.revival_reference, status=row.status.value)


# ============================================================================
# Wilful defaulter
# ============================================================================


@router.post(
    "/wilful-defaulter/initiate",
    response_model=_IdResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("LMS_APPROVE"))],
)
async def initiate_wilful_defaulter(
    data: WilfulDefaulterInitiateRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
) -> _IdResponse:
    async with db.begin():
        service = WilfulDefaulterService(db)
        row = await service.initiate(
            organization_id=current_user.organization_id,
            actor_user_id=current_user.id,
            **data.model_dump(),
        )
    await db.refresh(row)
    return _IdResponse(id=row.id, reference=row.proceeding_reference, status=row.stage.value)


@router.post(
    "/wilful-defaulter/{proceeding_id}/advance",
    response_model=_IdResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("LMS_APPROVE"))],
)
async def advance_wilful_defaulter(
    proceeding_id: UUID,
    data: WilfulDefaulterAdvanceRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
) -> _IdResponse:
    async with db.begin():
        service = WilfulDefaulterService(db)
        row = await service.advance(
            organization_id=current_user.organization_id,
            proceeding_id=proceeding_id,
            new_stage=data.new_stage,
            actor_user_id=current_user.id,
            decision_text=data.decision_text,
        )
    await db.refresh(row)
    return _IdResponse(id=row.id, reference=row.proceeding_reference, status=row.stage.value)
