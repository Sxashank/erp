"""Fixed Asset model for asset register."""

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Date,
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
from app.core.constants import (
    AssetStatus,
    AssetAcquisitionType,
    AssetDisposalType,
    DepreciationMethod,
    ITActAssetBlock,
)

if TYPE_CHECKING:
    from app.models.masters.organization import Organization
    from app.models.masters.unit import Unit
    from app.models.masters.department import Department
    from app.models.ap_ar.vendor import Vendor
    from app.models.fixed_assets.asset_category import AssetCategory
    from app.models.fixed_assets.depreciation import Depreciation
    from app.models.fixed_assets.asset_transfer import AssetTransfer
    from app.models.fixed_assets.asset_revaluation import AssetRevaluation
    from app.models.finance.voucher import Voucher


class FixedAsset(BaseModel):
    """Fixed asset register model."""

    __tablename__ = "mst_fixed_asset"
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "asset_code", name="uq_fixed_asset_org_code"
        ),
    )

    # Organization
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Basic Info
    asset_code: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        comment="Unique asset code within organization",
    )
    asset_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Category
    category_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_asset_category.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # Location & Custody
    location_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_unit.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Physical location (branch/unit)",
    )
    department_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_department.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    custodian_employee_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
        comment="Employee responsible for the asset",
    )

    # Acquisition Details
    acquisition_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )
    put_to_use_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Date when asset was put to use",
    )
    acquisition_type: Mapped[AssetAcquisitionType] = mapped_column(
        SQLEnum(AssetAcquisitionType),
        default=AssetAcquisitionType.PURCHASE,
        nullable=False,
    )
    vendor_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_vendor.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    invoice_number: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    invoice_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )
    po_number: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )

    # Cost Details
    acquisition_cost: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
        nullable=False,
        comment="Purchase price",
    )
    installation_cost: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    other_costs: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
        nullable=False,
        comment="Transport, taxes, etc.",
    )
    total_cost: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
        nullable=False,
        comment="Total capitalized cost",
    )
    residual_value: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    depreciable_value: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
        nullable=False,
        comment="Total cost - Residual value",
    )

    # Depreciation Settings (can override category defaults)
    useful_life_months: Mapped[int] = mapped_column(
        Integer,
        default=60,
        nullable=False,
    )
    depreciation_method: Mapped[DepreciationMethod] = mapped_column(
        SQLEnum(DepreciationMethod),
        default=DepreciationMethod.SLM,
        nullable=False,
    )
    depreciation_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        default=Decimal("0.00"),
        nullable=False,
        comment="Annual depreciation rate",
    )

    # Depreciation Tracking
    accumulated_depreciation: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    wdv_value: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
        nullable=False,
        comment="Written Down Value (book value)",
    )
    last_depreciation_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )
    depreciation_start_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Date from which depreciation starts",
    )

    # Revaluation & Impairment
    revaluation_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    impairment_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
        nullable=False,
    )

    # ============================================
    # IT Act Depreciation (Second Book)
    # ============================================
    it_act_block: Mapped[Optional[ITActAssetBlock]] = mapped_column(
        SQLEnum(ITActAssetBlock),
        nullable=True,
        comment="IT Act asset block for block depreciation",
    )
    it_act_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        default=Decimal("0.00"),
        nullable=False,
        comment="IT Act depreciation rate (from block)",
    )
    it_accumulated_depreciation: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
        nullable=False,
        comment="Accumulated depreciation as per IT Act",
    )
    it_wdv_value: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
        nullable=False,
        comment="Written Down Value as per IT Act",
    )
    it_last_depreciation_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Last IT depreciation date",
    )
    it_last_depreciation_fy: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
        comment="Last FY for IT depreciation (YYYY-YY format)",
    )
    is_additional_depreciation_eligible: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Eligible for additional 20% depreciation under IT Act",
    )
    additional_depreciation_claimed: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
        nullable=False,
        comment="Additional depreciation already claimed",
    )

    # Physical Details
    make: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    model: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    serial_number: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    quantity: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )

    # Warranty & Insurance
    warranty_start_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )
    warranty_expiry_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )
    insurance_policy_number: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    insurance_provider: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    insurance_expiry_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )
    insured_value: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2),
        nullable=True,
    )

    # AMC
    amc_vendor_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_vendor.id", ondelete="SET NULL"),
        nullable=True,
    )
    amc_start_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )
    amc_expiry_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )
    amc_value: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2),
        nullable=True,
    )

    # Component Tracking (for assets with sub-components)
    parent_asset_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_fixed_asset.id", ondelete="SET NULL"),
        nullable=True,
        comment="Parent asset if this is a component",
    )
    is_component: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # Disposal Details
    disposal_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )
    disposal_type: Mapped[Optional[AssetDisposalType]] = mapped_column(
        SQLEnum(AssetDisposalType),
        nullable=True,
    )
    disposal_value: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2),
        nullable=True,
        comment="Sale/scrap value",
    )
    disposal_gain_loss: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2),
        nullable=True,
        comment="Gain (+) or Loss (-) on disposal",
    )
    disposal_remarks: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    disposal_voucher_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("txn_voucher.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Capitalization Voucher
    capitalization_voucher_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("txn_voucher.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Status
    status: Mapped[AssetStatus] = mapped_column(
        SQLEnum(AssetStatus),
        default=AssetStatus.DRAFT,
        nullable=False,
        index=True,
    )

    # Flexible metadata
    tags: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Custom tags/metadata",
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        lazy="selectin",
    )
    category: Mapped["AssetCategory"] = relationship(
        "AssetCategory",
        lazy="selectin",
    )
    location: Mapped[Optional["Unit"]] = relationship(
        "Unit",
        lazy="selectin",
    )
    department: Mapped[Optional["Department"]] = relationship(
        "Department",
        lazy="selectin",
    )
    vendor: Mapped[Optional["Vendor"]] = relationship(
        "Vendor",
        foreign_keys=[vendor_id],
        lazy="selectin",
    )
    amc_vendor: Mapped[Optional["Vendor"]] = relationship(
        "Vendor",
        foreign_keys=[amc_vendor_id],
        lazy="selectin",
    )
    parent_asset: Mapped[Optional["FixedAsset"]] = relationship(
        "FixedAsset",
        remote_side="FixedAsset.id",
        foreign_keys=[parent_asset_id],
        lazy="selectin",
    )
    components: Mapped[List["FixedAsset"]] = relationship(
        "FixedAsset",
        foreign_keys=[parent_asset_id],
        lazy="selectin",
    )
    depreciation_entries: Mapped[List["Depreciation"]] = relationship(
        "Depreciation",
        back_populates="asset",
        lazy="selectin",
        order_by="desc(Depreciation.depreciation_period)",
    )
    transfers: Mapped[List["AssetTransfer"]] = relationship(
        "AssetTransfer",
        back_populates="asset",
        lazy="selectin",
    )
    revaluations: Mapped[List["AssetRevaluation"]] = relationship(
        "AssetRevaluation",
        back_populates="asset",
        lazy="selectin",
    )
    capitalization_voucher: Mapped[Optional["Voucher"]] = relationship(
        "Voucher",
        foreign_keys=[capitalization_voucher_id],
        lazy="selectin",
    )
    disposal_voucher: Mapped[Optional["Voucher"]] = relationship(
        "Voucher",
        foreign_keys=[disposal_voucher_id],
        lazy="selectin",
    )

    @property
    def book_value(self) -> Decimal:
        """Current book value (WDV)."""
        return self.wdv_value

    @property
    def is_fully_depreciated(self) -> bool:
        """Check if asset is fully depreciated (Companies Act)."""
        return self.wdv_value <= self.residual_value

    @property
    def it_book_value(self) -> Decimal:
        """Current book value as per IT Act."""
        return self.it_wdv_value

    @property
    def is_fully_depreciated_it(self) -> bool:
        """Check if asset is fully depreciated (IT Act)."""
        # IT Act depreciation continues until residual value
        return self.it_wdv_value <= Decimal("1.00")

    @property
    def depreciation_difference(self) -> Decimal:
        """Difference between Companies Act and IT Act accumulated depreciation."""
        return self.accumulated_depreciation - self.it_accumulated_depreciation

    def __repr__(self) -> str:
        return f"<FixedAsset(code={self.asset_code}, name={self.asset_name}, wdv={self.wdv_value})>"
