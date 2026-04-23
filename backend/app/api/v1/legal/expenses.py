"""Legal Expense API endpoints."""

from datetime import date
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user, RequirePermissions
from app.models.auth.user import User
from app.models.legal.enums import (
    ExpenseCategoryType,
    ExpenseStatus,
    RecoveryType,
)
from app.services.legal.expense_service import LegalExpenseService

router = APIRouter(prefix="/expenses", tags=["Legal Expenses"])


# =============================================================================
# Request/Response Schemas
# =============================================================================


class ExpenseCategoryCreate(BaseModel):
    """Create expense category request."""

    category_code: str = Field(..., max_length=50)
    category_name: str = Field(..., max_length=200)
    parent_category_id: Optional[UUID] = None
    description: Optional[str] = None
    gl_account_code: Optional[str] = None
    is_recoverable: bool = True
    requires_approval: bool = True
    approval_threshold: Optional[Decimal] = None
    tds_applicable: bool = False
    tds_section: Optional[str] = None
    default_tds_rate: Optional[Decimal] = None


class ExpenseCategoryResponse(BaseModel):
    """Expense category response."""

    id: UUID
    category_code: str
    category_name: str
    parent_category_id: Optional[UUID] = None
    is_recoverable: bool
    requires_approval: bool
    approval_threshold: Optional[float] = None
    tds_applicable: bool
    default_tds_rate: Optional[float] = None
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
    gst_rate: Optional[Decimal] = None
    gst_amount: Optional[Decimal] = None
    tds_rate: Optional[Decimal] = None
    tds_amount: Optional[Decimal] = None
    net_payable: Optional[Decimal] = None
    vendor_name: Optional[str] = None
    vendor_pan: Optional[str] = None
    vendor_gstin: Optional[str] = None
    invoice_number: Optional[str] = None
    invoice_date: Optional[date] = None
    payment_due_date: Optional[date] = None
    remarks: Optional[str] = None
    document_ids: Optional[List[UUID]] = None


class ExpenseResponse(BaseModel):
    """Legal expense response."""

    id: UUID
    expense_number: str
    legal_case_id: UUID
    expense_category: str
    expense_date: date
    description: str
    amount: float
    gst_amount: Optional[float] = None
    tds_amount: Optional[float] = None
    net_payable: float
    expense_status: str
    is_paid: bool
    paid_date: Optional[date] = None
    is_recovered: bool
    recovered_amount: Optional[float] = None
    vendor_name: Optional[str] = None
    invoice_number: Optional[str] = None

    class Config:
        from_attributes = True


class ExpenseApprovalRequest(BaseModel):
    """Approve/reject expense request."""

    action: str = Field(..., description="APPROVE or REJECT")
    remarks: Optional[str] = None


class ExpensePaymentRequest(BaseModel):
    """Record expense payment request."""

    payment_date: date
    payment_amount: Decimal
    payment_mode: str
    payment_reference: str
    bank_account_id: Optional[UUID] = None
    remarks: Optional[str] = None


class ExpenseRecoveryRequest(BaseModel):
    """Record expense recovery request."""

    recovery_source: RecoveryType
    recovery_date: date
    recovered_amount: Decimal
    recovery_reference: Optional[str] = None
    remarks: Optional[str] = None


class RecoveryResponse(BaseModel):
    """Expense recovery response."""

    id: UUID
    expense_id: UUID
    recovery_source: str
    recovery_date: date
    recovered_amount: float
    recovery_reference: Optional[str] = None

    class Config:
        from_attributes = True


class CourtFeeCalculateRequest(BaseModel):
    """Calculate court fee request."""

    forum_type: str
    claim_amount: Decimal
    state_code: Optional[str] = None


class CourtFeeResponse(BaseModel):
    """Court fee calculation response."""

    forum_type: str
    claim_amount: float
    court_fee: float
    fee_structure: str
    breakdown: Optional[dict] = None


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

    items: List
    total: int
    page: int
    page_size: int
    total_pages: int


# =============================================================================
# Expense Category Endpoints
# =============================================================================


@router.post(
    "/categories",
    response_model=ExpenseCategoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Expense Category",
)
async def create_category(
    organization_id: UUID,
    request: ExpenseCategoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("legal.expense_category.create")),
):
    """Create a new expense category."""
    service = LegalExpenseService(db)
    category = await service.create_category(
        organization_id=organization_id,
        created_by=current_user.id,
        **request.model_dump(),
    )
    await db.commit()
    return category


@router.get(
    "/categories",
    response_model=List[ExpenseCategoryResponse],
    summary="List Expense Categories",
)
async def list_categories(
    organization_id: UUID,
    is_active: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("legal.expense_category.read")),
):
    """List expense categories."""
    service = LegalExpenseService(db)
    categories = await service.list_categories(
        organization_id=organization_id,
        is_active=is_active,
    )
    return [ExpenseCategoryResponse.model_validate(c) for c in categories]


# =============================================================================
# Expense Management Endpoints
# =============================================================================


@router.post(
    "",
    response_model=ExpenseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record Legal Expense",
)
async def create_expense(
    organization_id: UUID,
    request: ExpenseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("legal.expense.create")),
):
    """Record a new legal expense."""
    service = LegalExpenseService(db)
    expense = await service.create_expense(
        organization_id=organization_id,
        created_by=current_user.id,
        **request.model_dump(),
    )
    await db.commit()
    return expense


@router.get(
    "",
    response_model=PaginatedResponse,
    summary="List Legal Expenses",
)
async def list_expenses(
    organization_id: UUID,
    legal_case_id: Optional[UUID] = None,
    expense_category: Optional[ExpenseCategoryType] = None,
    expense_status: Optional[ExpenseStatus] = None,
    is_paid: Optional[bool] = None,
    is_recovered: Optional[bool] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("legal.expense.read")),
):
    """List legal expenses with filtering."""
    service = LegalExpenseService(db)
    items, total = await service.list_expenses(
        organization_id=organization_id,
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
    response_model=ExpenseResponse,
    summary="Get Expense Details",
)
async def get_expense(
    expense_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("legal.expense.read")),
):
    """Get expense details."""
    service = LegalExpenseService(db)
    expense = await service.get_expense(expense_id)
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found",
        )
    return expense


@router.put(
    "/{expense_id}",
    response_model=ExpenseResponse,
    summary="Update Expense",
)
async def update_expense(
    expense_id: UUID,
    request: ExpenseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("legal.expense.update")),
):
    """Update expense details (only if not approved)."""
    service = LegalExpenseService(db)
    expense = await service.update_expense(
        expense_id=expense_id,
        updated_by=current_user.id,
        **request.model_dump(),
    )
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found",
        )
    await db.commit()
    return expense


# =============================================================================
# Approval Workflow
# =============================================================================


@router.post(
    "/{expense_id}/approve",
    response_model=ExpenseResponse,
    summary="Approve/Reject Expense",
)
async def approve_expense(
    expense_id: UUID,
    request: ExpenseApprovalRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("legal.expense.approve")),
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found",
        )
    await db.commit()
    return expense


@router.get(
    "/pending-approval",
    response_model=PaginatedResponse,
    summary="Get Pending Approvals",
)
async def get_pending_approvals(
    organization_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("legal.expense.approve")),
):
    """Get expenses pending approval."""
    service = LegalExpenseService(db)
    items, total = await service.get_pending_approvals(
        organization_id=organization_id,
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
    response_model=ExpenseResponse,
    summary="Record Expense Payment",
)
async def record_payment(
    expense_id: UUID,
    request: ExpensePaymentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("legal.expense.update")),
):
    """Record payment for an approved expense."""
    service = LegalExpenseService(db)
    expense = await service.record_payment(
        expense_id=expense_id,
        recorded_by=current_user.id,
        **request.model_dump(),
    )
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found",
        )
    await db.commit()
    return expense


@router.post(
    "/{expense_id}/recovery",
    response_model=RecoveryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record Expense Recovery",
)
async def record_recovery(
    expense_id: UUID,
    request: ExpenseRecoveryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("legal.expense.update")),
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
    response_model=List[RecoveryResponse],
    summary="Get Expense Recoveries",
)
async def get_expense_recoveries(
    expense_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("legal.expense.read")),
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
    response_model=CourtFeeResponse,
    summary="Calculate Court Fee",
)
async def calculate_court_fee(
    request: CourtFeeCalculateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("legal.expense.read")),
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
    response_model=CaseExpenseSummary,
    summary="Get Case Expense Summary",
)
async def get_case_expense_summary(
    legal_case_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("legal.expense.read")),
):
    """Get expense summary for a legal case."""
    service = LegalExpenseService(db)
    summary = await service.get_case_expense_summary(legal_case_id)
    return CaseExpenseSummary(**summary)


@router.get(
    "/pending-payment",
    response_model=PaginatedResponse,
    summary="Get Expenses Pending Payment",
)
async def get_pending_payment(
    organization_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("legal.expense.read")),
):
    """Get approved expenses pending payment."""
    service = LegalExpenseService(db)
    items, total = await service.get_pending_payment(
        organization_id=organization_id,
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
    response_model=PaginatedResponse,
    summary="Get Expenses Pending Recovery",
)
async def get_recovery_pending(
    organization_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequirePermissions("legal.expense.read")),
):
    """Get paid expenses pending recovery from borrower."""
    service = LegalExpenseService(db)
    items, total = await service.get_recovery_pending(
        organization_id=organization_id,
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
