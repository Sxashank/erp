"""Advocate and Law Firm management models."""

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
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
from app.models.legal.enums import (
    AdvocateRole,
    FeeStructureType,
    SpecializationType,
    BarCouncilState,
)

if TYPE_CHECKING:
    from app.models.lending.collections import LegalCase


class LawFirm(BaseModel, AddressMixin, ContactMixin):
    """Law firm master for legal service providers.

    Tracks law firms empaneled for handling legal cases including
    their registration details, contact information, and performance.
    """

    __tablename__ = "mst_law_firm"
    __table_args__ = (
        Index("ix_law_firm_organization", "organization_id"),
        Index("ix_law_firm_active", "is_empaneled"),
        UniqueConstraint(
            "organization_id", "registration_number", name="uq_law_firm_registration"
        ),
    )

    # Organization
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id"),
        nullable=False,
    )

    # Firm Details
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    registration_number: Mapped[Optional[str]] = mapped_column(String(50))
    bar_council_id: Mapped[Optional[str]] = mapped_column(String(50))

    # Tax Information
    pan: Mapped[Optional[str]] = mapped_column(String(10))
    gstin: Mapped[Optional[str]] = mapped_column(String(15))

    # Bank Details for Payments
    bank_name: Mapped[Optional[str]] = mapped_column(String(100))
    bank_account_number: Mapped[Optional[str]] = mapped_column(String(30))
    bank_ifsc: Mapped[Optional[str]] = mapped_column(String(11))
    bank_branch: Mapped[Optional[str]] = mapped_column(String(100))

    # Empanelment
    is_empaneled: Mapped[bool] = mapped_column(Boolean, default=True)
    empanelment_date: Mapped[Optional[date]] = mapped_column(Date)
    empanelment_expiry: Mapped[Optional[date]] = mapped_column(Date)
    empanelment_category: Mapped[Optional[str]] = mapped_column(
        String(50)
    )  # A, B, C etc.

    # Fee Structure
    default_fee_structure: Mapped[Optional[FeeStructureType]] = mapped_column(
        String(50)
    )
    retainer_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))

    # Performance
    total_cases_handled: Mapped[int] = mapped_column(Integer, default=0)
    cases_won: Mapped[int] = mapped_column(Integer, default=0)
    total_recovery_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), default=Decimal("0")
    )

    # Specializations as JSON array
    specializations: Mapped[Optional[dict]] = mapped_column(JSONB)

    remarks: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    advocates: Mapped[List["Advocate"]] = relationship(
        back_populates="law_firm",
        cascade="all, delete-orphan",
    )


class Advocate(BaseModel, ContactMixin):
    """Individual advocate/lawyer details.

    Stores details of advocates including their enrollment,
    specializations, and fee structures.
    """

    __tablename__ = "mst_advocate"
    __table_args__ = (
        Index("ix_advocate_organization", "organization_id"),
        Index("ix_advocate_law_firm", "law_firm_id"),
        Index("ix_advocate_enrollment", "enrollment_number"),
        UniqueConstraint(
            "organization_id",
            "enrollment_number",
            name="uq_advocate_enrollment",
        ),
    )

    # Organization
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id"),
        nullable=False,
    )

    # Law Firm (optional - some advocates may be independent)
    law_firm_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_law_firm.id"),
    )

    # Personal Details
    salutation: Mapped[Optional[str]] = mapped_column(String(10))  # Mr., Ms., Adv.
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    middle_name: Mapped[Optional[str]] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    full_name: Mapped[str] = mapped_column(String(300), nullable=False, index=True)

    # Professional Details
    enrollment_number: Mapped[str] = mapped_column(String(50), nullable=False)
    bar_council_state: Mapped[BarCouncilState] = mapped_column(String(5), nullable=False)
    enrollment_date: Mapped[Optional[date]] = mapped_column(Date)
    designation: Mapped[str] = mapped_column(
        String(50), default="Advocate"
    )  # Senior Advocate, AOR, etc.

    # Tax Information
    pan: Mapped[Optional[str]] = mapped_column(String(10))

    # Bank Details
    bank_name: Mapped[Optional[str]] = mapped_column(String(100))
    bank_account_number: Mapped[Optional[str]] = mapped_column(String(30))
    bank_ifsc: Mapped[Optional[str]] = mapped_column(String(11))

    # Address
    address_line1: Mapped[Optional[str]] = mapped_column(String(255))
    address_line2: Mapped[Optional[str]] = mapped_column(String(255))
    city: Mapped[Optional[str]] = mapped_column(String(100))
    state_code: Mapped[Optional[str]] = mapped_column(String(2))
    pincode: Mapped[Optional[str]] = mapped_column(String(10))

    # Fee Structure
    default_fee_structure: Mapped[Optional[FeeStructureType]] = mapped_column(
        String(50)
    )
    fee_per_appearance: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))
    hourly_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))
    success_fee_percentage: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))

    # Status
    is_empaneled: Mapped[bool] = mapped_column(Boolean, default=True)
    empanelment_date: Mapped[Optional[date]] = mapped_column(Date)

    # Experience & Specializations
    years_of_experience: Mapped[Optional[int]] = mapped_column(Integer)
    courts_practiced: Mapped[Optional[dict]] = mapped_column(JSONB)  # List of courts

    remarks: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    law_firm: Mapped[Optional["LawFirm"]] = relationship(back_populates="advocates")
    specializations: Mapped[List["AdvocateSpecialization"]] = relationship(
        back_populates="advocate",
        cascade="all, delete-orphan",
    )
    assignments: Mapped[List["AdvocateAssignment"]] = relationship(
        back_populates="advocate",
        cascade="all, delete-orphan",
    )
    performance: Mapped[Optional["AdvocatePerformance"]] = relationship(
        back_populates="advocate",
        uselist=False,
    )


class AdvocateSpecialization(BaseModel):
    """Advocate specialization areas.

    Tracks the areas of expertise for each advocate.
    """

    __tablename__ = "mst_advocate_specialization"
    __table_args__ = (
        Index("ix_advocate_spec_advocate", "advocate_id"),
        UniqueConstraint(
            "advocate_id",
            "specialization_type",
            name="uq_advocate_specialization",
        ),
    )

    # Foreign Keys
    advocate_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_advocate.id"),
        nullable=False,
    )

    # Specialization
    specialization_type: Mapped[SpecializationType] = mapped_column(
        String(50), nullable=False
    )
    experience_years: Mapped[Optional[int]] = mapped_column(Integer)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    cases_handled: Mapped[int] = mapped_column(Integer, default=0)
    success_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))

    remarks: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    advocate: Mapped["Advocate"] = relationship(back_populates="specializations")


class AdvocateAssignment(BaseModel):
    """Assignment of advocate to legal case.

    Tracks which advocates are assigned to which cases
    and their roles in those cases.
    """

    __tablename__ = "txn_advocate_assignment"
    __table_args__ = (
        Index("ix_advocate_assign_advocate", "advocate_id"),
        Index("ix_advocate_assign_case", "legal_case_id"),
        Index("ix_advocate_assign_active", "is_active"),
        UniqueConstraint(
            "legal_case_id",
            "advocate_id",
            "role",
            name="uq_advocate_case_role",
        ),
    )

    # Foreign Keys
    advocate_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_advocate.id"),
        nullable=False,
    )
    legal_case_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("col_legal_case.id"),
        nullable=False,
    )

    # Assignment Details
    role: Mapped[AdvocateRole] = mapped_column(
        String(50), default=AdvocateRole.LEAD_COUNSEL
    )
    assigned_date: Mapped[date] = mapped_column(Date, nullable=False)
    relieved_date: Mapped[Optional[date]] = mapped_column(Date)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Fee Agreement
    fee_structure: Mapped[Optional[FeeStructureType]] = mapped_column(String(50))
    agreed_fee: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))
    success_fee_percentage: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))

    # Performance on this case
    hearings_attended: Mapped[int] = mapped_column(Integer, default=0)
    total_fee_paid: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0")
    )

    # Assignment Reason
    assignment_reason: Mapped[Optional[str]] = mapped_column(Text)
    relieving_reason: Mapped[Optional[str]] = mapped_column(Text)

    remarks: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    advocate: Mapped["Advocate"] = relationship(back_populates="assignments")
    legal_case: Mapped["LegalCase"] = relationship()


class AdvocatePerformance(BaseModel):
    """Performance metrics for advocates.

    Aggregated performance statistics for each advocate.
    """

    __tablename__ = "txn_advocate_performance"
    __table_args__ = (
        Index("ix_advocate_perf_advocate", "advocate_id"),
        UniqueConstraint("advocate_id", name="uq_advocate_performance"),
    )

    # Foreign Keys
    advocate_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_advocate.id"),
        nullable=False,
    )

    # Case Statistics
    total_cases_assigned: Mapped[int] = mapped_column(Integer, default=0)
    active_cases: Mapped[int] = mapped_column(Integer, default=0)
    cases_won: Mapped[int] = mapped_column(Integer, default=0)
    cases_lost: Mapped[int] = mapped_column(Integer, default=0)
    cases_settled: Mapped[int] = mapped_column(Integer, default=0)
    cases_withdrawn: Mapped[int] = mapped_column(Integer, default=0)

    # Hearing Statistics
    total_hearings: Mapped[int] = mapped_column(Integer, default=0)
    hearings_attended: Mapped[int] = mapped_column(Integer, default=0)
    hearings_missed: Mapped[int] = mapped_column(Integer, default=0)

    # Recovery Statistics
    total_claim_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), default=Decimal("0")
    )
    total_recovered_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), default=Decimal("0")
    )
    recovery_percentage: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))

    # Time Statistics
    avg_case_resolution_days: Mapped[Optional[int]] = mapped_column(Integer)
    avg_hearings_per_case: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))

    # Fee Statistics
    total_fee_paid: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), default=Decimal("0")
    )
    avg_fee_per_case: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))

    # Success Rate
    success_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))

    # Rating
    internal_rating: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(3, 2)
    )  # 1.00 to 5.00
    rating_remarks: Mapped[Optional[str]] = mapped_column(Text)

    # Last Updated
    last_calculated_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Relationships
    advocate: Mapped["Advocate"] = relationship(back_populates="performance")
