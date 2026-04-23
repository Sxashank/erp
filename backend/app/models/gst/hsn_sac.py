"""HSN/SAC Code model."""

from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import String, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.core.constants import HSNSACType

if TYPE_CHECKING:
    from app.models.gst.gst_rate import GSTRate


class HSNSAC(BaseModel):
    """HSN (Harmonized System of Nomenclature) / SAC (Services Accounting Code) master."""

    __tablename__ = "mst_hsn_sac"

    code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        unique=True,
        index=True,
        comment="HSN/SAC code e.g. 8471, 998314",
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Description of goods/services",
    )
    hsn_sac_type: Mapped[HSNSACType] = mapped_column(
        SQLEnum(HSNSACType),
        nullable=False,
        comment="Type - HSN for goods, SAC for services",
    )
    chapter: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
        comment="HSN chapter number",
    )
    section: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
        comment="HSN section",
    )
    gst_rate_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_gst_rate.id", ondelete="SET NULL"),
        nullable=True,
        comment="Default GST rate for this HSN/SAC",
    )
    unit_of_measurement: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="Default UOM e.g. NOS, KGS, MTR",
    )

    # Relationships
    gst_rate: Mapped[Optional["GSTRate"]] = relationship(
        "GSTRate",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<HSNSAC(code={self.code}, type={self.hsn_sac_type})>"
