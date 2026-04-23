"""Payment API endpoints."""

from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_current_user, get_db
# from app.core.permissions import RequirePermissions
from app.core.responses import PaginatedResponse
from app.models.auth.user import User
from app.models.ap_ar.payment import (
    PaymentType,
    PartyType,
    PaymentMode,
    PaymentStatus,
    ChequeStatus,
)
from app.schemas.ap_ar.payment import (
    PaymentCreate,
    PaymentUpdate,
    ChequeStatusUpdate,
    PaymentResponse,
    PaymentDetailResponse,
    PaymentListResponse,
    PendingChequeResponse,
    OutstandingDocumentResponse,
)
from app.services.ap_ar.payment_service import PaymentService

router = APIRouter()


def _to_list_response(payment) -> PaymentListResponse:
    """Convert payment to list response."""
    return PaymentListResponse(
        id=payment.id,
        payment_number=payment.payment_number,
        payment_date=payment.payment_date,
        payment_type=payment.payment_type,
        party_type=payment.party_type,
        party_name=payment.party_name,
        payment_mode=payment.payment_mode,
        amount=payment.amount,
        net_amount=payment.net_amount,
        status=payment.status,
        cheque_status=payment.cheque_status,
        is_posted=payment.is_posted,
        created_at=payment.created_at,
    )


def _to_response(payment) -> PaymentResponse:
    """Convert payment to response."""
    return PaymentResponse(
        id=payment.id,
        payment_number=payment.payment_number,
        payment_date=payment.payment_date,
        payment_type=payment.payment_type,
        party_type=payment.party_type,
        vendor_id=payment.vendor_id,
        customer_id=payment.customer_id,
        organization_id=payment.organization_id,
        unit_id=payment.unit_id,
        payment_mode=payment.payment_mode,
        bank_account_id=payment.bank_account_id,
        cash_account_id=payment.cash_account_id,
        amount=payment.amount,
        tds_amount=payment.tds_amount,
        tds_section_id=payment.tds_section_id,
        tds_rate=payment.tds_rate,
        discount_amount=payment.discount_amount,
        write_off_amount=payment.write_off_amount,
        net_amount=payment.net_amount,
        currency_code=payment.currency_code,
        exchange_rate=payment.exchange_rate,
        cheque_number=payment.cheque_number,
        cheque_date=payment.cheque_date,
        cheque_bank_name=payment.cheque_bank_name,
        cheque_branch=payment.cheque_branch,
        cheque_status=payment.cheque_status,
        cheque_cleared_date=payment.cheque_cleared_date,
        cheque_bounced_date=payment.cheque_bounced_date,
        cheque_bounced_reason=payment.cheque_bounced_reason,
        reference_number=payment.reference_number,
        narration=payment.narration,
        status=payment.status,
        submitted_at=payment.submitted_at,
        approved_at=payment.approved_at,
        cancelled_at=payment.cancelled_at,
        cancellation_reason=payment.cancellation_reason,
        voucher_id=payment.voucher_id,
        is_posted=payment.is_posted,
        posted_at=payment.posted_at,
        allocated_amount=payment.allocated_amount,
        unallocated_amount=payment.unallocated_amount,
        vendor_name=payment.vendor.name if payment.vendor else None,
        customer_name=payment.customer.name if payment.customer else None,
        bank_account_name=payment.bank_account.name if payment.bank_account else None,
        cash_account_name=payment.cash_account.name if payment.cash_account else None,
        tds_section_code=payment.tds_section.section_code if payment.tds_section else None,
        created_at=payment.created_at,
        updated_at=payment.updated_at,
    )


def _to_detail_response(payment) -> PaymentDetailResponse:
    """Convert payment to detailed response with allocations."""
    from app.schemas.ap_ar.payment import PaymentAllocationResponse

    response = _to_response(payment)
    allocations = [
        PaymentAllocationResponse(
            id=alloc.id,
            document_type=alloc.document_type,
            document_id=alloc.document_id,
            document_number=alloc.document_number,
            document_date=alloc.document_date,
            document_amount=alloc.document_amount,
            outstanding_before=alloc.outstanding_before,
            allocated_amount=alloc.allocated_amount,
            allocation_date=alloc.allocation_date,
        )
        for alloc in payment.allocations
    ]

    return PaymentDetailResponse(
        **response.model_dump(),
        allocations=allocations,
    )


@router.get("", response_model=PaginatedResponse[PaymentListResponse])
# @RequirePermissions("APAR_PAYMENT_VIEW")
async def list_payments(
    organization_id: UUID = Query(...),
    search: Optional[str] = Query(None),
    payment_type: Optional[PaymentType] = Query(None),
    party_type: Optional[PartyType] = Query(None),
    vendor_id: Optional[UUID] = Query(None),
    customer_id: Optional[UUID] = Query(None),
    payment_mode: Optional[PaymentMode] = Query(None),
    status: Optional[PaymentStatus] = Query(None),
    cheque_status: Optional[ChequeStatus] = Query(None),
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    is_posted: Optional[bool] = Query(None),
    unit_id: Optional[UUID] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db=Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List payments with filters and pagination."""
    service = PaymentService(db)
    payments, total = await service.list_payments(
        organization_id,
        search=search,
        payment_type=payment_type,
        party_type=party_type,
        vendor_id=vendor_id,
        customer_id=customer_id,
        payment_mode=payment_mode,
        status=status,
        cheque_status=cheque_status,
        from_date=from_date,
        to_date=to_date,
        is_posted=is_posted,
        unit_id=unit_id,
        skip=skip,
        limit=limit,
    )

    # Convert skip/limit to page/page_size
    page = (skip // limit) + 1 if limit > 0 else 1
    return PaginatedResponse.create(
        items=[_to_list_response(p) for p in payments],
        total=total,
        page=page,
        page_size=limit,
    )


@router.get("/generate-number")
# @RequirePermissions("APAR_PAYMENT_CREATE")
async def generate_payment_number(
    organization_id: UUID = Query(...),
    payment_type: PaymentType = Query(...),
    db=Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate next payment number."""
    service = PaymentService(db)
    number = await service.generate_payment_number(organization_id, payment_type)
    return {"payment_number": number}


@router.get("/pending-cheques", response_model=PaginatedResponse[PendingChequeResponse])
# @RequirePermissions("APAR_PAYMENT_VIEW")
async def list_pending_cheques(
    organization_id: UUID = Query(...),
    party_type: Optional[PartyType] = Query(None),
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db=Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List pending (uncleared) cheques."""
    service = PaymentService(db)
    payments, total = await service.get_pending_cheques(
        organization_id,
        party_type=party_type,
        from_date=from_date,
        to_date=to_date,
        skip=skip,
        limit=limit,
    )

    today = date.today()
    items = [
        PendingChequeResponse(
            id=p.id,
            payment_number=p.payment_number,
            payment_date=p.payment_date,
            party_type=p.party_type,
            party_name=p.party_name,
            cheque_number=p.cheque_number,
            cheque_date=p.cheque_date,
            cheque_bank_name=p.cheque_bank_name,
            amount=p.amount,
            cheque_status=p.cheque_status,
            days_pending=(today - p.cheque_date).days if p.cheque_date else 0,
        )
        for p in payments
    ]

    # Convert skip/limit to page/page_size
    page = (skip // limit) + 1 if limit > 0 else 1
    return PaginatedResponse.create(
        items=items,
        total=total,
        page=page,
        page_size=limit,
    )


@router.get("/outstanding/{party_type}/{party_id}", response_model=list[OutstandingDocumentResponse])
# @RequirePermissions("APAR_PAYMENT_VIEW")
async def get_outstanding_documents(
    party_type: PartyType,
    party_id: UUID,
    organization_id: UUID = Query(...),
    db=Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get outstanding documents for allocation."""
    service = PaymentService(db)
    documents = await service.get_outstanding_documents(
        party_type, party_id, organization_id
    )
    return [OutstandingDocumentResponse(**doc) for doc in documents]


@router.get("/{payment_id}", response_model=PaymentDetailResponse)
# @RequirePermissions("APAR_PAYMENT_VIEW")
async def get_payment(
    payment_id: UUID,
    db=Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get payment details with allocations."""
    service = PaymentService(db)
    payment = await service.get_by_id(payment_id)
    return _to_detail_response(payment)


@router.post("", response_model=PaymentDetailResponse, status_code=status.HTTP_201_CREATED)
# @RequirePermissions("APAR_PAYMENT_CREATE")
async def create_payment(
    data: PaymentCreate,
    db=Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new payment entry."""
    service = PaymentService(db)
    payment = await service.create_payment(data, current_user.id)
    return _to_detail_response(payment)


@router.put("/{payment_id}", response_model=PaymentDetailResponse)
# @RequirePermissions("APAR_PAYMENT_UPDATE")
async def update_payment(
    payment_id: UUID,
    data: PaymentUpdate,
    db=Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a draft payment."""
    service = PaymentService(db)
    payment = await service.update_payment(payment_id, data, current_user.id)
    return _to_detail_response(payment)


@router.post("/{payment_id}/submit", response_model=PaymentResponse)
# @RequirePermissions("APAR_PAYMENT_UPDATE")
async def submit_payment(
    payment_id: UUID,
    db=Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Submit payment for approval."""
    service = PaymentService(db)
    payment = await service.submit_payment(payment_id, current_user.id)
    return _to_response(payment)


@router.post("/{payment_id}/approve", response_model=PaymentResponse)
# @RequirePermissions("APAR_PAYMENT_APPROVE")
async def approve_payment(
    payment_id: UUID,
    db=Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Approve and post payment."""
    service = PaymentService(db)
    payment = await service.approve_payment(payment_id, current_user.id)
    return _to_response(payment)


@router.post("/{payment_id}/cancel", response_model=PaymentResponse)
# @RequirePermissions("APAR_PAYMENT_UPDATE")
async def cancel_payment(
    payment_id: UUID,
    reason: str = Query(..., min_length=3),
    db=Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cancel a payment."""
    service = PaymentService(db)
    payment = await service.cancel_payment(payment_id, current_user.id, reason)
    return _to_response(payment)


@router.post("/{payment_id}/cheque-status", response_model=PaymentResponse)
# @RequirePermissions("APAR_PAYMENT_UPDATE")
async def update_cheque_status(
    payment_id: UUID,
    data: ChequeStatusUpdate,
    db=Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update cheque status (cleared/bounced/etc)."""
    service = PaymentService(db)
    payment = await service.update_cheque_status(payment_id, data, current_user.id)
    return _to_response(payment)


@router.delete("/{payment_id}", status_code=status.HTTP_204_NO_CONTENT)
# @RequirePermissions("APAR_PAYMENT_DELETE")
async def delete_payment(
    payment_id: UUID,
    db=Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a draft payment."""
    service = PaymentService(db)
    await service.delete_payment(payment_id, current_user.id)
