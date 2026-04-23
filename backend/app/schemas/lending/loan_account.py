"""Loan Account schemas for Phase 2 - Loan Accounting."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from pydantic import Field

from app.schemas.base import BaseSchema
from app.core.pii import MaskedPIIModel
from app.models.lending.enums import (
    LoanAccountStatus, DisbursementStatus, DisbursementMode,
    ScheduleType, InstallmentStatus,
    AccrualCategory, AccrualStatus, AssetClassification,
    ReceiptType, ReceiptStatus, ReceiptMode,
    AllocationPriority, AllocationComponent,
    AdjustmentType, WaiverType, ProvisioningCategory,
    MandateStatus,
    InterestType, RateResetFrequency, RepaymentFrequency,
    RepaymentMode, DayCountConvention
)


# =============================================================================
# Loan Account Schemas
# =============================================================================


class LoanAccountBase(BaseSchema):
    """Base schema for loan account."""
    loan_reference_number: Optional[str] = None
    remarks: Optional[str] = None


class LoanAccountCreate(LoanAccountBase):
    """Schema for creating a loan account."""
    organization_id: UUID
    sanction_id: UUID
    entity_id: UUID
    product_id: UUID
    account_open_date: date
    sanctioned_amount: Decimal
    tenure_months: int
    moratorium_months: int = 0
    interest_type: InterestType
    base_rate_id: Optional[UUID] = None
    current_base_rate: Optional[Decimal] = None
    spread_bps: int = 0
    current_interest_rate: Decimal
    rate_reset_frequency: Optional[RateResetFrequency] = None
    penal_interest_rate: Decimal = Decimal("2.00")
    repayment_frequency: RepaymentFrequency
    repayment_mode: RepaymentMode
    day_count_convention: DayCountConvention = DayCountConvention.ACT_365
    installment_day: int = 1
    prepayment_penalty_rate: Decimal = Decimal("0")
    foreclosure_penalty_rate: Decimal = Decimal("0")
    allocation_priority: AllocationPriority = AllocationPriority.FIFO
    allocation_order: List[str] = ["CHARGES", "PENAL_INTEREST", "INTEREST", "PRINCIPAL"]


class LoanAccountUpdate(BaseSchema):
    """Schema for updating a loan account."""
    loan_reference_number: Optional[str] = None
    current_interest_rate: Optional[Decimal] = None
    current_base_rate: Optional[Decimal] = None
    installment_day: Optional[int] = None
    allocation_priority: Optional[AllocationPriority] = None
    allocation_order: Optional[List[str]] = None
    remarks: Optional[str] = None


class LoanAccountResponse(MaskedPIIModel, LoanAccountBase):
    """Response schema for loan account."""
    id: UUID
    organization_id: UUID
    sanction_id: UUID
    entity_id: UUID
    product_id: UUID
    loan_account_number: str
    account_open_date: date
    first_disbursement_date: Optional[date] = None
    last_disbursement_date: Optional[date] = None
    repayment_start_date: Optional[date] = None
    maturity_date: Optional[date] = None
    closure_date: Optional[date] = None
    sanctioned_amount: Decimal
    tenure_months: int
    moratorium_months: int
    moratorium_end_date: Optional[date] = None
    interest_type: InterestType
    current_interest_rate: Decimal
    penal_interest_rate: Decimal
    repayment_frequency: RepaymentFrequency
    repayment_mode: RepaymentMode
    current_emi_amount: Optional[Decimal] = None
    total_disbursed_amount: Decimal
    undisbursed_amount: Decimal
    principal_outstanding: Decimal
    interest_outstanding: Decimal
    interest_overdue: Decimal
    principal_overdue: Decimal
    penal_interest_outstanding: Decimal
    charges_outstanding: Decimal
    total_outstanding: Decimal
    days_past_due: int
    asset_classification: AssetClassification
    npa_date: Optional[date] = None
    status: LoanAccountStatus
    created_at: datetime

    class Config:
        from_attributes = True


class LoanAccountListResponse(BaseSchema):
    """List response for loan accounts."""
    id: UUID
    loan_account_number: str
    entity_id: UUID
    entity_name: Optional[str] = None
    product_id: UUID
    product_name: Optional[str] = None
    sanctioned_amount: Decimal
    total_disbursed_amount: Decimal
    principal_outstanding: Decimal
    total_outstanding: Decimal
    current_interest_rate: Decimal
    days_past_due: int
    asset_classification: AssetClassification
    status: LoanAccountStatus
    account_open_date: date
    maturity_date: Optional[date] = None

    class Config:
        from_attributes = True


class LoanAccountDetailResponse(LoanAccountResponse):
    """Detailed response for loan account."""
    base_rate_id: Optional[UUID] = None
    current_base_rate: Optional[Decimal] = None
    spread_bps: int
    rate_reset_frequency: Optional[RateResetFrequency] = None
    next_rate_reset_date: Optional[date] = None
    last_rate_reset_date: Optional[date] = None
    day_count_convention: DayCountConvention
    installment_day: int
    total_principal_received: Decimal
    total_interest_received: Decimal
    total_penal_interest_received: Decimal
    total_charges_received: Decimal
    interest_accrued_not_due: Decimal
    last_accrual_date: Optional[date] = None
    accrual_suspended: bool
    accrual_suspension_date: Optional[date] = None
    suspended_interest: Decimal
    oldest_due_date: Optional[date] = None
    npa_amount: Decimal
    provision_percentage: Decimal
    provision_amount: Decimal
    provision_held: Decimal
    principal_written_off: Decimal
    interest_written_off: Decimal
    write_off_date: Optional[date] = None
    prepayment_penalty_rate: Decimal
    foreclosure_penalty_rate: Decimal
    lock_in_end_date: Optional[date] = None
    allocation_priority: AllocationPriority
    allocation_order: List[str]


# =============================================================================
# Disbursement Schemas
# =============================================================================


class DisbursementBase(BaseSchema):
    """Base schema for disbursement."""
    purpose: Optional[str] = None
    remarks: Optional[str] = None


class DisbursementCreate(DisbursementBase):
    """Schema for creating a disbursement."""
    loan_account_id: UUID
    requested_amount: Decimal
    request_date: date
    scheduled_date: Optional[date] = None
    disbursement_mode: DisbursementMode = DisbursementMode.RTGS
    beneficiary_name: str
    beneficiary_account_number: str
    beneficiary_ifsc: str
    beneficiary_bank: Optional[str] = None
    bank_account_id: Optional[UUID] = None
    milestone_id: Optional[UUID] = None


class DisbursementUpdate(BaseSchema):
    """Schema for updating a disbursement."""
    approved_amount: Optional[Decimal] = None
    scheduled_date: Optional[date] = None
    purpose: Optional[str] = None
    remarks: Optional[str] = None


class DisbursementApproval(BaseSchema):
    """Schema for disbursement approval."""
    approved_amount: Decimal
    approval_remarks: Optional[str] = None


class DisbursementProcess(BaseSchema):
    """Schema for processing disbursement."""
    disbursement_date: date
    value_date: date
    utr_number: Optional[str] = None
    cheque_number: Optional[str] = None


class DisbursementResponse(DisbursementBase):
    """Response schema for disbursement."""
    id: UUID
    loan_account_id: UUID
    disbursement_number: int
    disbursement_reference: str
    requested_amount: Decimal
    approved_amount: Optional[Decimal] = None
    disbursed_amount: Optional[Decimal] = None
    disbursement_charges: Decimal
    net_disbursement: Optional[Decimal] = None
    request_date: date
    approval_date: Optional[date] = None
    scheduled_date: Optional[date] = None
    disbursement_date: Optional[date] = None
    value_date: Optional[date] = None
    disbursement_mode: DisbursementMode
    beneficiary_name: str
    beneficiary_account_number: str
    beneficiary_ifsc: str
    utr_number: Optional[str] = None
    status: DisbursementStatus
    created_at: datetime

    class Config:
        from_attributes = True


# =============================================================================
# Repayment Schedule Schemas
# =============================================================================


class ScheduleInstallmentBase(BaseSchema):
    """Base schema for schedule installment."""
    pass


class ScheduleInstallmentResponse(ScheduleInstallmentBase):
    """Response schema for schedule installment."""
    id: UUID
    schedule_id: UUID
    installment_number: int
    due_date: date
    principal_amount: Decimal
    interest_amount: Decimal
    emi_amount: Decimal
    opening_balance: Decimal
    closing_balance: Decimal
    principal_paid: Decimal
    interest_paid: Decimal
    penal_interest_paid: Decimal
    principal_overdue: Decimal
    interest_overdue: Decimal
    penal_interest_due: Decimal
    status: InstallmentStatus
    paid_date: Optional[date] = None

    class Config:
        from_attributes = True


class RepaymentScheduleBase(BaseSchema):
    """Base schema for repayment schedule."""
    change_reason: Optional[str] = None
    remarks: Optional[str] = None


class RepaymentScheduleCreate(RepaymentScheduleBase):
    """Schema for creating repayment schedule."""
    loan_account_id: UUID
    schedule_type: ScheduleType = ScheduleType.ORIGINAL
    principal_amount: Decimal
    interest_rate: Decimal
    tenure_months: int
    effective_date: date
    first_installment_date: date


class RepaymentScheduleResponse(RepaymentScheduleBase):
    """Response schema for repayment schedule."""
    id: UUID
    loan_account_id: UUID
    schedule_number: int
    schedule_type: ScheduleType
    principal_amount: Decimal
    interest_rate: Decimal
    tenure_months: int
    emi_amount: Optional[Decimal] = None
    effective_date: date
    first_installment_date: date
    last_installment_date: date
    total_installments: int
    total_principal: Decimal
    total_interest: Decimal
    is_current: bool
    superseded_date: Optional[date] = None
    created_at: datetime

    class Config:
        from_attributes = True


class RepaymentScheduleDetailResponse(RepaymentScheduleResponse):
    """Detailed response for repayment schedule with installments."""
    installments: List[ScheduleInstallmentResponse] = []


# =============================================================================
# Loan Receipt Schemas
# =============================================================================


class ReceiptAllocationBase(BaseSchema):
    """Base schema for receipt allocation."""
    remarks: Optional[str] = None


class ReceiptAllocationCreate(ReceiptAllocationBase):
    """Schema for creating receipt allocation."""
    installment_id: Optional[UUID] = None
    allocation_component: AllocationComponent
    allocated_amount: Decimal
    allocation_sequence: int


class ReceiptAllocationResponse(ReceiptAllocationBase):
    """Response schema for receipt allocation."""
    id: UUID
    receipt_id: UUID
    installment_id: Optional[UUID] = None
    allocation_component: AllocationComponent
    allocated_amount: Decimal
    allocation_sequence: int

    class Config:
        from_attributes = True


class LoanReceiptBase(BaseSchema):
    """Base schema for loan receipt."""
    remarks: Optional[str] = None


class LoanReceiptCreate(LoanReceiptBase):
    """Schema for creating loan receipt."""
    organization_id: UUID
    loan_account_id: UUID
    receipt_date: date
    value_date: date
    receipt_amount: Decimal
    receipt_type: ReceiptType = ReceiptType.REGULAR
    receipt_mode: ReceiptMode
    instrument_number: Optional[str] = None
    instrument_date: Optional[date] = None
    instrument_bank: Optional[str] = None
    mandate_id: Optional[UUID] = None


class LoanReceiptUpdate(BaseSchema):
    """Schema for updating loan receipt."""
    remarks: Optional[str] = None


class LoanReceiptResponse(LoanReceiptBase):
    """Response schema for loan receipt."""
    id: UUID
    organization_id: UUID
    loan_account_id: UUID
    receipt_number: str
    receipt_date: date
    value_date: date
    receipt_amount: Decimal
    receipt_type: ReceiptType
    receipt_mode: ReceiptMode
    instrument_number: Optional[str] = None
    allocated_amount: Decimal
    unallocated_amount: Decimal
    principal_allocated: Decimal
    interest_allocated: Decimal
    penal_interest_allocated: Decimal
    charges_allocated: Decimal
    prepayment_charges: Decimal
    status: ReceiptStatus
    bounced: bool
    bounce_date: Optional[date] = None
    bounce_reason: Optional[str] = None
    bounce_charges: Decimal
    created_at: datetime

    class Config:
        from_attributes = True


class LoanReceiptDetailResponse(LoanReceiptResponse):
    """Detailed response for loan receipt with allocations."""
    allocations: List[ReceiptAllocationResponse] = []


class ReceiptBounceRequest(BaseSchema):
    """Schema for marking receipt as bounced."""
    bounce_date: date
    bounce_reason: str
    bounce_charges: Decimal = Decimal("0")


# =============================================================================
# Loan Mandate Schemas
# =============================================================================


class LoanMandateBase(BaseSchema):
    """Base schema for loan mandate."""
    mandate_type: str = "NACH"
    remarks: Optional[str] = None


class LoanMandateCreate(LoanMandateBase):
    """Schema for creating loan mandate."""
    loan_account_id: UUID
    bank_account_id: Optional[UUID] = None
    account_number: str
    ifsc_code: str
    bank_name: Optional[str] = None
    account_holder_name: str
    mandate_amount: Decimal
    amount_type: str = "FIXED"
    frequency: str = "MONTHLY"
    debit_day: int = 1
    start_date: date
    end_date: date


class LoanMandateUpdate(BaseSchema):
    """Schema for updating loan mandate."""
    mandate_amount: Optional[Decimal] = None
    debit_day: Optional[int] = None
    end_date: Optional[date] = None
    remarks: Optional[str] = None


class LoanMandateResponse(LoanMandateBase):
    """Response schema for loan mandate."""
    id: UUID
    loan_account_id: UUID
    mandate_reference: str
    umrn: Optional[str] = None
    account_number: str
    ifsc_code: str
    bank_name: Optional[str] = None
    account_holder_name: str
    mandate_amount: Decimal
    amount_type: str
    frequency: str
    debit_day: int
    start_date: date
    end_date: date
    registration_date: Optional[date] = None
    status: MandateStatus
    rejection_reason: Optional[str] = None
    cancellation_date: Optional[date] = None
    cancellation_reason: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class MandateRegisterRequest(BaseSchema):
    """Schema for registering mandate."""
    umrn: str
    registration_date: date


class MandateCancelRequest(BaseSchema):
    """Schema for cancelling mandate."""
    cancellation_date: date
    cancellation_reason: str


# =============================================================================
# Asset Classification History Schemas
# =============================================================================


class AssetClassificationHistoryBase(BaseSchema):
    """Base schema for asset classification history."""
    change_remarks: Optional[str] = None


class AssetClassificationHistoryCreate(AssetClassificationHistoryBase):
    """Schema for creating asset classification history."""
    loan_account_id: UUID
    effective_date: date
    previous_classification: Optional[AssetClassification] = None
    new_classification: AssetClassification
    days_past_due: int
    principal_outstanding: Decimal
    total_outstanding: Decimal
    change_reason: str


class AssetClassificationHistoryResponse(AssetClassificationHistoryBase):
    """Response schema for asset classification history."""
    id: UUID
    loan_account_id: UUID
    effective_date: date
    previous_classification: Optional[AssetClassification] = None
    new_classification: AssetClassification
    days_past_due: int
    principal_outstanding: Decimal
    total_outstanding: Decimal
    change_reason: str
    approved_by_id: Optional[UUID] = None
    created_at: datetime

    class Config:
        from_attributes = True


# =============================================================================
# Loan Provision Schemas
# =============================================================================


class LoanProvisionBase(BaseSchema):
    """Base schema for loan provision."""
    remarks: Optional[str] = None


class LoanProvisionCreate(LoanProvisionBase):
    """Schema for creating loan provision."""
    organization_id: UUID
    loan_account_id: UUID
    provision_date: date
    asset_classification: AssetClassification
    provisioning_category: ProvisioningCategory
    principal_outstanding: Decimal
    total_outstanding: Decimal
    security_value: Decimal = Decimal("0")
    unsecured_portion: Decimal = Decimal("0")
    provision_percentage: Decimal
    provision_required: Decimal
    provision_held: Decimal
    provision_movement: Decimal


class LoanProvisionResponse(LoanProvisionBase):
    """Response schema for loan provision."""
    id: UUID
    organization_id: UUID
    loan_account_id: UUID
    provision_date: date
    asset_classification: AssetClassification
    provisioning_category: ProvisioningCategory
    principal_outstanding: Decimal
    total_outstanding: Decimal
    security_value: Decimal
    unsecured_portion: Decimal
    provision_percentage: Decimal
    provision_required: Decimal
    provision_held: Decimal
    provision_movement: Decimal
    voucher_id: Optional[UUID] = None
    created_at: datetime

    class Config:
        from_attributes = True


# =============================================================================
# Loan Adjustment Schemas
# =============================================================================


class LoanAdjustmentBase(BaseSchema):
    """Base schema for loan adjustment."""
    adjustment_reason: str
    remarks: Optional[str] = None


class LoanAdjustmentCreate(LoanAdjustmentBase):
    """Schema for creating loan adjustment."""
    loan_account_id: UUID
    adjustment_type: AdjustmentType
    effective_date: date
    # Rate change
    new_interest_rate: Optional[Decimal] = None
    # EMI/Tenure change
    new_emi: Optional[Decimal] = None
    new_tenure: Optional[int] = None
    new_maturity_date: Optional[date] = None
    # Waiver
    waiver_type: Optional[WaiverType] = None
    waiver_amount: Decimal = Decimal("0")
    # Write-off
    write_off_amount: Decimal = Decimal("0")
    # Moratorium
    moratorium_months: Optional[int] = None
    moratorium_end_date: Optional[date] = None


class LoanAdjustmentResponse(LoanAdjustmentBase):
    """Response schema for loan adjustment."""
    id: UUID
    loan_account_id: UUID
    adjustment_reference: str
    adjustment_type: AdjustmentType
    effective_date: date
    previous_interest_rate: Optional[Decimal] = None
    previous_emi: Optional[Decimal] = None
    previous_tenure: Optional[int] = None
    previous_maturity_date: Optional[date] = None
    new_interest_rate: Optional[Decimal] = None
    new_emi: Optional[Decimal] = None
    new_tenure: Optional[int] = None
    new_maturity_date: Optional[date] = None
    waiver_type: Optional[WaiverType] = None
    waiver_amount: Decimal
    write_off_amount: Decimal
    moratorium_months: Optional[int] = None
    moratorium_end_date: Optional[date] = None
    new_schedule_id: Optional[UUID] = None
    approved_by_id: Optional[UUID] = None
    approved_at: Optional[datetime] = None
    voucher_id: Optional[UUID] = None
    created_at: datetime

    class Config:
        from_attributes = True


# =============================================================================
# Accrual Schemas
# =============================================================================


class LoanAccrualBase(BaseSchema):
    """Base schema for loan accrual."""
    pass


class LoanAccrualResponse(LoanAccrualBase):
    """Response schema for loan accrual."""
    id: UUID
    loan_account_id: UUID
    accrual_date: date
    accrual_category: AccrualCategory
    principal_balance: Decimal
    interest_rate: Decimal
    day_count_basis: int
    accrued_amount: Decimal
    cumulative_accrued: Decimal
    status: AccrualStatus
    moved_to_suspense: bool
    suspense_date: Optional[date] = None
    voucher_id: Optional[UUID] = None
    created_at: datetime

    class Config:
        from_attributes = True


# =============================================================================
# Summary/Report Schemas
# =============================================================================


class LoanAccountSummary(BaseSchema):
    """Summary schema for loan account portfolio."""
    total_accounts: int
    total_sanctioned: Decimal
    total_disbursed: Decimal
    total_outstanding: Decimal
    total_overdue: Decimal
    total_npa_amount: Decimal
    standard_count: int
    sma_count: int
    npa_count: int


class DPDBucket(BaseSchema):
    """DPD bucket for aging analysis."""
    bucket: str
    count: int
    principal_outstanding: Decimal
    total_outstanding: Decimal


class CollectionSummary(BaseSchema):
    """Collection summary for a period."""
    period_start: date
    period_end: date
    total_due: Decimal
    total_collected: Decimal
    collection_efficiency: Decimal
    principal_collected: Decimal
    interest_collected: Decimal
    penal_interest_collected: Decimal
    charges_collected: Decimal


class DisbursementSummary(BaseSchema):
    """Disbursement summary for a period."""
    period_start: date
    period_end: date
    total_sanctioned: Decimal
    total_disbursed: Decimal
    disbursement_count: int
    pending_disbursements: int
    pending_amount: Decimal
