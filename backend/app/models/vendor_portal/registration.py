"""Vendor Registration Models.

Handles vendor self-registration workflow with document uploads.
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
    Integer,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.vendor_portal.enums import (
    BusinessType,
    RegistrationStatus,
    RegistrationDocumentType,
)

if TYPE_CHECKING:
    from app.models.ap_ar.vendor import Vendor
    from app.models.masters.user import User


class VendorRegistration(BaseModel):
    """Vendor self-registration request.

    Captures all information needed to create a vendor master.
    Goes through approval workflow before vendor is created.
    """

    __tablename__ = "portal_vendor_registration"

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id"),
        nullable=False,
        index=True,
    )

    # Registration Number (auto-generated)
    registration_number: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False
    )

    # Company Details
    company_name: Mapped[str] = mapped_column(String(200), nullable=False)
    trade_name: Mapped[Optional[str]] = mapped_column(String(200))
    business_type: Mapped[BusinessType] = mapped_column(nullable=False)
    incorporation_date: Mapped[Optional[date]] = mapped_column(Date)
    website: Mapped[Optional[str]] = mapped_column(String(255))

    # Tax & Registration Numbers
    pan: Mapped[str] = mapped_column(String(10), nullable=False)
    gstin: Mapped[Optional[str]] = mapped_column(String(15))
    cin: Mapped[Optional[str]] = mapped_column(String(21))  # Company Identification Number
    msme_number: Mapped[Optional[str]] = mapped_column(String(20))
    msme_category: Mapped[Optional[str]] = mapped_column(String(20))  # MICRO, SMALL, MEDIUM

    # Registered Address
    registered_address: Mapped[str] = mapped_column(Text, nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(100), nullable=False)
    state_code: Mapped[Optional[str]] = mapped_column(String(2))
    pincode: Mapped[str] = mapped_column(String(10), nullable=False)
    country: Mapped[str] = mapped_column(String(50), default="India", nullable=False)

    # Primary Contact Person
    contact_name: Mapped[str] = mapped_column(String(100), nullable=False)
    contact_email: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_phone: Mapped[str] = mapped_column(String(15), nullable=False)
    contact_designation: Mapped[Optional[str]] = mapped_column(String(100))

    # Bank Details
    bank_name: Mapped[str] = mapped_column(String(100), nullable=False)
    bank_branch: Mapped[str] = mapped_column(String(100), nullable=False)
    account_number: Mapped[str] = mapped_column(String(50), nullable=False)
    ifsc_code: Mapped[str] = mapped_column(String(11), nullable=False)
    account_holder_name: Mapped[Optional[str]] = mapped_column(String(200))

    # Products/Services Offered
    product_categories: Mapped[Optional[List[str]]] = mapped_column(JSONB)
    product_description: Mapped[Optional[str]] = mapped_column(Text)
    service_areas: Mapped[Optional[List[str]]] = mapped_column(JSONB)

    # Additional Information
    annual_turnover: Mapped[Optional[str]] = mapped_column(String(50))
    employee_count: Mapped[Optional[int]] = mapped_column(Integer)
    years_in_business: Mapped[Optional[int]] = mapped_column(Integer)
    key_clients: Mapped[Optional[str]] = mapped_column(Text)
    certifications: Mapped[Optional[List[str]]] = mapped_column(JSONB)

    # Workflow Status
    status: Mapped[RegistrationStatus] = mapped_column(
        default=RegistrationStatus.DRAFT
    )
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Review Information
    reviewed_by_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id"),
        nullable=True,
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    review_remarks: Mapped[Optional[str]] = mapped_column(Text)

    # Additional Info Request
    additional_info_requested_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )
    additional_info_request: Mapped[Optional[str]] = mapped_column(Text)
    additional_info_response: Mapped[Optional[str]] = mapped_column(Text)
    additional_info_responded_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )

    # Rejection Details
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text)
    rejection_category: Mapped[Optional[str]] = mapped_column(String(100))

    # Approval & Vendor Creation
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    vendor_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_vendor.id"),
        nullable=True,
    )
    portal_user_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("portal_vendor_user.id"),
        nullable=True,
    )

    # Terms Acceptance
    terms_accepted: Mapped[bool] = mapped_column(Boolean, default=False)
    terms_accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    terms_version: Mapped[Optional[str]] = mapped_column(String(20))

    # Relationships
    documents: Mapped[List["VendorRegistrationDocument"]] = relationship(
        "VendorRegistrationDocument",
        back_populates="registration",
        cascade="all, delete-orphan",
    )
    reviewed_by: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[reviewed_by_id],
    )
    vendor: Mapped[Optional["Vendor"]] = relationship(
        "Vendor",
        foreign_keys=[vendor_id],
    )

    __table_args__ = (
        Index("ix_portal_vendor_reg_org_status", "organization_id", "status"),
        Index("ix_portal_vendor_reg_pan", "pan"),
        Index("ix_portal_vendor_reg_gstin", "gstin"),
        Index("ix_portal_vendor_reg_email", "contact_email"),
    )


class VendorRegistrationDocument(BaseModel):
    """Documents attached to vendor registration.

    Stores uploaded documents for verification during registration.
    """

    __tablename__ = "portal_vendor_reg_document"

    registration_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("portal_vendor_registration.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Document Details
    document_type: Mapped[RegistrationDocumentType] = mapped_column(nullable=False)
    document_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)  # in bytes
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    original_filename: Mapped[Optional[str]] = mapped_column(String(255))

    # Document Metadata
    document_number: Mapped[Optional[str]] = mapped_column(String(100))
    issue_date: Mapped[Optional[date]] = mapped_column(Date)
    expiry_date: Mapped[Optional[date]] = mapped_column(Date)

    # Verification Status
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verified_by_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id"),
        nullable=True,
    )
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    verification_remarks: Mapped[Optional[str]] = mapped_column(Text)

    # Rejection
    is_rejected: Mapped[bool] = mapped_column(Boolean, default=False)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    registration: Mapped["VendorRegistration"] = relationship(
        "VendorRegistration", back_populates="documents"
    )
    verified_by: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[verified_by_id],
    )

    __table_args__ = (
        Index("ix_portal_vendor_reg_doc_type", "registration_id", "document_type"),
    )
