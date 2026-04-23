"""Fixed Assets Configuration model for per-organization settings."""

from decimal import Decimal
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.masters.organization import Organization


class FAConfiguration(BaseModel):
    """
    Fixed Assets module configuration per organization.

    Stores configurable settings for asset management including:
    - Asset code format and prefix
    - Financial year settings
    - Approval thresholds
    - Depreciation defaults
    - Alert/reminder configurations
    - Pagination settings
    """

    __tablename__ = "mst_fa_configuration"
    __table_args__ = (
        UniqueConstraint("organization_id", name="uq_fa_config_org"),
    )

    # Organization
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # =============================================
    # Asset Code Format Settings
    # =============================================
    asset_code_prefix: Mapped[str] = mapped_column(
        String(10),
        default="FA",
        nullable=False,
        comment="Prefix for asset codes (e.g., FA, AST)",
    )
    asset_code_format: Mapped[str] = mapped_column(
        String(100),
        default="{prefix}/{category}/{year}/{sequence:05d}",
        nullable=False,
        comment="Format pattern for generating asset codes",
    )
    asset_code_separator: Mapped[str] = mapped_column(
        String(1),
        default="/",
        nullable=False,
        comment="Separator character in asset code",
    )
    auto_generate_code: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Auto-generate asset codes on creation",
    )

    # =============================================
    # Financial Year Settings
    # =============================================
    fy_start_month: Mapped[int] = mapped_column(
        Integer,
        default=4,
        nullable=False,
        comment="Financial year start month (1-12). Default: April (4)",
    )
    fy_start_day: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
        comment="Financial year start day",
    )

    # =============================================
    # Approval Thresholds (Maker-Checker)
    # =============================================
    creation_approval_threshold: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("1000000.00"),  # 10 Lakhs
        nullable=False,
        comment="Asset creation requires approval above this amount",
    )
    disposal_approval_threshold: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),  # All disposals require approval
        nullable=False,
        comment="Asset disposal requires approval above this amount (0 = all)",
    )
    revaluation_approval_threshold: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),  # All revaluations require approval
        nullable=False,
        comment="Revaluation requires approval above this amount (0 = all)",
    )
    transfer_requires_approval: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Require approval for asset transfers",
    )

    # =============================================
    # Depreciation Settings
    # =============================================
    days_in_year: Mapped[int] = mapped_column(
        Integer,
        default=365,
        nullable=False,
        comment="Days in year for depreciation calculation (365 or 360)",
    )
    pro_rata_method: Mapped[str] = mapped_column(
        String(20),
        default="DAILY",
        nullable=False,
        comment="Pro-rata calculation: DAILY, MONTHLY, HALF_YEARLY, FULL_MONTH",
    )
    min_asset_value_for_depreciation: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("5000.00"),
        nullable=False,
        comment="Minimum asset value to depreciate (below = expense)",
    )
    depreciation_posting_auto_approve: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Auto-approve depreciation run posting",
    )

    # =============================================
    # Alert/Reminder Settings (days before event)
    # =============================================
    amc_expiry_reminder_days: Mapped[int] = mapped_column(
        Integer,
        default=30,
        nullable=False,
        comment="Days before AMC expiry to trigger reminder",
    )
    insurance_expiry_reminder_days: Mapped[int] = mapped_column(
        Integer,
        default=30,
        nullable=False,
        comment="Days before insurance expiry to trigger reminder",
    )
    warranty_expiry_reminder_days: Mapped[int] = mapped_column(
        Integer,
        default=30,
        nullable=False,
        comment="Days before warranty expiry to trigger reminder",
    )
    lease_expiry_reminder_days: Mapped[int] = mapped_column(
        Integer,
        default=90,
        nullable=False,
        comment="Days before lease expiry to trigger reminder",
    )
    lease_payment_reminder_days: Mapped[int] = mapped_column(
        Integer,
        default=7,
        nullable=False,
        comment="Days before lease payment due to trigger reminder",
    )

    # =============================================
    # Physical Verification Settings
    # =============================================
    pv_frequency_months: Mapped[int] = mapped_column(
        Integer,
        default=12,
        nullable=False,
        comment="Physical verification frequency in months",
    )
    pv_tolerance_percentage: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        default=Decimal("5.00"),
        nullable=False,
        comment="Acceptable variance percentage for physical verification",
    )

    # =============================================
    # GL Integration Settings
    # =============================================
    auto_post_capitalization: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Auto-post GL entries on capitalization",
    )
    auto_post_disposal: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Auto-post GL entries on disposal",
    )
    auto_post_depreciation: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Auto-post GL entries on depreciation run",
    )

    # =============================================
    # Pagination Settings
    # =============================================
    default_page_size: Mapped[int] = mapped_column(
        Integer,
        default=50,
        nullable=False,
        comment="Default items per page in listings",
    )
    max_page_size: Mapped[int] = mapped_column(
        Integer,
        default=200,
        nullable=False,
        comment="Maximum items per page allowed",
    )

    # =============================================
    # Additional Settings (JSONB for flexibility)
    # =============================================
    custom_settings: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Additional custom settings as key-value pairs",
    )
    notification_emails: Mapped[Optional[list]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Email addresses for FA notifications",
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<FAConfiguration(org={self.organization_id})>"
