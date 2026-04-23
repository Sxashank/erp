"""Maintenance and AMC schemas."""

from datetime import date
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from pydantic import Field, field_validator

from app.schemas.base import BaseSchema, AuditSchema
from app.models.fixed_assets.maintenance import (
    AMCType,
    AMCStatus,
    MaintenanceType,
    MaintenanceStatus,
    MaintenancePriority,
)


# ============================================
# AMC Contract Schemas
# ============================================

class AMCContractCreate(BaseSchema):
    """Schema for creating AMC contract."""

    organization_id: UUID
    contract_number: str = Field(..., max_length=50)
    contract_name: str = Field(..., max_length=200)
    amc_type: AMCType = AMCType.COMPREHENSIVE
    vendor_id: UUID

    vendor_contact_person: Optional[str] = Field(None, max_length=100)
    vendor_contact_phone: Optional[str] = Field(None, max_length=20)
    vendor_contact_email: Optional[str] = Field(None, max_length=100)

    start_date: date
    end_date: date

    contract_value: Decimal = Field(..., ge=0)
    gst_rate: Decimal = Field(default=Decimal("18.00"), ge=0)

    payment_frequency: str = Field(default="YEARLY", max_length=20)

    coverage_details: Optional[str] = None
    exclusions: Optional[str] = None

    response_time_hours: Optional[int] = None
    resolution_time_hours: Optional[int] = None

    preventive_maintenance_frequency: Optional[str] = Field(None, max_length=20)
    visits_per_year: Optional[int] = None

    asset_ids: Optional[List[str]] = None  # UUIDs as strings

    is_renewable: bool = True
    renewal_reminder_days: int = Field(default=30, ge=1)
    auto_renewal: bool = False

    terms_conditions: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("end_date")
    @classmethod
    def end_after_start(cls, v, info):
        if "start_date" in info.data and v <= info.data["start_date"]:
            raise ValueError("End date must be after start date")
        return v


class AMCContractUpdate(BaseSchema):
    """Schema for updating AMC contract."""

    contract_name: Optional[str] = Field(None, max_length=200)
    vendor_contact_person: Optional[str] = Field(None, max_length=100)
    vendor_contact_phone: Optional[str] = Field(None, max_length=20)
    vendor_contact_email: Optional[str] = Field(None, max_length=100)

    coverage_details: Optional[str] = None
    exclusions: Optional[str] = None

    response_time_hours: Optional[int] = None
    resolution_time_hours: Optional[int] = None

    preventive_maintenance_frequency: Optional[str] = Field(None, max_length=20)
    visits_per_year: Optional[int] = None

    asset_ids: Optional[List[str]] = None

    renewal_reminder_days: Optional[int] = Field(None, ge=1)
    auto_renewal: Optional[bool] = None

    terms_conditions: Optional[str] = None
    notes: Optional[str] = None


class AMCContractRenew(BaseSchema):
    """Schema for renewing AMC contract."""

    new_start_date: date
    new_end_date: date
    new_contract_value: Decimal = Field(..., ge=0)
    new_terms_conditions: Optional[str] = None


class AMCContractResponse(AuditSchema):
    """Schema for AMC contract response."""

    id: UUID
    organization_id: UUID
    contract_number: str
    contract_name: str
    amc_type: AMCType
    status: AMCStatus

    vendor_id: UUID
    vendor_name: Optional[str] = None
    vendor_contact_person: Optional[str] = None
    vendor_contact_phone: Optional[str] = None
    vendor_contact_email: Optional[str] = None

    start_date: date
    end_date: date
    days_until_expiry: int
    is_expiring_soon: bool

    contract_value: Decimal
    gst_rate: Decimal
    gst_amount: Decimal
    total_value: Decimal

    payment_frequency: str
    next_payment_date: Optional[date] = None

    coverage_details: Optional[str] = None
    exclusions: Optional[str] = None

    response_time_hours: Optional[int] = None
    resolution_time_hours: Optional[int] = None

    preventive_maintenance_frequency: Optional[str] = None
    visits_per_year: Optional[int] = None
    visits_completed: int

    asset_ids: Optional[List[str]] = None
    asset_count: int = 0

    is_renewable: bool
    renewal_reminder_days: int
    auto_renewal: bool


# ============================================
# Maintenance Request Schemas
# ============================================

class MaintenanceRequestCreate(BaseSchema):
    """Schema for creating maintenance request."""

    organization_id: UUID
    asset_id: UUID
    amc_contract_id: Optional[UUID] = None

    maintenance_type: MaintenanceType
    priority: MaintenancePriority = MaintenancePriority.MEDIUM

    title: str = Field(..., max_length=200)
    description: Optional[str] = None

    reported_by: Optional[UUID] = None
    reported_date: date = Field(default_factory=date.today)

    scheduled_date: Optional[date] = None
    scheduled_time: Optional[str] = Field(None, max_length=10)

    assigned_to_vendor_id: Optional[UUID] = None
    assigned_technician: Optional[str] = Field(None, max_length=100)


class MaintenanceRequestUpdate(BaseSchema):
    """Schema for updating maintenance request."""

    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    priority: Optional[MaintenancePriority] = None
    status: Optional[MaintenanceStatus] = None

    scheduled_date: Optional[date] = None
    scheduled_time: Optional[str] = Field(None, max_length=10)

    assigned_to_vendor_id: Optional[UUID] = None
    assigned_technician: Optional[str] = Field(None, max_length=100)

    actual_start_date: Optional[date] = None
    actual_completion_date: Optional[date] = None
    downtime_hours: Optional[Decimal] = Field(None, ge=0)

    work_performed: Optional[str] = None
    parts_replaced: Optional[str] = None
    findings: Optional[str] = None
    recommendations: Optional[str] = None

    labor_cost: Optional[Decimal] = Field(None, ge=0)
    parts_cost: Optional[Decimal] = Field(None, ge=0)
    other_cost: Optional[Decimal] = Field(None, ge=0)
    is_covered_under_amc: Optional[bool] = None

    invoice_number: Optional[str] = Field(None, max_length=50)
    invoice_date: Optional[date] = None

    customer_feedback: Optional[str] = None
    satisfaction_rating: Optional[int] = Field(None, ge=1, le=5)

    next_maintenance_date: Optional[date] = None


class MaintenanceRequestComplete(BaseSchema):
    """Schema for completing maintenance request."""

    actual_completion_date: date = Field(default_factory=date.today)
    work_performed: str
    parts_replaced: Optional[str] = None
    findings: Optional[str] = None
    recommendations: Optional[str] = None

    labor_cost: Decimal = Field(default=Decimal("0.00"), ge=0)
    parts_cost: Decimal = Field(default=Decimal("0.00"), ge=0)
    other_cost: Decimal = Field(default=Decimal("0.00"), ge=0)
    is_covered_under_amc: bool = False

    next_maintenance_date: Optional[date] = None


class MaintenanceRequestResponse(AuditSchema):
    """Schema for maintenance request response."""

    id: UUID
    organization_id: UUID
    request_number: str

    asset_id: UUID
    asset_code: Optional[str] = None
    asset_name: Optional[str] = None

    amc_contract_id: Optional[UUID] = None
    amc_contract_number: Optional[str] = None

    maintenance_type: MaintenanceType
    status: MaintenanceStatus
    priority: MaintenancePriority

    title: str
    description: Optional[str] = None

    reported_by: Optional[UUID] = None
    reported_date: date

    scheduled_date: Optional[date] = None
    scheduled_time: Optional[str] = None

    assigned_to_vendor_id: Optional[UUID] = None
    assigned_vendor_name: Optional[str] = None
    assigned_technician: Optional[str] = None

    actual_start_date: Optional[date] = None
    actual_completion_date: Optional[date] = None
    downtime_hours: Decimal

    work_performed: Optional[str] = None
    parts_replaced: Optional[str] = None
    findings: Optional[str] = None
    recommendations: Optional[str] = None

    labor_cost: Decimal
    parts_cost: Decimal
    other_cost: Decimal
    total_cost: Decimal
    is_covered_under_amc: bool

    invoice_number: Optional[str] = None
    invoice_date: Optional[date] = None

    customer_signoff_by: Optional[UUID] = None
    customer_signoff_date: Optional[date] = None
    customer_feedback: Optional[str] = None
    satisfaction_rating: Optional[int] = None

    next_maintenance_date: Optional[date] = None


# ============================================
# Maintenance Schedule Schemas
# ============================================

class MaintenanceScheduleCreate(BaseSchema):
    """Schema for creating maintenance schedule."""

    organization_id: UUID
    schedule_name: str = Field(..., max_length=100)

    asset_id: Optional[UUID] = None
    category_id: Optional[UUID] = None

    maintenance_type: MaintenanceType = MaintenanceType.PREVENTIVE
    description: Optional[str] = None
    checklist: Optional[dict] = None

    frequency: str = Field(..., max_length=20)
    frequency_value: int = Field(default=1, ge=1)

    preferred_day_of_week: Optional[int] = Field(None, ge=0, le=6)
    preferred_day_of_month: Optional[int] = Field(None, ge=1, le=31)

    estimated_duration_hours: Decimal = Field(default=Decimal("1.00"), ge=0)
    estimated_cost: Decimal = Field(default=Decimal("0.00"), ge=0)

    default_vendor_id: Optional[UUID] = None


class MaintenanceScheduleUpdate(BaseSchema):
    """Schema for updating maintenance schedule."""

    schedule_name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    checklist: Optional[dict] = None

    frequency: Optional[str] = Field(None, max_length=20)
    frequency_value: Optional[int] = Field(None, ge=1)

    preferred_day_of_week: Optional[int] = Field(None, ge=0, le=6)
    preferred_day_of_month: Optional[int] = Field(None, ge=1, le=31)

    estimated_duration_hours: Optional[Decimal] = Field(None, ge=0)
    estimated_cost: Optional[Decimal] = Field(None, ge=0)

    default_vendor_id: Optional[UUID] = None
    is_active: Optional[bool] = None


class MaintenanceScheduleResponse(AuditSchema):
    """Schema for maintenance schedule response."""

    id: UUID
    organization_id: UUID
    schedule_name: str

    asset_id: Optional[UUID] = None
    asset_code: Optional[str] = None
    asset_name: Optional[str] = None

    category_id: Optional[UUID] = None
    category_name: Optional[str] = None

    maintenance_type: MaintenanceType
    description: Optional[str] = None
    checklist: Optional[dict] = None

    frequency: str
    frequency_value: int

    preferred_day_of_week: Optional[int] = None
    preferred_day_of_month: Optional[int] = None

    is_active: bool
    last_executed_date: Optional[date] = None
    next_due_date: Optional[date] = None

    estimated_duration_hours: Decimal
    estimated_cost: Decimal

    default_vendor_id: Optional[UUID] = None
    default_vendor_name: Optional[str] = None


# ============================================
# Warranty Schemas
# ============================================

class AssetWarrantyCreate(BaseSchema):
    """Schema for creating asset warranty."""

    organization_id: UUID
    asset_id: UUID

    warranty_type: str = Field(..., max_length=50)
    warranty_provider: str = Field(..., max_length=200)
    warranty_number: Optional[str] = Field(None, max_length=50)

    start_date: date
    end_date: date

    coverage_details: Optional[str] = None
    exclusions: Optional[str] = None

    contact_phone: Optional[str] = Field(None, max_length=20)
    contact_email: Optional[str] = Field(None, max_length=100)


class AssetWarrantyUpdate(BaseSchema):
    """Schema for updating asset warranty."""

    warranty_provider: Optional[str] = Field(None, max_length=200)
    warranty_number: Optional[str] = Field(None, max_length=50)

    coverage_details: Optional[str] = None
    exclusions: Optional[str] = None

    contact_phone: Optional[str] = Field(None, max_length=20)
    contact_email: Optional[str] = Field(None, max_length=100)

    is_active: Optional[bool] = None


class AssetWarrantyResponse(AuditSchema):
    """Schema for warranty response."""

    id: UUID
    organization_id: UUID
    asset_id: UUID
    asset_code: Optional[str] = None
    asset_name: Optional[str] = None

    warranty_type: str
    warranty_provider: str
    warranty_number: Optional[str] = None

    start_date: date
    end_date: date
    days_until_expiry: int
    is_expired: bool

    coverage_details: Optional[str] = None
    exclusions: Optional[str] = None

    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None

    claims_count: int
    last_claim_date: Optional[date] = None

    is_active: bool


# ============================================
# Summary and Analytics Schemas
# ============================================

class MaintenanceSummaryResponse(BaseSchema):
    """Summary of maintenance activities."""

    organization_id: UUID
    as_on_date: date

    # AMC Summary
    total_amc_contracts: int
    active_amc_contracts: int
    expiring_within_30_days: int
    expired_contracts: int
    total_amc_value: Decimal

    # Warranty Summary
    total_warranties: int
    active_warranties: int
    expiring_within_30_days_warranty: int

    # Maintenance Requests
    total_requests_ytd: int
    open_requests: int
    overdue_requests: int
    completed_this_month: int

    # Costs
    total_maintenance_cost_ytd: Decimal
    cost_covered_by_amc: Decimal
    cost_not_covered: Decimal

    # By type breakdown
    by_maintenance_type: List[dict]

    # Upcoming maintenance
    upcoming_scheduled_count: int


class AssetMaintenanceHistoryResponse(BaseSchema):
    """Maintenance history for a specific asset."""

    asset_id: UUID
    asset_code: str
    asset_name: str

    # Warranty info
    active_warranties: List[AssetWarrantyResponse]

    # AMC coverage
    covered_under_amc: bool
    amc_contract: Optional[AMCContractResponse] = None

    # Maintenance history
    total_maintenance_count: int
    total_maintenance_cost: Decimal
    total_downtime_hours: Decimal

    # Recent maintenance
    recent_maintenance: List[MaintenanceRequestResponse]

    # Scheduled maintenance
    next_scheduled_maintenance: Optional[date] = None
    maintenance_schedules: List[MaintenanceScheduleResponse]


class AMCExpiryAlertResponse(BaseSchema):
    """AMC expiry alerts."""

    contracts_expiring: List[AMCContractResponse]
    total_count: int
    total_value_at_risk: Decimal


class WarrantyExpiryAlertResponse(BaseSchema):
    """Warranty expiry alerts."""

    warranties_expiring: List[AssetWarrantyResponse]
    total_count: int
