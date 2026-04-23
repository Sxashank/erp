"""GST Registration model."""

from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import String, Text, ForeignKey, Enum as SQLEnum, Boolean
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.core.constants import GSTRegistrationType

if TYPE_CHECKING:
    from app.models.masters.organization import Organization
    from app.models.masters.unit import Unit


class GSTRegistration(BaseModel):
    """GST Registration master for organization/unit GSTIN details."""

    __tablename__ = "mst_gst_registration"

    gstin: Mapped[str] = mapped_column(
        String(15),
        nullable=False,
        unique=True,
        index=True,
        comment="15-digit GSTIN number",
    )
    legal_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Legal name as per GST registration",
    )
    trade_name: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="Trade name / business name",
    )
    registration_type: Mapped[GSTRegistrationType] = mapped_column(
        SQLEnum(GSTRegistrationType),
        nullable=False,
        default=GSTRegistrationType.REGULAR,
        comment="Type of GST registration",
    )
    state_code: Mapped[str] = mapped_column(
        String(2),
        nullable=False,
        comment="2-digit state code from GSTIN",
    )
    state_name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="State name",
    )
    address: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Registered address",
    )
    pincode: Mapped[Optional[str]] = mapped_column(
        String(6),
        nullable=True,
        comment="PIN code",
    )
    is_e_invoice_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="E-Invoice enabled for this GSTIN",
    )
    e_invoice_username: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="E-Invoice portal username",
    )
    e_invoice_password_encrypted: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Encrypted E-Invoice portal password",
    )
    is_e_way_bill_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="E-Way Bill enabled for this GSTIN",
    )
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    unit_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_unit.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Unit specific GSTIN (for branches)",
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        lazy="selectin",
    )
    unit: Mapped[Optional["Unit"]] = relationship(
        "Unit",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<GSTRegistration(gstin={self.gstin}, type={self.registration_type})>"
