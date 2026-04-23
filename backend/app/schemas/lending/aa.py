"""Account Aggregator schemas for consent management and data fetching."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List, Any, Dict
from uuid import UUID

from pydantic import Field, validator, EmailStr

from app.schemas.base import BaseSchema
from app.models.lending.enums import (
    AAProvider, AAConsentStatus, AAConsentPurpose, AAConsentMode,
    AAFetchFrequency, AAFIType, AAFetchSessionStatus, AADataStatus
)


# =============================================================================
# AA Consent Schemas
# =============================================================================


class AAConsentBase(BaseSchema):
    """Base schema for AA consent."""
    customer_id: str = Field(..., description="VUA (Virtual User Address) or mobile number")
    customer_name: Optional[str] = None
    customer_mobile: Optional[str] = None
    customer_email: Optional[str] = None
    provider: AAProvider
    purpose: AAConsentPurpose = AAConsentPurpose.UNDERWRITING
    purpose_description: Optional[str] = None
    consent_mode: AAConsentMode = AAConsentMode.VIEW
    fi_types: List[str] = Field(default_factory=list, description="List of FI types to fetch")
    fi_data_from: Optional[date] = None
    fi_data_to: Optional[date] = None
    fetch_frequency: AAFetchFrequency = AAFetchFrequency.ONETIME
    fetch_frequency_value: Optional[int] = None
    consent_expiry: Optional[datetime] = None
    data_life_unit: Optional[str] = None  # MONTH, YEAR, INF
    data_life_value: Optional[int] = None
    redirect_url: Optional[str] = None


class AAConsentCreate(AAConsentBase):
    """Schema for creating a consent request."""
    organization_id: UUID
    entity_id: Optional[UUID] = None
    loan_application_id: Optional[UUID] = None
    loan_account_id: Optional[UUID] = None


class AAConsentUpdate(BaseSchema):
    """Schema for updating consent status."""
    status: Optional[AAConsentStatus] = None
    consent_handle: Optional[str] = None
    consent_id: Optional[str] = None
    consent_url: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejected_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None


class AAConsentResponse(AAConsentBase):
    """Response schema for AA consent."""
    id: UUID
    organization_id: UUID
    entity_id: Optional[UUID] = None
    loan_application_id: Optional[UUID] = None
    loan_account_id: Optional[UUID] = None
    consent_handle: Optional[str] = None
    consent_id: Optional[str] = None
    consent_url: Optional[str] = None
    consent_start: Optional[datetime] = None
    status: AAConsentStatus
    status_updated_at: Optional[datetime] = None
    request_timestamp: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    rejected_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AAConsentDetailResponse(AAConsentResponse):
    """Detailed consent response with fetch sessions."""
    fetch_sessions: List["AAFetchSessionResponse"] = []
    entity_name: Optional[str] = None
    loan_application_number: Optional[str] = None
    loan_account_number: Optional[str] = None


class AAConsentListResponse(BaseSchema):
    """Paginated list of consents."""
    items: List[AAConsentResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class AAConsentRequestInitiate(BaseSchema):
    """Request to initiate a new consent."""
    organization_id: UUID
    entity_id: Optional[UUID] = None
    loan_application_id: Optional[UUID] = None
    loan_account_id: Optional[UUID] = None
    customer_id: str  # VUA or mobile
    customer_name: Optional[str] = None
    customer_mobile: Optional[str] = None
    customer_email: Optional[str] = None
    provider: AAProvider
    purpose: AAConsentPurpose = AAConsentPurpose.UNDERWRITING
    fi_types: List[AAFIType] = [AAFIType.DEPOSIT]
    fi_data_from: date
    fi_data_to: date
    fetch_frequency: AAFetchFrequency = AAFetchFrequency.ONETIME
    consent_validity_months: int = 6
    redirect_url: Optional[str] = None


class AAConsentInitiateResponse(BaseSchema):
    """Response from consent initiation."""
    consent_id: UUID
    consent_handle: str
    consent_url: str
    status: AAConsentStatus
    message: str


class AAConsentRevokeRequest(BaseSchema):
    """Request to revoke a consent."""
    reason: Optional[str] = None


# =============================================================================
# AA Fetch Session Schemas
# =============================================================================


class AAFetchSessionBase(BaseSchema):
    """Base schema for fetch session."""
    fi_types_requested: List[str] = Field(default_factory=list)
    data_from: Optional[date] = None
    data_to: Optional[date] = None


class AAFetchSessionCreate(AAFetchSessionBase):
    """Schema for creating a fetch session."""
    consent_id: UUID
    organization_id: UUID


class AAFetchSessionUpdate(BaseSchema):
    """Schema for updating fetch session."""
    session_id: Optional[str] = None
    data_session_id: Optional[str] = None
    status: Optional[AAFetchSessionStatus] = None
    accounts_received: Optional[int] = None
    accounts_failed: Optional[int] = None
    data_requested_at: Optional[datetime] = None
    data_received_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None


class AAFetchSessionResponse(AAFetchSessionBase):
    """Response schema for fetch session."""
    id: UUID
    consent_id: UUID
    organization_id: UUID
    session_id: Optional[str] = None
    data_session_id: Optional[str] = None
    status: AAFetchSessionStatus
    total_accounts_requested: int
    accounts_received: int
    accounts_failed: int
    initiated_at: datetime
    data_requested_at: Optional[datetime] = None
    data_received_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AAFetchSessionDetailResponse(AAFetchSessionResponse):
    """Detailed fetch session with accounts."""
    bank_accounts: List["AABankAccountResponse"] = []


class AAFetchSessionListResponse(BaseSchema):
    """Paginated list of fetch sessions."""
    items: List[AAFetchSessionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class AAFetchDataRequest(BaseSchema):
    """Request to fetch data for an approved consent."""
    consent_id: UUID
    fi_types: Optional[List[AAFIType]] = None  # None = all approved types
    data_from: Optional[date] = None  # Override consent dates
    data_to: Optional[date] = None


class AAFetchDataResponse(BaseSchema):
    """Response from data fetch initiation."""
    fetch_session_id: UUID
    session_id: str
    status: AAFetchSessionStatus
    message: str


# =============================================================================
# AA Bank Account Schemas
# =============================================================================


class AABankAccountBase(BaseSchema):
    """Base schema for bank account from AA."""
    fi_type: AAFIType = AAFIType.DEPOSIT
    fip_id: Optional[str] = None
    fip_name: Optional[str] = None
    account_type: Optional[str] = None
    account_number_masked: Optional[str] = None
    account_ref_number: Optional[str] = None
    ifsc_code: Optional[str] = None
    branch: Optional[str] = None
    holder_name: Optional[str] = None
    holder_pan: Optional[str] = None
    holder_mobile: Optional[str] = None
    holder_email: Optional[str] = None
    holder_dob: Optional[date] = None
    holder_type: Optional[str] = None
    currency: str = "INR"


class AABankAccountCreate(AABankAccountBase):
    """Schema for creating bank account record."""
    fetch_session_id: UUID
    organization_id: UUID
    entity_id: Optional[UUID] = None
    current_balance: Optional[Decimal] = None
    available_balance: Optional[Decimal] = None
    balance_as_on: Optional[datetime] = None
    opening_date: Optional[date] = None
    maturity_date: Optional[date] = None
    maturity_amount: Optional[Decimal] = None
    interest_rate: Optional[Decimal] = None
    principal_amount: Optional[Decimal] = None
    raw_data: Optional[Dict[str, Any]] = None
    profile_data: Optional[Dict[str, Any]] = None
    summary_data: Optional[Dict[str, Any]] = None
    data_fetched_at: Optional[datetime] = None
    data_from: Optional[date] = None
    data_to: Optional[date] = None


class AABankAccountResponse(AABankAccountBase):
    """Response schema for bank account."""
    id: UUID
    fetch_session_id: UUID
    organization_id: UUID
    entity_id: Optional[UUID] = None
    current_balance: Optional[Decimal] = None
    available_balance: Optional[Decimal] = None
    balance_as_on: Optional[datetime] = None
    opening_date: Optional[date] = None
    maturity_date: Optional[date] = None
    maturity_amount: Optional[Decimal] = None
    interest_rate: Optional[Decimal] = None
    principal_amount: Optional[Decimal] = None
    status: AADataStatus
    data_fetched_at: Optional[datetime] = None
    data_from: Optional[date] = None
    data_to: Optional[date] = None
    transaction_count: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AABankAccountDetailResponse(AABankAccountResponse):
    """Detailed bank account with transactions."""
    transactions: List["AABankTransactionResponse"] = []
    credit_summary: Optional[Dict[str, Any]] = None
    debit_summary: Optional[Dict[str, Any]] = None


class AABankAccountListResponse(BaseSchema):
    """Paginated list of bank accounts."""
    items: List[AABankAccountResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# =============================================================================
# AA Bank Transaction Schemas
# =============================================================================


class AABankTransactionBase(BaseSchema):
    """Base schema for bank transaction from AA."""
    txn_id: Optional[str] = None
    txn_type: str  # DEBIT, CREDIT
    mode: Optional[str] = None  # UPI, NEFT, IMPS, etc.
    amount: Decimal
    currency: str = "INR"
    balance_after: Optional[Decimal] = None
    transaction_date: date
    transaction_timestamp: Optional[datetime] = None
    value_date: Optional[date] = None
    narration: Optional[str] = None
    reference: Optional[str] = None
    counterparty_name: Optional[str] = None
    counterparty_account: Optional[str] = None
    counterparty_ifsc: Optional[str] = None
    category: Optional[str] = None
    sub_category: Optional[str] = None


class AABankTransactionCreate(AABankTransactionBase):
    """Schema for creating transaction record."""
    bank_account_id: UUID
    organization_id: UUID
    raw_data: Optional[Dict[str, Any]] = None


class AABankTransactionResponse(AABankTransactionBase):
    """Response schema for bank transaction."""
    id: UUID
    bank_account_id: UUID
    organization_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class AABankTransactionListResponse(BaseSchema):
    """Paginated list of transactions."""
    items: List[AABankTransactionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# =============================================================================
# AA Consent Log Schemas
# =============================================================================


class AAConsentLogBase(BaseSchema):
    """Base schema for consent log."""
    event_type: str
    old_status: Optional[AAConsentStatus] = None
    new_status: Optional[AAConsentStatus] = None
    source: Optional[str] = None
    message: Optional[str] = None


class AAConsentLogCreate(AAConsentLogBase):
    """Schema for creating consent log entry."""
    consent_id: UUID
    aa_response: Optional[Dict[str, Any]] = None
    created_by_id: Optional[UUID] = None


class AAConsentLogResponse(AAConsentLogBase):
    """Response schema for consent log."""
    id: UUID
    consent_id: UUID
    aa_response: Optional[Dict[str, Any]] = None
    created_at: datetime
    created_by_id: Optional[UUID] = None

    class Config:
        from_attributes = True


class AAConsentLogListResponse(BaseSchema):
    """List of consent logs."""
    items: List[AAConsentLogResponse]
    total: int


# =============================================================================
# AA Analytics & Reports
# =============================================================================


class AAConsentStatistics(BaseSchema):
    """Statistics for AA consents."""
    total_consents: int
    active_consents: int
    pending_consents: int
    expired_consents: int
    revoked_consents: int
    approval_rate: float
    provider_breakdown: Dict[str, int]  # {provider: count}
    purpose_breakdown: Dict[str, int]  # {purpose: count}


class AAFetchStatistics(BaseSchema):
    """Statistics for data fetches."""
    total_fetch_sessions: int
    successful_fetches: int
    failed_fetches: int
    total_accounts_fetched: int
    total_transactions_fetched: int
    success_rate: float
    avg_accounts_per_fetch: float
    fi_type_breakdown: Dict[str, int]  # {fi_type: count}


class AABankStatementAnalysis(BaseSchema):
    """Analysis of fetched bank statements."""
    entity_id: Optional[UUID] = None
    loan_application_id: Optional[UUID] = None
    account_count: int
    analysis_period_from: date
    analysis_period_to: date
    total_credits: Decimal
    total_debits: Decimal
    average_balance: Decimal
    min_balance: Decimal
    max_balance: Decimal
    credit_count: int
    debit_count: int
    salary_credits: Optional[Decimal] = None
    emi_debits: Optional[Decimal] = None
    cheque_bounces: int
    high_value_transactions: List[Dict[str, Any]]
    category_breakdown: Dict[str, Dict[str, Any]]  # {category: {count, amount}}


class AADataImportRequest(BaseSchema):
    """Request to import AA data into bank reconciliation."""
    fetch_session_id: UUID
    bank_account_ids: Optional[List[UUID]] = None  # None = all accounts
    target_bank_account_id: UUID  # Organization's bank account to reconcile


class AADataImportResponse(BaseSchema):
    """Response from data import."""
    imported_transactions: int
    matched_transactions: int
    unmatched_transactions: int
    import_errors: List[str]


# =============================================================================
# AA Provider Configuration
# =============================================================================


class AAProviderConfig(BaseSchema):
    """Configuration for AA provider."""
    provider: AAProvider
    client_id: str
    client_secret: str
    entity_id: str  # FIU entity ID
    token_url: Optional[str] = None
    api_base_url: Optional[str] = None
    callback_url: str
    webhook_secret: Optional[str] = None
    sandbox_mode: bool = True


class AAProviderHealthCheck(BaseSchema):
    """Health check response for AA provider."""
    provider: AAProvider
    is_healthy: bool
    response_time_ms: Optional[int] = None
    last_check_at: datetime
    error_message: Optional[str] = None


# =============================================================================
# AA Webhook Schemas
# =============================================================================


class AAWebhookNotification(BaseSchema):
    """Webhook notification from AA provider."""
    notification_type: str  # CONSENT_STATUS, FI_NOTIFICATION, etc.
    consent_handle: Optional[str] = None
    consent_id: Optional[str] = None
    session_id: Optional[str] = None
    status: Optional[str] = None
    timestamp: datetime
    payload: Dict[str, Any]


class AAConsentStatusWebhook(BaseSchema):
    """Consent status update webhook."""
    consent_handle: str
    consent_id: Optional[str] = None
    status: str  # ACTIVE, REJECTED, REVOKED, PAUSED, EXPIRED
    reason: Optional[str] = None
    timestamp: datetime


class AAFINotificationWebhook(BaseSchema):
    """FI data notification webhook."""
    consent_id: str
    session_id: str
    status: str  # READY, DENIED, TIMEOUT
    fi_status_response: Optional[List[Dict[str, Any]]] = None
    timestamp: datetime


# Update forward references
AAConsentDetailResponse.model_rebuild()
AAFetchSessionDetailResponse.model_rebuild()
AABankAccountDetailResponse.model_rebuild()
