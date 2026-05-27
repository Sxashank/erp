"""Loan Account schemas for Phase 2 - Loan Accounting."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import Field, model_validator

from app.core.pii import MaskedPIIModel
from app.models.lending.enums import (
    AccrualCategory,
    AccrualStatus,
    AdjustmentType,
    AllocationComponent,
    AllocationPriority,
    AssetClassification,
    DayCountConvention,
    DisbursementMode,
    DisbursementStatus,
    InstallmentStatus,
    LoanAccountStatus,
    MandateStatus,
    ProvisioningCategory,
    ReceiptMode,
    ReceiptStatus,
    ReceiptType,
    ScheduleType,
    WaiverType,
)
from app.schemas.base import BaseSchema, CamelSchema

# =============================================================================
# Loan Account Schemas
# =============================================================================


class LoanAccountBase(CamelSchema):
    """Base schema for loan account."""

    loan_reference_number: str | None = None
    remarks: str | None = None


class LoanAccountCreate(LoanAccountBase):
    """Schema for creating a loan account from an accepted sanction.

    The frontend supplies the sanction and optional operational overrides.
    Tenant, borrower, product, amount, interest, and repayment terms are
    derived server-side from the sanction so the LMS account contract remains
    canonical.
    """

    sanction_id: UUID
    account_open_date: date | None = None
    installment_day: int = Field(default=1, ge=1, le=28)
    day_count_convention: DayCountConvention | None = None
    allocation_priority: AllocationPriority = AllocationPriority.FIFO
    allocation_order: list[str] = Field(
        default_factory=lambda: ["PENAL_INTEREST", "CHARGES", "INTEREST", "PRINCIPAL"]
    )


class HistoricalInstallmentCreate(CamelSchema):
    """One EMI/EPI row imported from the client's existing loan register.

    This is intentionally an operational-history contract. It preserves the
    original due dates, component split, payment status and receipt reference
    without forcing the historical period through today's new-loan workflow.
    """

    installment_number: int = Field(..., ge=1)
    due_date: date
    opening_balance: Decimal = Field(..., ge=0)
    principal_amount: Decimal = Field(default=Decimal("0"), ge=0)
    interest_amount: Decimal = Field(default=Decimal("0"), ge=0)
    emi_amount: Decimal = Field(..., ge=0)
    closing_balance: Decimal = Field(..., ge=0)
    principal_paid: Decimal = Field(default=Decimal("0"), ge=0)
    interest_paid: Decimal = Field(default=Decimal("0"), ge=0)
    penal_interest_due: Decimal = Field(default=Decimal("0"), ge=0)
    penal_interest_paid: Decimal = Field(default=Decimal("0"), ge=0)
    status: InstallmentStatus | None = None
    paid_date: date | None = None
    receipt_reference: str | None = Field(None, max_length=50)
    receipt_mode: ReceiptMode = ReceiptMode.ADJUSTMENT
    remarks: str | None = None

    @model_validator(mode="after")
    def _validate_paid_amounts(self):
        if self.principal_paid > self.principal_amount:
            raise ValueError("principalPaid cannot exceed principalAmount")
        if self.interest_paid > self.interest_amount:
            raise ValueError("interestPaid cannot exceed interestAmount")
        if self.penal_interest_paid > self.penal_interest_due:
            raise ValueError("penalInterestPaid cannot exceed penalInterestDue")
        if (self.principal_paid + self.interest_paid + self.penal_interest_paid) > (
            self.emi_amount + self.penal_interest_due
        ):
            raise ValueError("paid components cannot exceed EMI plus penal due")
        return self


class HistoricalLoanOnboardingCreate(CamelSchema):
    """Create an active/closed legacy loan account from pre-go-live records."""

    entity_id: UUID | None = None
    entity_code: str | None = Field(None, max_length=50)
    product_id: UUID | None = None
    product_code: str | None = Field(None, max_length=50)

    legacy_loan_number: str | None = Field(None, max_length=50)
    loan_account_number: str | None = Field(None, max_length=50)
    loan_reference_number: str | None = Field(None, max_length=50)

    application_date: date
    sanction_date: date
    account_open_date: date
    first_disbursement_date: date | None = None
    last_disbursement_date: date | None = None
    repayment_start_date: date | None = None
    maturity_date: date | None = None
    cutover_date: date

    sanctioned_amount: Decimal = Field(..., gt=0)
    total_disbursed_amount: Decimal = Field(..., ge=0)
    principal_outstanding: Decimal = Field(..., ge=0)
    interest_outstanding: Decimal = Field(default=Decimal("0"), ge=0)
    interest_overdue: Decimal | None = Field(default=None, ge=0)
    principal_overdue: Decimal | None = Field(default=None, ge=0)
    penal_interest_outstanding: Decimal = Field(default=Decimal("0"), ge=0)
    charges_outstanding: Decimal = Field(default=Decimal("0"), ge=0)
    total_outstanding: Decimal | None = Field(default=None, ge=0)

    tenure_months: int = Field(..., ge=1)
    moratorium_months: int = Field(default=0, ge=0)
    interest_type: str = Field(..., min_length=1, max_length=80)
    current_interest_rate: Decimal = Field(..., ge=0, le=100)
    penal_interest_rate: Decimal = Field(default=Decimal("2.00"), ge=0, le=100)
    repayment_frequency: str = Field(..., min_length=1, max_length=80)
    repayment_mode: str = Field(..., min_length=1, max_length=80)
    day_count_convention: DayCountConvention = DayCountConvention.ACT_365
    current_emi_amount: Decimal | None = Field(default=None, ge=0)

    days_past_due: int | None = Field(default=None, ge=0)
    asset_classification: AssetClassification | None = None
    npa_date: date | None = None

    purpose: str = Field(default="Legacy loan onboarding", max_length=500)
    project_name: str | None = Field(None, max_length=500)
    remarks: str | None = None
    create_historical_receipts: bool = True
    post_historical_accounting: bool = False
    installments: list[HistoricalInstallmentCreate] = Field(default_factory=list)

    @model_validator(mode="after")
    def _validate_onboarding(self):
        if not self.entity_id and not self.entity_code:
            raise ValueError("entityId or entityCode is required")
        if not self.product_id and not self.product_code:
            raise ValueError("productId or productCode is required")
        if self.total_disbursed_amount > self.sanctioned_amount:
            raise ValueError("totalDisbursedAmount cannot exceed sanctionedAmount")
        if self.account_open_date < self.sanction_date:
            raise ValueError("accountOpenDate cannot be before sanctionDate")
        if self.cutover_date < self.account_open_date:
            raise ValueError("cutoverDate cannot be before accountOpenDate")
        if self.first_disbursement_date and self.first_disbursement_date < self.account_open_date:
            raise ValueError("firstDisbursementDate cannot be before accountOpenDate")
        if self.last_disbursement_date and self.first_disbursement_date:
            if self.last_disbursement_date < self.first_disbursement_date:
                raise ValueError("lastDisbursementDate cannot be before firstDisbursementDate")
        installment_numbers = [row.installment_number for row in self.installments]
        if len(installment_numbers) != len(set(installment_numbers)):
            raise ValueError("installmentNumber must be unique within a loan")
        return self


class HistoricalLoanOnboardingResult(CamelSchema):
    """Result for one historical loan onboarding operation."""

    loan_account_id: UUID | None = None
    loan_account_number: str | None = None
    application_id: UUID | None = None
    sanction_id: UUID | None = None
    schedule_id: UUID | None = None
    imported_installments: int = 0
    imported_receipts: int = 0
    dry_run: bool = False
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class HistoricalLoanOnboardingBatchResponse(CamelSchema):
    """Import/validation response for a batch of historical loans."""

    dry_run: bool
    total_loans: int
    imported_loans: int
    total_installments: int
    imported_receipts: int
    results: list[HistoricalLoanOnboardingResult]


class LoanAccountUpdate(CamelSchema):
    """Schema for updating a loan account."""

    loan_reference_number: str | None = None
    current_interest_rate: Decimal | None = None
    current_base_rate: Decimal | None = None
    installment_day: int | None = Field(None, ge=1, le=28)
    allocation_priority: AllocationPriority | None = None
    allocation_order: list[str] | None = None
    remarks: str | None = None


class LoanAccountResponse(MaskedPIIModel, LoanAccountBase):
    """Response schema for loan account."""

    id: UUID
    organization_id: UUID
    sanction_id: UUID
    entity_id: UUID
    product_id: UUID
    loan_account_number: str
    account_open_date: date
    first_disbursement_date: date | None = None
    last_disbursement_date: date | None = None
    repayment_start_date: date | None = None
    maturity_date: date | None = None
    closure_date: date | None = None
    sanctioned_amount: Decimal
    tenure_months: int
    moratorium_months: int
    moratorium_end_date: date | None = None
    interest_type: str
    current_interest_rate: Decimal
    penal_interest_rate: Decimal
    repayment_frequency: str
    repayment_mode: str
    current_emi_amount: Decimal | None = None
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
    npa_date: date | None = None
    status: LoanAccountStatus
    created_at: datetime

    class Config:
        from_attributes = True


class LoanAccountListResponse(CamelSchema):
    """List response for loan accounts.

    Wire format is camelCase via CamelSchema. Monetary + rate fields stay
    Decimal per CLAUDE.md §6.2 ("Float is banned for money"). Pydantic v2
    serializes Decimal to JSON as a string, preserving precision; the FE
    types those fields as `string` and only parses at display time via
    `AmountDisplay` / `PercentageDisplay`.
    """

    id: UUID
    loan_account_number: str
    entity_id: UUID
    entity_name: str | None = None
    product_id: UUID
    product_name: str | None = None
    sanctioned_amount: Decimal
    total_disbursed_amount: Decimal
    principal_outstanding: Decimal
    total_outstanding: Decimal
    current_interest_rate: Decimal
    days_past_due: int
    asset_classification: AssetClassification
    status: LoanAccountStatus
    account_open_date: date
    maturity_date: date | None = None

    @model_validator(mode="before")
    @classmethod
    def _derive_join_names(cls, obj):
        # Walk the eager-loaded relationships (selectinload(entity), (product))
        # and surface their display names. We can't `model_validate` an ORM
        # instance and *also* override field values, so we read off the ORM
        # and merge with a dict only when needed.
        if isinstance(obj, dict):
            return obj
        entity = getattr(obj, "entity", None)
        product = getattr(obj, "product", None)
        # Build a shallow dict that Pydantic will then validate.
        data = {
            "id": obj.id,
            "loan_account_number": obj.loan_account_number,
            "entity_id": obj.entity_id,
            "entity_name": (
                getattr(entity, "trade_name", None) or getattr(entity, "legal_name", None)
            ),
            "product_id": obj.product_id,
            "product_name": getattr(product, "name", None),
            "sanctioned_amount": obj.sanctioned_amount,
            "total_disbursed_amount": obj.total_disbursed_amount,
            "principal_outstanding": obj.principal_outstanding,
            "total_outstanding": obj.total_outstanding,
            "current_interest_rate": obj.current_interest_rate,
            "days_past_due": obj.days_past_due,
            "asset_classification": obj.asset_classification,
            "status": obj.status,
            "account_open_date": obj.account_open_date,
            "maturity_date": obj.maturity_date,
        }
        return data


class LoanAccountViewResponse(CamelSchema):
    """Slim detail response for the LoanAccountView page (camelCase wire).

    Surfaces just the fields the view page renders. Monetary + rate fields
    stay Decimal per CLAUDE.md §6.2 — Pydantic v2 serializes them to JSON
    strings, preserving precision.
    """

    id: UUID
    loan_account_number: str
    status: LoanAccountStatus
    entity_id: UUID
    entity_name: str | None = None
    entity_legal_name: str | None = None
    entity_pan: str | None = None
    entity_code: str | None = None
    product_id: UUID
    product_name: str | None = None
    product_code: str | None = None
    product_category: str | None = None
    sanction_id: UUID
    sanctioned_amount: Decimal
    total_disbursed_amount: Decimal
    undisbursed_amount: Decimal
    principal_outstanding: Decimal
    interest_outstanding: Decimal
    penal_interest_outstanding: Decimal
    charges_outstanding: Decimal
    total_outstanding: Decimal
    interest_type: str
    current_interest_rate: Decimal
    penal_interest_rate: Decimal
    current_base_rate: Decimal | None = None
    spread_bps: int = 0
    repayment_frequency: str
    repayment_mode: str
    day_count_convention: DayCountConvention
    tenure_months: int
    moratorium_months: int
    moratorium_end_date: date | None = None
    account_open_date: date
    first_disbursement_date: date | None = None
    repayment_start_date: date | None = None
    maturity_date: date | None = None
    last_rate_reset_date: date | None = None
    next_rate_reset_date: date | None = None
    days_past_due: int
    asset_classification: AssetClassification
    npa_date: date | None = None
    current_emi_amount: Decimal | None = None
    created_at: datetime

    @model_validator(mode="before")
    @classmethod
    def _flatten(cls, obj):
        if isinstance(obj, dict):
            return obj
        entity = getattr(obj, "entity", None)
        product = getattr(obj, "product", None)
        return {
            "id": obj.id,
            "loan_account_number": obj.loan_account_number,
            "status": obj.status,
            "entity_id": obj.entity_id,
            "entity_name": (
                getattr(entity, "trade_name", None) or getattr(entity, "legal_name", None)
            ),
            "entity_legal_name": getattr(entity, "legal_name", None),
            "entity_pan": getattr(entity, "pan", None),
            "entity_code": getattr(entity, "entity_code", None),
            "product_id": obj.product_id,
            "product_name": getattr(product, "name", None),
            "product_code": getattr(product, "code", None),
            "product_category": (
                getattr(product, "category", None).value
                if getattr(product, "category", None) is not None
                and hasattr(product.category, "value")
                else getattr(product, "category", None)
            ),
            "sanction_id": obj.sanction_id,
            "sanctioned_amount": obj.sanctioned_amount,
            "total_disbursed_amount": obj.total_disbursed_amount,
            "undisbursed_amount": obj.undisbursed_amount,
            "principal_outstanding": obj.principal_outstanding,
            "interest_outstanding": obj.interest_outstanding,
            "penal_interest_outstanding": obj.penal_interest_outstanding,
            "charges_outstanding": obj.charges_outstanding,
            "total_outstanding": obj.total_outstanding,
            "interest_type": obj.interest_type,
            "current_interest_rate": obj.current_interest_rate,
            "penal_interest_rate": obj.penal_interest_rate,
            "current_base_rate": getattr(obj, "current_base_rate", None),
            "spread_bps": getattr(obj, "spread_bps", 0) or 0,
            "repayment_frequency": obj.repayment_frequency,
            "repayment_mode": obj.repayment_mode,
            "day_count_convention": obj.day_count_convention,
            "tenure_months": obj.tenure_months,
            "moratorium_months": obj.moratorium_months,
            "moratorium_end_date": obj.moratorium_end_date,
            "account_open_date": obj.account_open_date,
            "first_disbursement_date": obj.first_disbursement_date,
            "repayment_start_date": obj.repayment_start_date,
            "maturity_date": obj.maturity_date,
            "last_rate_reset_date": getattr(obj, "last_rate_reset_date", None),
            "next_rate_reset_date": getattr(obj, "next_rate_reset_date", None),
            "days_past_due": obj.days_past_due,
            "asset_classification": obj.asset_classification,
            "npa_date": obj.npa_date,
            "current_emi_amount": obj.current_emi_amount,
            "created_at": obj.created_at,
        }


class LoanAccountDetailResponse(LoanAccountResponse):
    """Detailed response for loan account."""

    base_rate_id: UUID | None = None
    current_base_rate: Decimal | None = None
    spread_bps: int
    rate_reset_frequency: str | None = None
    next_rate_reset_date: date | None = None
    last_rate_reset_date: date | None = None
    day_count_convention: DayCountConvention
    installment_day: int
    total_principal_received: Decimal
    total_interest_received: Decimal
    total_penal_interest_received: Decimal
    total_charges_received: Decimal
    interest_accrued_not_due: Decimal
    last_accrual_date: date | None = None
    accrual_suspended: bool
    accrual_suspension_date: date | None = None
    suspended_interest: Decimal
    oldest_due_date: date | None = None
    npa_amount: Decimal
    provision_percentage: Decimal
    provision_amount: Decimal
    provision_held: Decimal
    principal_written_off: Decimal
    interest_written_off: Decimal
    write_off_date: date | None = None
    prepayment_penalty_rate: Decimal
    foreclosure_penalty_rate: Decimal
    lock_in_end_date: date | None = None
    allocation_priority: AllocationPriority
    allocation_order: list[str]


# =============================================================================
# Disbursement Schemas
# =============================================================================


class DisbursementBase(BaseSchema):
    """Base schema for disbursement."""

    purpose: str | None = None
    remarks: str | None = None


class DisbursementCreate(DisbursementBase):
    """Schema for creating a disbursement."""

    loan_account_id: UUID
    requested_amount: Decimal
    request_date: date
    scheduled_date: date | None = None
    disbursement_mode: DisbursementMode = DisbursementMode.RTGS
    beneficiary_name: str
    beneficiary_account_number: str
    beneficiary_ifsc: str
    beneficiary_bank: str | None = None
    bank_account_id: UUID | None = None
    milestone_id: UUID | None = None


class DisbursementUpdate(BaseSchema):
    """Schema for updating a disbursement."""

    approved_amount: Decimal | None = None
    scheduled_date: date | None = None
    purpose: str | None = None
    remarks: str | None = None


class DisbursementApproval(BaseSchema):
    """Schema for disbursement approval."""

    approved_amount: Decimal
    approval_remarks: str | None = None


class DisbursementProcess(BaseSchema):
    """Schema for processing disbursement."""

    disbursement_date: date
    value_date: date
    utr_number: str | None = None
    cheque_number: str | None = None


class DisbursementResponse(DisbursementBase):
    """Response schema for disbursement."""

    id: UUID
    loan_account_id: UUID
    disbursement_number: int
    disbursement_reference: str
    requested_amount: Decimal
    approved_amount: Decimal | None = None
    disbursed_amount: Decimal | None = None
    disbursement_charges: Decimal
    net_disbursement: Decimal | None = None
    request_date: date
    approval_date: date | None = None
    scheduled_date: date | None = None
    disbursement_date: date | None = None
    value_date: date | None = None
    disbursement_mode: DisbursementMode
    beneficiary_name: str
    beneficiary_account_number: str
    beneficiary_ifsc: str
    utr_number: str | None = None
    status: DisbursementStatus
    created_at: datetime

    class Config:
        from_attributes = True


class DisbursementListResponse(CamelSchema):
    """Slim list response for disbursements (camelCase wire format)."""

    id: UUID
    disbursement_reference: str
    disbursement_number: int
    loan_account_id: UUID
    loan_account_number: str | None = None
    entity_id: UUID | None = None
    entity_name: str | None = None
    requested_amount: Decimal
    approved_amount: Decimal | None = None
    disbursed_amount: Decimal | None = None
    request_date: date
    disbursement_date: date | None = None
    status: DisbursementStatus
    beneficiary_name: str
    utr_number: str | None = None

    @model_validator(mode="before")
    @classmethod
    def _flatten(cls, obj):
        if isinstance(obj, dict):
            return obj
        loan = getattr(obj, "loan_account", None)
        entity = getattr(loan, "entity", None) if loan is not None else None
        return {
            "id": obj.id,
            "disbursement_reference": obj.disbursement_reference,
            "disbursement_number": obj.disbursement_number,
            "loan_account_id": obj.loan_account_id,
            "loan_account_number": getattr(loan, "loan_account_number", None),
            "entity_id": getattr(loan, "entity_id", None),
            "entity_name": (
                getattr(entity, "trade_name", None) or getattr(entity, "legal_name", None)
            ),
            "requested_amount": obj.requested_amount,
            "approved_amount": obj.approved_amount,
            "disbursed_amount": obj.disbursed_amount,
            "request_date": obj.request_date,
            "disbursement_date": obj.disbursement_date,
            "status": obj.status,
            "beneficiary_name": obj.beneficiary_name,
            "utr_number": obj.utr_number,
        }


# =============================================================================
# Repayment Schedule Schemas
# =============================================================================


class ScheduleInstallmentBase(CamelSchema):
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
    paid_date: date | None = None

    class Config:
        from_attributes = True


class RepaymentScheduleBase(CamelSchema):
    """Base schema for repayment schedule."""

    change_reason: str | None = None
    remarks: str | None = None


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
    emi_amount: Decimal | None = None
    effective_date: date
    first_installment_date: date
    last_installment_date: date
    total_installments: int
    total_principal: Decimal
    total_interest: Decimal
    is_current: bool
    superseded_date: date | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class RepaymentScheduleDetailResponse(RepaymentScheduleResponse):
    """Detailed response for repayment schedule with installments."""

    installments: list[ScheduleInstallmentResponse] = []


# =============================================================================
# Loan Receipt Schemas
# =============================================================================


class ReceiptAllocationBase(CamelSchema):
    """Base schema for receipt allocation."""

    remarks: str | None = None


class ReceiptAllocationCreate(ReceiptAllocationBase):
    """Schema for creating receipt allocation."""

    installment_id: UUID | None = None
    allocation_component: AllocationComponent
    allocated_amount: Decimal
    allocation_sequence: int


class ReceiptAllocationResponse(ReceiptAllocationBase):
    """Response schema for receipt allocation."""

    id: UUID
    receipt_id: UUID
    installment_id: UUID | None = None
    allocation_component: AllocationComponent
    allocated_amount: Decimal
    allocation_sequence: int

    class Config:
        from_attributes = True


class LoanReceiptBase(CamelSchema):
    """Base schema for loan receipt."""

    remarks: str | None = None


class LoanReceiptCreate(LoanReceiptBase):
    """Schema for creating loan receipt."""

    loan_account_id: UUID | None = None
    receipt_date: date
    value_date: date | None = None
    receipt_amount: Decimal
    receipt_type: ReceiptType = ReceiptType.REGULAR
    receipt_mode: ReceiptMode
    instrument_number: str | None = None
    instrument_date: date | None = None
    instrument_bank: str | None = None
    mandate_id: UUID | None = None


class LoanReceiptUpdate(CamelSchema):
    """Schema for updating loan receipt."""

    remarks: str | None = None


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
    instrument_number: str | None = None
    allocated_amount: Decimal
    unallocated_amount: Decimal
    principal_allocated: Decimal
    interest_allocated: Decimal
    penal_interest_allocated: Decimal
    charges_allocated: Decimal
    prepayment_charges: Decimal
    status: ReceiptStatus
    bounced: bool
    bounce_date: date | None = None
    bounce_reason: str | None = None
    bounce_charges: Decimal
    created_at: datetime

    class Config:
        from_attributes = True


class LoanReceiptDetailResponse(LoanReceiptResponse):
    """Detailed response for loan receipt with allocations."""

    allocations: list[ReceiptAllocationResponse] = []


class LoanReceiptListResponse(CamelSchema):
    """Slim list response for receipts (camelCase wire format)."""

    id: UUID
    receipt_number: str
    loan_account_id: UUID
    loan_account_number: str | None = None
    entity_id: UUID | None = None
    entity_name: str | None = None
    receipt_date: date
    value_date: date
    receipt_amount: Decimal
    allocated_amount: Decimal
    unallocated_amount: Decimal
    receipt_type: ReceiptType
    receipt_mode: ReceiptMode
    instrument_number: str | None = None
    status: ReceiptStatus
    bounced: bool

    @model_validator(mode="before")
    @classmethod
    def _flatten(cls, obj):
        if isinstance(obj, dict):
            return obj
        loan = getattr(obj, "loan_account", None)
        entity = getattr(loan, "entity", None) if loan is not None else None
        return {
            "id": obj.id,
            "receipt_number": obj.receipt_number,
            "loan_account_id": obj.loan_account_id,
            "loan_account_number": getattr(loan, "loan_account_number", None),
            "entity_id": getattr(loan, "entity_id", None),
            "entity_name": (
                getattr(entity, "trade_name", None) or getattr(entity, "legal_name", None)
            ),
            "receipt_date": obj.receipt_date,
            "value_date": obj.value_date,
            "receipt_amount": obj.receipt_amount,
            "allocated_amount": obj.allocated_amount,
            "unallocated_amount": obj.unallocated_amount,
            "receipt_type": obj.receipt_type,
            "receipt_mode": obj.receipt_mode,
            "instrument_number": obj.instrument_number,
            "status": obj.status,
            "bounced": obj.bounced,
        }


class ReceiptBounceRequest(CamelSchema):
    """Schema for marking receipt as bounced."""

    bounce_date: date
    bounce_reason: str
    bounce_charges: Decimal = Decimal("0")


# =============================================================================
# Loan Mandate Schemas
# =============================================================================


class LoanMandateBase(CamelSchema):
    """Base schema for loan mandate."""

    mandate_type: str = "NACH"
    remarks: str | None = None


class LoanMandateCreate(LoanMandateBase):
    """Schema for creating loan mandate."""

    loan_account_id: UUID
    bank_account_id: UUID | None = None
    account_number: str
    ifsc_code: str
    bank_name: str | None = None
    account_holder_name: str
    mandate_amount: Decimal
    amount_type: str = "FIXED"
    frequency: str = "MONTHLY"
    debit_day: int = 1
    start_date: date
    end_date: date


class LoanMandateUpdate(CamelSchema):
    """Schema for updating loan mandate."""

    mandate_amount: Decimal | None = None
    debit_day: int | None = None
    end_date: date | None = None
    remarks: str | None = None


class LoanMandateResponse(LoanMandateBase):
    """Response schema for loan mandate."""

    id: UUID
    loan_account_id: UUID
    mandate_reference: str
    umrn: str | None = None
    account_number: str
    ifsc_code: str
    bank_name: str | None = None
    account_holder_name: str
    mandate_amount: Decimal
    amount_type: str
    frequency: str
    debit_day: int
    start_date: date
    end_date: date
    registration_date: date | None = None
    status: MandateStatus
    rejection_reason: str | None = None
    cancellation_date: date | None = None
    cancellation_reason: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class MandateRegisterRequest(CamelSchema):
    """Schema for registering mandate."""

    umrn: str
    registration_date: date


class MandateCancelRequest(CamelSchema):
    """Schema for cancelling mandate."""

    cancellation_date: date
    cancellation_reason: str


# =============================================================================
# Asset Classification History Schemas
# =============================================================================


class AssetClassificationHistoryBase(CamelSchema):
    """Base schema for asset classification history."""

    change_remarks: str | None = None


class AssetClassificationHistoryCreate(AssetClassificationHistoryBase):
    """Schema for creating asset classification history."""

    loan_account_id: UUID
    effective_date: date
    previous_classification: AssetClassification | None = None
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
    previous_classification: AssetClassification | None = None
    new_classification: AssetClassification
    days_past_due: int
    principal_outstanding: Decimal
    total_outstanding: Decimal
    change_reason: str
    approved_by_id: UUID | None = None
    created_at: datetime

    class Config:
        from_attributes = True


# =============================================================================
# Loan Provision Schemas
# =============================================================================


class LoanProvisionBase(CamelSchema):
    """Base schema for loan provision."""

    remarks: str | None = None


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
    voucher_id: UUID | None = None
    created_at: datetime

    class Config:
        from_attributes = True


# =============================================================================
# Loan Adjustment Schemas
# =============================================================================


class LoanAdjustmentBase(CamelSchema):
    """Base schema for loan adjustment."""

    adjustment_reason: str
    remarks: str | None = None


class LoanAdjustmentCreate(LoanAdjustmentBase):
    """Schema for creating loan adjustment."""

    loan_account_id: UUID
    adjustment_type: AdjustmentType
    effective_date: date
    # Rate change
    new_interest_rate: Decimal | None = None
    # EMI/Tenure change
    new_emi: Decimal | None = None
    new_tenure: int | None = None
    new_maturity_date: date | None = None
    # Waiver
    waiver_type: WaiverType | None = None
    waiver_amount: Decimal = Decimal("0")
    # Write-off
    write_off_amount: Decimal = Decimal("0")
    # Moratorium
    moratorium_months: int | None = None
    moratorium_end_date: date | None = None


class LoanAdjustmentResponse(LoanAdjustmentBase):
    """Response schema for loan adjustment."""

    id: UUID
    loan_account_id: UUID
    adjustment_reference: str
    adjustment_type: AdjustmentType
    effective_date: date
    previous_interest_rate: Decimal | None = None
    previous_emi: Decimal | None = None
    previous_tenure: int | None = None
    previous_maturity_date: date | None = None
    new_interest_rate: Decimal | None = None
    new_emi: Decimal | None = None
    new_tenure: int | None = None
    new_maturity_date: date | None = None
    waiver_type: WaiverType | None = None
    waiver_amount: Decimal
    write_off_amount: Decimal
    moratorium_months: int | None = None
    moratorium_end_date: date | None = None
    new_schedule_id: UUID | None = None
    approved_by_id: UUID | None = None
    approved_at: datetime | None = None
    voucher_id: UUID | None = None
    created_at: datetime

    class Config:
        from_attributes = True


# =============================================================================
# Accrual Schemas
# =============================================================================


class LoanAccrualBase(CamelSchema):
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
    suspense_date: date | None = None
    voucher_id: UUID | None = None
    created_at: datetime

    class Config:
        from_attributes = True


# =============================================================================
# Summary/Report Schemas
# =============================================================================


class LoanAccountSummary(CamelSchema):
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


class DPDBucket(CamelSchema):
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
