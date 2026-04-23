"""Lease Accounting models as per Ind AS 116.

Ind AS 116 requires lessees to recognize:
- Right-of-Use Asset (ROUA) on the balance sheet
- Lease Liability for future lease payments
- Interest expense on lease liability
- Depreciation on ROUA

This module implements complete lease accounting for NBFC compliance.
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
    from app.models.masters.unit import Unit
    from app.models.masters.department import Department
    from app.models.masters.gl_account import GLAccount


class LeaseType(str, Enum):
    """Type of lease."""
    FINANCE = "FINANCE"  # Previously capital lease
    OPERATING = "OPERATING"  # Short-term or low-value
    SUBLEASE = "SUBLEASE"


class LeaseAssetType(str, Enum):
    """Type of leased asset."""
    BUILDING = "BUILDING"
    VEHICLE = "VEHICLE"
    EQUIPMENT = "EQUIPMENT"
    LAND = "LAND"
    IT_EQUIPMENT = "IT_EQUIPMENT"
    FURNITURE = "FURNITURE"
    OTHER = "OTHER"


class LeaseStatus(str, Enum):
    """Lease lifecycle status."""
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    MODIFIED = "MODIFIED"
    TERMINATED = "TERMINATED"
    EXPIRED = "EXPIRED"


class PaymentFrequency(str, Enum):
    """Lease payment frequency."""
    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"
    HALF_YEARLY = "HALF_YEARLY"
    YEARLY = "YEARLY"


class Lease(BaseModel):
    """Lease master with Ind AS 116 compliance.

    This model tracks:
    - Lease terms and conditions
    - Right-of-Use Asset (ROUA) valuation
    - Lease liability calculations
    - Payment schedules
    """

    __tablename__ = "mst_lease"

    # Organization reference
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id"),
        nullable=False,
        index=True,
    )

    # Lease identification
    lease_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Unique lease reference number",
    )

    lease_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Descriptive name for the lease",
    )

    lease_type: Mapped[LeaseType] = mapped_column(
        SAEnum(LeaseType, name="lease_type_enum", create_type=False),
        nullable=False,
        default=LeaseType.FINANCE,
    )

    asset_type: Mapped[LeaseAssetType] = mapped_column(
        SAEnum(LeaseAssetType, name="lease_asset_type_enum", create_type=False),
        nullable=False,
    )

    status: Mapped[LeaseStatus] = mapped_column(
        SAEnum(LeaseStatus, name="lease_status_enum", create_type=False),
        nullable=False,
        default=LeaseStatus.DRAFT,
    )

    # Lessor details
    lessor_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_vendor.id"),
        nullable=True,
        comment="Lessor/Landlord",
    )

    lessor_name: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="Lessor name if not in vendor master",
    )

    # Asset details
    asset_description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Description of leased asset",
    )

    asset_location_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_unit.id"),
        nullable=True,
    )

    department_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_department.id"),
        nullable=True,
    )

    # Lease terms
    commencement_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Lease start date",
    )

    end_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Lease end date",
    )

    lease_term_months: Mapped[int] = mapped_column(
        nullable=False,
        comment="Total lease term in months",
    )

    # Payment details
    payment_frequency: Mapped[PaymentFrequency] = mapped_column(
        SAEnum(PaymentFrequency, name="payment_frequency_enum", create_type=False),
        nullable=False,
        default=PaymentFrequency.MONTHLY,
    )

    payment_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        comment="Periodic lease payment amount",
    )

    payment_day: Mapped[int] = mapped_column(
        nullable=False,
        default=1,
        comment="Day of month/quarter when payment is due",
    )

    payment_in_advance: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="True if payments are made in advance",
    )

    # Variable lease payments
    has_variable_payments: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    variable_payment_description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Escalation
    has_escalation: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    escalation_percentage: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        default=Decimal("0.00"),
        comment="Annual escalation percentage",
    )

    escalation_frequency_months: Mapped[int] = mapped_column(
        default=12,
        comment="Months between escalations",
    )

    # Security deposit
    security_deposit: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
    )

    # Options
    has_renewal_option: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    renewal_term_months: Mapped[Optional[int]] = mapped_column(
        nullable=True,
    )

    renewal_reasonably_certain: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="If true, renewal is included in lease term",
    )

    has_purchase_option: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    purchase_option_price: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
    )

    purchase_reasonably_certain: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    has_termination_option: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    termination_penalty: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
    )

    # Discount rate (Incremental Borrowing Rate)
    discount_rate: Mapped[Decimal] = mapped_column(
        Numeric(8, 4),
        nullable=False,
        comment="Incremental borrowing rate for NPV calculation",
    )

    # Initial direct costs
    initial_direct_costs: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
        comment="Costs directly attributable to obtaining the lease",
    )

    # Restoration costs
    estimated_restoration_cost: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
        comment="Estimated cost to restore asset at lease end",
    )

    # Ind AS 116 Calculated Values
    # Right-of-Use Asset
    roua_initial_value: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
        comment="Initial ROUA = Lease Liability + Initial Costs + Restoration",
    )

    roua_accumulated_depreciation: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
    )

    roua_carrying_value: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
        comment="ROUA - Accumulated Depreciation",
    )

    roua_depreciation_method: Mapped[str] = mapped_column(
        String(20),
        default="SLM",
        comment="Depreciation method for ROUA",
    )

    # Lease Liability
    lease_liability_initial: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
        comment="NPV of lease payments at commencement",
    )

    lease_liability_current: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
        comment="Current lease liability balance",
    )

    # Bifurcation for balance sheet
    lease_liability_current_portion: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
        comment="Due within 12 months",
    )

    lease_liability_non_current: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
        comment="Due after 12 months",
    )

    # Totals
    total_lease_payments: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
        comment="Total undiscounted lease payments",
    )

    total_interest_expense: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
        comment="Total interest over lease term",
    )

    interest_expense_ytd: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
        comment="Interest expense year-to-date",
    )

    depreciation_expense_ytd: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
        comment="ROUA depreciation year-to-date",
    )

    # Processing dates
    last_payment_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )

    next_payment_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )

    last_interest_calculation_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )

    last_depreciation_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )

    # GL Account mappings
    roua_account_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_account.id"),
        nullable=True,
        comment="GL account for Right-of-Use Asset",
    )

    lease_liability_account_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_account.id"),
        nullable=True,
        comment="GL account for Lease Liability",
    )

    interest_expense_account_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_account.id"),
        nullable=True,
        comment="GL account for Interest Expense",
    )

    depreciation_expense_account_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_account.id"),
        nullable=True,
        comment="GL account for ROUA Depreciation",
    )

    accumulated_depreciation_account_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_account.id"),
        nullable=True,
    )

    # Modification tracking
    is_modified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    modification_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )

    modification_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Notes
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        back_populates="leases",
        foreign_keys=[organization_id],
    )

    lessor: Mapped[Optional["Vendor"]] = relationship(
        foreign_keys=[lessor_id],
    )

    location: Mapped[Optional["Unit"]] = relationship(
        foreign_keys=[asset_location_id],
    )

    department: Mapped[Optional["Department"]] = relationship(
        foreign_keys=[department_id],
    )

    # Schedule relationship
    payment_schedule: Mapped[List["LeasePaymentSchedule"]] = relationship(
        back_populates="lease",
        cascade="all, delete-orphan",
        order_by="LeasePaymentSchedule.payment_number",
    )

    __table_args__ = (
        Index("ix_lease_org_number", "organization_id", "lease_number", unique=True),
        Index("ix_lease_status", "organization_id", "status"),
        Index("ix_lease_dates", "commencement_date", "end_date"),
    )

    @property
    def remaining_term_months(self) -> int:
        """Calculate remaining lease term in months."""
        from datetime import date as dt
        today = dt.today()
        if today >= self.end_date:
            return 0
        remaining_days = (self.end_date - today).days
        return max(0, remaining_days // 30)

    @property
    def is_short_term(self) -> bool:
        """Check if lease qualifies for short-term exemption (< 12 months)."""
        return self.lease_term_months <= 12

    @property
    def is_low_value(self) -> bool:
        """Check if lease qualifies for low-value exemption (< USD 5000)."""
        # Assuming INR 4 lakhs as threshold
        return self.roua_initial_value < Decimal("400000.00")


class LeasePaymentSchedule(BaseModel):
    """Lease payment schedule with principal and interest breakdown.

    This table stores the amortization schedule for each lease,
    showing how each payment is split between principal and interest.
    """

    __tablename__ = "txn_lease_payment_schedule"

    # Lease reference
    lease_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_lease.id"),
        nullable=False,
        index=True,
    )

    # Payment identification
    payment_number: Mapped[int] = mapped_column(
        nullable=False,
        comment="Sequential payment number",
    )

    payment_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Due date for this payment",
    )

    financial_year: Mapped[str] = mapped_column(
        String(7),
        nullable=False,
        comment="Financial year (YYYY-YY format)",
    )

    # Payment breakdown
    opening_liability: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        comment="Lease liability at start of period",
    )

    payment_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        comment="Total payment amount",
    )

    interest_component: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        comment="Interest portion of payment",
    )

    principal_component: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        comment="Principal portion of payment",
    )

    closing_liability: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        comment="Lease liability at end of period",
    )

    # ROUA depreciation for the period
    depreciation_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
        comment="ROUA depreciation for this period",
    )

    roua_carrying_value: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
        comment="ROUA carrying value after depreciation",
    )

    # Processing status
    is_paid: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    paid_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )

    paid_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
    )

    payment_reference: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Payment voucher/transaction reference",
    )

    # Interest posted
    interest_posted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    interest_voucher_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
        comment="GL voucher for interest posting",
    )

    # Depreciation posted
    depreciation_posted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    depreciation_voucher_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
        comment="GL voucher for depreciation posting",
    )

    # Variance tracking
    variance_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
        comment="Difference between scheduled and actual payment",
    )

    variance_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationship
    lease: Mapped["Lease"] = relationship(
        back_populates="payment_schedule",
    )

    __table_args__ = (
        Index("ix_lease_schedule_lease", "lease_id", "payment_number", unique=True),
        Index("ix_lease_schedule_date", "payment_date"),
        Index("ix_lease_schedule_unpaid", "lease_id", "is_paid"),
    )


class LeaseModification(BaseModel):
    """Track lease modifications as per Ind AS 116.

    A lease modification requires remeasurement of:
    - Lease liability using revised discount rate
    - ROUA adjustment
    """

    __tablename__ = "txn_lease_modification"

    lease_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_lease.id"),
        nullable=False,
        index=True,
    )

    modification_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    modification_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="TERM_EXTENSION, PAYMENT_CHANGE, SCOPE_CHANGE, etc.",
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # Before modification
    old_lease_term_months: Mapped[int] = mapped_column(nullable=False)
    old_payment_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    old_discount_rate: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False)
    old_lease_liability: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    old_roua_value: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)

    # After modification
    new_lease_term_months: Mapped[int] = mapped_column(nullable=False)
    new_payment_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    new_discount_rate: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False)
    new_lease_liability: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    new_roua_value: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)

    # Adjustment
    liability_adjustment: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        comment="Change in lease liability",
    )

    roua_adjustment: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        comment="Change in ROUA",
    )

    gain_loss_on_modification: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
        comment="P&L impact if scope decreased",
    )

    # GL posting
    adjustment_voucher_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
    )

    approved_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
    )

    approved_at: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )

    __table_args__ = (
        Index("ix_lease_mod_lease", "lease_id", "modification_date"),
    )
