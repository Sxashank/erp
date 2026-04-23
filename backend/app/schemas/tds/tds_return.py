"""TDS Return schemas."""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.tds.tds_return import ReturnType, ReturnStatus, Quarter


class DeductorDetails(BaseModel):
    """Deductor details for return."""

    deductor_tan: str = Field(..., max_length=10)
    deductor_name: str = Field(..., max_length=200)
    deductor_pan: Optional[str] = Field(None, max_length=10)
    deductor_type: Optional[str] = Field(None, max_length=20)
    deductor_category: Optional[str] = Field(None, max_length=5)
    deductor_address: Optional[str] = None
    deductor_city: Optional[str] = Field(None, max_length=100)
    deductor_state: Optional[str] = Field(None, max_length=50)
    deductor_pincode: Optional[str] = Field(None, max_length=10)
    deductor_email: Optional[str] = Field(None, max_length=100)
    deductor_phone: Optional[str] = Field(None, max_length=20)


class ResponsiblePersonDetails(BaseModel):
    """Responsible person details."""

    responsible_person_name: Optional[str] = Field(None, max_length=200)
    responsible_person_designation: Optional[str] = Field(None, max_length=100)
    responsible_person_address: Optional[str] = None
    responsible_person_pan: Optional[str] = Field(None, max_length=10)


class TDSReturnCreate(BaseModel):
    """Schema for creating TDS Return."""

    organization_id: UUID
    return_type: ReturnType
    financial_year_id: UUID
    financial_year: str = Field(..., max_length=10)
    quarter: Quarter

    # Deductor details
    deductor_tan: str = Field(..., max_length=10)
    deductor_name: str = Field(..., max_length=200)
    deductor_pan: Optional[str] = Field(None, max_length=10)
    deductor_type: Optional[str] = Field(None, max_length=20)
    deductor_category: Optional[str] = Field(None, max_length=5)
    deductor_address: Optional[str] = None
    deductor_city: Optional[str] = Field(None, max_length=100)
    deductor_state: Optional[str] = Field(None, max_length=50)
    deductor_pincode: Optional[str] = Field(None, max_length=10)
    deductor_email: Optional[str] = Field(None, max_length=100)
    deductor_phone: Optional[str] = Field(None, max_length=20)

    # Responsible person
    responsible_person_name: Optional[str] = Field(None, max_length=200)
    responsible_person_designation: Optional[str] = Field(None, max_length=100)
    responsible_person_address: Optional[str] = None
    responsible_person_pan: Optional[str] = Field(None, max_length=10)

    remarks: Optional[str] = None


class TDSReturnUpdate(BaseModel):
    """Schema for updating TDS Return."""

    # Deductor details
    deductor_tan: Optional[str] = Field(None, max_length=10)
    deductor_name: Optional[str] = Field(None, max_length=200)
    deductor_pan: Optional[str] = Field(None, max_length=10)
    deductor_type: Optional[str] = Field(None, max_length=20)
    deductor_category: Optional[str] = Field(None, max_length=5)
    deductor_address: Optional[str] = None
    deductor_city: Optional[str] = Field(None, max_length=100)
    deductor_state: Optional[str] = Field(None, max_length=50)
    deductor_pincode: Optional[str] = Field(None, max_length=10)
    deductor_email: Optional[str] = Field(None, max_length=100)
    deductor_phone: Optional[str] = Field(None, max_length=20)

    # Responsible person
    responsible_person_name: Optional[str] = Field(None, max_length=200)
    responsible_person_designation: Optional[str] = Field(None, max_length=100)
    responsible_person_address: Optional[str] = None
    responsible_person_pan: Optional[str] = Field(None, max_length=10)

    remarks: Optional[str] = None


class FilingDetailsUpdate(BaseModel):
    """Schema for updating filing details."""

    provisional_receipt_number: Optional[str] = Field(None, max_length=50)
    token_number: Optional[str] = Field(None, max_length=50)
    acknowledgment_number: Optional[str] = Field(None, max_length=50)
    filed_date: Optional[date] = None


class ValidationError(BaseModel):
    """Validation error item."""

    code: str
    message: str
    field: Optional[str] = None
    row: Optional[int] = None


class TDSReturnResponse(BaseModel):
    """TDS Return response schema."""

    id: UUID
    organization_id: UUID
    return_type: ReturnType
    financial_year_id: UUID
    financial_year: str
    assessment_year: str
    quarter: Quarter
    period_from: date
    period_to: date

    # Status
    status: ReturnStatus
    is_original: bool
    revision_number: int
    original_return_id: Optional[UUID]

    # Deductor details
    deductor_tan: str
    deductor_name: str
    deductor_pan: Optional[str]
    deductor_type: Optional[str]
    deductor_category: Optional[str]
    deductor_address: Optional[str]
    deductor_city: Optional[str]
    deductor_state: Optional[str]
    deductor_pincode: Optional[str]
    deductor_email: Optional[str]
    deductor_phone: Optional[str]

    # Responsible person
    responsible_person_name: Optional[str]
    responsible_person_designation: Optional[str]
    responsible_person_address: Optional[str]
    responsible_person_pan: Optional[str]

    # Summary
    total_challans: int
    total_deductees: int
    total_amount_paid: Decimal
    total_tds_deducted: Decimal
    total_tds_deposited: Decimal
    total_interest: Decimal
    total_late_fee: Decimal

    # File generation
    file_generated_at: Optional[datetime]
    file_name: Optional[str]

    # Filing details
    provisional_receipt_number: Optional[str]
    token_number: Optional[str]
    acknowledgment_number: Optional[str]
    filed_date: Optional[date]
    accepted_at: Optional[datetime]

    # Due date
    due_date: date
    is_late: bool
    days_late: int

    # Validation
    validation_errors: Optional[List[dict]]
    validation_warnings: Optional[List[dict]]
    last_validated_at: Optional[datetime]

    remarks: Optional[str]
    created_at: date
    updated_at: Optional[date]
    is_active: bool

    class Config:
        from_attributes = True


class TDSReturnListResponse(BaseModel):
    """TDS Return list response."""

    id: UUID
    organization_id: UUID
    return_type: ReturnType
    financial_year: str
    quarter: Quarter
    period_from: date
    period_to: date
    status: ReturnStatus
    is_original: bool
    revision_number: int
    total_challans: int
    total_deductees: int
    total_tds_deducted: Decimal
    total_tds_deposited: Decimal
    due_date: date
    is_late: bool
    filed_date: Optional[date]
    acknowledgment_number: Optional[str]
    created_at: date

    class Config:
        from_attributes = True


class ReturnValidationResult(BaseModel):
    """Return validation result."""

    is_valid: bool
    errors: List[ValidationError] = []
    warnings: List[ValidationError] = []
    total_challans: int
    total_deductees: int
    total_tds_deducted: Decimal
    total_tds_deposited: Decimal


class ReturnFileGenerationRequest(BaseModel):
    """Request to generate return file."""

    include_nil_return: bool = Field(
        False,
        description="Generate nil return if no transactions",
    )
    file_format: str = Field(
        "TXT",
        description="File format: TXT (NSDL format)",
    )


class ReturnFileResponse(BaseModel):
    """Return file generation response."""

    file_name: str
    file_path: str
    file_size: int
    file_hash: str
    generated_at: datetime


class RevisionRequest(BaseModel):
    """Request to create a revision."""

    reason: str = Field(..., description="Reason for revision")


class DeducteeSummary(BaseModel):
    """Deductee summary for return."""

    deductee_name: str
    deductee_pan: Optional[str]
    tds_section_code: str
    total_amount_paid: Decimal
    total_tds_deducted: Decimal
    transaction_count: int


class ChallanSummary(BaseModel):
    """Challan summary for return."""

    challan_number: str
    bsr_code: str
    payment_date: date
    total_amount: Decimal
    tds_section_code: str
