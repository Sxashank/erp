"""
Compliance Schemas

Pydantic schemas for compliance API validation and serialization.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List, Any
from uuid import UUID

from pydantic import BaseModel, Field


# ============== Compliance Item Schemas ==============

class ComplianceItemCreate(BaseModel):
    """Schema for creating a compliance item"""
    organization_id: UUID
    item_code: str = Field(..., max_length=30)
    item_name: str = Field(..., max_length=200)
    description: Optional[str] = None
    regulatory_body: str  # RBI, SEBI, MCA, GST, INCOME_TAX, EPFO, ESIC, STATE, OTHER
    regulation_reference: Optional[str] = None
    section_reference: Optional[str] = None
    frequency: str = "MONTHLY"  # DAILY, WEEKLY, MONTHLY, QUARTERLY, etc.
    due_day: Optional[int] = None
    due_month: Optional[int] = None
    grace_days: int = 0
    priority: str = "MEDIUM"  # CRITICAL, HIGH, MEDIUM, LOW
    penalty_type: Optional[str] = None
    penalty_amount: Optional[Decimal] = None
    penalty_rate_per_day: Optional[Decimal] = None
    responsible_designation: Optional[str] = None
    department: Optional[str] = None
    required_documents: Optional[List[str]] = None
    form_name: Optional[str] = None
    filing_portal: Optional[str] = None
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    is_active: bool = True


class ComplianceItemUpdate(BaseModel):
    """Schema for updating a compliance item"""
    item_name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    regulation_reference: Optional[str] = None
    section_reference: Optional[str] = None
    frequency: Optional[str] = None
    due_day: Optional[int] = None
    due_month: Optional[int] = None
    grace_days: Optional[int] = None
    priority: Optional[str] = None
    penalty_type: Optional[str] = None
    penalty_amount: Optional[Decimal] = None
    penalty_rate_per_day: Optional[Decimal] = None
    responsible_designation: Optional[str] = None
    department: Optional[str] = None
    required_documents: Optional[List[str]] = None
    form_name: Optional[str] = None
    filing_portal: Optional[str] = None
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    is_active: Optional[bool] = None


class ComplianceItemResponse(BaseModel):
    """Schema for compliance item response"""
    id: UUID
    organization_id: UUID
    item_code: str
    item_name: str
    description: Optional[str]
    regulatory_body: str
    regulation_reference: Optional[str]
    section_reference: Optional[str]
    frequency: str
    due_day: Optional[int]
    due_month: Optional[int]
    grace_days: int
    priority: str
    penalty_type: Optional[str]
    penalty_amount: Optional[Decimal]
    penalty_rate_per_day: Optional[Decimal]
    responsible_designation: Optional[str]
    department: Optional[str]
    required_documents: Optional[List[str]]
    form_name: Optional[str]
    filing_portal: Optional[str]
    effective_from: Optional[date]
    effective_to: Optional[date]
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ComplianceItemList(BaseModel):
    """Schema for compliance item list"""
    id: UUID
    item_code: str
    item_name: str
    regulatory_body: str
    frequency: str
    priority: str
    form_name: Optional[str]
    is_active: bool

    model_config = {"from_attributes": True}


# ============== Compliance Instance Schemas ==============

class ComplianceInstanceCreate(BaseModel):
    """Schema for creating a compliance instance"""
    compliance_item_id: UUID
    period_year: int
    period_month: Optional[int] = None
    period_quarter: Optional[int] = None
    period_from: Optional[date] = None
    period_to: Optional[date] = None
    original_due_date: date
    extended_due_date: Optional[date] = None
    status: str = "PENDING"
    assigned_to: Optional[UUID] = None
    reviewer: Optional[UUID] = None
    reminder_days: Optional[int] = None
    remarks: Optional[str] = None


class ComplianceInstanceUpdate(BaseModel):
    """Schema for updating a compliance instance"""
    status: Optional[str] = None
    extended_due_date: Optional[date] = None
    filed_date: Optional[date] = None
    acknowledgment_number: Optional[str] = None
    acknowledgment_date: Optional[date] = None
    reference_number: Optional[str] = None
    is_delayed: Optional[bool] = None
    delay_days: Optional[int] = None
    penalty_paid: Optional[Decimal] = None
    penalty_reference: Optional[str] = None
    assigned_to: Optional[UUID] = None
    reviewer: Optional[UUID] = None
    remarks: Optional[str] = None
    internal_notes: Optional[str] = None
    reminder_days: Optional[int] = None


class ComplianceInstanceResponse(BaseModel):
    """Schema for compliance instance response"""
    id: UUID
    compliance_item_id: UUID
    compliance_item: Optional[ComplianceItemList] = None
    period_year: int
    period_month: Optional[int]
    period_quarter: Optional[int]
    period_from: Optional[date]
    period_to: Optional[date]
    original_due_date: date
    extended_due_date: Optional[date]
    actual_due_date: date
    status: str
    filed_date: Optional[date]
    acknowledgment_number: Optional[str]
    acknowledgment_date: Optional[date]
    reference_number: Optional[str]
    is_delayed: bool
    delay_days: Optional[int]
    penalty_paid: Optional[Decimal]
    penalty_reference: Optional[str]
    assigned_to: Optional[UUID]
    reviewer: Optional[UUID]
    remarks: Optional[str]
    internal_notes: Optional[str]
    reminder_days: Optional[int]
    created_at: datetime

    model_config = {"from_attributes": True}


class ComplianceInstanceList(BaseModel):
    """Schema for compliance instance list"""
    id: UUID
    compliance_item_id: UUID
    item_code: Optional[str] = None
    item_name: Optional[str] = None
    regulatory_body: Optional[str] = None
    period_year: int
    period_month: Optional[int]
    period_quarter: Optional[int]
    actual_due_date: date
    status: str
    is_delayed: bool
    filed_date: Optional[date]

    model_config = {"from_attributes": True}


# ============== Compliance Document Schemas ==============

class ComplianceDocumentCreate(BaseModel):
    """Schema for creating a compliance document"""
    instance_id: UUID
    document_type: str
    document_name: str
    file_path: str
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    remarks: Optional[str] = None


class ComplianceDocumentResponse(BaseModel):
    """Schema for compliance document response"""
    id: UUID
    instance_id: UUID
    document_type: str
    document_name: str
    file_path: str
    file_size: Optional[int]
    mime_type: Optional[str]
    uploaded_at: datetime
    uploaded_by: Optional[UUID]
    is_active: bool
    remarks: Optional[str]

    model_config = {"from_attributes": True}


# ============== Dashboard/Summary Schemas ==============

class ComplianceSummary(BaseModel):
    """Summary of compliance status"""
    total: int = 0
    pending: int = 0
    in_progress: int = 0
    prepared: int = 0
    filed: int = 0
    delayed: int = 0
    not_applicable: int = 0


class ComplianceCalendarItem(BaseModel):
    """Item for compliance calendar view"""
    id: UUID
    item_code: str
    item_name: str
    regulatory_body: str
    due_date: date
    status: str
    is_delayed: bool


class UpcomingCompliance(BaseModel):
    """Upcoming compliance items"""
    due_this_week: List[ComplianceCalendarItem] = []
    due_this_month: List[ComplianceCalendarItem] = []
    overdue: List[ComplianceCalendarItem] = []
