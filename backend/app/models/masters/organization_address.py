"""Organization Address model."""

from decimal import Decimal
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Index, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.masters.organization import Organization


class OrganizationAddress(BaseModel):
    """Organization Address model for storing multiple addresses."""

    __tablename__ = "mst_organization_address"

    # Organization
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Address Type
    address_type: Mapped[str] = mapped_column(
        String(30), nullable=False, index=True
    )  # REGISTERED, CORPORATE, FACTORY, WAREHOUSE, COMMUNICATION
    address_label: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )  # Custom label like "Mumbai Factory"

    # Address Fields
    address_line1: Mapped[str] = mapped_column(String(255), nullable=False)
    address_line2: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    address_line3: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    landmark: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    district: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state_code: Mapped[str] = mapped_column(String(2), nullable=False)
    state_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    pincode: Mapped[str] = mapped_column(String(10), nullable=False)
    country: Mapped[str] = mapped_column(String(50), nullable=False, default="India")

    # Contact at this address
    contact_person: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Geo-coordinates (optional)
    latitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 8), nullable=True)
    longitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(11, 8), nullable=True)

    # Flags
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="addresses"
    )

    __table_args__ = (
        Index("ix_org_address_org_type", "organization_id", "address_type"),
        Index("ix_org_address_org_active", "organization_id", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<OrganizationAddress {self.address_type} - {self.city}>"
