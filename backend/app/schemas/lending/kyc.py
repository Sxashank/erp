"""KYC schemas for the lending module."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import Field, field_validator

from app.schemas.base import BaseSchema
from app.models.lending.enums import (
    KYCDocCategory,
    KYCVerificationStatus,
    KYCVerificationMethod,
    CKYCTransactionType,
    BureauType,
    BureauPullStatus,
    EntityType,
)


# =============================================================================
# KYC Document Type Schemas
# =============================================================================


class KYCDocumentTypeBase(BaseSchema):
    """Base schema for KYC document type."""

    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    category: KYCDocCategory
    applicable_entity_types: List[EntityType] = []
    is_mandatory: bool = False
    validity_days: Optional[int] = Field(None, ge=1, description="Validity period in days")
    verification_required: bool = True
    sample_document_url: Optional[str] = Field(None, max_length=500)
    guidelines: Optional[str] = None


class KYCDocumentTypeCreate(KYCDocumentTypeBase):
    """Schema for creating KYC document type."""

    organization_id: UUID


class KYCDocumentTypeUpdate(BaseSchema):
    """Schema for updating KYC document type."""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    category: Optional[KYCDocCategory] = None
    applicable_entity_types: Optional[List[EntityType]] = None
    is_mandatory: Optional[bool] = None
    validity_days: Optional[int] = Field(None, ge=1)
    verification_required: Optional[bool] = None
    sample_document_url: Optional[str] = Field(None, max_length=500)
    guidelines: Optional[str] = None
    is_active: Optional[bool] = None


class KYCDocumentTypeResponse(KYCDocumentTypeBase):
    """Schema for KYC document type response."""

    id: UUID
    organization_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = True


# =============================================================================
# Entity KYC Document Schemas
# =============================================================================


class EntityKYCDocumentBase(BaseSchema):
    """Base schema for entity KYC document."""

    document_type_id: UUID
    document_number: Optional[str] = Field(None, max_length=100)
    document_name: Optional[str] = Field(None, max_length=200)
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    issuing_authority: Optional[str] = Field(None, max_length=200)
    file_path: Optional[str] = Field(None, max_length=500)
    file_name: Optional[str] = Field(None, max_length=200)
    file_size_kb: Optional[int] = Field(None, ge=0)
    mime_type: Optional[str] = Field(None, max_length=100)
    verification_status: KYCVerificationStatus = KYCVerificationStatus.PENDING
    verification_method: Optional[KYCVerificationMethod] = None
    verified_by_id: Optional[UUID] = None
    verified_at: Optional[datetime] = None
    verification_remarks: Optional[str] = None
    rejection_reason: Optional[str] = None
    extracted_data: Optional[Dict[str, Any]] = None
    ocr_confidence_score: Optional[Decimal] = Field(None, ge=0, le=100)


class EntityKYCDocumentCreate(EntityKYCDocumentBase):
    """Schema for creating entity KYC document."""

    entity_id: UUID


class EntityKYCDocumentUpdate(BaseSchema):
    """Schema for updating entity KYC document."""

    document_number: Optional[str] = Field(None, max_length=100)
    document_name: Optional[str] = Field(None, max_length=200)
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    issuing_authority: Optional[str] = Field(None, max_length=200)
    file_path: Optional[str] = Field(None, max_length=500)
    file_name: Optional[str] = Field(None, max_length=200)
    file_size_kb: Optional[int] = Field(None, ge=0)
    mime_type: Optional[str] = Field(None, max_length=100)
    verification_status: Optional[KYCVerificationStatus] = None
    verification_method: Optional[KYCVerificationMethod] = None
    verified_by_id: Optional[UUID] = None
    verified_at: Optional[datetime] = None
    verification_remarks: Optional[str] = None
    rejection_reason: Optional[str] = None
    extracted_data: Optional[Dict[str, Any]] = None
    ocr_confidence_score: Optional[Decimal] = Field(None, ge=0, le=100)
    is_active: Optional[bool] = None


class EntityKYCDocumentResponse(EntityKYCDocumentBase):
    """Schema for entity KYC document response."""

    id: UUID
    entity_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = True


# =============================================================================
# CKYC Transaction Schemas
# =============================================================================


class CKYCSearchRequest(BaseSchema):
    """Schema for CKYC search request."""

    entity_id: UUID
    pan: str = Field(..., min_length=10, max_length=10)
    date_of_birth: Optional[date] = None
    mobile_number: Optional[str] = Field(None, max_length=15)

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
    request_id: Optional[str] = None
    ckyc_number: Optional[str] = None
    search_pan: Optional[str] = None
    search_dob: Optional[date] = None
    search_mobile: Optional[str] = None
    request_payload: Optional[Dict[str, Any]] = None
    response_payload: Optional[Dict[str, Any]] = None
    status: str
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    initiated_by_id: Optional[UUID] = None
    initiated_at: datetime
    completed_at: Optional[datetime] = None
    created_at: datetime


# =============================================================================
# Bureau Pull Schemas
# =============================================================================


class BureauPullRequest(BaseSchema):
    """Schema for bureau pull request."""

    entity_id: UUID
    bureau_type: BureauType
    consent_id: Optional[str] = Field(None, max_length=100)
    consent_timestamp: Optional[datetime] = None
    purpose: str = Field(default="LOAN_APPLICATION", max_length=50)
    inquiry_amount: Optional[Decimal] = Field(None, ge=0)

    # For individual/personal bureaus
    pan: Optional[str] = Field(None, max_length=10)
    name: Optional[str] = Field(None, max_length=200)
    date_of_birth: Optional[date] = None
    mobile: Optional[str] = Field(None, max_length=15)
    email: Optional[str] = Field(None, max_length=100)

    # For company bureau
    cin: Optional[str] = Field(None, max_length=25)

    @field_validator("pan")
    @classmethod
    def validate_pan(cls, v: Optional[str]) -> Optional[str]:
        if v:
            return v.upper().strip()
        return v


class BureauPullResponse(BaseSchema):
    """Schema for bureau pull response."""

    id: UUID
    entity_id: UUID
    bureau_type: BureauType
    pull_reference_number: Optional[str] = None
    consent_id: Optional[str] = None
    consent_timestamp: Optional[datetime] = None
    request_payload: Optional[Dict[str, Any]] = None
    status: BureauPullStatus
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    initiated_by_id: Optional[UUID] = None
    initiated_at: datetime
    completed_at: Optional[datetime] = None
    report_valid_till: Optional[date] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class BureauReportResponse(BaseSchema):
    """Schema for bureau report response."""

    id: UUID
    bureau_pull_id: UUID
    report_reference_number: Optional[str] = None
    report_date: Optional[date] = None
    report_version: Optional[str] = None

    # Scores
    credit_score: Optional[int] = None
    score_version: Optional[str] = None
    score_factors: Optional[List[str]] = None

    # Account Summary
    total_accounts: Optional[int] = None
    active_accounts: Optional[int] = None
    closed_accounts: Optional[int] = None
    overdue_accounts: Optional[int] = None
    zero_balance_accounts: Optional[int] = None

    # DPD History
    current_balance: Optional[Decimal] = None
    sanctioned_amount: Optional[Decimal] = None
    overdue_amount: Optional[Decimal] = None
    written_off_amount: Optional[Decimal] = None
    dpd_history: Optional[Dict[str, Any]] = None

    # Enquiry Details
    enquiry_count_30_days: Optional[int] = None
    enquiry_count_90_days: Optional[int] = None
    enquiry_count_180_days: Optional[int] = None
    enquiry_count_365_days: Optional[int] = None

    # Other flags
    suit_filed_status: Optional[str] = None
    wilful_defaulter: bool = False
    fraud_indicator: bool = False

    # Raw data
    raw_report: Optional[Dict[str, Any]] = None
    parsed_report: Optional[Dict[str, Any]] = None
    report_pdf_path: Optional[str] = None

    created_at: datetime
    updated_at: Optional[datetime] = None
