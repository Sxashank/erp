"""ESS Reimbursement Claims API endpoints."""

from datetime import date
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.services.ess.reimbursement_service import ESSReimbursementService
from app.models.ess.enums import ClaimType, ClaimStatus


router = APIRouter(prefix="/reimbursements", tags=["ESS Reimbursements"])


# ==================== Schemas ====================

class ReimbursementCategoryResponse(BaseModel):
    """Reimbursement category response."""
    id: str
    code: str
    name: str
    description: Optional[str]
    claim_type: str
    max_amount_per_claim: Optional[float]
    max_claims_per_month: Optional[int]
    max_amount_per_month: Optional[float]
    requires_bills: bool


class ClaimLineItemCreate(BaseModel):
    """Create claim line item."""
    expense_date: date
    description: str
    amount: Decimal
    bill_number: Optional[str] = None
    bill_date: Optional[date] = None
    vendor_name: Optional[str] = None
    vendor_gstin: Optional[str] = None
    gst_amount: Optional[Decimal] = None
    gst_rate: Optional[Decimal] = None
    attachment_url: Optional[str] = None
    attachment_name: Optional[str] = None


class ClaimCreate(BaseModel):
    """Create reimbursement claim."""
    claim_type: ClaimType
    category_id: Optional[UUID] = None
    expense_from: date
    expense_to: date
    description: str
    claimed_amount: Decimal = Field(..., gt=0)
    purpose: Optional[str] = None
    travel_from: Optional[str] = None
    travel_to: Optional[str] = None
    travel_mode: Optional[str] = None
    kilometers: Optional[Decimal] = None
    attachments: Optional[dict] = None
    save_as_draft: bool = False


class ClaimUpdate(BaseModel):
    """Update claim details."""
    description: Optional[str] = None
    purpose: Optional[str] = None
    expense_from: Optional[date] = None
    expense_to: Optional[date] = None
    travel_from: Optional[str] = None
    travel_to: Optional[str] = None
    travel_mode: Optional[str] = None
    kilometers: Optional[Decimal] = None


class ClaimLineItemResponse(BaseModel):
    """Claim line item response."""
    id: str
    line_number: int
    expense_date: date
    description: str
    amount: float
    approved_amount: Optional[float]
    bill_number: Optional[str]
    vendor_name: Optional[str]
    attachment_url: Optional[str]
    is_verified: bool


class ClaimResponse(BaseModel):
    """Claim response."""
    id: str
    claim_number: str
    claim_date: date
    claim_type: str
    category: Optional[str]
    expense_from: date
    expense_to: date
    description: str
    claimed_amount: float
    approved_amount: Optional[float]
    status: str
    bills_attached: int
    created_at: str


class ClaimDetailResponse(ClaimResponse):
    """Detailed claim response with line items."""
    purpose: Optional[str]
    travel_from: Optional[str]
    travel_to: Optional[str]
    travel_mode: Optional[str]
    kilometers: Optional[float]
    approved_by: Optional[str]
    approved_date: Optional[date]
    rejection_reason: Optional[str]
    payment_date: Optional[date]
    payment_reference: Optional[str]
    line_items: List[ClaimLineItemResponse]


class ClaimSummaryResponse(BaseModel):
    """Claim summary response."""
    financial_year: str
    total_claims: int
    total_claimed: float
    total_approved: float
    total_paid: float
    pending_claims: int
    by_status: dict


# ==================== Endpoints ====================

@router.get("/categories", response_model=List[ReimbursementCategoryResponse])
async def get_categories(
    organization_id: UUID,  # From authenticated user
    session: AsyncSession = Depends(get_session),
):
    """Get reimbursement categories."""
    service = ESSReimbursementService(session)
    categories = await service.get_categories(organization_id)

    return [
        ReimbursementCategoryResponse(
            id=str(c.id),
            code=c.code,
            name=c.name,
            description=c.description,
            claim_type=c.claim_type.value,
            max_amount_per_claim=float(c.max_amount_per_claim) if c.max_amount_per_claim else None,
            max_claims_per_month=c.max_claims_per_month,
            max_amount_per_month=float(c.max_amount_per_month) if c.max_amount_per_month else None,
            requires_bills=c.requires_bills,
        )
        for c in categories
    ]


@router.post("", response_model=ClaimResponse)
async def create_claim(
    request: ClaimCreate,
    organization_id: UUID,  # From authenticated user
    ess_user_id: UUID,  # From authenticated user
    employee_id: UUID,  # From authenticated user
    session: AsyncSession = Depends(get_session),
):
    """Create a new reimbursement claim."""
    service = ESSReimbursementService(session)

    claim = await service.create_claim(
        organization_id=organization_id,
        ess_user_id=ess_user_id,
        employee_id=employee_id,
        claim_type=request.claim_type,
        category_id=request.category_id,
        expense_from=request.expense_from,
        expense_to=request.expense_to,
        description=request.description,
        claimed_amount=request.claimed_amount,
        purpose=request.purpose,
        travel_from=request.travel_from,
        travel_to=request.travel_to,
        travel_mode=request.travel_mode,
        kilometers=request.kilometers,
        attachments=request.attachments,
        save_as_draft=request.save_as_draft,
    )

    await session.commit()

    return ClaimResponse(
        id=str(claim.id),
        claim_number=claim.claim_number,
        claim_date=claim.claim_date,
        claim_type=claim.claim_type.value,
        category=claim.category.name if claim.category else None,
        expense_from=claim.expense_from,
        expense_to=claim.expense_to,
        description=claim.description,
        claimed_amount=float(claim.claimed_amount),
        approved_amount=float(claim.approved_amount) if claim.approved_amount else None,
        status=claim.status.value,
        bills_attached=claim.bills_attached,
        created_at=claim.created_at.isoformat(),
    )


@router.get("", response_model=List[ClaimResponse])
async def get_claims(
    employee_id: UUID,  # From authenticated user
    status: Optional[ClaimStatus] = None,
    claim_type: Optional[ClaimType] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    """Get claims for the employee."""
    service = ESSReimbursementService(session)

    claims, total = await service.get_claims_by_employee(
        employee_id=employee_id,
        status=status,
        claim_type=claim_type,
        from_date=from_date,
        to_date=to_date,
        limit=limit,
        offset=offset,
    )

    return [
        ClaimResponse(
            id=str(c.id),
            claim_number=c.claim_number,
            claim_date=c.claim_date,
            claim_type=c.claim_type.value,
            category=c.category.name if c.category else None,
            expense_from=c.expense_from,
            expense_to=c.expense_to,
            description=c.description,
            claimed_amount=float(c.claimed_amount),
            approved_amount=float(c.approved_amount) if c.approved_amount else None,
            status=c.status.value,
            bills_attached=c.bills_attached,
            created_at=c.created_at.isoformat(),
        )
        for c in claims
    ]


@router.get("/summary", response_model=ClaimSummaryResponse)
async def get_claim_summary(
    employee_id: UUID,  # From authenticated user
    financial_year: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
):
    """Get claim summary for the employee."""
    service = ESSReimbursementService(session)
    summary = await service.get_claim_summary(employee_id, financial_year)
    return ClaimSummaryResponse(**summary)


@router.get("/{claim_id}", response_model=ClaimDetailResponse)
async def get_claim_detail(
    claim_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """Get claim details with line items."""
    service = ESSReimbursementService(session)
    claim = await service.get_claim_by_id(claim_id, include_items=True)

    if not claim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Claim not found",
        )

    return ClaimDetailResponse(
        id=str(claim.id),
        claim_number=claim.claim_number,
        claim_date=claim.claim_date,
        claim_type=claim.claim_type.value,
        category=claim.category.name if claim.category else None,
        expense_from=claim.expense_from,
        expense_to=claim.expense_to,
        description=claim.description,
        claimed_amount=float(claim.claimed_amount),
        approved_amount=float(claim.approved_amount) if claim.approved_amount else None,
        status=claim.status.value,
        bills_attached=claim.bills_attached,
        created_at=claim.created_at.isoformat(),
        purpose=claim.purpose,
        travel_from=claim.travel_from,
        travel_to=claim.travel_to,
        travel_mode=claim.travel_mode,
        kilometers=float(claim.kilometers) if claim.kilometers else None,
        approved_by=str(claim.approved_by) if claim.approved_by else None,
        approved_date=claim.approved_date,
        rejection_reason=claim.rejection_reason,
        payment_date=claim.payment_date,
        payment_reference=claim.payment_reference,
        line_items=[
            ClaimLineItemResponse(
                id=str(item.id),
                line_number=item.line_number,
                expense_date=item.expense_date,
                description=item.description,
                amount=float(item.amount),
                approved_amount=float(item.approved_amount) if item.approved_amount else None,
                bill_number=item.bill_number,
                vendor_name=item.vendor_name,
                attachment_url=item.attachment_url,
                is_verified=item.is_verified,
            )
            for item in claim.line_items
        ],
    )


@router.patch("/{claim_id}", response_model=ClaimResponse)
async def update_claim(
    claim_id: UUID,
    request: ClaimUpdate,
    session: AsyncSession = Depends(get_session),
):
    """Update a draft claim."""
    service = ESSReimbursementService(session)

    try:
        claim = await service.update_claim(
            claim_id=claim_id,
            **request.model_dump(exclude_unset=True)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    if not claim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Claim not found",
        )

    await session.commit()

    return ClaimResponse(
        id=str(claim.id),
        claim_number=claim.claim_number,
        claim_date=claim.claim_date,
        claim_type=claim.claim_type.value,
        category=claim.category.name if claim.category else None,
        expense_from=claim.expense_from,
        expense_to=claim.expense_to,
        description=claim.description,
        claimed_amount=float(claim.claimed_amount),
        approved_amount=float(claim.approved_amount) if claim.approved_amount else None,
        status=claim.status.value,
        bills_attached=claim.bills_attached,
        created_at=claim.created_at.isoformat(),
    )


@router.post("/{claim_id}/submit", response_model=ClaimResponse)
async def submit_claim(
    claim_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """Submit a draft claim for approval."""
    service = ESSReimbursementService(session)

    try:
        claim = await service.submit_claim(claim_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    if not claim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Claim not found",
        )

    await session.commit()

    return ClaimResponse(
        id=str(claim.id),
        claim_number=claim.claim_number,
        claim_date=claim.claim_date,
        claim_type=claim.claim_type.value,
        category=claim.category.name if claim.category else None,
        expense_from=claim.expense_from,
        expense_to=claim.expense_to,
        description=claim.description,
        claimed_amount=float(claim.claimed_amount),
        approved_amount=float(claim.approved_amount) if claim.approved_amount else None,
        status=claim.status.value,
        bills_attached=claim.bills_attached,
        created_at=claim.created_at.isoformat(),
    )


@router.post("/{claim_id}/cancel")
async def cancel_claim(
    claim_id: UUID,
    reason: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
):
    """Cancel a claim."""
    service = ESSReimbursementService(session)

    try:
        claim = await service.cancel_claim(claim_id, reason)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    if not claim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Claim not found",
        )

    await session.commit()

    return {"success": True, "message": "Claim cancelled successfully"}


# ==================== Line Items ====================

@router.post("/{claim_id}/items", response_model=ClaimLineItemResponse)
async def add_line_item(
    claim_id: UUID,
    request: ClaimLineItemCreate,
    session: AsyncSession = Depends(get_session),
):
    """Add a line item to a claim."""
    service = ESSReimbursementService(session)

    try:
        item = await service.add_line_item(
            claim_id=claim_id,
            **request.model_dump()
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    await session.commit()

    return ClaimLineItemResponse(
        id=str(item.id),
        line_number=item.line_number,
        expense_date=item.expense_date,
        description=item.description,
        amount=float(item.amount),
        approved_amount=float(item.approved_amount) if item.approved_amount else None,
        bill_number=item.bill_number,
        vendor_name=item.vendor_name,
        attachment_url=item.attachment_url,
        is_verified=item.is_verified,
    )


@router.delete("/{claim_id}/items/{item_id}")
async def remove_line_item(
    claim_id: UUID,
    item_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """Remove a line item from a claim."""
    service = ESSReimbursementService(session)

    try:
        success = await service.remove_line_item(claim_id, item_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Line item not found",
        )

    await session.commit()

    return {"success": True, "message": "Line item removed successfully"}
