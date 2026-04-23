"""Vendor Registration Schemas."""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import Field, EmailStr

from app.schemas.base import BaseSchema, AuditSchema
from app.models.vendor_portal.enums import (
    BusinessType,
    RegistrationStatus,
    RegistrationDocumentType,
)


class VendorRegistrationBase(BaseSchema):
    """Base schema for vendor registration."""

    # Company Details
    company_name: str = Field(..., min_length=1, max_length=200)
    trade_name: Optional[str] = Field(None, max_length=200)
    business_type: BusinessType
    incorporation_date: Optional[date] = None
    website: Optional[str] = Field(None, max_length=255)

    # Tax & Registration
    pan: str = Field(..., min_length=10, max_length=10)
    gstin: Optional[str] = Field(None, max_length=15)
    cin: Optional[str] = Field(None, max_length=21)
    msme_number: Optional[str] = Field(None, max_length=20)
    msme_category: Optional[str] = Field(None, max_length=20)

    # Address
    registered_address: str = Field(..., min_length=1)
    city: str = Field(..., max_length=100)
    state: str = Field(..., max_length=100)
    state_code: Optional[str] = Field(None, max_length=2)
    pincode: str = Field(..., max_length=10)
    country: str = Field(default="India", max_length=50)

    # Contact
    contact_name: str = Field(..., max_length=100)
    contact_email: EmailStr
    contact_phone: str = Field(..., max_length=15)
    contact_designation: Optional[str] = Field(None, max_length=100)

    # Bank Details
    bank_name: str = Field(..., max_length=100)
    bank_branch: str = Field(..., max_length=100)
    account_number: str = Field(..., max_length=50)
    ifsc_code: str = Field(..., min_length=11, max_length=11)
    account_holder_name: Optional[str] = Field(None, max_length=200)

    # Products/Services
    product_categories: Optional[List[str]] = None
    product_description: Optional[str] = None
    service_areas: Optional[List[str]] = None

    # Additional Info
    annual_turnover: Optional[str] = Field(None, max_length=50)
    employee_count: Optional[int] = Field(None, ge=0)
    years_in_business: Optional[int] = Field(None, ge=0)
    key_clients: Optional[str] = None
    certifications: Optional[List[str]] = None


class VendorRegistrationCreate(VendorRegistrationBase):
    """Create vendor registration."""

    organization_id: UUID
    terms_accepted: bool = False


class VendorRegistrationUpdate(BaseSchema):
    """Update vendor registration."""

    company_name: Optional[str] = Field(None, max_length=200)
    trade_name: Optional[str] = Field(None, max_length=200)
    business_type: Optional[BusinessType] = None
    incorporation_date: Optional[date] = None
    website: Optional[str] = Field(None, max_length=255)

    pan: Optional[str] = Field(None, max_length=10)
    gstin: Optional[str] = Field(None, max_length=15)
    cin: Optional[str] = Field(None, max_length=21)
    msme_number: Optional[str] = Field(None, max_length=20)
    msme_category: Optional[str] = Field(None, max_length=20)

    registered_address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    state_code: Optional[str] = Field(None, max_length=2)
    pincode: Optional[str] = Field(None, max_length=10)

    contact_name: Optional[str] = Field(None, max_length=100)
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = Field(None, max_length=15)
    contact_designation: Optional[str] = Field(None, max_length=100)

    bank_name: Optional[str] = Field(None, max_length=100)
    bank_branch: Optional[str] = Field(None, max_length=100)
    account_number: Optional[str] = Field(None, max_length=50)
    ifsc_code: Optional[str] = Field(None, max_length=11)
    account_holder_name: Optional[str] = Field(None, max_length=200)

    product_categories: Optional[List[str]] = None
    product_description: Optional[str] = None
    service_areas: Optional[List[str]] = None

    annual_turnover: Optional[str] = Field(None, max_length=50)
    employee_count: Optional[int] = Field(None, ge=0)
    years_in_business: Optional[int] = Field(None, ge=0)
    key_clients: Optional[str] = None
    certifications: Optional[List[str]] = None

    additional_info_response: Optional[str] = None


class VendorRegistrationSubmit(BaseSchema):
    """Submit registration for review."""

    terms_accepted: bool = True
    terms_version: str = Field(default="1.0", max_length=20)


class VendorRegistrationDocumentCreate(BaseSchema):
    """Create registration document."""

    document_type: RegistrationDocumentType
    document_name: str = Field(..., max_length=255)
    document_number: Optional[str] = Field(None, max_length=100)
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None


class VendorRegistrationDocumentResponse(BaseSchema):
    """Registration document response."""

    id: UUID
    registration_id: UUID
    document_type: RegistrationDocumentType
    document_name: str
    file_path: str
    file_size: int
    mime_type: str
    document_number: Optional[str] = None
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    is_verified: bool
    verified_at: Optional[datetime] = None
    verification_remarks: Optional[str] = None
    is_rejected: bool
    rejection_reason: Optional[str] = None
    created_at: datetime


class VendorRegistrationResponse(VendorRegistrationBase, AuditSchema):
    """Vendor registration response."""

    id: UUID
    organization_id: UUID
    registration_number: str
    status: RegistrationStatus
    submitted_at: Optional[datetime] = None
    reviewed_at: Optional[datetime] = None
    review_remarks: Optional[str] = None
    additional_info_requested_at: Optional[datetime] = None
    additional_info_request: Optional[str] = None
    additional_info_response: Optional[str] = None
    rejection_reason: Optional[str] = None
    approved_at: Optional[datetime] = None
    vendor_id: Optional[UUID] = None
    terms_accepted: bool
    terms_accepted_at: Optional[datetime] = None
    documents: List[VendorRegistrationDocumentResponse] = []


class VendorRegistrationListResponse(BaseSchema):
    """Registration list item response."""

    id: UUID
    registration_number: str
    company_name: str
    pan: str
    gstin: Optional[str] = None
    contact_email: str
    status: RegistrationStatus
    submitted_at: Optional[datetime] = None
    created_at: datetime
