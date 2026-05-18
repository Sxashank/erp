"""TDS Return schemas."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import Field

from app.models.tds.tds_return import Quarter, ReturnStatus, ReturnType
from app.schemas.base import CamelSchema


class DeductorDetails(CamelSchema):
    """Deductor details for return."""

    deductor_tan: str = Field(..., max_length=10)
    deductor_name: str = Field(..., max_length=200)
    deductor_pan: str | None = Field(None, max_length=10)
    deductor_type: str | None = Field(None, max_length=20)
    deductor_category: str | None = Field(None, max_length=5)
    deductor_address: str | None = None
    deductor_city: str | None = Field(None, max_length=100)
    deductor_state: str | None = Field(None, max_length=50)
    deductor_pincode: str | None = Field(None, max_length=10)
    deductor_email: str | None = Field(None, max_length=100)
    deductor_phone: str | None = Field(None, max_length=20)


class ResponsiblePersonDetails(CamelSchema):
    """Responsible person details."""

    responsible_person_name: str | None = Field(None, max_length=200)
    responsible_person_designation: str | None = Field(None, max_length=100)
    responsible_person_address: str | None = None
    responsible_person_pan: str | None = Field(None, max_length=10)


class TDSReturnCreate(CamelSchema):
    """Schema for creating TDS Return."""

    organization_id: UUID
    return_type: ReturnType
    financial_year_id: UUID
    financial_year: str = Field(..., max_length=10)
    quarter: Quarter

    # Deductor details
    deductor_tan: str = Field(..., max_length=10)
    deductor_name: str = Field(..., max_length=200)
    deductor_pan: str | None = Field(None, max_length=10)
    deductor_type: str | None = Field(None, max_length=20)
    deductor_category: str | None = Field(None, max_length=5)
    deductor_address: str | None = None
    deductor_city: str | None = Field(None, max_length=100)
    deductor_state: str | None = Field(None, max_length=50)
    deductor_pincode: str | None = Field(None, max_length=10)
    deductor_email: str | None = Field(None, max_length=100)
    deductor_phone: str | None = Field(None, max_length=20)

    # Responsible person
    responsible_person_name: str | None = Field(None, max_length=200)
    responsible_person_designation: str | None = Field(None, max_length=100)
    responsible_person_address: str | None = None
    responsible_person_pan: str | None = Field(None, max_length=10)

    remarks: str | None = None


class TDSReturnUpdate(CamelSchema):
    """Schema for updating TDS Return."""

    # Deductor details
    deductor_tan: str | None = Field(None, max_length=10)
    deductor_name: str | None = Field(None, max_length=200)
    deductor_pan: str | None = Field(None, max_length=10)
    deductor_type: str | None = Field(None, max_length=20)
    deductor_category: str | None = Field(None, max_length=5)
    deductor_address: str | None = None
    deductor_city: str | None = Field(None, max_length=100)
    deductor_state: str | None = Field(None, max_length=50)
    deductor_pincode: str | None = Field(None, max_length=10)
    deductor_email: str | None = Field(None, max_length=100)
    deductor_phone: str | None = Field(None, max_length=20)

    # Responsible person
    responsible_person_name: str | None = Field(None, max_length=200)
    responsible_person_designation: str | None = Field(None, max_length=100)
    responsible_person_address: str | None = None
    responsible_person_pan: str | None = Field(None, max_length=10)

    remarks: str | None = None


class FilingDetailsUpdate(CamelSchema):
    """Schema for updating filing details."""

    provisional_receipt_number: str | None = Field(None, max_length=50)
    token_number: str | None = Field(None, max_length=50)
    acknowledgment_number: str | None = Field(None, max_length=50)
    filed_date: date | None = None


class ValidationError(CamelSchema):
    """Validation error item."""

    code: str
    message: str
    field: str | None = None
    row: int | None = None


class TDSReturnResponse(CamelSchema):
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
    original_return_id: UUID | None

    # Deductor details
    deductor_tan: str
    deductor_name: str
    deductor_pan: str | None
    deductor_type: str | None
    deductor_category: str | None
    deductor_address: str | None
    deductor_city: str | None
    deductor_state: str | None
    deductor_pincode: str | None
    deductor_email: str | None
    deductor_phone: str | None

    # Responsible person
    responsible_person_name: str | None
    responsible_person_designation: str | None
    responsible_person_address: str | None
    responsible_person_pan: str | None

    # Summary
    total_challans: int
    total_deductees: int
    total_amount_paid: Decimal
    total_tds_deducted: Decimal
    total_tds_deposited: Decimal
    total_interest: Decimal
    total_late_fee: Decimal

    # File generation
    file_generated_at: datetime | None
    file_name: str | None

    # Filing details
    provisional_receipt_number: str | None
    token_number: str | None
    acknowledgment_number: str | None
    filed_date: date | None
    accepted_at: datetime | None

    # Due date
    due_date: date
    is_late: bool
    days_late: int

    # Validation
    validation_errors: list[dict] | None
    validation_warnings: list[dict] | None
    last_validated_at: datetime | None

    remarks: str | None
    created_at: date
    updated_at: date | None
    is_active: bool


class TDSReturnListResponse(CamelSchema):
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
    filed_date: date | None
    acknowledgment_number: str | None
    created_at: date


class ReturnValidationResult(CamelSchema):
    """Return validation result."""

    is_valid: bool
    errors: list[ValidationError] = Field(default_factory=list)
    warnings: list[ValidationError] = Field(default_factory=list)
    total_challans: int
    total_deductees: int
    total_tds_deducted: Decimal
    total_tds_deposited: Decimal


class ReturnFileGenerationRequest(CamelSchema):
    """Request to generate return file."""

    include_nil_return: bool = Field(
        False,
        description="Generate nil return if no transactions",
    )
    file_format: str = Field(
        "TXT",
        description="File format: TXT (NSDL format)",
    )


class ReturnFileResponse(CamelSchema):
    """Return file generation response."""

    file_name: str
    file_size: int
    file_hash: str
    generated_at: datetime
    file_content: str
    artifact_status: str
    statutory_status: str
    compliance_note: str


class RevisionRequest(CamelSchema):
    """Request to create a revision."""

    reason: str = Field(..., description="Reason for revision")


class DeducteeSummary(CamelSchema):
    """Deductee summary for return."""

    deductee_name: str
    deductee_pan: str | None
    tds_section_code: str
    total_amount_paid: Decimal
    total_tds_deducted: Decimal
    transaction_count: int


class ChallanSummary(CamelSchema):
    """Challan summary for return."""

    challan_number: str
    bsr_code: str
    payment_date: date
    total_amount: Decimal
    tds_section_code: str
