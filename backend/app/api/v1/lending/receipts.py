"""Loan Receipt API endpoints."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from pydantic import Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RequirePermissions, get_db_with_tenant
from app.models.auth.user import User
from app.models.lending.enums import ReceiptStatus
from app.schemas.base import CamelSchema, PaginatedResponse
from app.schemas.lending.loan_account import LoanReceiptListResponse
from app.services.lending import ReceiptService
from app.core.exceptions import BadRequestException, ForbiddenException, NotFoundException

router = APIRouter()


@router.get(
    "",
    response_model=PaginatedResponse[LoanReceiptListResponse],
    response_model_by_alias=True,
)
async def list_receipts(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    search: str | None = Query(None),
    status: ReceiptStatus | None = Query(None),
    current_user: User = Depends(RequirePermissions("LMS_ACCOUNT_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Paginated list of receipts scoped to caller's org."""
    service = ReceiptService(db)
    skip = (page - 1) * page_size
    items, total = await service.list_receipts_for_org(
        organization_id=current_user.organization_id,
        skip=skip,
        limit=page_size,
        search=search,
        status=status,
    )
    list_items = [LoanReceiptListResponse.model_validate(r) for r in items]
    return PaginatedResponse.create(list_items, total, page, page_size)


# Request/Response Schemas
class ReceiptCreateRequest(CamelSchema):
    """Request to create a receipt."""

    loan_account_id: UUID
    receipt_amount: Decimal = Field(..., gt=0)
    receipt_date: date
    value_date: date | None = None
    receipt_type: str = Field(default="REGULAR")
    receipt_mode: str
    instrument_number: str | None = None
    instrument_date: date | None = None
    instrument_bank: str | None = None
    mandate_id: UUID | None = None
    remarks: str | None = None


class ReceiptResponse(CamelSchema):
    """Receipt response."""

    id: UUID
    receipt_number: str
    loan_account_id: UUID
    receipt_amount: Decimal
    receipt_date: date
    value_date: date
    receipt_type: str
    receipt_mode: str
    status: str
    allocated_amount: Decimal
    unallocated_amount: Decimal
    principal_allocated: Decimal
    interest_allocated: Decimal
    penal_interest_allocated: Decimal
    charges_allocated: Decimal


class SpecificAllocation(CamelSchema):
    """Specific allocation row for manual allocation."""

    installment_id: UUID | None = None
    schedule_id: UUID | None = None
    component: str
    amount: Decimal = Field(..., gt=0)


class AllocationRequest(CamelSchema):
    """Request to allocate a receipt."""

    receipt_id: UUID
    allocation_method: str = Field(default="fifo", description="fifo, proportional, or specific")
    specific_allocations: list[SpecificAllocation] | None = None


class AllocationItemResponse(CamelSchema):
    """Allocation response."""

    id: UUID
    receipt_id: UUID
    installment_id: UUID | None
    component: str
    amount: Decimal
    sequence: int


class AllocationResponse(CamelSchema):
    """Receipt allocation action response."""

    receipt_id: UUID
    allocation_count: int
    allocations: list[AllocationItemResponse]


class ReceiptReversalRequest(CamelSchema):
    """Request to reverse a receipt."""

    receipt_id: UUID
    reversal_reason: str
    reversal_date: date | None = None


class ReceiptReversalResponse(CamelSchema):
    """Receipt reversal action response."""

    receipt_id: UUID
    receipt_number: str
    status: str
    message: str


class BulkReceiptItem(CamelSchema):
    """Single receipt in bulk upload."""

    loan_account_number: str
    receipt_amount: Decimal
    receipt_date: date
    receipt_mode: str
    instrument_number: str | None = None
    remarks: str | None = None


class BulkReceiptRequest(CamelSchema):
    """Bulk receipt upload request."""

    receipts: list[BulkReceiptItem]
    auto_allocate: bool = Field(default=True)


class BulkReceiptResponse(CamelSchema):
    """Bulk receipt response."""

    total_count: int
    success_count: int
    failed_count: int
    total_amount: Decimal
    failures: list[dict]


# Endpoints
class LoanReceiptByLoanItem(CamelSchema):
    """Receipt row returned for one loan account."""

    id: UUID
    receipt_number: str
    receipt_date: date
    receipt_amount: Decimal
    receipt_type: str
    receipt_mode: str
    status: str
    allocated_amount: Decimal
    unallocated_amount: Decimal


class LoanReceiptsByLoanResponse(CamelSchema):
    """Receipts response for one loan account."""

    loan_account_id: UUID
    count: int
    receipts: list[LoanReceiptByLoanItem]


class ReceiptSummaryResponse(CamelSchema):
    """Receipt summary response."""

    receipt_count: int
    receipt_amount: Decimal
    allocated_amount: Decimal
    unallocated_amount: Decimal


class ReceiptBankStatementMatchResponse(CamelSchema):
    """Bank statement match already recorded against a receipt."""

    id: UUID
    statement_id: UUID
    bank_account_id: UUID
    matched_amount: Decimal
    match_confidence: Decimal
    match_type: str
    match_basis: dict
    matched_at: datetime | None
    matched_by_id: UUID | None


class ReceiptDetailResponse(ReceiptResponse):
    """Detailed receipt response."""

    instrument_number: str | None = None
    instrument_date: date | None = None
    instrument_bank: str | None = None
    bounced: bool
    bounce_reason: str | None = None
    remarks: str | None = None
    allocations: list[AllocationItemResponse]
    bank_statement_matches: list[ReceiptBankStatementMatchResponse]


class ReceiptBounceResponse(CamelSchema):
    """Receipt bounce action response."""

    receipt_id: UUID
    receipt_number: str
    status: str
    bounced: bool
    bounce_reason: str | None
    bounce_charges: Decimal
    message: str


@router.post("/", response_model=ReceiptResponse, response_model_by_alias=True)
async def create_receipt(
    request: ReceiptCreateRequest,
    current_user: User = Depends(RequirePermissions("LMS_RECEIPT_CREATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Create a new receipt."""
    service = ReceiptService(db)

    try:
        receipt = await service.create_receipt(
            loan_account_id=request.loan_account_id,
            receipt_amount=request.receipt_amount,
            receipt_date=request.receipt_date,
            value_date=request.value_date,
            receipt_type=request.receipt_type,
            receipt_mode=request.receipt_mode,
            instrument_number=request.instrument_number,
            instrument_date=request.instrument_date,
            instrument_bank=request.instrument_bank,
            mandate_id=request.mandate_id,
            remarks=request.remarks,
            user_id=current_user.id,
        )
    except ValueError as exc:
        raise BadRequestException(detail=str(exc), error_code="BAD_REQUEST") from exc

    return ReceiptResponse(
        id=receipt.id,
        receipt_number=receipt.receipt_number,
        loan_account_id=receipt.loan_account_id,
        receipt_amount=receipt.receipt_amount,
        receipt_date=receipt.receipt_date,
        value_date=receipt.value_date,
        receipt_type=receipt.receipt_type.name,
        receipt_mode=receipt.receipt_mode.name,
        status=receipt.status.name,
        allocated_amount=receipt.allocated_amount,
        unallocated_amount=receipt.unallocated_amount,
        principal_allocated=receipt.principal_allocated,
        interest_allocated=receipt.interest_allocated,
        penal_interest_allocated=receipt.penal_interest_allocated,
        charges_allocated=receipt.charges_allocated,
    )


@router.post(
    "/allocate",
    response_model=AllocationResponse,
    response_model_by_alias=True,
)
async def allocate_receipt(
    request: AllocationRequest,
    current_user: User = Depends(RequirePermissions("LMS_RECEIPT_ALLOCATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Allocate a receipt to installments."""
    service = ReceiptService(db)

    try:
        allocations = await service.allocate_receipt(
            receipt_id=request.receipt_id,
            allocation_method=request.allocation_method,
            specific_allocations=(
                [item.model_dump() for item in request.specific_allocations]
                if request.specific_allocations
                else None
            ),
            user_id=current_user.id,
        )
    except ValueError as exc:
        raise BadRequestException(detail=str(exc), error_code="BAD_REQUEST") from exc

    return {
        "receipt_id": request.receipt_id,
        "allocation_count": len(allocations),
        "allocations": [
            {
                "id": a.id,
                "receipt_id": a.receipt_id,
                "installment_id": a.installment_id,
                "component": a.allocation_component.name,
                "amount": a.allocated_amount,
                "sequence": a.allocation_sequence,
            }
            for a in allocations
        ],
    }


@router.post(
    "/reverse",
    response_model=ReceiptReversalResponse,
    response_model_by_alias=True,
)
async def reverse_receipt(
    request: ReceiptReversalRequest,
    current_user: User = Depends(RequirePermissions("LMS_RECEIPT_UPDATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Reverse a receipt."""
    service = ReceiptService(db)

    try:
        receipt = await service.reverse_receipt(
            receipt_id=request.receipt_id,
            reversal_reason=request.reversal_reason,
            reversal_date=request.reversal_date,
            user_id=current_user.id,
        )
    except ValueError as exc:
        raise BadRequestException(detail=str(exc), error_code="BAD_REQUEST") from exc

    return {
        "receipt_id": receipt.id,
        "receipt_number": receipt.receipt_number,
        "status": receipt.status.name,
        "message": "Receipt reversed successfully",
    }


@router.post("/bulk", response_model=BulkReceiptResponse, response_model_by_alias=True)
async def process_bulk_receipts(
    request: BulkReceiptRequest,
    current_user: User = Depends(RequirePermissions("LMS_RECEIPT_CREATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Process bulk receipt upload."""
    service = ReceiptService(db)

    # Convert to dict format expected by service
    receipts_data = [r.dict() for r in request.receipts]

    result = await service.process_bulk_receipts(
        receipts_data=receipts_data,
        organization_id=current_user.organization_id,
        auto_allocate=request.auto_allocate,
        user_id=current_user.id,
    )

    return BulkReceiptResponse(
        total_count=result["total_count"],
        success_count=result["success_count"],
        failed_count=result["failed_count"],
        total_amount=result["total_amount"],
        failures=result.get("failures", []),
    )


@router.get(
    "/loan/{loan_account_id}",
    response_model=LoanReceiptsByLoanResponse,
    response_model_by_alias=True,
)
async def get_receipts_by_loan(
    loan_account_id: UUID,
    from_date: date | None = None,
    to_date: date | None = None,
    status: str | None = None,
    current_user: User = Depends(RequirePermissions("LMS_ACCOUNT_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Get receipts for a loan account."""
    service = ReceiptService(db)

    receipts = await service.get_receipts(
        loan_account_id=loan_account_id,
        from_date=from_date,
        to_date=to_date,
        status=status,
    )

    return {
        "loan_account_id": loan_account_id,
        "count": len(receipts),
        "receipts": [
            {
                "id": r.id,
                "receipt_number": r.receipt_number,
                "receipt_date": r.receipt_date,
                "receipt_amount": r.receipt_amount,
                "receipt_type": r.receipt_type.name,
                "receipt_mode": r.receipt_mode.name,
                "status": r.status.name,
                "allocated_amount": r.allocated_amount,
                "unallocated_amount": r.unallocated_amount,
            }
            for r in receipts
        ],
    }


@router.get(
    "/summary",
    response_model=ReceiptSummaryResponse,
    response_model_by_alias=True,
)
async def get_receipt_summary(
    from_date: date | None = None,
    to_date: date | None = None,
    current_user: User = Depends(RequirePermissions("LMS_ACCOUNT_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Get receipt summary for organization."""
    service = ReceiptService(db)

    summary = await service.get_receipt_summary(
        organization_id=current_user.organization_id,
        from_date=from_date,
        to_date=to_date,
    )

    return summary


@router.get(
    "/{receipt_id}",
    response_model=ReceiptDetailResponse,
    response_model_by_alias=True,
)
async def get_receipt(
    receipt_id: UUID,
    current_user: User = Depends(RequirePermissions("LMS_ACCOUNT_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Get receipt details with allocations."""
    service = ReceiptService(db)

    receipt = await service.get_receipt(receipt_id)

    if not receipt:
        raise NotFoundException(detail="Receipt not found", error_code="RECEIPT_NOT_FOUND")

    allocations = await service.get_allocations(receipt_id)

    return {
        "id": receipt.id,
        "receipt_number": receipt.receipt_number,
        "loan_account_id": receipt.loan_account_id,
        "receipt_date": receipt.receipt_date,
        "value_date": receipt.value_date,
        "receipt_amount": receipt.receipt_amount,
        "receipt_type": receipt.receipt_type.name,
        "receipt_mode": receipt.receipt_mode.name,
        "instrument_number": receipt.instrument_number,
        "instrument_date": receipt.instrument_date,
        "instrument_bank": receipt.instrument_bank,
        "status": receipt.status.name,
        "allocated_amount": receipt.allocated_amount,
        "unallocated_amount": receipt.unallocated_amount,
        "principal_allocated": receipt.principal_allocated,
        "interest_allocated": receipt.interest_allocated,
        "penal_interest_allocated": receipt.penal_interest_allocated,
        "charges_allocated": receipt.charges_allocated,
        "bounced": receipt.bounced,
        "bounce_reason": receipt.bounce_reason,
        "remarks": receipt.remarks,
        "allocations": [
            {
                "id": a.id,
                "receipt_id": a.receipt_id,
                "installment_id": a.installment_id,
                "component": a.allocation_component.name,
                "amount": a.allocated_amount,
                "sequence": a.allocation_sequence,
            }
            for a in allocations
        ],
        "bank_statement_matches": [
            {
                "id": match.id,
                "statement_id": match.statement_id,
                "bank_account_id": match.bank_account_id,
                "matched_amount": match.matched_amount,
                "match_confidence": match.match_confidence,
                "match_type": match.match_type,
                "match_basis": match.match_basis or {},
                "matched_at": match.matched_at,
                "matched_by_id": match.matched_by_id,
            }
            for match in receipt.bank_statement_matches
        ],
    }


@router.post(
    "/{receipt_id}/bounce",
    response_model=ReceiptBounceResponse,
    response_model_by_alias=True,
)
async def mark_receipt_bounced(
    receipt_id: UUID,
    bounce_reason: str = Query(..., description="Reason for bounce"),
    bounce_date: date | None = None,
    bounce_charges: Decimal = Query(
        default=Decimal("0"),
        description="Bounce charges",
    ),
    current_user: User = Depends(RequirePermissions("LMS_RECEIPT_UPDATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Mark a receipt as bounced."""
    service = ReceiptService(db)

    try:
        receipt = await service.mark_bounced(
            receipt_id=receipt_id,
            bounce_reason=bounce_reason,
            bounce_date=bounce_date,
            bounce_charges=bounce_charges,
            user_id=current_user.id,
        )
    except ValueError as exc:
        raise BadRequestException(detail=str(exc), error_code="BAD_REQUEST") from exc

    return {
        "receipt_id": receipt.id,
        "receipt_number": receipt.receipt_number,
        "status": receipt.status.name,
        "bounced": receipt.bounced,
        "bounce_reason": receipt.bounce_reason,
        "bounce_charges": receipt.bounce_charges,
        "message": "Receipt marked as bounced",
    }
