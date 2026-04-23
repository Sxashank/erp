"""TDS Return model for quarterly TDS return filing."""

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID
import enum

from sqlalchemy import Date, DateTime, Numeric, String, Text, ForeignKey, Enum as SQLEnum, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.tds.tds_challan import TDSChallan
    from app.models.masters.organization import Organization
    from app.models.finance.financial_year import FinancialYear


class ReturnType(str, enum.Enum):
    """TDS Return form type."""
    FORM_24Q = "24Q"  # Salary TDS
    FORM_26Q = "26Q"  # Non-salary TDS (other than company deductees)
    FORM_27Q = "27Q"  # TDS on payments to non-residents
    FORM_27EQ = "27EQ"  # TCS


class ReturnStatus(str, enum.Enum):
    """TDS Return filing status."""
    DRAFT = "DRAFT"
    VALIDATED = "VALIDATED"
    GENERATED = "GENERATED"  # File generated
    UPLOADED = "UPLOADED"  # Uploaded to TRACES/NSDL
    ACCEPTED = "ACCEPTED"  # Accepted with provisional receipt
    FILED = "FILED"  # Final filing complete
    REVISED = "REVISED"  # Revision filed
    REJECTED = "REJECTED"


class Quarter(str, enum.Enum):
    """Quarter for TDS return."""
    Q1 = "Q1"  # Apr-Jun
    Q2 = "Q2"  # Jul-Sep
    Q3 = "Q3"  # Oct-Dec
    Q4 = "Q4"  # Jan-Mar


class TDSReturn(BaseModel):
    """
    TDS Return for quarterly filing.

    Aggregates challans and entries for a quarter for generating
    return files and tracking filing status.
    """

    __tablename__ = "txn_tds_return"

    # Organization
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Return identification
    return_type: Mapped[ReturnType] = mapped_column(
        SQLEnum(ReturnType),
        nullable=False,
        index=True,
    )
    financial_year_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_financial_year.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    financial_year: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment="Financial year e.g. 2024-25",
    )
    assessment_year: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment="Assessment year e.g. 2025-26",
    )
    quarter: Mapped[Quarter] = mapped_column(
        SQLEnum(Quarter),
        nullable=False,
        index=True,
    )
    period_from: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    period_to: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    # Status tracking
    status: Mapped[ReturnStatus] = mapped_column(
        SQLEnum(ReturnStatus),
        nullable=False,
        default=ReturnStatus.DRAFT,
        index=True,
    )
    is_original: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="True if original, False if revised",
    )
    revision_number: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="0 for original, 1+ for revisions",
    )
    original_return_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("txn_tds_return.id", ondelete="SET NULL"),
        nullable=True,
        comment="Reference to original return if this is a revision",
    )

    # Deductor details
    deductor_tan: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment="TAN of deductor",
    )
    deductor_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    deductor_pan: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
    )
    deductor_type: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="Type: COMPANY, GOVERNMENT, etc.",
    )
    deductor_category: Mapped[Optional[str]] = mapped_column(
        String(5),
        nullable=True,
        comment="Category code for return",
    )
    deductor_address: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    deductor_city: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    deductor_state: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    deductor_pincode: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
    )
    deductor_email: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    deductor_phone: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
    )

    # Responsible person details
    responsible_person_name: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
    )
    responsible_person_designation: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    responsible_person_address: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    responsible_person_pan: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
    )

    # Summary amounts
    total_challans: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    total_deductees: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    total_amount_paid: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="Total amount paid/credited",
    )
    total_tds_deducted: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    total_tds_deposited: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    total_interest: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    total_late_fee: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    # File generation
    file_generated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    file_name: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
    )
    file_path: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    file_hash: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        comment="SHA256 hash of generated file",
    )

    # Filing details
    provisional_receipt_number: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="PRN from TRACES upload",
    )
    token_number: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Token number from NSDL",
    )
    acknowledgment_number: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Final ARN after acceptance",
    )
    filed_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )
    accepted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Due date and late filing
    due_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Return filing due date",
    )
    is_late: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    days_late: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # Validation
    validation_errors: Mapped[Optional[List[dict]]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Validation errors if any",
    )
    validation_warnings: Mapped[Optional[List[dict]]] = mapped_column(
        JSONB,
        nullable=True,
    )
    last_validated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Additional metadata
    remarks: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    extra_data: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        lazy="selectin",
    )
    fy: Mapped["FinancialYear"] = relationship(
        "FinancialYear",
        foreign_keys=[financial_year_id],
        lazy="selectin",
    )
    original_return: Mapped[Optional["TDSReturn"]] = relationship(
        "TDSReturn",
        remote_side="TDSReturn.id",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<TDSReturn({self.return_type.value} {self.financial_year} {self.quarter.value})>"

    @property
    def return_period(self) -> str:
        """Get return period string."""
        return f"{self.return_type.value} {self.financial_year} {self.quarter.value}"

    def calculate_late_fee(self) -> Decimal:
        """Calculate late filing fee.

        Late fee: Rs. 200 per day (max Rs. 10,000 for quarterly returns)
        """
        if not self.is_late or self.days_late <= 0:
            return Decimal("0")

        fee = Decimal("200") * self.days_late
        return min(fee, Decimal("10000"))
