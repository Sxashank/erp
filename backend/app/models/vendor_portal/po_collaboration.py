"""Purchase Order Collaboration Models.

Handles PO acknowledgement and change request workflows from vendor portal.
"""

from datetime import date, datetime
from typing import Optional, List, TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    String,
    Boolean,
    ForeignKey,
    Text,
    DateTime,
    Date,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.vendor_portal.enums import (
    POAcknowledgementStatus,
    ChangeRequestType,
    ChangeRequestStatus,
)

if TYPE_CHECKING:
    from app.models.vendor_portal.portal_vendor_user import PortalVendorUser


class POAcknowledgement(BaseModel):
    """Purchase Order acknowledgement from vendor.

    Tracks vendor response to POs - acknowledgement, rejection, or change request.
    """

    __tablename__ = "portal_po_acknowledgement"

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id"),
        nullable=False,
        index=True,
    )

    # PO Reference (FK will be added when PO model exists)
    purchase_order_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    purchase_order_number: Mapped[str] = mapped_column(String(50), nullable=False)

    vendor_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_vendor.id"),
        nullable=False,
        index=True,
    )

    vendor_user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("portal_vendor_user.id"),
        nullable=False,
    )

    # Acknowledgement Status
    status: Mapped[POAcknowledgementStatus] = mapped_column(
        default=POAcknowledgementStatus.PENDING
    )
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Delivery Commitment
    po_delivery_date: Mapped[Optional[date]] = mapped_column(Date)  # Original PO date
    committed_delivery_date: Mapped[Optional[date]] = mapped_column(Date)  # Vendor's commitment
    delivery_remarks: Mapped[Optional[str]] = mapped_column(Text)

    # Rejection Details (if rejected)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text)
    rejection_category: Mapped[Optional[str]] = mapped_column(String(100))

    # Response History (JSON array of all responses)
    response_history: Mapped[Optional[List[dict]]] = mapped_column(JSONB)

    # Relationships
    vendor_user: Mapped["PortalVendorUser"] = relationship(
        "PortalVendorUser",
        foreign_keys=[vendor_user_id],
    )
    change_requests: Mapped[List["POChangeRequest"]] = relationship(
        "POChangeRequest",
        back_populates="acknowledgement",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_portal_po_ack_org_po", "organization_id", "purchase_order_id"),
        Index("ix_portal_po_ack_vendor_status", "vendor_id", "status"),
    )


class POChangeRequest(BaseModel):
    """PO Change Request from vendor.

    Vendors can request changes to PO terms, quantities, prices, etc.
    Goes through approval workflow on buyer side.
    """

    __tablename__ = "portal_po_change_request"

    acknowledgement_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("portal_po_acknowledgement.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id"),
        nullable=False,
        index=True,
    )

    # Change Request Details
    request_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    change_type: Mapped[ChangeRequestType] = mapped_column(nullable=False)
    change_description: Mapped[str] = mapped_column(Text, nullable=False)

    # Line Item Reference (if change is for specific line)
    po_line_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True))
    po_line_number: Mapped[Optional[int]] = mapped_column()

    # Original vs Requested Values
    original_value: Mapped[Optional[str]] = mapped_column(Text)  # JSON
    requested_value: Mapped[Optional[str]] = mapped_column(Text)  # JSON
    justification: Mapped[Optional[str]] = mapped_column(Text)

    # Attachments
    supporting_documents: Mapped[Optional[List[str]]] = mapped_column(JSONB)

    # Workflow Status
    status: Mapped[ChangeRequestStatus] = mapped_column(
        default=ChangeRequestStatus.PENDING
    )
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
    )
    submitted_by_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("portal_vendor_user.id"),
        nullable=False,
    )

    # Review Details
    reviewed_by_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id"),
        nullable=True,
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    review_remarks: Mapped[Optional[str]] = mapped_column(Text)
    approved_value: Mapped[Optional[str]] = mapped_column(Text)  # JSON - for partial approval

    # Communication
    vendor_remarks: Mapped[Optional[str]] = mapped_column(Text)
    buyer_response: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    acknowledgement: Mapped["POAcknowledgement"] = relationship(
        "POAcknowledgement", back_populates="change_requests"
    )
    submitted_by: Mapped["PortalVendorUser"] = relationship(
        "PortalVendorUser",
        foreign_keys=[submitted_by_id],
    )

    __table_args__ = (
        Index("ix_portal_po_cr_ack_status", "acknowledgement_id", "status"),
        Index("ix_portal_po_cr_org_status", "organization_id", "status"),
    )
