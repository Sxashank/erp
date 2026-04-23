"""Pydantic schemas for Employee and related models."""

from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, EmailStr, field_validator

from app.core.constants import (
    Gender,
    MaritalStatus,
    Salutation,
    EmploymentType,
    EmploymentStatus,
    DocumentType,
    FamilyRelation,
    EducationLevel,
    LifecycleEventType,
)
from app.core.pii import MaskedPIIModel


# ============================================
# Address Schema
# ============================================
class AddressSchema(BaseModel):
    """Address schema for JSONB storage."""
    line1: str = Field(..., max_length=200)
    line2: Optional[str] = Field(None, max_length=200)
    city: str = Field(..., max_length=100)
    state: str = Field(..., max_length=100)
    pincode: str = Field(..., max_length=10)
    country: str = Field("India", max_length=100)


# ============================================
# Employee Document Schemas
# ============================================
class EmployeeDocumentBase(BaseModel):
    """Base schema for employee document."""
    document_type: DocumentType
    document_number: Optional[str] = Field(None, max_length=100)
    document_name: str = Field(..., max_length=200)
    file_url: str = Field(..., max_length=500)
    file_type: Optional[str] = Field(None, max_length=50)
    file_size: Optional[int] = None
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    remarks: Optional[str] = None


class EmployeeDocumentCreate(EmployeeDocumentBase):
    """Schema for creating employee document."""
    pass


class EmployeeDocumentUpdate(BaseModel):
    """Schema for updating employee document."""
    document_type: Optional[DocumentType] = None
    document_number: Optional[str] = None
    document_name: Optional[str] = None
    file_url: Optional[str] = None
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    is_verified: Optional[bool] = None
    remarks: Optional[str] = None


class EmployeeDocumentResponse(EmployeeDocumentBase):
    """Response schema for employee document."""
    id: UUID
    employee_id: UUID
    is_verified: bool
    verified_at: Optional[date] = None

    class Config:
        from_attributes = True


# ============================================
# Employee Family Schemas
# ============================================
class EmployeeFamilyBase(BaseModel):
    """Base schema for employee family."""
    relation: FamilyRelation
    name: str = Field(..., max_length=200)
    date_of_birth: Optional[date] = None
    gender: Optional[Gender] = None
    occupation: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    is_dependent: bool = False
    is_nominee: bool = False
    nominee_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    is_emergency_contact: bool = False
    aadhaar_number: Optional[str] = Field(None, max_length=12)


class EmployeeFamilyCreate(EmployeeFamilyBase):
    """Schema for creating employee family."""
    pass


class EmployeeFamilyUpdate(BaseModel):
    """Schema for updating employee family."""
    relation: Optional[FamilyRelation] = None
    name: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[Gender] = None
    occupation: Optional[str] = None
    phone: Optional[str] = None
    is_dependent: Optional[bool] = None
    is_nominee: Optional[bool] = None
    nominee_percentage: Optional[Decimal] = None
    is_emergency_contact: Optional[bool] = None
    aadhaar_number: Optional[str] = None


class EmployeeFamilyResponse(EmployeeFamilyBase):
    """Response schema for employee family."""
    id: UUID
    employee_id: UUID

    class Config:
        from_attributes = True


# ============================================
# Employee Bank Account Schemas
# ============================================
class EmployeeBankAccountBase(BaseModel):
    """Base schema for employee bank account."""
    bank_name: str = Field(..., max_length=200)
    branch_name: Optional[str] = Field(None, max_length=200)
    account_number: str = Field(..., max_length=30)
    ifsc_code: str = Field(..., max_length=11)
    account_holder_name: str = Field(..., max_length=200)
    account_type: Optional[str] = Field("SAVINGS", max_length=20)
    is_primary: bool = False
    is_salary_account: bool = True


class EmployeeBankAccountCreate(EmployeeBankAccountBase):
    """Schema for creating employee bank account."""
    pass


class EmployeeBankAccountUpdate(BaseModel):
    """Schema for updating employee bank account."""
    bank_name: Optional[str] = None
    branch_name: Optional[str] = None
    account_number: Optional[str] = None
    ifsc_code: Optional[str] = None
    account_holder_name: Optional[str] = None
    account_type: Optional[str] = None
    is_primary: Optional[bool] = None
    is_salary_account: Optional[bool] = None
    is_verified: Optional[bool] = None


class EmployeeBankAccountResponse(EmployeeBankAccountBase):
    """Response schema for employee bank account."""
    id: UUID
    employee_id: UUID
    is_verified: bool
    verified_at: Optional[date] = None

    class Config:
        from_attributes = True


# ============================================
# Employee Education Schemas
# ============================================
class EmployeeEducationBase(BaseModel):
    """Base schema for employee education."""
    level: EducationLevel
    degree_name: str = Field(..., max_length=200)
    specialization: Optional[str] = Field(None, max_length=200)
    institution_name: str = Field(..., max_length=300)
    university_board: Optional[str] = Field(None, max_length=200)
    start_year: Optional[int] = None
    end_year: Optional[int] = None
    percentage_cgpa: Optional[Decimal] = Field(None, ge=0, le=100)
    grade: Optional[str] = Field(None, max_length=20)
    is_highest_qualification: bool = False
    document_url: Optional[str] = None


class EmployeeEducationCreate(EmployeeEducationBase):
    """Schema for creating employee education."""
    pass


class EmployeeEducationUpdate(BaseModel):
    """Schema for updating employee education."""
    level: Optional[EducationLevel] = None
    degree_name: Optional[str] = None
    specialization: Optional[str] = None
    institution_name: Optional[str] = None
    university_board: Optional[str] = None
    start_year: Optional[int] = None
    end_year: Optional[int] = None
    percentage_cgpa: Optional[Decimal] = None
    grade: Optional[str] = None
    is_highest_qualification: Optional[bool] = None
    document_url: Optional[str] = None


class EmployeeEducationResponse(EmployeeEducationBase):
    """Response schema for employee education."""
    id: UUID
    employee_id: UUID

    class Config:
        from_attributes = True


# ============================================
# Employee Experience Schemas
# ============================================
class EmployeeExperienceBase(BaseModel):
    """Base schema for employee experience."""
    company_name: str = Field(..., max_length=300)
    designation: str = Field(..., max_length=200)
    department: Optional[str] = Field(None, max_length=200)
    location: Optional[str] = Field(None, max_length=200)
    start_date: date
    end_date: Optional[date] = None
    is_current: bool = False
    last_ctc: Optional[Decimal] = None
    reason_for_leaving: Optional[str] = None
    reference_name: Optional[str] = None
    reference_phone: Optional[str] = None
    reference_email: Optional[EmailStr] = None
    experience_letter_url: Optional[str] = None
    relieving_letter_url: Optional[str] = None


class EmployeeExperienceCreate(EmployeeExperienceBase):
    """Schema for creating employee experience."""
    pass


class EmployeeExperienceUpdate(BaseModel):
    """Schema for updating employee experience."""
    company_name: Optional[str] = None
    designation: Optional[str] = None
    department: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_current: Optional[bool] = None
    last_ctc: Optional[Decimal] = None
    reason_for_leaving: Optional[str] = None
    reference_name: Optional[str] = None
    reference_phone: Optional[str] = None
    reference_email: Optional[EmailStr] = None
    experience_letter_url: Optional[str] = None
    relieving_letter_url: Optional[str] = None


class EmployeeExperienceResponse(EmployeeExperienceBase):
    """Response schema for employee experience."""
    id: UUID
    employee_id: UUID
    duration_months: Optional[int] = None

    class Config:
        from_attributes = True


# ============================================
# Employee Statutory Schemas
# ============================================
class EmployeeStatutoryBase(BaseModel):
    """Base schema for employee statutory."""
    # PF
    pf_applicable: bool = True
    pf_account_number: Optional[str] = Field(None, max_length=30)
    pf_join_date: Optional[date] = None
    pf_exit_date: Optional[date] = None
    is_pf_capped: bool = True
    voluntary_pf_rate: Optional[Decimal] = Field(None, ge=0, le=100)

    # ESI
    esi_applicable: bool = False
    esi_number: Optional[str] = Field(None, max_length=17)
    esi_dispensary: Optional[str] = None

    # PT
    pt_applicable: bool = True
    pt_state: Optional[str] = None
    pt_location: Optional[str] = None

    # LWF
    lwf_applicable: bool = False

    # Tax
    tax_regime: Optional[str] = Field("NEW", max_length=10)
    it_section_declarations: Optional[Dict[str, Any]] = None

    # Gratuity
    gratuity_applicable: bool = True


class EmployeeStatutoryCreate(EmployeeStatutoryBase):
    """Schema for creating employee statutory."""
    pass


class EmployeeStatutoryUpdate(BaseModel):
    """Schema for updating employee statutory."""
    pf_applicable: Optional[bool] = None
    pf_account_number: Optional[str] = None
    pf_join_date: Optional[date] = None
    pf_exit_date: Optional[date] = None
    is_pf_capped: Optional[bool] = None
    voluntary_pf_rate: Optional[Decimal] = None
    esi_applicable: Optional[bool] = None
    esi_number: Optional[str] = None
    esi_dispensary: Optional[str] = None
    pt_applicable: Optional[bool] = None
    pt_state: Optional[str] = None
    pt_location: Optional[str] = None
    lwf_applicable: Optional[bool] = None
    tax_regime: Optional[str] = None
    it_section_declarations: Optional[Dict[str, Any]] = None
    gratuity_applicable: Optional[bool] = None


class EmployeeStatutoryResponse(EmployeeStatutoryBase):
    """Response schema for employee statutory."""
    id: UUID
    employee_id: UUID

    class Config:
        from_attributes = True


# ============================================
# Employee Lifecycle Event Schemas
# ============================================
class EmployeeLifecycleEventBase(BaseModel):
    """Base schema for lifecycle event."""
    event_type: LifecycleEventType
    event_date: date
    effective_date: date
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    from_department_id: Optional[UUID] = None
    to_department_id: Optional[UUID] = None
    from_designation_id: Optional[UUID] = None
    to_designation_id: Optional[UUID] = None
    from_unit_id: Optional[UUID] = None
    to_unit_id: Optional[UUID] = None
    document_reference: Optional[str] = None
    document_url: Optional[str] = None
    remarks: Optional[str] = None


class EmployeeLifecycleEventCreate(EmployeeLifecycleEventBase):
    """Schema for creating lifecycle event."""
    pass


class EmployeeLifecycleEventResponse(EmployeeLifecycleEventBase):
    """Response schema for lifecycle event."""
    id: UUID
    employee_id: UUID
    approved_by: Optional[UUID] = None
    approved_at: Optional[date] = None

    class Config:
        from_attributes = True


# ============================================
# Main Employee Schemas
# ============================================
class EmployeeBase(BaseModel):
    """Base schema for employee."""
    # Personal Info
    salutation: Optional[Salutation] = None
    first_name: str = Field(..., max_length=100)
    middle_name: Optional[str] = Field(None, max_length=100)
    last_name: str = Field(..., max_length=100)
    display_name: Optional[str] = Field(None, max_length=200)
    gender: Gender
    date_of_birth: date
    blood_group: Optional[str] = Field(None, max_length=5)
    marital_status: Optional[MaritalStatus] = None
    nationality: Optional[str] = Field("Indian", max_length=50)

    # Contact
    personal_email: Optional[EmailStr] = None
    personal_mobile: str = Field(..., max_length=20)
    official_email: Optional[EmailStr] = None
    official_mobile: Optional[str] = Field(None, max_length=20)

    # Emergency Contact
    emergency_contact_name: Optional[str] = Field(None, max_length=200)
    emergency_contact_phone: Optional[str] = Field(None, max_length=20)
    emergency_contact_relation: Optional[str] = Field(None, max_length=50)

    # Address
    current_address: Optional[AddressSchema] = None
    permanent_address: Optional[AddressSchema] = None
    is_address_same: bool = False

    # Photo
    photo_url: Optional[str] = None

    # Organization
    department_id: Optional[UUID] = None
    designation_id: Optional[UUID] = None
    reporting_manager_id: Optional[UUID] = None
    unit_id: Optional[UUID] = None
    cost_center_id: Optional[UUID] = None

    # Employment
    date_of_joining: date
    confirmation_date: Optional[date] = None
    probation_end_date: Optional[date] = None
    employment_type: EmploymentType = EmploymentType.PERMANENT
    notice_period_days: int = 30

    # Shift
    shift_id: Optional[UUID] = None
    week_off_days: Optional[List[str]] = Field(default=["SUNDAY"])

    # IDs
    pan_number: Optional[str] = Field(None, max_length=10)
    aadhaar_number: Optional[str] = Field(None, max_length=12)
    uan_number: Optional[str] = Field(None, max_length=12)
    esic_number: Optional[str] = Field(None, max_length=17)


class EmployeeCreate(EmployeeBase):
    """Schema for creating employee."""
    organization_id: UUID
    employee_code: Optional[str] = Field(None, max_length=20)  # Auto-generate if not provided

    # Nested creates (optional)
    documents: Optional[List[EmployeeDocumentCreate]] = None
    family_members: Optional[List[EmployeeFamilyCreate]] = None
    bank_accounts: Optional[List[EmployeeBankAccountCreate]] = None
    education: Optional[List[EmployeeEducationCreate]] = None
    experience: Optional[List[EmployeeExperienceCreate]] = None
    statutory_info: Optional[EmployeeStatutoryCreate] = None


class EmployeeUpdate(BaseModel):
    """Schema for updating employee."""
    # Personal Info
    salutation: Optional[Salutation] = None
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    display_name: Optional[str] = None
    gender: Optional[Gender] = None
    date_of_birth: Optional[date] = None
    blood_group: Optional[str] = None
    marital_status: Optional[MaritalStatus] = None
    nationality: Optional[str] = None

    # Contact
    personal_email: Optional[EmailStr] = None
    personal_mobile: Optional[str] = None
    official_email: Optional[EmailStr] = None
    official_mobile: Optional[str] = None

    # Emergency Contact
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relation: Optional[str] = None

    # Address
    current_address: Optional[AddressSchema] = None
    permanent_address: Optional[AddressSchema] = None
    is_address_same: Optional[bool] = None

    # Photo
    photo_url: Optional[str] = None

    # Organization
    department_id: Optional[UUID] = None
    designation_id: Optional[UUID] = None
    reporting_manager_id: Optional[UUID] = None
    unit_id: Optional[UUID] = None
    cost_center_id: Optional[UUID] = None

    # Employment
    confirmation_date: Optional[date] = None
    probation_end_date: Optional[date] = None
    employment_type: Optional[EmploymentType] = None
    employment_status: Optional[EmploymentStatus] = None
    notice_period_days: Optional[int] = None
    date_of_leaving: Optional[date] = None

    # Shift
    shift_id: Optional[UUID] = None
    week_off_days: Optional[List[str]] = None

    # User link
    user_id: Optional[UUID] = None

    # IDs
    pan_number: Optional[str] = None
    aadhaar_number: Optional[str] = None
    uan_number: Optional[str] = None
    esic_number: Optional[str] = None


class EmployeeListResponse(BaseModel):
    """Minimal response for employee list."""
    id: UUID
    employee_code: str
    first_name: str
    last_name: str
    display_name: Optional[str] = None
    gender: Gender
    personal_mobile: str
    official_email: Optional[str] = None
    department_id: Optional[UUID] = None
    department_name: Optional[str] = None
    designation_id: Optional[UUID] = None
    designation_name: Optional[str] = None
    date_of_joining: date
    employment_type: EmploymentType
    employment_status: EmploymentStatus
    photo_url: Optional[str] = None

    class Config:
        from_attributes = True


class EmployeeResponse(MaskedPIIModel, EmployeeBase):
    """Full response schema for employee."""
    id: UUID
    organization_id: UUID
    employee_code: str
    employment_status: EmploymentStatus
    date_of_leaving: Optional[date] = None
    user_id: Optional[UUID] = None

    # Computed
    full_name: Optional[str] = None
    age: Optional[int] = None

    # Related names
    department_name: Optional[str] = None
    designation_name: Optional[str] = None
    unit_name: Optional[str] = None
    reporting_manager_name: Optional[str] = None
    shift_name: Optional[str] = None

    # Nested responses (optional, based on query)
    documents: Optional[List[EmployeeDocumentResponse]] = None
    family_members: Optional[List[EmployeeFamilyResponse]] = None
    bank_accounts: Optional[List[EmployeeBankAccountResponse]] = None
    education: Optional[List[EmployeeEducationResponse]] = None
    experience: Optional[List[EmployeeExperienceResponse]] = None
    statutory_info: Optional[EmployeeStatutoryResponse] = None
    lifecycle_events: Optional[List[EmployeeLifecycleEventResponse]] = None

    class Config:
        from_attributes = True


# ============================================
# Filter Schemas
# ============================================
class EmployeeFilters(BaseModel):
    """Filters for employee list."""
    organization_id: Optional[UUID] = None
    department_id: Optional[UUID] = None
    designation_id: Optional[UUID] = None
    unit_id: Optional[UUID] = None
    employment_type: Optional[EmploymentType] = None
    employment_status: Optional[EmploymentStatus] = None
    reporting_manager_id: Optional[UUID] = None
    search: Optional[str] = None  # Search in name, code, email, phone
    date_of_joining_from: Optional[date] = None
    date_of_joining_to: Optional[date] = None
