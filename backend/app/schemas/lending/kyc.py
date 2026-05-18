"""KYC schemas for the lending module."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import Field, field_validator

from app.models.lending.enums import (
    BureauPullStatus,
    BureauType,
    CKYCTransactionType,
    EntityType,
    KYCDocCategory,
    KYCVerificationMethod,
    KYCVerificationStatus,
)
from app.schemas.base import BaseSchema, CamelSchema

# =============================================================================
# KYC Document Type Schemas
# =============================================================================


class KYCDocumentTypeBase(BaseSchema):
    """Base schema for KYC document type."""

    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    category: KYCDocCategory
    applicable_entity_types: list[EntityType] = []
    is_mandatory: bool = False
    validity_days: int | None = Field(None, ge=1, description="Validity period in days")
    verification_required: bool = True
    sample_document_url: str | None = Field(None, max_length=500)
    guidelines: str | None = None


class KYCDocumentTypeCreate(KYCDocumentTypeBase):
    """Schema for creating KYC document type."""

    organization_id: UUID


class KYCDocumentTypeUpdate(BaseSchema):
    """Schema for updating KYC document type."""

    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    category: KYCDocCategory | None = None
    applicable_entity_types: list[EntityType] | None = None
    is_mandatory: bool | None = None
    validity_days: int | None = Field(None, ge=1)
    verification_required: bool | None = None
    sample_document_url: str | None = Field(None, max_length=500)
    guidelines: str | None = None
    is_active: bool | None = None


class KYCDocumentTypeResponse(KYCDocumentTypeBase):
    """Schema for KYC document type response."""

    id: UUID
    organization_id: UUID
    created_at: datetime
    updated_at: datetime | None = None
    is_active: bool = True


# =============================================================================
# Entity KYC Document Schemas
# =============================================================================


class EntityKYCDocumentBase(CamelSchema):
    """Base schema for entity KYC document."""

    document_type_id: UUID
    document_number: str | None = Field(None, max_length=100)
    document_name: str | None = Field(None, max_length=200)
    issue_date: date | None = None
    expiry_date: date | None = None
    file_path: str | None = Field(None, max_length=500)
    file_name: str | None = Field(None, max_length=200)
    file_size_bytes: int | None = Field(None, ge=0)
    file_mime_type: str | None = Field(None, max_length=100)
    verification_status: KYCVerificationStatus = KYCVerificationStatus.PENDING
    verification_method: KYCVerificationMethod | None = None
    verified_by_id: UUID | None = None
    verified_at: datetime | None = None
    rejection_reason: str | None = None
    remarks: str | None = None
    ocr_extracted_data: dict[str, Any] | None = None
    ocr_confidence_score: Decimal | None = Field(None, ge=0, le=100)


class EntityKYCDocumentCreate(EntityKYCDocumentBase):
    """Schema for creating entity KYC document."""

    entity_id: UUID


class EntityKYCDocumentUpdate(CamelSchema):
    """Schema for updating entity KYC document."""

    document_number: str | None = Field(None, max_length=100)
    document_name: str | None = Field(None, max_length=200)
    issue_date: date | None = None
    expiry_date: date | None = None
    file_path: str | None = Field(None, max_length=500)
    file_name: str | None = Field(None, max_length=200)
    file_size_bytes: int | None = Field(None, ge=0)
    file_mime_type: str | None = Field(None, max_length=100)
    verification_status: KYCVerificationStatus | None = None
    verification_method: KYCVerificationMethod | None = None
    verified_by_id: UUID | None = None
    verified_at: datetime | None = None
    rejection_reason: str | None = None
    remarks: str | None = None
    ocr_extracted_data: dict[str, Any] | None = None
    ocr_confidence_score: Decimal | None = Field(None, ge=0, le=100)
    is_active: bool | None = None


class EntityKYCDocumentResponse(EntityKYCDocumentBase):
    """Schema for entity KYC document response."""

    id: UUID
    entity_id: UUID
    created_at: datetime
    updated_at: datetime | None = None
    is_active: bool = True


# =============================================================================
# CKYC Transaction Schemas
# =============================================================================


class CKYCSearchRequest(BaseSchema):
    """Schema for CKYC search request."""

    entity_id: UUID
    pan: str = Field(..., min_length=10, max_length=10)
    date_of_birth: date | None = None
    mobile_number: str | None = Field(None, max_length=15)

    @field_validator("pan")
    @classmethod
    def validate_pan(cls, v: str) -> str:
        return v.upper().strip()


class CKYCDownloadRequest(BaseSchema):
    """Schema for CKYC download request."""

    entity_id: UUID
    ckyc_number: str = Field(..., min_length=1, max_length=20)


class CKYCTransactionResponse(BaseSchema):
    """Schema for CKYC transaction response."""

    id: UUID
    entity_id: UUID
    transaction_type: CKYCTransactionType
    request_id: str | None = None
    ckyc_number: str | None = None
    search_pan: str | None = None
    search_dob: date | None = None
    search_mobile: str | None = None
    request_payload: dict[str, Any] | None = None
    response_payload: dict[str, Any] | None = None
    status: str
    error_code: str | None = None
    error_message: str | None = None
    initiated_by_id: UUID | None = None
    initiated_at: datetime
    completed_at: datetime | None = None
    created_at: datetime


# =============================================================================
# Bureau Pull Schemas
# =============================================================================


class BureauPullRequest(BaseSchema):
    """Schema for bureau pull request."""

    entity_id: UUID
    bureau_type: BureauType
    consent_id: str | None = Field(None, max_length=100)
    consent_timestamp: datetime | None = None
    purpose: str = Field(default="LOAN_APPLICATION", max_length=50)
    inquiry_amount: Decimal | None = Field(None, ge=0)

    # For individual/personal bureaus
    pan: str | None = Field(None, max_length=10)
    name: str | None = Field(None, max_length=200)
    date_of_birth: date | None = None
    mobile: str | None = Field(None, max_length=15)
    email: str | None = Field(None, max_length=100)

    # For company bureau
    cin: str | None = Field(None, max_length=25)

    @field_validator("pan")
    @classmethod
    def validate_pan(cls, v: str | None) -> str | None:
        if v:
            return v.upper().strip()
        return v


class BureauPullResponse(BaseSchema):
    """Schema for bureau pull response."""

    id: UUID
    entity_id: UUID
    bureau_type: BureauType
    pull_reference_number: str | None = None
    consent_id: str | None = None
    consent_timestamp: datetime | None = None
    request_payload: dict[str, Any] | None = None
    status: BureauPullStatus
    error_code: str | None = None
    error_message: str | None = None
    initiated_by_id: UUID | None = None
    initiated_at: datetime
    completed_at: datetime | None = None
    report_valid_till: date | None = None
    created_at: datetime
    updated_at: datetime | None = None


class BureauReportResponse(BaseSchema):
    """Schema for bureau report response."""

    id: UUID
    bureau_pull_id: UUID
    report_reference_number: str | None = None
    report_date: date | None = None
    report_version: str | None = None

    # Scores
    credit_score: int | None = None
    score_version: str | None = None
    score_factors: list[str] | None = None

    # Account Summary
    total_accounts: int | None = None
    active_accounts: int | None = None
    closed_accounts: int | None = None
    overdue_accounts: int | None = None
    zero_balance_accounts: int | None = None

    # DPD History
    current_balance: Decimal | None = None
    sanctioned_amount: Decimal | None = None
    overdue_amount: Decimal | None = None
    written_off_amount: Decimal | None = None
    dpd_history: dict[str, Any] | None = None

    # Enquiry Details
    enquiry_count_30_days: int | None = None
    enquiry_count_90_days: int | None = None
    enquiry_count_180_days: int | None = None
    enquiry_count_365_days: int | None = None

    # Other flags
    suit_filed_status: str | None = None
    wilful_defaulter: bool = False
    fraud_indicator: bool = False

    # Raw data
    raw_report: dict[str, Any] | None = None
    parsed_report: dict[str, Any] | None = None
    report_pdf_path: str | None = None

    created_at: datetime
    updated_at: datetime | None = None
