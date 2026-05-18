"""Account Aggregator schemas for consent management and data fetching."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import Field, model_validator

from app.models.lending.enums import (
    AAConsentMode,
    AAConsentPurpose,
    AAConsentStatus,
    AADataStatus,
    AAFetchFrequency,
    AAFetchSessionStatus,
    AAFIType,
    AAProvider,
)
from app.schemas.base import CamelSchema

# =============================================================================
# AA Consent Schemas
# =============================================================================


class AAConsentBase(CamelSchema):
    """Base schema for AA consent."""

    customer_id: str = Field(..., description="VUA (Virtual User Address) or mobile number")
    customer_name: str | None = None
    customer_mobile: str | None = None
    customer_email: str | None = None
    provider: AAProvider
    purpose: AAConsentPurpose = AAConsentPurpose.UNDERWRITING
    purpose_description: str | None = None
    consent_mode: AAConsentMode = AAConsentMode.VIEW
    fi_types: list[str] = Field(default_factory=list, description="List of FI types to fetch")
    fi_data_from: date | None = None
    fi_data_to: date | None = None
    fetch_frequency: AAFetchFrequency = AAFetchFrequency.ONETIME
    fetch_frequency_value: int | None = None
    consent_expiry: datetime | None = None
    data_life_unit: str | None = None  # MONTH, YEAR, INF
    data_life_value: int | None = None
    redirect_url: str | None = None


class AAConsentCreate(AAConsentBase):
    """Schema for creating a consent request."""

    organization_id: UUID
    entity_id: UUID | None = None
    loan_application_id: UUID | None = None
    loan_account_id: UUID | None = None


class AAConsentUpdate(CamelSchema):
    """Schema for updating consent status."""

    status: AAConsentStatus | None = None
    consent_handle: str | None = None
    consent_id: str | None = None
    consent_url: str | None = None
    approved_at: datetime | None = None
    rejected_at: datetime | None = None
    revoked_at: datetime | None = None
    rejection_reason: str | None = None
    error_code: str | None = None
    error_message: str | None = None


class AAConsentResponse(AAConsentBase):
    """Response schema for AA consent."""

    id: UUID
    organization_id: UUID
    entity_id: UUID | None = None
    loan_application_id: UUID | None = None
    loan_account_id: UUID | None = None
    consent_handle: str | None = None
    consent_id: str | None = None
    consent_url: str | None = None
    consent_start: datetime | None = None
    status: AAConsentStatus
    status_updated_at: datetime | None = None
    request_timestamp: datetime | None = None
    approved_at: datetime | None = None
    rejected_at: datetime | None = None
    revoked_at: datetime | None = None
    rejection_reason: str | None = None
    error_code: str | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class AAConsentListItemResponse(CamelSchema):
    """Slim list-item for AA consents page (camelCase wire format)."""

    id: UUID
    consent_handle: str | None = None
    consent_id: str | None = None
    customer_id: str
    customer_name: str | None = None
    customer_mobile: str | None = None
    provider: AAProvider
    purpose: AAConsentPurpose
    fi_types: list[str] = []
    fi_data_from: date | None = None
    fi_data_to: date | None = None
    status: AAConsentStatus
    consent_expiry: datetime | None = None
    entity_name: str | None = None
    loan_application_number: str | None = None
    fetch_session_count: int = 0
    last_fetch_at: datetime | None = None
    created_at: datetime
    approved_at: datetime | None = None
    rejected_at: datetime | None = None
    revoked_at: datetime | None = None

    @model_validator(mode="before")
    @classmethod
    def _flatten(cls, obj):
        if isinstance(obj, dict):
            return obj
        sessions = getattr(obj, "fetch_sessions", None) or []
        # Derive fetch_session_count + last_fetch_at from the relation if loaded.
        try:
            session_count = len(sessions)
            last_fetch = (
                max(
                    (s.created_at for s in sessions if getattr(s, "created_at", None)),
                    default=None,
                )
                if sessions
                else None
            )
        except Exception:
            session_count = 0
            last_fetch = None
        return {
            "id": obj.id,
            "consent_handle": obj.consent_handle,
            "consent_id": obj.consent_id,
            "customer_id": obj.customer_id,
            "customer_name": obj.customer_name,
            "customer_mobile": obj.customer_mobile,
            "provider": obj.provider,
            "purpose": obj.purpose,
            "fi_types": obj.fi_types or [],
            "fi_data_from": obj.fi_data_from,
            "fi_data_to": obj.fi_data_to,
            "status": obj.status,
            "consent_expiry": obj.consent_expiry,
            "entity_name": None,  # joined name is loaded only via detail endpoint
            "loan_application_number": None,
            "fetch_session_count": session_count,
            "last_fetch_at": last_fetch,
            "created_at": obj.created_at,
            "approved_at": obj.approved_at,
            "rejected_at": obj.rejected_at,
            "revoked_at": obj.revoked_at,
        }


class AAConsentDetailResponse(AAConsentResponse):
    """Detailed consent response with fetch sessions."""

    fetch_sessions: list["AAFetchSessionResponse"] = []
    entity_name: str | None = None
    loan_application_number: str | None = None
    loan_account_number: str | None = None


class AAConsentListResponse(CamelSchema):
    """Paginated list of consents."""

    items: list[AAConsentResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class AAConsentRequestInitiate(CamelSchema):
    """Request to initiate a new consent."""

    organization_id: UUID
    entity_id: UUID | None = None
    loan_application_id: UUID | None = None
    loan_account_id: UUID | None = None
    customer_id: str  # VUA or mobile
    customer_name: str | None = None
    customer_mobile: str | None = None
    customer_email: str | None = None
    provider: AAProvider
    purpose: AAConsentPurpose = AAConsentPurpose.UNDERWRITING
    fi_types: list[AAFIType] = [AAFIType.DEPOSIT]
    fi_data_from: date
    fi_data_to: date
    fetch_frequency: AAFetchFrequency = AAFetchFrequency.ONETIME
    consent_validity_months: int = 6
    redirect_url: str | None = None


class AAConsentInitiateResponse(CamelSchema):
    """Response from consent initiation."""

    consent_id: UUID
    consent_handle: str
    consent_url: str
    status: AAConsentStatus
    message: str


class AAConsentRevokeRequest(CamelSchema):
    """Request to revoke a consent."""

    reason: str | None = None


# =============================================================================
# AA Fetch Session Schemas
# =============================================================================


class AAFetchSessionBase(CamelSchema):
    """Base schema for fetch session."""

    fi_types_requested: list[str] = Field(default_factory=list)
    data_from: date | None = None
    data_to: date | None = None


class AAFetchSessionCreate(AAFetchSessionBase):
    """Schema for creating a fetch session."""

    consent_id: UUID
    organization_id: UUID


class AAFetchSessionUpdate(CamelSchema):
    """Schema for updating fetch session."""

    session_id: str | None = None
    data_session_id: str | None = None
    status: AAFetchSessionStatus | None = None
    accounts_received: int | None = None
    accounts_failed: int | None = None
    data_requested_at: datetime | None = None
    data_received_at: datetime | None = None
    completed_at: datetime | None = None
    error_code: str | None = None
    error_message: str | None = None


class AAFetchSessionResponse(AAFetchSessionBase):
    """Response schema for fetch session."""

    id: UUID
    consent_id: UUID
    organization_id: UUID
    session_id: str | None = None
    data_session_id: str | None = None
    status: AAFetchSessionStatus
    total_accounts_requested: int
    accounts_received: int
    accounts_failed: int
    initiated_at: datetime
    data_requested_at: datetime | None = None
    data_received_at: datetime | None = None
    completed_at: datetime | None = None
    error_code: str | None = None
    error_message: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class AAFetchSessionDetailResponse(AAFetchSessionResponse):
    """Detailed fetch session with accounts."""

    bank_accounts: list["AABankAccountResponse"] = []


class AAFetchSessionListResponse(CamelSchema):
    """Paginated list of fetch sessions."""

    items: list[AAFetchSessionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class AAFetchDataRequest(CamelSchema):
    """Request to fetch data for an approved consent."""

    consent_id: UUID
    fi_types: list[AAFIType] | None = None  # None = all approved types
    data_from: date | None = None  # Override consent dates
    data_to: date | None = None


class AAFetchDataResponse(CamelSchema):
    """Response from data fetch initiation."""

    fetch_session_id: UUID
    session_id: str
    status: AAFetchSessionStatus
    message: str


# =============================================================================
# AA Bank Account Schemas
# =============================================================================


class AABankAccountBase(CamelSchema):
    """Base schema for bank account from AA."""

    fi_type: AAFIType = AAFIType.DEPOSIT
    fip_id: str | None = None
    fip_name: str | None = None
    account_type: str | None = None
    account_number_masked: str | None = None
    account_ref_number: str | None = None
    ifsc_code: str | None = None
    branch: str | None = None
    holder_name: str | None = None
    holder_pan: str | None = None
    holder_mobile: str | None = None
    holder_email: str | None = None
    holder_dob: date | None = None
    holder_type: str | None = None
    currency: str = "INR"


class AABankAccountCreate(AABankAccountBase):
    """Schema for creating bank account record."""

    fetch_session_id: UUID
    organization_id: UUID
    entity_id: UUID | None = None
    current_balance: Decimal | None = None
    available_balance: Decimal | None = None
    balance_as_on: datetime | None = None
    opening_date: date | None = None
    maturity_date: date | None = None
    maturity_amount: Decimal | None = None
    interest_rate: Decimal | None = None
    principal_amount: Decimal | None = None
    raw_data: dict[str, Any] | None = None
    profile_data: dict[str, Any] | None = None
    summary_data: dict[str, Any] | None = None
    data_fetched_at: datetime | None = None
    data_from: date | None = None
    data_to: date | None = None


class AABankAccountResponse(AABankAccountBase):
    """Response schema for bank account."""

    id: UUID
    fetch_session_id: UUID
    organization_id: UUID
    entity_id: UUID | None = None
    current_balance: Decimal | None = None
    available_balance: Decimal | None = None
    balance_as_on: datetime | None = None
    opening_date: date | None = None
    maturity_date: date | None = None
    maturity_amount: Decimal | None = None
    interest_rate: Decimal | None = None
    principal_amount: Decimal | None = None
    status: AADataStatus
    data_fetched_at: datetime | None = None
    data_from: date | None = None
    data_to: date | None = None
    transaction_count: int | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class AABankAccountDetailResponse(AABankAccountResponse):
    """Detailed bank account with transactions."""

    transactions: list["AABankTransactionResponse"] = []
    credit_summary: dict[str, Any] | None = None
    debit_summary: dict[str, Any] | None = None


class AABankAccountListResponse(CamelSchema):
    """Paginated list of bank accounts."""

    items: list[AABankAccountResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# =============================================================================
# AA Bank Transaction Schemas
# =============================================================================


class AABankTransactionBase(CamelSchema):
    """Base schema for bank transaction from AA."""

    txn_id: str | None = None
    txn_type: str  # DEBIT, CREDIT
    mode: str | None = None  # UPI, NEFT, IMPS, etc.
    amount: Decimal
    currency: str = "INR"
    balance_after: Decimal | None = None
    transaction_date: date
    transaction_timestamp: datetime | None = None
    value_date: date | None = None
    narration: str | None = None
    reference: str | None = None
    counterparty_name: str | None = None
    counterparty_account: str | None = None
    counterparty_ifsc: str | None = None
    category: str | None = None
    sub_category: str | None = None


class AABankTransactionCreate(AABankTransactionBase):
    """Schema for creating transaction record."""

    bank_account_id: UUID
    organization_id: UUID
    raw_data: dict[str, Any] | None = None


class AABankTransactionResponse(AABankTransactionBase):
    """Response schema for bank transaction."""

    id: UUID
    bank_account_id: UUID
    organization_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class AABankTransactionListResponse(CamelSchema):
    """Paginated list of transactions."""

    items: list[AABankTransactionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# =============================================================================
# AA Consent Log Schemas
# =============================================================================


class AAConsentLogBase(CamelSchema):
    """Base schema for consent log."""

    event_type: str
    old_status: AAConsentStatus | None = None
    new_status: AAConsentStatus | None = None
    source: str | None = None
    message: str | None = None


class AAConsentLogCreate(AAConsentLogBase):
    """Schema for creating consent log entry."""

    consent_id: UUID
    aa_response: dict[str, Any] | None = None
    created_by_id: UUID | None = None


class AAConsentLogResponse(AAConsentLogBase):
    """Response schema for consent log."""

    id: UUID
    consent_id: UUID
    aa_response: dict[str, Any] | None = None
    created_at: datetime
    created_by_id: UUID | None = None

    class Config:
        from_attributes = True


class AAConsentLogListResponse(CamelSchema):
    """List of consent logs."""

    items: list[AAConsentLogResponse]
    total: int


# =============================================================================
# AA Analytics & Reports
# =============================================================================


class AAConsentStatistics(CamelSchema):
    """Statistics for AA consents."""

    total_consents: int
    active_consents: int
    pending_consents: int
    expired_consents: int
    revoked_consents: int
    approval_rate: float
    provider_breakdown: dict[str, int]  # {provider: count}
    purpose_breakdown: dict[str, int]  # {purpose: count}


class AAFetchStatistics(CamelSchema):
    """Statistics for data fetches."""

    total_fetch_sessions: int
    successful_fetches: int
    failed_fetches: int
    total_accounts_fetched: int
    total_transactions_fetched: int
    success_rate: float
    avg_accounts_per_fetch: float
    fi_type_breakdown: dict[str, int]  # {fi_type: count}


class AABankStatementAnalysis(CamelSchema):
    """Analysis of fetched bank statements."""

    entity_id: UUID | None = None
    loan_application_id: UUID | None = None
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
    salary_credits: Decimal | None = None
    emi_debits: Decimal | None = None
    cheque_bounces: int
    high_value_transactions: list[dict[str, Any]]
    category_breakdown: dict[str, dict[str, Any]]  # {category: {count, amount}}


class AADataImportRequest(CamelSchema):
    """Request to import AA data into bank reconciliation."""

    fetch_session_id: UUID
    bank_account_ids: list[UUID] | None = None  # None = all accounts
    target_bank_account_id: UUID  # Organization's bank account to reconcile


class AADataImportResponse(CamelSchema):
    """Response from data import."""

    imported_transactions: int
    matched_transactions: int
    unmatched_transactions: int
    import_errors: list[str]


# =============================================================================
# AA Provider Configuration
# =============================================================================


class AAProviderConfig(CamelSchema):
    """Configuration for AA provider."""

    provider: AAProvider
    client_id: str
    client_secret: str
    entity_id: str  # FIU entity ID
    token_url: str | None = None
    api_base_url: str | None = None
    callback_url: str
    webhook_secret: str | None = None
    sandbox_mode: bool = True


class AAProviderHealthCheck(CamelSchema):
    """Health check response for AA provider."""

    provider: AAProvider
    is_healthy: bool
    response_time_ms: int | None = None
    last_check_at: datetime
    error_message: str | None = None


# =============================================================================
# AA Webhook Schemas
# =============================================================================


class AAWebhookNotification(CamelSchema):
    """Webhook notification from AA provider."""

    notification_type: str  # CONSENT_STATUS, FI_NOTIFICATION, etc.
    consent_handle: str | None = None
    consent_id: str | None = None
    session_id: str | None = None
    status: str | None = None
    timestamp: datetime
    payload: dict[str, Any]


class AAConsentStatusWebhook(CamelSchema):
    """Consent status update webhook."""

    consent_handle: str
    consent_id: str | None = None
    status: str  # ACTIVE, REJECTED, REVOKED, PAUSED, EXPIRED
    reason: str | None = None
    timestamp: datetime


class AAFINotificationWebhook(CamelSchema):
    """FI data notification webhook."""

    consent_id: str
    session_id: str
    status: str  # READY, DENIED, TIMEOUT
    fi_status_response: list[dict[str, Any]] | None = None
    timestamp: datetime


# Update forward references
AAConsentDetailResponse.model_rebuild()
AAFetchSessionDetailResponse.model_rebuild()
AABankAccountDetailResponse.model_rebuild()
