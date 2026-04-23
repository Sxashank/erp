"""Asset Transfer model for Fixed Assets module."""

from datetime import date, datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    String,
    Text,
    Enum as SQLEnum,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.core.constants import AssetTransferStatus

if TYPE_CHECKING:
    from app.models.masters.unit import Unit
    from app.models.masters.department import Department
    from app.models.fixed_assets.fixed_asset import FixedAsset


class AssetTransfer(BaseModel):
    """Asset transfer between locations, departments, or custodians."""

    __tablename__ = "txn_asset_transfer"

    # Asset
    asset_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_fixed_asset.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Transfer Details
    transfer_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )
    transfer_reference: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Internal transfer reference number",
    )

    # From
    from_location_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_unit.id", ondelete="SET NULL"),
        nullable=True,
    )
    from_department_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_department.id", ondelete="SET NULL"),
        nullable=True,
    )
    from_custodian_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
        comment="Employee ID who was custodian before transfer",
    )

    # To
    to_location_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_unit.id", ondelete="SET NULL"),
        nullable=True,
    )
    to_department_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_department.id", ondelete="SET NULL"),
        nullable=True,
    )
    to_custodian_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
        comment="Employee ID who will be custodian after transfer",
    )

    # Reason
    reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Status
    status: Mapped[AssetTransferStatus] = mapped_column(
        SQLEnum(AssetTransferStatus),
        default=AssetTransferStatus.PENDING,
        nullable=False,
        index=True,
    )

    # Approval
    requested_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
    )
    requested_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    approved_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    rejection_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Completion
    completed_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    remarks: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    asset: Mapped["FixedAsset"] = relationship(
        "FixedAsset",
        back_populates="transfers",
        lazy="selectin",
    )
    from_location: Mapped[Optional["Unit"]] = relationship(
        "Unit",
        foreign_keys=[from_location_id],
        lazy="selectin",
    )
    to_location: Mapped[Optional["Unit"]] = relationship(
        "Unit",
        foreign_keys=[to_location_id],
        lazy="selectin",
    )
    from_department: Mapped[Optional["Department"]] = relationship(
        "Department",
        foreign_keys=[from_department_id],
        lazy="selectin",
    )
    to_department: Mapped[Optional["Department"]] = relationship(
        "Department",
        foreign_keys=[to_department_id],
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<AssetTransfer(asset={self.asset_id}, date={self.transfer_date}, status={self.status})>"
