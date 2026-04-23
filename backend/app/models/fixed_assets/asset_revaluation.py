"""Asset Revaluation model for Fixed Assets module."""

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import (
    Date,
    ForeignKey,
    Numeric,
    String,
    Text,
    Enum as SQLEnum,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.core.constants import RevaluationType

if TYPE_CHECKING:
    from app.models.fixed_assets.fixed_asset import FixedAsset
    from app.models.finance.voucher import Voucher


class AssetRevaluation(BaseModel):
    """Asset revaluation and impairment records."""

    __tablename__ = "txn_asset_revaluation"

    # Asset
    asset_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_fixed_asset.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Revaluation Details
    revaluation_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )
    revaluation_type: Mapped[RevaluationType] = mapped_column(
        SQLEnum(RevaluationType),
        nullable=False,
        comment="INCREASE, DECREASE, IMPAIRMENT",
    )

    # Values
    previous_value: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        comment="WDV before revaluation",
    )
    new_value: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        comment="WDV after revaluation",
    )
    revaluation_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        comment="Absolute change in value",
    )

    # Previous accumulated depreciation (for adjustment)
    previous_accumulated_depreciation: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    new_accumulated_depreciation: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
        nullable=False,
    )

    # Valuation Details
    valuer_name: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
    )
    valuation_report_number: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    valuation_report_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )
    valuation_method: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="e.g., Market Value, Replacement Cost, DCF",
    )

    # GL Posting
    voucher_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("txn_voucher.id", ondelete="SET NULL"),
        nullable=True,
    )

    reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    remarks: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    asset: Mapped["FixedAsset"] = relationship(
        "FixedAsset",
        back_populates="revaluations",
        lazy="selectin",
    )
    voucher: Mapped[Optional["Voucher"]] = relationship(
        "Voucher",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<AssetRevaluation(asset={self.asset_id}, type={self.revaluation_type}, amount={self.revaluation_amount})>"
