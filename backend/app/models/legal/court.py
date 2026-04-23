"""Court and Forum management models.

Provides master data for courts, tribunals, and
their fee structures under Indian legal system.
"""

from datetime import date
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Date,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.mixins import AddressMixin, ContactMixin
from app.models.legal.enums import CourtType


class Court(BaseModel, AddressMixin, ContactMixin):
    """Master table for courts and tribunals.

    Contains details of all Indian courts and tribunals
    where legal proceedings can be filed.
    """

    __tablename__ = "mst_court"
    __table_args__ = (
        Index("ix_court_org", "organization_id"),
        Index("ix_court_type", "court_type"),
        Index("ix_court_state", "state_code"),
        UniqueConstraint("organization_id", "court_code", name="uq_court_code"),
    )

    # Organization
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id"),
        nullable=False,
    )

    # Court Identity
    court_code: Mapped[str] = mapped_column(String(50), nullable=False)
    court_name: Mapped[str] = mapped_column(String(300), nullable=False)
    court_type: Mapped[CourtType] = mapped_column(String(50), nullable=False)
    short_name: Mapped[Optional[str]] = mapped_column(String(50))

    # Location
    jurisdiction: Mapped[str] = mapped_column(
        String(200), nullable=False
    )  # Territorial jurisdiction
    jurisdiction_area: Mapped[Optional[str]] = mapped_column(
        Text
    )  # Detailed description

    # For DRT/NCLT specific
    bench_number: Mapped[Optional[str]] = mapped_column(String(20))
    circuit_bench: Mapped[bool] = mapped_column(Boolean, default=False)
    circuit_location: Mapped[Optional[str]] = mapped_column(String(200))

    # Functioning Details
    establishment_date: Mapped[Optional[date]] = mapped_column(Date)
    working_days: Mapped[Optional[dict]] = mapped_column(
        JSONB
    )  # ["MONDAY", "TUESDAY", ...]
    working_hours: Mapped[Optional[str]] = mapped_column(String(50))
    filing_time: Mapped[Optional[str]] = mapped_column(String(50))

    # E-Filing
    e_filing_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    e_filing_portal: Mapped[Optional[str]] = mapped_column(String(255))
    e_filing_instructions: Mapped[Optional[str]] = mapped_column(Text)

    # Parent Court (for appellate hierarchy)
    parent_court_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_court.id"),
    )
    appellate_court_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_court.id"),
    )

    # Pecuniary Jurisdiction
    min_claim_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    max_claim_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))

    # Officials (current)
    presiding_officer: Mapped[Optional[str]] = mapped_column(String(200))
    presiding_officer_designation: Mapped[Optional[str]] = mapped_column(String(100))
    registrar: Mapped[Optional[str]] = mapped_column(String(200))

    # Status
    is_operational: Mapped[bool] = mapped_column(Boolean, default=True)

    remarks: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    benches: Mapped[List["CourtBench"]] = relationship(back_populates="court")
    fee_slabs: Mapped[List["CourtFeeSlab"]] = relationship(back_populates="court")


class CourtBench(BaseModel):
    """Bench information for courts/tribunals.

    Tracks different benches and their presiding officers.
    """

    __tablename__ = "mst_court_bench"
    __table_args__ = (
        Index("ix_court_bench_court", "court_id"),
        UniqueConstraint("court_id", "bench_code", name="uq_court_bench_code"),
    )

    # Foreign Keys
    court_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_court.id"),
        nullable=False,
    )

    # Bench Details
    bench_code: Mapped[str] = mapped_column(String(20), nullable=False)
    bench_name: Mapped[str] = mapped_column(String(200), nullable=False)
    bench_type: Mapped[str] = mapped_column(
        String(50), default="REGULAR"
    )  # REGULAR, DIVISION, SINGLE

    # Presiding Officers
    presiding_member: Mapped[Optional[str]] = mapped_column(String(200))
    presiding_member_designation: Mapped[Optional[str]] = mapped_column(String(100))
    judicial_member: Mapped[Optional[str]] = mapped_column(String(200))
    technical_member: Mapped[Optional[str]] = mapped_column(String(200))

    # Subject Matter
    subject_allocation: Mapped[Optional[dict]] = mapped_column(
        JSONB
    )  # Types of cases handled

    # Sitting Days
    sitting_days: Mapped[Optional[dict]] = mapped_column(JSONB)  # Days of the week
    court_hall: Mapped[Optional[str]] = mapped_column(String(50))

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    effective_from: Mapped[Optional[date]] = mapped_column(Date)
    effective_to: Mapped[Optional[date]] = mapped_column(Date)

    remarks: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    court: Mapped["Court"] = relationship(back_populates="benches")


class CourtFeeSlab(BaseModel):
    """Court fee structure by claim amount.

    Defines court fees payable based on claim amount
    and forum type.
    """

    __tablename__ = "mst_court_fee_slab"
    __table_args__ = (
        Index("ix_court_fee_court", "court_id"),
        Index("ix_court_fee_type", "fee_type"),
        UniqueConstraint(
            "court_id",
            "fee_type",
            "min_claim_amount",
            "max_claim_amount",
            name="uq_court_fee_slab",
        ),
    )

    # Foreign Keys
    court_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_court.id"),
    )

    # Organization (for court-agnostic fee rules)
    organization_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id"),
    )

    # Court Type (if not court-specific)
    court_type: Mapped[Optional[CourtType]] = mapped_column(String(50))

    # Fee Type
    fee_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # FILING, INTERIM_APPLICATION, APPEAL, EXECUTION, CERTIFIED_COPY

    # Claim Amount Range
    min_claim_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False, default=Decimal("0")
    )
    max_claim_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2)
    )  # NULL for unlimited

    # Fee Calculation
    calculation_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # FIXED, PERCENTAGE, SLAB
    fixed_fee: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))
    percentage_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 4))
    min_fee: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))
    max_fee: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))

    # Additional Fee Components
    process_fee: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))
    service_fee: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))

    # Exemptions
    exemption_available: Mapped[bool] = mapped_column(Boolean, default=False)
    exemption_conditions: Mapped[Optional[str]] = mapped_column(Text)

    # Validity
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[Optional[date]] = mapped_column(Date)

    # Reference
    notification_reference: Mapped[Optional[str]] = mapped_column(
        String(200)
    )  # Govt. notification

    remarks: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    court: Mapped[Optional["Court"]] = relationship(back_populates="fee_slabs")

    def calculate_fee(self, claim_amount: Decimal) -> Decimal:
        """Calculate court fee based on claim amount.

        Args:
            claim_amount: The claim/suit value

        Returns:
            Calculated court fee amount
        """
        if self.calculation_type == "FIXED":
            fee = self.fixed_fee or Decimal("0")
        elif self.calculation_type == "PERCENTAGE":
            fee = claim_amount * (self.percentage_rate or Decimal("0")) / 100
        else:
            fee = self.fixed_fee or Decimal("0")

        # Apply min/max limits
        if self.min_fee and fee < self.min_fee:
            fee = self.min_fee
        if self.max_fee and fee > self.max_fee:
            fee = self.max_fee

        # Add process and service fees
        if self.process_fee:
            fee += self.process_fee
        if self.service_fee:
            fee += self.service_fee

        return fee
