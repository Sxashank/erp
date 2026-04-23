"""NACH batch and transaction schemas for automated EMI collection."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List, Any
from uuid import UUID

from pydantic import Field

from app.schemas.base import BaseSchema
from app.models.lending.enums import (
    NachBatchStatus, NachTransactionStatus, NachReturnCode, NachFileFormat
)


# =============================================================================
# NACH Batch Schemas
# =============================================================================


class NachBatchBase(BaseSchema):
    """Base schema for NACH batch."""
    batch_date: date
    debit_date: date
    file_format: NachFileFormat = NachFileFormat.ACH_DEBIT
    remarks: Optional[str] = None


class NachBatchCreate(NachBatchBase):
    """Schema for creating a NACH batch."""
    organization_id: UUID
    integration_config_id: Optional[UUID] = None


class NachBatchGenerateRequest(BaseSchema):
    """Request schema for auto-generating a NACH batch from due EMIs."""
    organization_id: UUID
    debit_date: date
    integration_config_id: Optional[UUID] = None
    include_overdue: bool = True  # Include overdue installments
    max_dpd: int = 90  # Maximum days past due to include
    loan_account_ids: Optional[List[UUID]] = None  # Specific accounts (None = all)
    product_ids: Optional[List[UUID]] = None  # Filter by products


class NachBatchUpdate(BaseSchema):
    """Schema for updating a NACH batch."""
    debit_date: Optional[date] = None
    status: Optional[NachBatchStatus] = None
    remarks: Optional[str] = None


class NachBatchSubmit(BaseSchema):
    """Schema for submitting a batch to provider."""
    submission_reference: Optional[str] = None


class NachBatchResponseUpload(BaseSchema):
    """Schema for uploading response file."""
    response_file_path: str


class NachTransactionSummary(BaseSchema):
    """Summary of transaction in a batch."""
    id: UUID
    transaction_reference: str
    loan_account_number: str
    borrower_name: str
    umrn: str
    debit_amount: Decimal
    debit_date: date
    status: NachTransactionStatus
    return_code: Optional[NachReturnCode] = None
    failure_reason: Optional[str] = None


class NachBatchResponse(NachBatchBase):
    """Response schema for NACH batch."""
    id: UUID
    organization_id: UUID
    batch_reference: str
    integration_config_id: Optional[UUID] = None
    total_transactions: int
    total_amount: Decimal
    success_count: int
    success_amount: Decimal
    failure_count: int
    failure_amount: Decimal
    pending_count: int
    file_name: Optional[str] = None
    file_generated_at: Optional[datetime] = None
    submitted_at: Optional[datetime] = None
    submission_reference: Optional[str] = None
    response_received_at: Optional[datetime] = None
    status: NachBatchStatus
    error_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class NachBatchDetailResponse(NachBatchResponse):
    """Detailed response with transactions."""
    transactions: List[NachTransactionSummary] = []


class NachBatchListResponse(BaseSchema):
    """Paginated list of batches."""
    items: List[NachBatchResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# =============================================================================
# NACH Transaction Schemas
# =============================================================================


class NachTransactionBase(BaseSchema):
    """Base schema for NACH transaction."""
    debit_amount: Decimal
    debit_date: date
    narration: Optional[str] = None
    remarks: Optional[str] = None


class NachTransactionCreate(NachTransactionBase):
    """Schema for creating a NACH transaction."""
    batch_id: UUID
    loan_account_id: UUID
    loan_mandate_id: UUID
    installment_id: Optional[UUID] = None


class NachTransactionUpdate(BaseSchema):
    """Schema for updating a NACH transaction."""
    status: Optional[NachTransactionStatus] = None
    bank_reference: Optional[str] = None
    return_code: Optional[NachReturnCode] = None
    failure_reason: Optional[str] = None
    remarks: Optional[str] = None


class NachTransactionBulkStatusUpdate(BaseSchema):
    """Schema for bulk status update from response file."""
    transaction_reference: str
    status: NachTransactionStatus
    bank_reference: Optional[str] = None
    return_code: Optional[NachReturnCode] = None
    failure_reason: Optional[str] = None
    processed_at: Optional[datetime] = None


class NachTransactionResponse(NachTransactionBase):
    """Response schema for NACH transaction."""
    id: UUID
    batch_id: UUID
    loan_account_id: UUID
    loan_mandate_id: UUID
    installment_id: Optional[UUID] = None
    transaction_reference: str
    umrn: str
    account_number: str
    ifsc_code: str
    account_holder_name: str
    bank_name: Optional[str] = None
    status: NachTransactionStatus
    bank_reference: Optional[str] = None
    return_code: Optional[NachReturnCode] = None
    failure_reason: Optional[str] = None
    processed_at: Optional[datetime] = None
    settled_at: Optional[datetime] = None
    receipt_id: Optional[UUID] = None
    retry_count: int
    next_retry_date: Optional[date] = None
    bounce_charges_applied: Decimal
    created_at: datetime

    class Config:
        from_attributes = True


class NachTransactionDetailResponse(NachTransactionResponse):
    """Detailed response with loan info."""
    loan_account_number: Optional[str] = None
    borrower_name: Optional[str] = None
    batch_reference: Optional[str] = None


class NachTransactionListResponse(BaseSchema):
    """Paginated list of transactions."""
    items: List[NachTransactionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# =============================================================================
# NACH Mandate Log Schemas
# =============================================================================


class NachMandateLogBase(BaseSchema):
    """Base schema for mandate log."""
    operation: NachFileFormat
    request_date: date


class NachMandateLogCreate(NachMandateLogBase):
    """Schema for creating mandate log entry."""
    organization_id: UUID
    loan_mandate_id: UUID
    request_reference: str
    request_payload: Optional[dict] = None
    integration_config_id: Optional[UUID] = None


class NachMandateLogUpdate(BaseSchema):
    """Schema for updating mandate log with response."""
    response_date: Optional[date] = None
    response_payload: Optional[dict] = None
    is_success: bool = False
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    umrn_assigned: Optional[str] = None


class NachMandateLogResponse(NachMandateLogBase):
    """Response schema for mandate log."""
    id: UUID
    organization_id: UUID
    loan_mandate_id: UUID
    request_reference: str
    response_date: Optional[date] = None
    is_success: bool
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    umrn_assigned: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# =============================================================================
# Mandate Registration Schemas
# =============================================================================


class MandateRegistrationRequest(BaseSchema):
    """Request for registering a new mandate."""
    loan_mandate_id: UUID
    integration_config_id: Optional[UUID] = None


class MandateRegistrationResponse(BaseSchema):
    """Response from mandate registration."""
    request_reference: str
    status: str
    redirect_url: Optional[str] = None  # For eMandate flows
    message: str


class MandateCancellationRequest(BaseSchema):
    """Request for cancelling a mandate."""
    loan_mandate_id: UUID
    cancellation_reason: str
    integration_config_id: Optional[UUID] = None


# =============================================================================
# NACH Statistics & Reports
# =============================================================================


class NachBatchStatistics(BaseSchema):
    """Statistics for NACH batches."""
    total_batches: int
    total_transactions: int
    total_amount: Decimal
    success_rate: float
    avg_batch_size: float
    status_breakdown: dict  # {status: count}


class NachMonthlyReport(BaseSchema):
    """Monthly NACH report."""
    month: str  # YYYY-MM
    total_batches: int
    total_presented: Decimal
    total_collected: Decimal
    total_bounced: Decimal
    collection_rate: float
    bounce_rate: float
    top_bounce_reasons: List[dict]  # [{reason, count, amount}]


class NachBounceAnalysis(BaseSchema):
    """Analysis of NACH bounces."""
    period_start: date
    period_end: date
    total_bounced: int
    total_bounce_amount: Decimal
    reason_breakdown: List[dict]  # [{return_code, reason, count, amount, percentage}]
    retry_success_rate: float
    avg_retries_to_success: float


class NachRetryDue(BaseSchema):
    """Transactions due for retry."""
    id: UUID
    transaction_reference: str
    loan_account_number: str
    borrower_name: str
    original_debit_date: date
    retry_count: int
    next_retry_date: date
    debit_amount: Decimal
    last_failure_reason: Optional[str] = None


class NachRetryDueList(BaseSchema):
    """List of transactions due for retry."""
    items: List[NachRetryDue]
    total: int
    total_amount: Decimal


# =============================================================================
# NACH File Generation
# =============================================================================


class NachFileGenerationRequest(BaseSchema):
    """Request to generate NACH file."""
    batch_id: UUID


class NachFileGenerationResponse(BaseSchema):
    """Response with generated file info."""
    batch_id: UUID
    file_name: str
    file_path: str
    file_checksum: str
    total_records: int
    total_amount: Decimal


class NachResponseFileParseRequest(BaseSchema):
    """Request to parse NACH response file."""
    batch_id: UUID
    file_path: str


class NachResponseFileParseResponse(BaseSchema):
    """Response from parsing response file."""
    batch_id: UUID
    total_records: int
    success_count: int
    failure_count: int
    success_amount: Decimal
    failure_amount: Decimal
    errors: List[str]  # Any parsing errors
