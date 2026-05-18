"""Legal Expense API endpoints."""

from datetime import date
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RequirePermissions, get_db, get_db_with_tenant
from app.models.auth.user import User
from app.models.legal.enums import (
    ExpenseCategoryType,
    ExpenseStatus,
    RecoveryType,
)
from app.services.legal.expense_service import LegalExpenseService
from app.core.exceptions import NotFoundException

router = APIRouter(prefix="/expenses", tags=["Legal Expenses"])


# =============================================================================
# Request/Response Schemas
# =============================================================================


class ExpenseCategoryCreate(BaseModel):
    """Create expense category request."""

    category_code: str = Field(..., max_length=50)
    category_name: str = Field(..., max_length=200)
    parent_category_id: UUID | None = None
    description: str | None = None
    gl_account_code: str | None = None
    is_recoverable: bool = True
    requires_approval: bool = True
    approval_threshold: Decimal | None = None
    tds_applicable: bool = False
    tds_section: str | None = None
    default_tds_rate: Decimal | None = None


class ExpenseCategoryResponse(BaseModel):
    """Expense category response."""

    id: UUID
    category_code: str
    category_name: str
    parent_category_id: UUID | None = None
    is_recoverable: bool
    requires_approval: bool
    approval_threshold: float | None = None
    tds_applicable: bool
    default_tds_rate: float | None = None
    is_active: bool

    class Config:
        from_attributes = True


class ExpenseCreate(BaseModel):
    """Create expense request."""

    legal_case_id: UUID
    expense_category: ExpenseCategoryType
    expense_date: date
    description: str
    amount: Decimal
    gst_rate: Decimal | None = None
    gst_amount: Decimal | None = None
    tds_rate: Decimal | None = None
    tds_amount: Decimal | None = None
    net_payable: Decimal | None = None
    vendor_name: str | None = None
    vendor_pan: str | None = None
    vendor_gstin: str | None = None
    invoice_number: str | None = None
    invoice_date: date | None = None
    payment_due_date: date | None = None
    remarks: str | None = None
    document_ids: list[UUID] | None = None


class ExpenseResponse(BaseModel):
    """Legal expense response."""

    id: UUID
    expense_number: str
    legal_case_id: UUID
    expense_category: str
    expense_date: date
    description: str
    amount: float
    gst_amount: float | None = None
    tds_amount: float | None = None
    net_payable: float
    expense_status: str
    is_paid: bool
    paid_date: date | None = None
    is_recovered: bool
    recovered_amount: float | None = None
    vendor_name: str | None = None
    invoice_number: str | None = None

    class Config:
        from_attributes = True


class ExpenseApprovalRequest(BaseModel):
    """Approve/reject expense request."""

    action: str = Field(..., description="APPROVE or REJECT")
    remarks: str | None = None


class ExpensePaymentRequest(BaseModel):
    """Record expense payment request."""

    payment_date: date
    payment_amount: Decimal
    payment_mode: str
    payment_reference: str
    bank_account_id: UUID | None = None
    remarks: str | None = None


class ExpenseRecoveryRequest(BaseModel):
    """Record expense recovery request."""

    recovery_source: RecoveryType
    recovery_date: date
    recovered_amount: Decimal
    recovery_reference: str | None = None
    remarks: str | None = None


class RecoveryResponse(BaseModel):
    """Expense recovery response."""

    id: UUID
    expense_id: UUID
    recovery_source: str
    recovery_date: date
    recovered_amount: float
    recovery_reference: str | None = None

    class Config:
        from_attributes = True


class CourtFeeCalculateRequest(BaseModel):
    """Calculate court fee request."""

    forum_type: str
    claim_amount: Decimal
    state_code: str | None = None


class CourtFeeResponse(BaseModel):
    """Court fee calculation response."""

    forum_type: str
    claim_amount: float
    court_fee: float
    fee_structure: str
    breakdown: dict | None = None


class CaseExpenseSummary(BaseModel):
    """Case expense summary."""

    legal_case_id: UUID
    total_expenses: float
    paid_expenses: float
    pending_expenses: float
    recovered_expenses: float
    recovery_pending: float
    by_category: dict


class PaginatedResponse(BaseModel):
    """Paginated list response."""

    items: list
    total: int
    page: int
    page_size: int
    total_pages: int


# =============================================================================
# Expense Category Endpoints
# =============================================================================


@router.post(
    "/categories",
    response_model=ExpenseCategoryResponse, response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
    summary="Create Expense Category",
)
async def create_category(
    request: ExpenseCategoryCreate,
    organization_id: UUID | None = Query(None),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("LMS_COLLECTION_UPDATE")),
):
    """Create a new expense category."""
    service = LegalExpenseService(db)
    category = await service.create_category(
        organization_id=(organization_id or current_user.organization_id),
        created_by=current_user.id,
        **request.model_dump(),
    )
    await db.commit()
    return category


@router.get(
    "/categories",
    response_model=list[ExpenseCategoryResponse], response_model_by_alias=True,
    summary="List Expense Categories",
)
async def list_categories(
    organization_id: UUID | None = Query(None),
    is_active: bool = True,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("LMS_COLLECTION_VIEW")),
):
    """List expense categories."""
    service = LegalExpenseService(db)
    categories = await service.list_categories(
        organization_id=(organization_id or current_user.organization_id),
        is_active=is_active,
    )
    return [ExpenseCategoryResponse.model_validate(c) for c in categories]


# =============================================================================
# Expense Management Endpoints
# =============================================================================


@router.post(
    "",
    response_model=ExpenseResponse, response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
    summary="Record Legal Expense",
)
async def create_expense(
    request: ExpenseCreate,
    organization_id: UUID | None = Query(None),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("LMS_COLLECTION_UPDATE")),
):
    """Record a new legal expense."""
    service = LegalExpenseService(db)
    expense = await service.create_expense(
        organization_id=(organization_id or current_user.organization_id),
        created_by=current_user.id,
        **request.model_dump(),
    )
    await db.commit()
    return expense


@router.get(
    "",
    response_model=PaginatedResponse, response_model_by_alias=True,
    summary="List Legal Expenses",
)
async def list_expenses(
    organization_id: UUID | None = Query(None),
    legal_case_id: UUID | None = None,
    expense_category: ExpenseCategoryType | None = None,
    expense_status: ExpenseStatus | None = None,
    is_paid: bool | None = None,
    is_recovered: bool | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("LMS_COLLECTION_VIEW")),
):
    """List legal expenses with filtering."""
    service = LegalExpenseService(db)
    items, total = await service.list_expenses(
        organization_id=(organization_id or current_user.organization_id),
        legal_case_id=legal_case_id,
        expense_category=expense_category,
        expense_status=expense_status,
        is_paid=is_paid,
        is_recovered=is_recovered,
        from_date=from_date,
        to_date=to_date,
        page=page,
        page_size=page_size,
    )
    return PaginatedResponse(
        items=[ExpenseResponse.model_validate(e) for e in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get(
    "/{expense_id}",
    response_model=ExpenseResponse, response_model_by_alias=True,
    summary="Get Expense Details",
)
async def get_expense(
    expense_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("LMS_COLLECTION_VIEW")),
):
    """Get expense details."""
    service = LegalExpenseService(db)
    expense = await service.get_expense(expense_id)
    if not expense:
        raise NotFoundException(detail="Expense not found", error_code="EXPENSE_NOT_FOUND")
    return expense


@router.put(
    "/{expense_id}",
    response_model=ExpenseResponse, response_model_by_alias=True,
    summary="Update Expense",
)
async def update_expense(
    expense_id: UUID,
    request: ExpenseCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("LMS_COLLECTION_UPDATE")),
):
    """Update expense details (only if not approved)."""
    service = LegalExpenseService(db)
    expense = await service.update_expense(
        expense_id=expense_id,
        updated_by=current_user.id,
        **request.model_dump(),
    )
    if not expense:
        raise NotFoundException(detail="Expense not found", error_code="EXPENSE_NOT_FOUND")
    await db.commit()
    return expense


# =============================================================================
# Approval Workflow
# =============================================================================


@router.post(
    "/{expense_id}/approve",
    response_model=ExpenseResponse, response_model_by_alias=True,
    summary="Approve/Reject Expense",
)
async def approve_expense(
    expense_id: UUID,
    request: ExpenseApprovalRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("LMS_COLLECTION_UPDATE")),
):
    """Approve or reject an expense."""
    service = LegalExpenseService(db)
    expense = await service.process_approval(
        expense_id=expense_id,
        action=request.action,
        approved_by=current_user.id,
        remarks=request.remarks,
    )
    if not expense:
        raise NotFoundException(detail="Expense not found", error_code="EXPENSE_NOT_FOUND")
    await db.commit()
    return expense


@router.get(
    "/pending-approval",
    response_model=PaginatedResponse, response_model_by_alias=True,
    summary="Get Pending Approvals",
)
async def get_pending_approvals(
    organization_id: UUID | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("LMS_COLLECTION_UPDATE")),
):
    """Get expenses pending approval."""
    service = LegalExpenseService(db)
    items, total = await service.get_pending_approvals(
        organization_id=(organization_id or current_user.organization_id),
        page=page,
        page_size=page_size,
    )
    return PaginatedResponse(
        items=[ExpenseResponse.model_validate(e) for e in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


# =============================================================================
# Payment & Recovery
# =============================================================================


@router.post(
    "/{expense_id}/payment",
    response_model=ExpenseResponse, response_model_by_alias=True,
    summary="Record Expense Payment",
)
async def record_payment(
    expense_id: UUID,
    request: ExpensePaymentRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("LMS_COLLECTION_UPDATE")),
):
    """Record payment for an approved expense."""
    service = LegalExpenseService(db)
    expense = await service.record_payment(
        expense_id=expense_id,
        recorded_by=current_user.id,
        **request.model_dump(),
    )
    if not expense:
        raise NotFoundException(detail="Expense not found", error_code="EXPENSE_NOT_FOUND")
    await db.commit()
    return expense


@router.post(
    "/{expense_id}/recovery",
    response_model=RecoveryResponse, response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
    summary="Record Expense Recovery",
)
async def record_recovery(
    expense_id: UUID,
    request: ExpenseRecoveryRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("LMS_COLLECTION_UPDATE")),
):
    """Record recovery of expense from borrower or sale proceeds."""
    service = LegalExpenseService(db)
    recovery = await service.record_recovery(
        expense_id=expense_id,
        recorded_by=current_user.id,
        **request.model_dump(),
    )
    await db.commit()
    return recovery


@router.get(
    "/{expense_id}/recoveries",
    response_model=list[RecoveryResponse], response_model_by_alias=True,
    summary="Get Expense Recoveries",
)
async def get_expense_recoveries(
    expense_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("LMS_COLLECTION_VIEW")),
):
    """Get all recovery records for an expense."""
    service = LegalExpenseService(db)
    recoveries = await service.get_expense_recoveries(expense_id)
    return [RecoveryResponse.model_validate(r) for r in recoveries]


# =============================================================================
# Court Fee Calculator
# =============================================================================


@router.post(
    "/court-fees/calculate",
    response_model=CourtFeeResponse, response_model_by_alias=True,
    summary="Calculate Court Fee",
)
async def calculate_court_fee(
    request: CourtFeeCalculateRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("LMS_COLLECTION_VIEW")),
):
    """
    Calculate court fee based on forum type and claim amount.

    Supports: DRT, DRAT, NCLT, Civil Court, High Court
    """
    service = LegalExpenseService(db)
    result = await service.calculate_court_fee(
        forum_type=request.forum_type,
        claim_amount=request.claim_amount,
        state_code=request.state_code,
    )
    return CourtFeeResponse(**result)


# =============================================================================
# Reports & Summary
# =============================================================================


@router.get(
    "/case/{legal_case_id}/summary",
    response_model=CaseExpenseSummary, response_model_by_alias=True,
    summary="Get Case Expense Summary",
)
async def get_case_expense_summary(
    legal_case_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("LMS_COLLECTION_VIEW")),
):
    """Get expense summary for a legal case."""
    service = LegalExpenseService(db)
    summary = await service.get_case_expense_summary(legal_case_id)
    return CaseExpenseSummary(**summary)


@router.get(
    "/pending-payment",
    response_model=PaginatedResponse, response_model_by_alias=True,
    summary="Get Expenses Pending Payment",
)
async def get_pending_payment(
    organization_id: UUID | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("LMS_COLLECTION_VIEW")),
):
    """Get approved expenses pending payment."""
    service = LegalExpenseService(db)
    items, total = await service.get_pending_payment(
        organization_id=(organization_id or current_user.organization_id),
        page=page,
        page_size=page_size,
    )
    return PaginatedResponse(
        items=[ExpenseResponse.model_validate(e) for e in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get(
    "/recovery-pending",
    response_model=PaginatedResponse, response_model_by_alias=True,
    summary="Get Expenses Pending Recovery",
)
async def get_recovery_pending(
    organization_id: UUID | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions("LMS_COLLECTION_VIEW")),
):
    """Get paid expenses pending recovery from borrower."""
    service = LegalExpenseService(db)
    items, total = await service.get_recovery_pending(
        organization_id=(organization_id or current_user.organization_id),
        page=page,
        page_size=page_size,
    )
    return PaginatedResponse(
        items=[ExpenseResponse.model_validate(e) for e in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )
