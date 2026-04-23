"""Asset Maintenance and AMC models.

This module provides:
- AMC (Annual Maintenance Contract) tracking
- Preventive maintenance scheduling
- Maintenance/service history
- Warranty tracking
- Breakdown/repair logging
"""

from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Optional, List, TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, String, Text, Numeric, Date, Boolean, Index, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.masters.organization import Organization
    from app.models.masters.vendor import Vendor
    from app.models.fixed_assets.fixed_asset import FixedAsset


class AMCType(str, Enum):
    """Type of AMC contract."""
    COMPREHENSIVE = "COMPREHENSIVE"  # Parts + Labor
    NON_COMPREHENSIVE = "NON_COMPREHENSIVE"  # Labor only
    EXTENDED_WARRANTY = "EXTENDED_WARRANTY"
    CALIBRATION = "CALIBRATION"
    PREVENTIVE_MAINTENANCE = "PREVENTIVE_MAINTENANCE"


class AMCStatus(str, Enum):
    """AMC contract status."""
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"
    RENEWED = "RENEWED"


class MaintenanceType(str, Enum):
    """Type of maintenance activity."""
    PREVENTIVE = "PREVENTIVE"  # Scheduled maintenance
    CORRECTIVE = "CORRECTIVE"  # Breakdown repair
    PREDICTIVE = "PREDICTIVE"  # Based on condition monitoring
    CALIBRATION = "CALIBRATION"
    INSPECTION = "INSPECTION"
    UPGRADE = "UPGRADE"


class MaintenanceStatus(str, Enum):
    """Status of maintenance request."""
    SCHEDULED = "SCHEDULED"
    IN_PROGRESS = "IN_PROGRESS"
    ON_HOLD = "ON_HOLD"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class MaintenancePriority(str, Enum):
    """Priority of maintenance request."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AMCContract(BaseModel):
    """Annual Maintenance Contract master.

    Tracks AMC contracts with vendors for fixed assets.
    """

    __tablename__ = "mst_amc_contract"

    # Organization
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id"),
        nullable=False,
        index=True,
    )

    # Contract identification
    contract_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="AMC contract reference number",
    )

    contract_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    amc_type: Mapped[AMCType] = mapped_column(
        SAEnum(AMCType, name="amc_type_enum", create_type=False),
        nullable=False,
        default=AMCType.COMPREHENSIVE,
    )

    status: Mapped[AMCStatus] = mapped_column(
        SAEnum(AMCStatus, name="amc_status_enum", create_type=False),
        nullable=False,
        default=AMCStatus.DRAFT,
    )

    # Vendor details
    vendor_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_vendor.id"),
        nullable=False,
    )

    vendor_contact_person: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )

    vendor_contact_phone: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
    )

    vendor_contact_email: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )

    # Contract period
    start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    end_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    # Contract value
    contract_value: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
    )

    gst_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        default=Decimal("18.00"),
    )

    gst_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
    )

    total_value: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
    )

    # Payment terms
    payment_frequency: Mapped[str] = mapped_column(
        String(20),
        default="YEARLY",
        comment="UPFRONT, QUARTERLY, HALF_YEARLY, YEARLY",
    )

    next_payment_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )

    # Coverage details
    coverage_details: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="What is covered under this AMC",
    )

    exclusions: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="What is NOT covered",
    )

    # SLA details
    response_time_hours: Mapped[Optional[int]] = mapped_column(
        nullable=True,
        comment="SLA response time in hours",
    )

    resolution_time_hours: Mapped[Optional[int]] = mapped_column(
        nullable=True,
        comment="SLA resolution time in hours",
    )

    # Maintenance schedule
    preventive_maintenance_frequency: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="MONTHLY, QUARTERLY, HALF_YEARLY, YEARLY",
    )

    visits_per_year: Mapped[Optional[int]] = mapped_column(
        nullable=True,
    )

    visits_completed: Mapped[int] = mapped_column(
        default=0,
    )

    # Asset linking
    asset_ids: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String),
        nullable=True,
        comment="List of asset IDs covered under this AMC",
    )

    # Renewal
    is_renewable: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )

    renewal_reminder_days: Mapped[int] = mapped_column(
        default=30,
        comment="Days before expiry to send reminder",
    )

    auto_renewal: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    previous_contract_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_amc_contract.id"),
        nullable=True,
        comment="Link to previous contract if renewed",
    )

    # Documents
    document_urls: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String),
        nullable=True,
    )

    # Notes
    terms_conditions: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        foreign_keys=[organization_id],
    )

    vendor: Mapped["Vendor"] = relationship(
        foreign_keys=[vendor_id],
    )

    service_requests: Mapped[List["MaintenanceRequest"]] = relationship(
        back_populates="amc_contract",
        foreign_keys="MaintenanceRequest.amc_contract_id",
    )

    __table_args__ = (
        Index("ix_amc_org_number", "organization_id", "contract_number", unique=True),
        Index("ix_amc_status", "organization_id", "status"),
        Index("ix_amc_expiry", "end_date", "status"),
        Index("ix_amc_vendor", "vendor_id"),
    )

    @property
    def days_until_expiry(self) -> int:
        """Days until contract expires."""
        return (self.end_date - date.today()).days

    @property
    def is_expiring_soon(self) -> bool:
        """Check if expiring within renewal reminder period."""
        return 0 < self.days_until_expiry <= self.renewal_reminder_days


class MaintenanceRequest(BaseModel):
    """Maintenance/service request.

    Tracks all maintenance activities - scheduled preventive
    maintenance, breakdown repairs, calibrations, etc.
    """

    __tablename__ = "txn_maintenance_request"

    # Organization
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id"),
        nullable=False,
        index=True,
    )

    # Request identification
    request_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    # Asset being maintained
    asset_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_fixed_asset.id"),
        nullable=False,
        index=True,
    )

    # AMC link (if covered)
    amc_contract_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_amc_contract.id"),
        nullable=True,
    )

    # Request details
    maintenance_type: Mapped[MaintenanceType] = mapped_column(
        SAEnum(MaintenanceType, name="maintenance_type_enum", create_type=False),
        nullable=False,
    )

    status: Mapped[MaintenanceStatus] = mapped_column(
        SAEnum(MaintenanceStatus, name="maintenance_status_enum", create_type=False),
        nullable=False,
        default=MaintenanceStatus.SCHEDULED,
    )

    priority: Mapped[MaintenancePriority] = mapped_column(
        SAEnum(MaintenancePriority, name="maintenance_priority_enum", create_type=False),
        nullable=False,
        default=MaintenancePriority.MEDIUM,
    )

    # Problem/request description
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # For breakdown - problem reported
    reported_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
    )

    reported_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        default=date.today,
    )

    # Scheduling
    scheduled_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )

    scheduled_time: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
        comment="HH:MM format",
    )

    # Assignment
    assigned_to_vendor_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_vendor.id"),
        nullable=True,
    )

    assigned_technician: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )

    # Execution
    actual_start_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )

    actual_completion_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )

    downtime_hours: Mapped[Decimal] = mapped_column(
        Numeric(8, 2),
        default=Decimal("0.00"),
        comment="Asset downtime due to maintenance",
    )

    # Work done
    work_performed: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    parts_replaced: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    findings: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    recommendations: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Costs
    labor_cost: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
    )

    parts_cost: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
    )

    other_cost: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
    )

    total_cost: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
    )

    is_covered_under_amc: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    # Invoicing
    invoice_number: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )

    invoice_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )

    # Sign-off
    customer_signoff_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
    )

    customer_signoff_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )

    customer_feedback: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    satisfaction_rating: Mapped[Optional[int]] = mapped_column(
        nullable=True,
        comment="1-5 rating",
    )

    # Documents
    photo_urls: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String),
        nullable=True,
    )

    document_urls: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String),
        nullable=True,
    )

    # Next maintenance
    next_maintenance_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        foreign_keys=[organization_id],
    )

    asset: Mapped["FixedAsset"] = relationship(
        foreign_keys=[asset_id],
    )

    amc_contract: Mapped[Optional["AMCContract"]] = relationship(
        back_populates="service_requests",
        foreign_keys=[amc_contract_id],
    )

    assigned_vendor: Mapped[Optional["Vendor"]] = relationship(
        foreign_keys=[assigned_to_vendor_id],
    )

    __table_args__ = (
        Index("ix_maint_org_number", "organization_id", "request_number", unique=True),
        Index("ix_maint_asset", "asset_id", "status"),
        Index("ix_maint_scheduled", "scheduled_date", "status"),
        Index("ix_maint_type", "organization_id", "maintenance_type", "status"),
    )


class MaintenanceSchedule(BaseModel):
    """Preventive maintenance schedule template.

    Defines recurring maintenance schedules for assets.
    """

    __tablename__ = "mst_maintenance_schedule"

    # Organization
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id"),
        nullable=False,
        index=True,
    )

    # Schedule name
    schedule_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    # Target - either specific asset or category
    asset_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_fixed_asset.id"),
        nullable=True,
    )

    category_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_asset_category.id"),
        nullable=True,
    )

    # Maintenance details
    maintenance_type: Mapped[MaintenanceType] = mapped_column(
        SAEnum(MaintenanceType, name="maintenance_type_enum", create_type=False),
        nullable=False,
        default=MaintenanceType.PREVENTIVE,
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    checklist: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="JSON checklist items for maintenance",
    )

    # Frequency
    frequency: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="DAILY, WEEKLY, MONTHLY, QUARTERLY, HALF_YEARLY, YEARLY",
    )

    frequency_value: Mapped[int] = mapped_column(
        default=1,
        comment="E.g., every 2 months",
    )

    # Timing
    preferred_day_of_week: Mapped[Optional[int]] = mapped_column(
        nullable=True,
        comment="0=Monday, 6=Sunday",
    )

    preferred_day_of_month: Mapped[Optional[int]] = mapped_column(
        nullable=True,
    )

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )

    last_executed_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )

    next_due_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )

    # Estimated duration and cost
    estimated_duration_hours: Mapped[Decimal] = mapped_column(
        Numeric(6, 2),
        default=Decimal("1.00"),
    )

    estimated_cost: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
    )

    # Assignment
    default_vendor_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_vendor.id"),
        nullable=True,
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        foreign_keys=[organization_id],
    )

    asset: Mapped[Optional["FixedAsset"]] = relationship(
        foreign_keys=[asset_id],
    )

    __table_args__ = (
        Index("ix_maint_sched_org", "organization_id", "is_active"),
        Index("ix_maint_sched_asset", "asset_id"),
        Index("ix_maint_sched_next", "next_due_date", "is_active"),
    )


class AssetWarranty(BaseModel):
    """Asset warranty tracking."""

    __tablename__ = "mst_asset_warranty"

    # Organization
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id"),
        nullable=False,
        index=True,
    )

    # Asset
    asset_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_fixed_asset.id"),
        nullable=False,
        index=True,
    )

    # Warranty details
    warranty_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="MANUFACTURER, EXTENDED, PARTS, LABOR",
    )

    warranty_provider: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    warranty_number: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )

    # Period
    start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    end_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    # Coverage
    coverage_details: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    exclusions: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Contact
    contact_phone: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
    )

    contact_email: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )

    # Documents
    document_urls: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String),
        nullable=True,
    )

    # Claims tracking
    claims_count: Mapped[int] = mapped_column(
        default=0,
    )

    last_claim_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        foreign_keys=[organization_id],
    )

    asset: Mapped["FixedAsset"] = relationship(
        foreign_keys=[asset_id],
    )

    __table_args__ = (
        Index("ix_warranty_asset", "asset_id", "is_active"),
        Index("ix_warranty_expiry", "end_date", "is_active"),
    )

    @property
    def days_until_expiry(self) -> int:
        """Days until warranty expires."""
        return (self.end_date - date.today()).days

    @property
    def is_expired(self) -> bool:
        """Check if warranty has expired."""
        return self.end_date < date.today()
