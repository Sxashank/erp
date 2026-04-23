"""Depreciation models for Fixed Assets module."""

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
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.core.constants import DepreciationType, DepreciationBook, ITActAssetBlock

if TYPE_CHECKING:
    from app.models.masters.organization import Organization
    from app.models.fixed_assets.fixed_asset import FixedAsset
    from app.models.finance.voucher import Voucher


class DepreciationRunStatus(str):
    """Status of depreciation run."""
    DRAFT = "DRAFT"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    POSTED = "POSTED"
    CANCELLED = "CANCELLED"


class DepreciationRun(BaseModel):
    """Depreciation batch run for periodic processing."""

    __tablename__ = "txn_depreciation_run"
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "depreciation_period", "depreciation_book",
            name="uq_depreciation_run_org_period_book"
        ),
    )

    # Organization
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Depreciation Book
    depreciation_book: Mapped[DepreciationBook] = mapped_column(
        SQLEnum(DepreciationBook),
        default=DepreciationBook.COMPANIES_ACT,
        nullable=False,
        index=True,
        comment="Companies Act or IT Act depreciation",
    )

    # Period
    depreciation_period: Mapped[str] = mapped_column(
        String(7),
        nullable=False,
        index=True,
        comment="Period in YYYY-MM format",
    )
    period_from: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    period_to: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    # Summary
    total_assets: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    total_depreciation: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    processed_assets: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    skipped_assets: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Fully depreciated or inactive assets",
    )

    # Processing
    status: Mapped[str] = mapped_column(
        String(20),
        default=DepreciationRunStatus.DRAFT,
        nullable=False,
        index=True,
    )
    run_started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    run_completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    run_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
    )

    # GL Posting
    voucher_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("txn_voucher.id", ondelete="SET NULL"),
        nullable=True,
    )
    posted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    posted_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
    )

    remarks: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        lazy="selectin",
    )
    entries: Mapped[List["Depreciation"]] = relationship(
        "Depreciation",
        back_populates="depreciation_run",
        lazy="selectin",
    )
    voucher: Mapped[Optional["Voucher"]] = relationship(
        "Voucher",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<DepreciationRun(period={self.depreciation_period}, total={self.total_depreciation})>"


class Depreciation(BaseModel):
    """Individual asset depreciation entry."""

    __tablename__ = "txn_depreciation"
    __table_args__ = (
        UniqueConstraint(
            "asset_id", "depreciation_period", "depreciation_type", "depreciation_book",
            name="uq_depreciation_asset_period_type_book"
        ),
    )

    # Asset
    asset_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_fixed_asset.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Run Reference
    depreciation_run_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("txn_depreciation_run.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Period
    depreciation_period: Mapped[str] = mapped_column(
        String(7),
        nullable=False,
        index=True,
        comment="Period in YYYY-MM format",
    )
    period_from: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    period_to: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    days_in_period: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Number of days for pro-rata calculation",
    )

    # Values
    opening_wdv: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        comment="WDV at start of period",
    )
    depreciation_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        comment="Rate applied",
    )
    depreciation_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
    )
    accumulated_depreciation: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        comment="Total accumulated after this entry",
    )
    closing_wdv: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        comment="WDV at end of period",
    )

    # Type
    depreciation_type: Mapped[DepreciationType] = mapped_column(
        SQLEnum(DepreciationType),
        default=DepreciationType.REGULAR,
        nullable=False,
    )

    # Depreciation Book
    depreciation_book: Mapped[DepreciationBook] = mapped_column(
        SQLEnum(DepreciationBook),
        default=DepreciationBook.COMPANIES_ACT,
        nullable=False,
        index=True,
        comment="Companies Act or IT Act depreciation",
    )

    # GL Posting
    voucher_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("txn_voucher.id", ondelete="SET NULL"),
        nullable=True,
    )
    is_posted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # Reversal tracking
    is_reversed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    reversal_of_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("txn_depreciation.id", ondelete="SET NULL"),
        nullable=True,
        comment="If this is a reversal, reference to original",
    )
    reversed_by_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("txn_depreciation.id", ondelete="SET NULL"),
        nullable=True,
        comment="Reference to the reversal entry",
    )

    remarks: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    asset: Mapped["FixedAsset"] = relationship(
        "FixedAsset",
        back_populates="depreciation_entries",
        lazy="selectin",
    )
    depreciation_run: Mapped[Optional["DepreciationRun"]] = relationship(
        "DepreciationRun",
        back_populates="entries",
        lazy="selectin",
    )
    voucher: Mapped[Optional["Voucher"]] = relationship(
        "Voucher",
        lazy="selectin",
    )
    reversal_of: Mapped[Optional["Depreciation"]] = relationship(
        "Depreciation",
        remote_side="Depreciation.id",
        foreign_keys=[reversal_of_id],
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Depreciation(asset={self.asset_id}, period={self.depreciation_period}, amount={self.depreciation_amount})>"


class ITBlockSummary(BaseModel):
    """IT Act Block-level depreciation summary.

    Under IT Act, assets in the same block are pooled together and depreciation
    is calculated on the pooled WDV. This table tracks block-level balances
    for each financial year.
    """

    __tablename__ = "txn_it_block_summary"
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "it_block", "financial_year",
            name="uq_it_block_summary_org_block_fy"
        ),
    )

    # Organization
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Block Identity
    it_block: Mapped[ITActAssetBlock] = mapped_column(
        SQLEnum(ITActAssetBlock),
        nullable=False,
        index=True,
        comment="IT Act asset block (BLOCK_1 to BLOCK_12)",
    )
    financial_year: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        index=True,
        comment="Financial Year in YYYY-YY format",
    )

    # Block Values
    opening_wdv: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
        nullable=False,
        comment="Block WDV at start of FY",
    )
    additions_during_year: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
        nullable=False,
        comment="Assets added to block during FY",
    )
    disposals_during_year: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
        nullable=False,
        comment="Assets disposed from block during FY",
    )
    depreciation_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        comment="Applicable depreciation rate for block",
    )
    depreciation_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
        nullable=False,
        comment="Total depreciation for block during FY",
    )
    additional_depreciation: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
        nullable=False,
        comment="Additional 20% depreciation for new manufacturing assets",
    )
    closing_wdv: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
        nullable=False,
        comment="Block WDV at end of FY",
    )

    # Asset Count
    asset_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Number of assets in block",
    )

    # Processing Status
    is_finalized: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether FY depreciation is finalized",
    )
    finalized_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    finalized_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
    )

    remarks: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<ITBlockSummary(block={self.it_block}, fy={self.financial_year}, wdv={self.closing_wdv})>"
