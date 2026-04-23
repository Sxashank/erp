"""Loan Account API endpoints for Phase 2 - Loan Accounting."""

from datetime import date
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import RequirePermissions
from app.models.auth.user import User
from app.models.lending.enums import (
    LoanAccountStatus,
    AssetClassification,
)
from app.services.lending.loan_account_service import LoanAccountService
from app.schemas.lending.loan_account import (
    LoanAccountCreate,
    LoanAccountUpdate,
    LoanAccountResponse,
    LoanAccountListResponse,
    LoanAccountDetailResponse,
    DisbursementCreate,
    DisbursementResponse,
    DisbursementApproval,
    DisbursementProcess,
    RepaymentScheduleCreate,
    RepaymentScheduleResponse,
    RepaymentScheduleDetailResponse,
    ScheduleInstallmentResponse,
    LoanReceiptCreate,
    LoanReceiptResponse,
    LoanReceiptDetailResponse,
    ReceiptBounceRequest,
    LoanMandateCreate,
    LoanMandateUpdate,
    LoanMandateResponse,
    MandateRegisterRequest,
    MandateCancelRequest,
    AssetClassificationHistoryResponse,
    LoanProvisionResponse,
    LoanAdjustmentCreate,
    LoanAdjustmentResponse,
    LoanAccrualResponse,
    LoanAccountSummary,
    DPDBucket,
)
from app.schemas.base import PaginatedResponse

router = APIRouter()


# =============================================================================
# Loan Account CRUD Endpoints
# =============================================================================


@router.get("", response_model=PaginatedResponse[LoanAccountListResponse])
async def list_loan_accounts(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    include_inactive: bool = Query(False),
    search: Optional[str] = Query(None, description="Search in account number"),
    entity_id: Optional[UUID] = Query(None),
    product_id: Optional[UUID] = Query(None),
    status: Optional[LoanAccountStatus] = Query(None),
    asset_classification: Optional[AssetClassification] = Query(None),
    min_dpd: Optional[int] = Query(None),
    max_dpd: Optional[int] = Query(None),
    current_user: User = Depends(RequirePermissions("LMS_ACCOUNT_VIEW")),
    db: AsyncSession = Depends(get_db),
):
    """Get paginated list of loan accounts."""
    service = LoanAccountService(db)
    skip = (page - 1) * page_size
    accounts, total = await service.get_all_loan_accounts(
        organization_id=current_user.organization_id,
        skip=skip,
        limit=page_size,
        include_inactive=include_inactive,
        search=search,
        entity_id=entity_id,
        product_id=product_id,
        loan_status=status,
        asset_classification=asset_classification,
        min_dpd=min_dpd,
        max_dpd=max_dpd,
    )
    items = [LoanAccountListResponse.model_validate(a) for a in accounts]
    return PaginatedResponse.create(items, total, page, page_size)


@router.get("/summary", response_model=LoanAccountSummary)
async def get_portfolio_summary(
    current_user: User = Depends(RequirePermissions("LMS_ACCOUNT_VIEW")),
    db: AsyncSession = Depends(get_db),
):
    """Get portfolio summary for organization."""
    service = LoanAccountService(db)
    summary = await service.get_portfolio_summary(current_user.organization_id)
    return LoanAccountSummary(**summary)


@router.get("/dpd-buckets", response_model=List[DPDBucket])
async def get_dpd_buckets(
    current_user: User = Depends(RequirePermissions("LMS_ACCOUNT_VIEW")),
    db: AsyncSession = Depends(get_db),
):
    """Get DPD bucket wise analysis."""
    service = LoanAccountService(db)
    buckets = await service.get_dpd_buckets(current_user.organization_id)
    return [DPDBucket(**b) for b in buckets]


@router.post("", response_model=LoanAccountResponse)
async def create_loan_account(
    data: LoanAccountCreate,
    current_user: User = Depends(RequirePermissions("LMS_ACCOUNT_CREATE")),
    db: AsyncSession = Depends(get_db),
):
    """Create a new loan account from sanction."""
    service = LoanAccountService(db)
    account = await service.create_loan_account(data, current_user.id)
    return LoanAccountResponse.model_validate(account)


@router.get("/{loan_account_id}", response_model=LoanAccountResponse)
async def get_loan_account(
    loan_account_id: UUID,
    current_user: User = Depends(RequirePermissions("LMS_ACCOUNT_VIEW")),
    db: AsyncSession = Depends(get_db),
):
    """Get loan account by ID."""
    service = LoanAccountService(db)
    account = await service.get_loan_account(loan_account_id)
    return LoanAccountResponse.model_validate(account)


@router.get("/{loan_account_id}/details", response_model=LoanAccountDetailResponse)
async def get_loan_account_details(
    loan_account_id: UUID,
    current_user: User = Depends(RequirePermissions("LMS_ACCOUNT_VIEW")),
    db: AsyncSession = Depends(get_db),
):
    """Get loan account with all related data."""
    service = LoanAccountService(db)
    account = await service.get_loan_account_with_details(loan_account_id)
    return LoanAccountDetailResponse.model_validate(account)


@router.put("/{loan_account_id}", response_model=LoanAccountResponse)
async def update_loan_account(
    loan_account_id: UUID,
    data: LoanAccountUpdate,
    current_user: User = Depends(RequirePermissions("LMS_ACCOUNT_UPDATE")),
    db: AsyncSession = Depends(get_db),
):
    """Update a loan account."""
    service = LoanAccountService(db)
    account = await service.update_loan_account(loan_account_id, data, current_user.id)
    return LoanAccountResponse.model_validate(account)


@router.post("/{loan_account_id}/activate", response_model=LoanAccountResponse)
async def activate_loan_account(
    loan_account_id: UUID,
    current_user: User = Depends(RequirePermissions("LMS_ACCOUNT_UPDATE")),
    db: AsyncSession = Depends(get_db),
):
    """Activate loan account after first disbursement."""
    service = LoanAccountService(db)
    account = await service.activate_loan_account(loan_account_id, current_user.id)
    return LoanAccountResponse.model_validate(account)


# =============================================================================
# Disbursement Endpoints
# =============================================================================


@router.get("/{loan_account_id}/disbursements", response_model=List[DisbursementResponse])
async def list_disbursements(
    loan_account_id: UUID,
    include_inactive: bool = Query(False),
    current_user: User = Depends(RequirePermissions("LMS_ACCOUNT_VIEW")),
    db: AsyncSession = Depends(get_db),
):
    """Get all disbursements for a loan account."""
    service = LoanAccountService(db)
    disbursements = await service.get_loan_disbursements(loan_account_id, include_inactive)
    return [DisbursementResponse.model_validate(d) for d in disbursements]


@router.post("/{loan_account_id}/disbursements", response_model=DisbursementResponse)
async def create_disbursement(
    loan_account_id: UUID,
    data: DisbursementCreate,
    current_user: User = Depends(RequirePermissions("LMS_DISBURSEMENT_CREATE")),
    db: AsyncSession = Depends(get_db),
):
    """Create a new disbursement request."""
    data.loan_account_id = loan_account_id
    service = LoanAccountService(db)
    disbursement = await service.create_disbursement(data, current_user.id)
    return DisbursementResponse.model_validate(disbursement)


@router.post("/disbursements/{disbursement_id}/approve", response_model=DisbursementResponse)
async def approve_disbursement(
    disbursement_id: UUID,
    approval: DisbursementApproval,
    current_user: User = Depends(RequirePermissions("LMS_DISBURSEMENT_APPROVE")),
    db: AsyncSession = Depends(get_db),
):
    """Approve a disbursement request."""
    service = LoanAccountService(db)
    disbursement = await service.approve_disbursement(disbursement_id, approval, current_user.id)
    return DisbursementResponse.model_validate(disbursement)


@router.post("/disbursements/{disbursement_id}/process", response_model=DisbursementResponse)
async def process_disbursement(
    disbursement_id: UUID,
    process_data: DisbursementProcess,
    current_user: User = Depends(RequirePermissions("LMS_DISBURSEMENT_PROCESS")),
    db: AsyncSession = Depends(get_db),
):
    """Process an approved disbursement."""
    service = LoanAccountService(db)
    disbursement = await service.process_disbursement(disbursement_id, process_data, current_user.id)
    return DisbursementResponse.model_validate(disbursement)


# =============================================================================
# Repayment Schedule Endpoints
# =============================================================================


@router.get("/{loan_account_id}/schedule", response_model=RepaymentScheduleDetailResponse)
async def get_current_schedule(
    loan_account_id: UUID,
    current_user: User = Depends(RequirePermissions("LMS_ACCOUNT_VIEW")),
    db: AsyncSession = Depends(get_db),
):
    """Get current repayment schedule for a loan account."""
    service = LoanAccountService(db)
    schedule = await service.get_current_schedule(loan_account_id)
    if schedule:
        return RepaymentScheduleDetailResponse.model_validate(schedule)
    return None


@router.post("/{loan_account_id}/schedule", response_model=RepaymentScheduleResponse)
async def generate_schedule(
    loan_account_id: UUID,
    data: RepaymentScheduleCreate,
    current_user: User = Depends(RequirePermissions("LMS_SCHEDULE_CREATE")),
    db: AsyncSession = Depends(get_db),
):
    """Generate repayment schedule for a loan account."""
    data.loan_account_id = loan_account_id
    service = LoanAccountService(db)
    schedule = await service.generate_schedule(data, current_user.id)
    return RepaymentScheduleResponse.model_validate(schedule)


@router.get("/{loan_account_id}/schedule/due", response_model=List[ScheduleInstallmentResponse])
async def get_due_installments(
    loan_account_id: UUID,
    as_of_date: Optional[date] = Query(None),
    current_user: User = Depends(RequirePermissions("LMS_ACCOUNT_VIEW")),
    db: AsyncSession = Depends(get_db),
):
    """Get due installments for a loan account."""
    service = LoanAccountService(db)
    installments = await service.get_due_installments(loan_account_id, as_of_date)
    return [ScheduleInstallmentResponse.model_validate(i) for i in installments]


# =============================================================================
# Receipt Endpoints
# =============================================================================


@router.get("/{loan_account_id}/receipts", response_model=List[LoanReceiptResponse])
async def list_receipts(
    loan_account_id: UUID,
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    current_user: User = Depends(RequirePermissions("LMS_ACCOUNT_VIEW")),
    db: AsyncSession = Depends(get_db),
):
    """Get all receipts for a loan account."""
    service = LoanAccountService(db)
    receipts = await service.get_loan_receipts(loan_account_id, from_date, to_date)
    return [LoanReceiptResponse.model_validate(r) for r in receipts]


@router.post("/{loan_account_id}/receipts", response_model=LoanReceiptResponse)
async def create_receipt(
    loan_account_id: UUID,
    data: LoanReceiptCreate,
    current_user: User = Depends(RequirePermissions("LMS_RECEIPT_CREATE")),
    db: AsyncSession = Depends(get_db),
):
    """Create a new loan receipt."""
    data.loan_account_id = loan_account_id
    service = LoanAccountService(db)
    receipt = await service.create_receipt(data, current_user.id)
    return LoanReceiptResponse.model_validate(receipt)


@router.post("/receipts/{receipt_id}/allocate", response_model=LoanReceiptResponse)
async def allocate_receipt(
    receipt_id: UUID,
    current_user: User = Depends(RequirePermissions("LMS_RECEIPT_ALLOCATE")),
    db: AsyncSession = Depends(get_db),
):
    """Allocate receipt to loan dues using FIFO."""
    service = LoanAccountService(db)
    receipt = await service.allocate_receipt(receipt_id, current_user.id)
    return LoanReceiptResponse.model_validate(receipt)


@router.post("/receipts/{receipt_id}/bounce", response_model=LoanReceiptResponse)
async def mark_receipt_bounced(
    receipt_id: UUID,
    bounce_data: ReceiptBounceRequest,
    current_user: User = Depends(RequirePermissions("LMS_RECEIPT_UPDATE")),
    db: AsyncSession = Depends(get_db),
):
    """Mark a receipt as bounced."""
    service = LoanAccountService(db)
    receipt = await service.mark_receipt_bounced(receipt_id, bounce_data, current_user.id)
    return LoanReceiptResponse.model_validate(receipt)


# =============================================================================
# Mandate Endpoints
# =============================================================================


@router.get("/{loan_account_id}/mandates", response_model=List[LoanMandateResponse])
async def list_mandates(
    loan_account_id: UUID,
    current_user: User = Depends(RequirePermissions("LMS_ACCOUNT_VIEW")),
    db: AsyncSession = Depends(get_db),
):
    """Get all mandates for a loan account."""
    service = LoanAccountService(db)
    mandates = await service.get_loan_mandates(loan_account_id)
    return [LoanMandateResponse.model_validate(m) for m in mandates]


@router.post("/{loan_account_id}/mandates", response_model=LoanMandateResponse)
async def create_mandate(
    loan_account_id: UUID,
    data: LoanMandateCreate,
    current_user: User = Depends(RequirePermissions("LMS_MANDATE_CREATE")),
    db: AsyncSession = Depends(get_db),
):
    """Create a new NACH mandate."""
    data.loan_account_id = loan_account_id
    service = LoanAccountService(db)
    mandate = await service.create_mandate(data, current_user.id)
    return LoanMandateResponse.model_validate(mandate)


@router.post("/mandates/{mandate_id}/register", response_model=LoanMandateResponse)
async def register_mandate(
    mandate_id: UUID,
    register_data: MandateRegisterRequest,
    current_user: User = Depends(RequirePermissions("LMS_MANDATE_UPDATE")),
    db: AsyncSession = Depends(get_db),
):
    """Register mandate with UMRN."""
    service = LoanAccountService(db)
    mandate = await service.register_mandate(mandate_id, register_data, current_user.id)
    return LoanMandateResponse.model_validate(mandate)


@router.post("/mandates/{mandate_id}/cancel", response_model=LoanMandateResponse)
async def cancel_mandate(
    mandate_id: UUID,
    cancel_data: MandateCancelRequest,
    current_user: User = Depends(RequirePermissions("LMS_MANDATE_UPDATE")),
    db: AsyncSession = Depends(get_db),
):
    """Cancel a mandate."""
    service = LoanAccountService(db)
    mandate = await service.cancel_mandate(mandate_id, cancel_data, current_user.id)
    return LoanMandateResponse.model_validate(mandate)


# =============================================================================
# Asset Classification Endpoints
# =============================================================================


@router.get("/{loan_account_id}/classification-history", response_model=List[AssetClassificationHistoryResponse])
async def get_classification_history(
    loan_account_id: UUID,
    current_user: User = Depends(RequirePermissions("LMS_ACCOUNT_VIEW")),
    db: AsyncSession = Depends(get_db),
):
    """Get asset classification history for a loan account."""
    service = LoanAccountService(db)
    history = await service.get_classification_history(loan_account_id)
    return [AssetClassificationHistoryResponse.model_validate(h) for h in history]


@router.post("/{loan_account_id}/update-classification", response_model=LoanAccountResponse)
async def update_classification(
    loan_account_id: UUID,
    current_user: User = Depends(RequirePermissions("LMS_CLASSIFICATION_UPDATE")),
    db: AsyncSession = Depends(get_db),
):
    """Update asset classification based on DPD."""
    service = LoanAccountService(db)
    account = await service.update_asset_classification(loan_account_id, current_user.id)
    return LoanAccountResponse.model_validate(account)


# =============================================================================
# Accrual Endpoints
# =============================================================================


@router.post("/{loan_account_id}/accrual", response_model=LoanAccrualResponse)
async def run_daily_accrual(
    loan_account_id: UUID,
    accrual_date: date = Query(...),
    current_user: User = Depends(RequirePermissions("LMS_ACCRUAL_RUN")),
    db: AsyncSession = Depends(get_db),
):
    """Run daily interest accrual for a loan account."""
    service = LoanAccountService(db)
    accrual = await service.run_daily_accrual(loan_account_id, accrual_date, current_user.id)
    if accrual:
        return LoanAccrualResponse.model_validate(accrual)
    return None


# =============================================================================
# Provision Endpoints
# =============================================================================


@router.post("/{loan_account_id}/provision", response_model=LoanProvisionResponse)
async def calculate_provision(
    loan_account_id: UUID,
    provision_date: date = Query(...),
    current_user: User = Depends(RequirePermissions("LMS_PROVISION_CALCULATE")),
    db: AsyncSession = Depends(get_db),
):
    """Calculate and create provision for a loan account."""
    service = LoanAccountService(db)
    provision = await service.calculate_provision(loan_account_id, provision_date, current_user.id)
    return LoanProvisionResponse.model_validate(provision)


# =============================================================================
# Adjustment Endpoints
# =============================================================================


@router.get("/{loan_account_id}/adjustments", response_model=List[LoanAdjustmentResponse])
async def list_adjustments(
    loan_account_id: UUID,
    current_user: User = Depends(RequirePermissions("LMS_ACCOUNT_VIEW")),
    db: AsyncSession = Depends(get_db),
):
    """Get all adjustments for a loan account."""
    service = LoanAccountService(db)
    adjustments = await service.get_loan_adjustments(loan_account_id)
    return [LoanAdjustmentResponse.model_validate(a) for a in adjustments]


@router.post("/{loan_account_id}/adjustments", response_model=LoanAdjustmentResponse)
async def create_adjustment(
    loan_account_id: UUID,
    data: LoanAdjustmentCreate,
    current_user: User = Depends(RequirePermissions("LMS_ADJUSTMENT_CREATE")),
    db: AsyncSession = Depends(get_db),
):
    """Create a loan adjustment (rate change, waiver, etc.)."""
    data.loan_account_id = loan_account_id
    service = LoanAccountService(db)
    adjustment = await service.create_adjustment(data, current_user.id)
    return LoanAdjustmentResponse.model_validate(adjustment)
