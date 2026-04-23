"""Asset Insurance models.

This module provides:
- Insurance policy tracking
- Premium payment tracking
- Claims management
- Renewal tracking
- Coverage analytics
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


class InsuranceType(str, Enum):
    """Type of insurance coverage."""
    FIRE = "FIRE"
    THEFT = "THEFT"
    COMPREHENSIVE = "COMPREHENSIVE"
    MOTOR = "MOTOR"
    ELECTRONICS = "ELECTRONICS"
    MACHINERY_BREAKDOWN = "MACHINERY_BREAKDOWN"
    ALL_RISK = "ALL_RISK"
    BURGLARY = "BURGLARY"
    OTHER = "OTHER"


class InsurancePolicyStatus(str, Enum):
    """Insurance policy status."""
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"
    LAPSED = "LAPSED"
    RENEWED = "RENEWED"


class ClaimStatus(str, Enum):
    """Insurance claim status."""
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    DOCUMENTS_REQUIRED = "DOCUMENTS_REQUIRED"
    APPROVED = "APPROVED"
    PARTIALLY_APPROVED = "PARTIALLY_APPROVED"
    REJECTED = "REJECTED"
    SETTLED = "SETTLED"
    WITHDRAWN = "WITHDRAWN"


class InsurancePolicy(BaseModel):
    """Insurance policy master.

    Tracks insurance policies for fixed assets.
    """

    __tablename__ = "mst_insurance_policy"

    # Organization
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id"),
        nullable=False,
        index=True,
    )

    # Policy identification
    policy_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Insurance policy number",
    )

    policy_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    insurance_type: Mapped[InsuranceType] = mapped_column(
        SAEnum(InsuranceType, name="insurance_type_enum", create_type=False),
        nullable=False,
    )

    status: Mapped[InsurancePolicyStatus] = mapped_column(
        SAEnum(InsurancePolicyStatus, name="insurance_policy_status_enum", create_type=False),
        nullable=False,
        default=InsurancePolicyStatus.DRAFT,
    )

    # Insurer details
    insurer_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    insurer_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_vendor.id"),
        nullable=True,
    )

    broker_name: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
    )

    broker_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_vendor.id"),
        nullable=True,
    )

    # Contact details
    contact_person: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )

    contact_phone: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
    )

    contact_email: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )

    claim_helpline: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
    )

    # Policy period
    start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    end_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    # Coverage details
    sum_insured: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        comment="Total sum insured under this policy",
    )

    coverage_description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="What is covered",
    )

    exclusions: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="What is NOT covered",
    )

    deductible_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
        comment="Deductible/Excess per claim",
    )

    deductible_percentage: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        default=Decimal("0.00"),
        comment="Percentage deductible if applicable",
    )

    # Premium details
    base_premium: Mapped[Decimal] = mapped_column(
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

    stamp_duty: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
    )

    total_premium: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
    )

    # Payment
    payment_mode: Mapped[str] = mapped_column(
        String(20),
        default="ANNUAL",
        comment="ANNUAL, HALF_YEARLY, QUARTERLY, MONTHLY",
    )

    next_premium_due: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )

    premium_paid: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    premium_paid_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )

    payment_reference: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )

    # Asset linking
    asset_ids: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String),
        nullable=True,
        comment="List of asset IDs covered",
    )

    covers_all_assets: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="If true, covers all assets of organization",
    )

    # Claims tracking
    total_claims_count: Mapped[int] = mapped_column(
        default=0,
    )

    total_claims_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
    )

    total_settled_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
    )

    # Renewal
    is_renewable: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )

    renewal_reminder_days: Mapped[int] = mapped_column(
        default=30,
    )

    previous_policy_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_insurance_policy.id"),
        nullable=True,
    )

    # Documents
    policy_document_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )

    other_document_urls: Mapped[Optional[List[str]]] = mapped_column(
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

    insurer: Mapped[Optional["Vendor"]] = relationship(
        foreign_keys=[insurer_id],
    )

    broker: Mapped[Optional["Vendor"]] = relationship(
        foreign_keys=[broker_id],
    )

    claims: Mapped[List["InsuranceClaim"]] = relationship(
        back_populates="policy",
        foreign_keys="InsuranceClaim.policy_id",
    )

    __table_args__ = (
        Index("ix_insurance_org_number", "organization_id", "policy_number", unique=True),
        Index("ix_insurance_status", "organization_id", "status"),
        Index("ix_insurance_expiry", "end_date", "status"),
    )

    @property
    def days_until_expiry(self) -> int:
        """Days until policy expires."""
        return (self.end_date - date.today()).days

    @property
    def is_expiring_soon(self) -> bool:
        """Check if expiring within renewal reminder period."""
        return 0 < self.days_until_expiry <= self.renewal_reminder_days

    @property
    def remaining_coverage(self) -> Decimal:
        """Remaining coverage after claims."""
        return self.sum_insured - self.total_settled_amount


class InsuranceClaim(BaseModel):
    """Insurance claim record."""

    __tablename__ = "txn_insurance_claim"

    # Organization
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id"),
        nullable=False,
        index=True,
    )

    # Policy reference
    policy_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_insurance_policy.id"),
        nullable=False,
        index=True,
    )

    # Claim identification
    claim_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    insurer_claim_number: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Claim number assigned by insurer",
    )

    # Asset affected
    asset_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_fixed_asset.id"),
        nullable=False,
        index=True,
    )

    # Claim status
    status: Mapped[ClaimStatus] = mapped_column(
        SAEnum(ClaimStatus, name="claim_status_enum", create_type=False),
        nullable=False,
        default=ClaimStatus.DRAFT,
    )

    # Incident details
    incident_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    incident_description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    incident_location: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
    )

    cause_of_loss: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="FIRE, THEFT, ACCIDENT, NATURAL_DISASTER, etc.",
    )

    # Reporting
    reported_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    reported_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
    )

    fir_number: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="FIR number if theft/burglary",
    )

    fir_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )

    # Claim amounts
    estimated_loss: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        comment="Estimated loss amount",
    )

    claim_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        comment="Amount claimed from insurer",
    )

    deductible_applied: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
    )

    approved_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
    )

    settled_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
    )

    rejection_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Processing dates
    submitted_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )

    surveyor_assigned_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )

    surveyor_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )

    surveyor_report_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )

    approval_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )

    settlement_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )

    payment_received_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )

    payment_reference: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
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

    surveyor_report_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )

    # Notes
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Asset update after claim
    asset_written_off: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    asset_repaired: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    repair_cost: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        foreign_keys=[organization_id],
    )

    policy: Mapped["InsurancePolicy"] = relationship(
        back_populates="claims",
        foreign_keys=[policy_id],
    )

    asset: Mapped["FixedAsset"] = relationship(
        foreign_keys=[asset_id],
    )

    __table_args__ = (
        Index("ix_claim_org_number", "organization_id", "claim_number", unique=True),
        Index("ix_claim_policy", "policy_id", "status"),
        Index("ix_claim_asset", "asset_id"),
        Index("ix_claim_status", "organization_id", "status"),
    )

    @property
    def processing_days(self) -> int:
        """Days since claim was submitted."""
        if not self.submitted_date:
            return 0
        end_date = self.settlement_date or date.today()
        return (end_date - self.submitted_date).days
