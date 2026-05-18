"""NACH batch and transaction schemas for automated EMI collection."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from app.models.lending.enums import (
    NachBatchStatus,
    NachFileFormat,
    NachReturnCode,
    NachTransactionStatus,
)
from app.schemas.base import CamelSchema

# =============================================================================
# NACH Batch Schemas
# =============================================================================


class NachBatchBase(CamelSchema):
    """Base schema for NACH batch."""

    batch_date: date
    debit_date: date
    file_format: NachFileFormat = NachFileFormat.ACH_DEBIT
    remarks: str | None = None


class NachBatchCreate(NachBatchBase):
    """Schema for creating a NACH batch."""

    organization_id: UUID
    integration_config_id: UUID | None = None


class NachBatchGenerateRequest(CamelSchema):
    """Request schema for auto-generating a NACH batch from due EMIs."""

    organization_id: UUID
    debit_date: date
    integration_config_id: UUID | None = None
    include_overdue: bool = True  # Include overdue installments
    max_dpd: int = 90  # Maximum days past due to include
    loan_account_ids: list[UUID] | None = None  # Specific accounts (None = all)
    product_ids: list[UUID] | None = None  # Filter by products


class NachBatchUpdate(CamelSchema):
    """Schema for updating a NACH batch."""

    debit_date: date | None = None
    status: NachBatchStatus | None = None
    remarks: str | None = None


class NachBatchSubmit(CamelSchema):
    """Schema for submitting a batch to provider."""

    submission_reference: str | None = None


class NachBatchResponseUpload(CamelSchema):
    """Schema for uploading response file."""

    response_file_path: str


class NachTransactionSummary(CamelSchema):
    """Summary of transaction in a batch."""

    id: UUID
    transaction_reference: str
    loan_account_number: str
    borrower_name: str
    umrn: str
    debit_amount: Decimal
    debit_date: date
    status: NachTransactionStatus
    return_code: NachReturnCode | None = None
    failure_reason: str | None = None


class NachBatchResponse(NachBatchBase):
    """Response schema for NACH batch."""

    id: UUID
    organization_id: UUID
    batch_reference: str
    integration_config_id: UUID | None = None
    total_transactions: int
    total_amount: Decimal
    success_count: int
    success_amount: Decimal
    failure_count: int
    failure_amount: Decimal
    pending_count: int
    file_name: str | None = None
    file_generated_at: datetime | None = None
    submitted_at: datetime | None = None
    submission_reference: str | None = None
    response_received_at: datetime | None = None
    status: NachBatchStatus
    error_message: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class NachBatchListItemResponse(CamelSchema):
    """Slim list-item for NACH batches page (camelCase wire format).

    Monetary fields stay Decimal per CLAUDE.md §6.2.
    """

    id: UUID
    batch_reference: str
    batch_date: date
    debit_date: date
    integration_config_id: UUID | None = None
    total_transactions: int
    total_amount: Decimal
    success_count: int
    failure_count: int
    pending_count: int
    file_name: str | None = None
    file_generated_at: datetime | None = None
    submitted_at: datetime | None = None
    response_received_at: datetime | None = None
    status: NachBatchStatus
    created_at: datetime


class NachBatchDetailResponse(NachBatchResponse):
    """Detailed response with transactions."""

    transactions: list[NachTransactionSummary] = []


class NachBatchListResponse(CamelSchema):
    """Paginated list of batches (camelCase wire format)."""

    items: list[NachBatchListItemResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# =============================================================================
# NACH Transaction Schemas
# =============================================================================


class NachTransactionBase(CamelSchema):
    """Base schema for NACH transaction."""

    debit_amount: Decimal
    debit_date: date
    narration: str | None = None
    remarks: str | None = None


class NachTransactionCreate(NachTransactionBase):
    """Schema for creating a NACH transaction."""

    batch_id: UUID
    loan_account_id: UUID
    loan_mandate_id: UUID
    installment_id: UUID | None = None


class NachTransactionUpdate(CamelSchema):
    """Schema for updating a NACH transaction."""

    status: NachTransactionStatus | None = None
    bank_reference: str | None = None
    return_code: NachReturnCode | None = None
    failure_reason: str | None = None
    remarks: str | None = None


class NachTransactionBulkStatusUpdate(CamelSchema):
    """Schema for bulk status update from response file."""

    transaction_reference: str
    status: NachTransactionStatus
    bank_reference: str | None = None
    return_code: NachReturnCode | None = None
    failure_reason: str | None = None
    processed_at: datetime | None = None


class NachTransactionResponse(NachTransactionBase):
    """Response schema for NACH transaction."""

    id: UUID
    batch_id: UUID
    loan_account_id: UUID
    loan_mandate_id: UUID
    installment_id: UUID | None = None
    transaction_reference: str
    umrn: str
    account_number: str
    ifsc_code: str
    account_holder_name: str
    bank_name: str | None = None
    status: NachTransactionStatus
    bank_reference: str | None = None
    return_code: NachReturnCode | None = None
    failure_reason: str | None = None
    processed_at: datetime | None = None
    settled_at: datetime | None = None
    receipt_id: UUID | None = None
    retry_count: int
    next_retry_date: date | None = None
    bounce_charges_applied: Decimal
    created_at: datetime

    class Config:
        from_attributes = True


class NachTransactionDetailResponse(NachTransactionResponse):
    """Detailed response with loan info."""

    loan_account_number: str | None = None
    borrower_name: str | None = None
    batch_reference: str | None = None


class NachTransactionListResponse(CamelSchema):
    """Paginated list of transactions."""

    items: list[NachTransactionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# =============================================================================
# NACH Mandate Log Schemas
# =============================================================================


class NachMandateLogBase(CamelSchema):
    """Base schema for mandate log."""

    operation: NachFileFormat
    request_date: date


class NachMandateLogCreate(NachMandateLogBase):
    """Schema for creating mandate log entry."""

    organization_id: UUID
    loan_mandate_id: UUID
    request_reference: str
    request_payload: dict | None = None
    integration_config_id: UUID | None = None


class NachMandateLogUpdate(CamelSchema):
    """Schema for updating mandate log with response."""

    response_date: date | None = None
    response_payload: dict | None = None
    is_success: bool = False
    error_code: str | None = None
    error_message: str | None = None
    umrn_assigned: str | None = None


class NachMandateLogResponse(NachMandateLogBase):
    """Response schema for mandate log."""

    id: UUID
    organization_id: UUID
    loan_mandate_id: UUID
    request_reference: str
    response_date: date | None = None
    is_success: bool
    error_code: str | None = None
    error_message: str | None = None
    umrn_assigned: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


# =============================================================================
# Mandate Registration Schemas
# =============================================================================


class MandateRegistrationRequest(CamelSchema):
    """Request for registering a new mandate."""

    loan_mandate_id: UUID
    integration_config_id: UUID | None = None


class MandateRegistrationResponse(CamelSchema):
    """Response from mandate registration."""

    request_reference: str
    status: str
    redirect_url: str | None = None  # For eMandate flows
    message: str


class MandateCancellationRequest(CamelSchema):
    """Request for cancelling a mandate."""

    loan_mandate_id: UUID
    cancellation_reason: str
    integration_config_id: UUID | None = None


# =============================================================================
# NACH Statistics & Reports
# =============================================================================


class NachBatchStatistics(CamelSchema):
    """Statistics for NACH batches."""

    total_batches: int
    total_transactions: int
    total_amount: Decimal
    success_rate: float
    avg_batch_size: float
    status_breakdown: dict  # {status: count}


class NachMonthlyReport(CamelSchema):
    """Monthly NACH report."""

    month: str  # YYYY-MM
    total_batches: int
    total_presented: Decimal
    total_collected: Decimal
    total_bounced: Decimal
    collection_rate: float
    bounce_rate: float
    top_bounce_reasons: list[dict]  # [{reason, count, amount}]


class NachBounceAnalysis(CamelSchema):
    """Analysis of NACH bounces."""

    period_start: date
    period_end: date
    total_bounced: int
    total_bounce_amount: Decimal
    reason_breakdown: list[dict]  # [{return_code, reason, count, amount, percentage}]
    retry_success_rate: float
    avg_retries_to_success: float


class NachRetryDue(CamelSchema):
    """Transactions due for retry (camelCase wire format).

    Monetary fields stay Decimal per CLAUDE.md §6.2.
    """

    id: UUID
    transaction_reference: str
    loan_account_number: str
    borrower_name: str
    original_debit_date: date
    retry_count: int
    next_retry_date: date
    debit_amount: Decimal
    last_failure_reason: str | None = None
    umrn: str | None = None
    bank_name: str | None = None
    return_code: str | None = None
    mandate_status: str | None = None
    max_retries: int = 3


class NachRetryDueList(CamelSchema):
    """List of transactions due for retry (camelCase wire format)."""

    items: list[NachRetryDue]
    total: int
    total_amount: Decimal


# =============================================================================
# NACH File Generation
# =============================================================================


class NachFileGenerationRequest(CamelSchema):
    """Request to generate NACH file."""

    batch_id: UUID


class NachFileGenerationResponse(CamelSchema):
    """Response with generated file info."""

    batch_id: UUID
    file_name: str
    file_path: str
    file_checksum: str
    total_records: int
    total_amount: Decimal


class NachResponseFileParseRequest(CamelSchema):
    """Request to parse NACH response file."""

    batch_id: UUID
    file_path: str


class NachResponseFileParseResponse(CamelSchema):
    """Response from parsing response file."""

    batch_id: UUID
    total_records: int
    success_count: int
    failure_count: int
    success_amount: Decimal
    failure_amount: Decimal
    errors: list[str]  # Any parsing errors
