"""Physical Verification model for Fixed Assets module.

Per RBI NBFC requirements, physical verification of fixed assets
must be conducted annually. This module tracks:
- Verification schedules and assignments
- Verification results (found, missing, condition)
- Discrepancy reporting and resolution
"""

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Enum as SQLEnum,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.masters.organization import Organization
    from app.models.masters.unit import Unit
    from app.models.fixed_assets.fixed_asset import FixedAsset


class VerificationStatus(str):
    """Status of physical verification."""

    SCHEDULED = "SCHEDULED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class AssetCondition(str):
    """Condition of asset during verification."""

    GOOD = "GOOD"
    FAIR = "FAIR"
    POOR = "POOR"
    DAMAGED = "DAMAGED"
    NOT_WORKING = "NOT_WORKING"


class VerificationResult(str):
    """Result of individual asset verification."""

    FOUND = "FOUND"
    MISSING = "MISSING"
    MISPLACED = "MISPLACED"  # Found at different location
    EXCESS = "EXCESS"  # Found but not in register


class DiscrepancyStatus(str):
    """Status of discrepancy resolution."""

    OPEN = "OPEN"
    INVESTIGATING = "INVESTIGATING"
    RESOLVED = "RESOLVED"
    WRITTEN_OFF = "WRITTEN_OFF"


class PhysicalVerificationSchedule(BaseModel):
    """Physical verification schedule/batch."""

    __tablename__ = "txn_pv_schedule"
    __table_args__ = (
        UniqueConstraint("organization_id", "schedule_reference", name="uq_pv_schedule_org_ref"),
    )

    # Organization
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Schedule Identity
    schedule_reference: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        comment="Unique reference number (e.g., PV/2024-25/001)",
    )
    schedule_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Description (e.g., 'Annual PV Q4 FY 2024-25')",
    )
    financial_year: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        index=True,
        comment="Financial Year in YYYY-YY format",
    )

    # Scope
    location_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_unit.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Specific location to verify (null = all locations)",
    )
    category_ids: Mapped[Optional[List[UUID]]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Specific categories to verify (null = all)",
    )

    # Schedule Dates
    scheduled_start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    scheduled_end_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    actual_start_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )
    actual_end_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )

    # Assignment
    assigned_to: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
        comment="Primary person responsible",
    )
    team_members: Mapped[Optional[List[UUID]]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Additional team member IDs",
    )

    # Summary
    total_assets: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Total assets to verify",
    )
    verified_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    found_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    missing_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    discrepancy_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    total_value_verified: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    total_value_missing: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
        nullable=False,
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        default=VerificationStatus.SCHEDULED,
        nullable=False,
        index=True,
    )

    remarks: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Approval
    approved_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        lazy="selectin",
    )
    location: Mapped[Optional["Unit"]] = relationship(
        "Unit",
        lazy="selectin",
    )
    entries: Mapped[List["PhysicalVerificationEntry"]] = relationship(
        "PhysicalVerificationEntry",
        back_populates="schedule",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<PVSchedule({self.schedule_reference}, {self.status})>"


class PhysicalVerificationEntry(BaseModel):
    """Individual asset verification entry."""

    __tablename__ = "txn_pv_entry"
    __table_args__ = (
        UniqueConstraint("schedule_id", "asset_id", name="uq_pv_entry_schedule_asset"),
    )

    # Schedule Reference
    schedule_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("txn_pv_schedule.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Asset
    asset_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_fixed_asset.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    legacy_status: Mapped[str] = mapped_column(
        "status",
        String(20),
        nullable=False,
        default="PENDING",
        comment="Legacy verification status kept in sync for backward compatibility",
    )

    # Expected Location (from asset register)
    expected_location_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
    )
    expected_department_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
    )

    # Verification
    verification_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )
    verified_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
    )

    physical_location: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
    )
    physical_condition: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )

    # Result
    verification_result: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="FOUND, MISSING, MISPLACED, EXCESS",
    )
    asset_condition: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="GOOD, FAIR, POOR, DAMAGED, NOT_WORKING",
    )

    # Actual Location (if found)
    actual_location_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
        comment="Actual location where found",
    )
    actual_department_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
    )

    # Value
    book_value: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
        nullable=False,
        comment="WDV at verification time",
    )

    # Evidence
    photo_urls: Mapped[Optional[List[str]]] = mapped_column(
        JSONB,
        nullable=True,
        comment="URLs of verification photos",
    )
    barcode_scan: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Scanned barcode/QR code",
    )

    # Notes
    condition_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Notes on asset condition",
    )
    remarks: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    schedule: Mapped["PhysicalVerificationSchedule"] = relationship(
        "PhysicalVerificationSchedule",
        back_populates="entries",
        lazy="selectin",
    )
    asset: Mapped["FixedAsset"] = relationship(
        "FixedAsset",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<PVEntry(asset={self.asset_id}, result={self.verification_result})>"


class PhysicalVerificationDiscrepancy(BaseModel):
    """Discrepancy found during verification."""

    __tablename__ = "txn_pv_discrepancy"

    # Entry Reference
    entry_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("txn_pv_entry.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Discrepancy Type
    discrepancy_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        comment="MISSING, LOCATION_MISMATCH, CONDITION_ISSUE, EXCESS",
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # Value Impact
    value_impact: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
        nullable=False,
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        default=DiscrepancyStatus.OPEN,
        nullable=False,
        index=True,
    )

    # Investigation
    investigated_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
    )
    investigation_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Resolution
    resolution: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    resolved_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    remarks: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    entry: Mapped["PhysicalVerificationEntry"] = relationship(
        "PhysicalVerificationEntry",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<PVDiscrepancy({self.discrepancy_type}, {self.status})>"
