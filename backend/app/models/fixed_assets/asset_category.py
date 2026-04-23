"""Asset Category model for Fixed Assets module."""

from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID

from sqlalchemy import (
    Boolean,
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
from app.core.constants import AssetType, DepreciationMethod

if TYPE_CHECKING:
    from app.models.masters.organization import Organization
    from app.models.finance.account import Account


class AssetCategory(BaseModel):
    """Asset category master for classifying fixed assets."""

    __tablename__ = "mst_asset_category"
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "category_code", name="uq_asset_category_org_code"
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
    category_code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Unique code within organization",
    )
    category_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Hierarchy
    parent_category_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_asset_category.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Parent category for hierarchical structure",
    )

    # Asset Type
    asset_type: Mapped[AssetType] = mapped_column(
        SQLEnum(AssetType),
        default=AssetType.TANGIBLE,
        nullable=False,
        comment="TANGIBLE, INTANGIBLE, RIGHT_OF_USE",
    )

    # Depreciation Settings
    depreciation_method: Mapped[DepreciationMethod] = mapped_column(
        SQLEnum(DepreciationMethod),
        default=DepreciationMethod.SLM,
        nullable=False,
        comment="SLM, WDV, UNIT_OF_PRODUCTION, NO_DEPRECIATION",
    )
    useful_life_years: Mapped[int] = mapped_column(
        Integer,
        default=5,
        nullable=False,
        comment="Default useful life in years",
    )
    residual_value_pct: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        default=Decimal("5.00"),
        nullable=False,
        comment="Residual value as percentage of cost",
    )
    depreciation_rate_slm: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        default=Decimal("0.00"),
        nullable=False,
        comment="Annual depreciation rate for SLM",
    )
    depreciation_rate_wdv: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        default=Decimal("0.00"),
        nullable=False,
        comment="Annual depreciation rate for WDV",
    )

    # IT Act Settings
    it_act_rate: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        comment="Depreciation rate as per Income Tax Act",
    )
    it_act_block: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
        comment="Block of assets under IT Act",
    )

    # Capitalization
    capitalization_threshold: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("5000.00"),
        nullable=False,
        comment="Minimum value for capitalization",
    )

    # GL Account Mapping
    gl_asset_account_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_account.id", ondelete="SET NULL"),
        nullable=True,
        comment="Asset GL account",
    )
    gl_accum_dep_account_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_account.id", ondelete="SET NULL"),
        nullable=True,
        comment="Accumulated depreciation GL account",
    )
    gl_dep_expense_account_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_account.id", ondelete="SET NULL"),
        nullable=True,
        comment="Depreciation expense GL account",
    )
    gl_disposal_gain_account_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_account.id", ondelete="SET NULL"),
        nullable=True,
        comment="Gain on disposal GL account",
    )
    gl_disposal_loss_account_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_account.id", ondelete="SET NULL"),
        nullable=True,
        comment="Loss on disposal GL account",
    )
    gl_revaluation_reserve_account_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_account.id", ondelete="SET NULL"),
        nullable=True,
        comment="Revaluation reserve GL account",
    )
    gl_impairment_account_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_account.id", ondelete="SET NULL"),
        nullable=True,
        comment="Impairment loss GL account",
    )

    # Additional Settings
    requires_insurance: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether assets in this category require insurance",
    )
    requires_amc: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether assets in this category require AMC",
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        lazy="selectin",
    )
    parent_category: Mapped[Optional["AssetCategory"]] = relationship(
        "AssetCategory",
        remote_side="AssetCategory.id",
        lazy="selectin",
    )
    children: Mapped[List["AssetCategory"]] = relationship(
        "AssetCategory",
        back_populates="parent_category",
        lazy="selectin",
    )
    gl_asset_account: Mapped[Optional["Account"]] = relationship(
        "Account",
        foreign_keys=[gl_asset_account_id],
        lazy="selectin",
    )
    gl_accum_dep_account: Mapped[Optional["Account"]] = relationship(
        "Account",
        foreign_keys=[gl_accum_dep_account_id],
        lazy="selectin",
    )
    gl_dep_expense_account: Mapped[Optional["Account"]] = relationship(
        "Account",
        foreign_keys=[gl_dep_expense_account_id],
        lazy="selectin",
    )
    gl_disposal_gain_account: Mapped[Optional["Account"]] = relationship(
        "Account",
        foreign_keys=[gl_disposal_gain_account_id],
        lazy="selectin",
    )
    gl_disposal_loss_account: Mapped[Optional["Account"]] = relationship(
        "Account",
        foreign_keys=[gl_disposal_loss_account_id],
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<AssetCategory(code={self.category_code}, name={self.category_name})>"
