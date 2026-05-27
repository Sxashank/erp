"""Entity/Borrower models for the lending module."""

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.lending.enums import (
    EntityStatus,
    RelationType,
)

if TYPE_CHECKING:
    from app.models.auth.user import User
    from app.models.lending.application import LoanApplication
    from app.models.lending.kyc import BureauPull, EntityKYCDocument
    from app.models.lending.rating import EntityRating
    from app.models.masters.organization import Organization


class Entity(BaseModel):
    """Borrower/Entity master - Corporate, Individual, LLP, etc."""

    __tablename__ = "los_entity"

    # Organization scope
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Organization this entity belongs to",
    )

    # Entity identification
    entity_code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Unique entity code e.g., 'ENT/2025/00001'",
    )
    entity_type: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
        index=True,
        comment="Tenant master code from ENTITY_TYPE_CORPORATE.",
    )
    legal_name: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="Legal/registered name of the entity",
    )
    trade_name: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Trading/brand name if different from legal name",
    )

    # Government identifiers
    pan: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        index=True,
        comment="PAN number (mandatory)",
    )
    cin: Mapped[str | None] = mapped_column(
        String(21),
        nullable=True,
        comment="Corporate Identification Number (for companies)",
    )
    llpin: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="LLP Identification Number",
    )
    gstin: Mapped[str | None] = mapped_column(
        String(15),
        nullable=True,
        comment="GST Identification Number",
    )
    udyam_number: Mapped[str | None] = mapped_column(
        String(25),
        nullable=True,
        comment="UDYAM registration number for MSMEs",
    )
    tan: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
        comment="Tax Deduction Account Number",
    )

    # KYC/CKYC
    ckyc_number: Mapped[str | None] = mapped_column(
        String(14),
        nullable=True,
        index=True,
        comment="Central KYC Identifier",
    )
    kyc_verified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="KYC verification status",
    )
    kyc_verified_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment="Date of KYC verification",
    )

    # Incorporation/Registration details
    date_of_incorporation: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment="Date of incorporation/registration",
    )
    date_of_birth: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment="Date of birth (for individuals)",
    )
    place_of_incorporation: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        comment="City/State of incorporation",
    )
    country_of_incorporation: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="IND",
        comment="Country code (ISO 3166-1 alpha-3)",
    )

    # Industry classification
    industry_sector: Mapped[str | None] = mapped_column(
        String(80),
        nullable=True,
        index=True,
        comment="Tenant master code from INDUSTRY_SECTOR.",
    )
    industry_sub_sector: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        comment="Industry sub-sector/NIC code",
    )
    nic_code: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
        comment="National Industrial Classification code",
    )

    # Risk classification
    risk_category: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
        default="MEDIUM",
        index=True,
        comment="Tenant master code from RISK_GRADE.",
    )
    internal_rating: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
        comment="Internal credit rating (AAA to D)",
    )
    external_rating: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="External credit rating (CRISIL, ICRA, etc.)",
    )
    external_rating_agency: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="External rating agency name",
    )

    # Financial information
    authorized_capital: Mapped[Decimal | None] = mapped_column(
        Numeric(20, 2),
        nullable=True,
        comment="Authorized share capital",
    )
    paid_up_capital: Mapped[Decimal | None] = mapped_column(
        Numeric(20, 2),
        nullable=True,
        comment="Paid-up share capital",
    )
    net_worth: Mapped[Decimal | None] = mapped_column(
        Numeric(20, 2),
        nullable=True,
        comment="Latest net worth",
    )
    turnover: Mapped[Decimal | None] = mapped_column(
        Numeric(20, 2),
        nullable=True,
        comment="Latest annual turnover",
    )
    employee_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Number of employees",
    )

    # Contact information
    primary_email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Primary email address",
    )
    primary_phone: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="Primary phone number",
    )
    website: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Website URL",
    )

    # Relationship management
    relationship_manager_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Assigned relationship manager",
    )
    branch_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="Branch handling this entity",
    )
    region: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Region/Zone",
    )

    # Status
    status: Mapped[EntityStatus] = mapped_column(
        Enum(EntityStatus),
        nullable=False,
        default=EntityStatus.PROSPECT,
        index=True,
        comment="Entity status - PROSPECT, ACTIVE, INACTIVE, BLACKLISTED",
    )
    onboarding_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment="Date when entity became active customer",
    )
    blacklist_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Reason for blacklisting if applicable",
    )

    # Additional data
    remarks: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Internal remarks/notes",
    )
    extra_data: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Additional metadata as JSON",
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        lazy="selectin",
    )
    relationship_manager: Mapped[Optional["User"]] = relationship(
        "User",
        lazy="selectin",
        foreign_keys=[relationship_manager_id],
    )
    contacts: Mapped[list["EntityContact"]] = relationship(
        "EntityContact",
        back_populates="entity",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    addresses: Mapped[list["EntityAddress"]] = relationship(
        "EntityAddress",
        back_populates="entity",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    bank_accounts: Mapped[list["EntityBankAccount"]] = relationship(
        "EntityBankAccount",
        back_populates="entity",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    relations: Mapped[list["EntityRelation"]] = relationship(
        "EntityRelation",
        back_populates="entity",
        cascade="all, delete-orphan",
        foreign_keys="EntityRelation.entity_id",
        lazy="noload",
    )
    financials: Mapped[list["EntityFinancial"]] = relationship(
        "EntityFinancial",
        back_populates="entity",
        cascade="all, delete-orphan",
        lazy="noload",
    )
    kyc_documents: Mapped[list["EntityKYCDocument"]] = relationship(
        "EntityKYCDocument",
        back_populates="entity",
        cascade="all, delete-orphan",
        lazy="noload",
    )
    bureau_pulls: Mapped[list["BureauPull"]] = relationship(
        "BureauPull",
        back_populates="entity",
        cascade="all, delete-orphan",
        lazy="noload",
    )
    ratings: Mapped[list["EntityRating"]] = relationship(
        "EntityRating",
        back_populates="entity",
        cascade="all, delete-orphan",
        lazy="noload",
    )
    applications: Mapped[list["LoanApplication"]] = relationship(
        "LoanApplication",
        back_populates="entity",
        lazy="noload",
    )

    __table_args__ = (
        UniqueConstraint("organization_id", "entity_code", name="uq_entity_org_code"),
        UniqueConstraint("organization_id", "pan", name="uq_entity_org_pan"),
        Index("ix_los_entity_org_status", "organization_id", "status"),
        Index("ix_los_entity_org_type", "organization_id", "entity_type"),
        Index("ix_los_entity_org_rating", "organization_id", "internal_rating"),
        CheckConstraint("LENGTH(pan) = 10", name="ck_entity_pan_length"),
    )

    def __repr__(self) -> str:
        return f"<Entity(code={self.entity_code}, name={self.legal_name}, type={self.entity_type})>"


class EntityContact(BaseModel):
    """Key contacts/persons associated with an entity."""

    __tablename__ = "los_entity_contact"

    # Parent entity
    entity_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("los_entity.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent entity",
    )

    # Contact type and role
    contact_type: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
        comment="Tenant master code from CONTACT_TYPE.",
    )
    designation: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        comment="Designation/title",
    )
    is_primary: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Is this the primary contact?",
    )
    is_authorized_signatory: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Is authorized to sign on behalf of entity?",
    )

    # Personal details
    salutation: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
        comment="Mr/Mrs/Ms/Dr etc.",
    )
    first_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="First name",
    )
    middle_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Middle name",
    )
    last_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Last name/surname",
    )
    date_of_birth: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment="Date of birth",
    )
    gender: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
        comment="Gender - MALE, FEMALE, OTHER",
    )
    nationality: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="Indian",
        comment="Nationality",
    )

    # Identification
    pan: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
        index=True,
        comment="PAN number",
    )
    aadhaar_masked: Mapped[str | None] = mapped_column(
        String(12),
        nullable=True,
        comment="Masked Aadhaar (XXXX-XXXX-1234)",
    )
    din: Mapped[str | None] = mapped_column(
        String(8),
        nullable=True,
        comment="Director Identification Number",
    )
    dpin: Mapped[str | None] = mapped_column(
        String(8),
        nullable=True,
        comment="Designated Partner Identification Number (for LLP)",
    )
    passport_number: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="Passport number",
    )

    # Contact information
    email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Email address",
    )
    mobile: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="Mobile number",
    )
    phone: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="Landline number",
    )

    # Address
    address_line1: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Address line 1",
    )
    address_line2: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Address line 2",
    )
    city: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="City",
    )
    state: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="State",
    )
    pincode: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
        comment="PIN code",
    )
    country: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="India",
        comment="Country",
    )

    # Shareholding (for promoters/directors)
    shareholding_percentage: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        comment="Shareholding percentage",
    )
    shareholding_value: Mapped[Decimal | None] = mapped_column(
        Numeric(20, 2),
        nullable=True,
        comment="Shareholding value in INR",
    )

    # Director/Partner specific
    appointment_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment="Date of appointment",
    )
    cessation_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment="Date of cessation (if applicable)",
    )

    # KYC
    kyc_verified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="KYC verification status",
    )
    ckyc_number: Mapped[str | None] = mapped_column(
        String(14),
        nullable=True,
        comment="Central KYC Identifier",
    )

    # Additional info
    remarks: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Remarks/notes",
    )

    # Relationships
    entity: Mapped["Entity"] = relationship(
        "Entity",
        back_populates="contacts",
    )

    __table_args__ = (Index("ix_los_entity_contact_entity_type", "entity_id", "contact_type"),)

    @property
    def full_name(self) -> str:
        """Get full name of contact."""
        parts = [self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        parts.append(self.last_name)
        return " ".join(parts)

    @property
    def name(self) -> str:
        """API-facing display name for contact."""
        return self.full_name

    def __repr__(self) -> str:
        return f"<EntityContact(name={self.full_name}, type={self.contact_type})>"


class EntityAddress(BaseModel):
    """Addresses associated with an entity."""

    __tablename__ = "los_entity_address"

    # Parent entity
    entity_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("los_entity.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent entity",
    )

    # Address type
    address_type: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
        comment="Tenant master code from ADDRESS_TYPE.",
    )
    is_primary: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Is this the primary address for this type?",
    )

    # Address details
    address_line1: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="Address line 1",
    )
    address_line2: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Address line 2",
    )
    address_line3: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Address line 3/landmark",
    )
    city: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="City",
    )
    district: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="District",
    )
    state: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="State",
    )
    state_code: Mapped[str | None] = mapped_column(
        String(2),
        nullable=True,
        comment="State code (for GST)",
    )
    pincode: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment="PIN code",
    )
    country: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="India",
        comment="Country",
    )
    country_code: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="IND",
        comment="ISO 3166-1 alpha-3 country code",
    )

    # Geo coordinates (for site visits)
    latitude: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 7),
        nullable=True,
        comment="Latitude coordinate",
    )
    longitude: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 7),
        nullable=True,
        comment="Longitude coordinate",
    )

    # Contact at address
    contact_person: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        comment="Contact person at this address",
    )
    contact_phone: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="Contact phone at this address",
    )

    # Verification
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Address verification status",
    )
    verified_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment="Date of verification",
    )
    verified_by: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        comment="Verified by (person/agency)",
    )

    # Ownership
    ownership_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="OWNED, RENTED, LEASED",
    )
    occupied_since: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment="Occupied since date",
    )

    # Relationships
    entity: Mapped["Entity"] = relationship(
        "Entity",
        back_populates="addresses",
    )

    __table_args__ = (Index("ix_los_entity_address_entity_type", "entity_id", "address_type"),)

    @property
    def full_address(self) -> str:
        """Get formatted full address."""
        parts = [self.address_line1]
        if self.address_line2:
            parts.append(self.address_line2)
        if self.address_line3:
            parts.append(self.address_line3)
        parts.append(f"{self.city}, {self.state} - {self.pincode}")
        parts.append(self.country)
        return ", ".join(parts)

    def __repr__(self) -> str:
        return f"<EntityAddress(type={self.address_type}, city={self.city})>"


class EntityBankAccount(BaseModel):
    """Bank accounts associated with an entity."""

    __tablename__ = "los_entity_bank_account"

    # Parent entity
    entity_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("los_entity.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent entity",
    )

    # Bank details
    bank_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Bank name",
    )
    branch_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Branch name",
    )
    branch_address: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Branch address",
    )
    ifsc_code: Mapped[str] = mapped_column(
        String(11),
        nullable=False,
        index=True,
        comment="IFSC code",
    )
    micr_code: Mapped[str | None] = mapped_column(
        String(9),
        nullable=True,
        comment="MICR code",
    )

    # Account details
    account_number: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        comment="Bank account number",
    )
    account_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Account type - CURRENT, SAVINGS, CC, OD",
    )
    account_holder_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Account holder name as in bank",
    )

    # Purpose
    is_primary: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Is this the primary account?",
    )
    is_disbursement_account: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Use for disbursement?",
    )
    is_collection_account: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Use for EMI/collection?",
    )
    is_escrow_account: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Is this an escrow account?",
    )

    # Verification
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Bank account verification status",
    )
    verified_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment="Date of verification",
    )
    verification_method: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Verification method - PENNY_DROP, CANCELLED_CHEQUE, BANK_STATEMENT",
    )
    penny_drop_reference: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Penny drop transaction reference",
    )

    # NACH/Mandate details
    nach_registered: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="NACH mandate registered?",
    )
    nach_umrn: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="NACH Unique Mandate Reference Number",
    )
    nach_max_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 2),
        nullable=True,
        comment="NACH maximum amount",
    )
    nach_start_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment="NACH mandate start date",
    )
    nach_end_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment="NACH mandate end date",
    )

    # Relationships
    entity: Mapped["Entity"] = relationship(
        "Entity",
        back_populates="bank_accounts",
    )

    __table_args__ = (
        Index("ix_los_entity_bank_ifsc", "ifsc_code"),
        UniqueConstraint("entity_id", "account_number", "ifsc_code", name="uq_entity_bank_account"),
        CheckConstraint("LENGTH(ifsc_code) = 11", name="ck_bank_ifsc_length"),
    )

    def __repr__(self) -> str:
        return f"<EntityBankAccount(bank={self.bank_name}, account=***{self.account_number[-4:]})>"


class EntityRelation(BaseModel):
    """Relationships between entities - group companies, guarantors, etc."""

    __tablename__ = "los_entity_relation"

    # Parent entity
    entity_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("los_entity.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent entity",
    )

    # Related entity
    related_entity_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("los_entity.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Related entity (if already registered)",
    )

    # Relation details
    relation_type: Mapped[RelationType] = mapped_column(
        Enum(RelationType),
        nullable=False,
        comment="Type of relationship - PARENT, SUBSIDIARY, GUARANTOR, etc.",
    )

    # If related entity not registered, store basic info
    related_entity_name: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Related entity name (if not registered)",
    )
    related_entity_pan: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
        comment="Related entity PAN (if not registered)",
    )
    related_entity_cin: Mapped[str | None] = mapped_column(
        String(21),
        nullable=True,
        comment="Related entity CIN (if not registered)",
    )

    # Shareholding/ownership details
    shareholding_percentage: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        comment="Shareholding percentage",
    )
    voting_percentage: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        comment="Voting rights percentage",
    )

    # Guarantee details (if guarantor)
    guarantee_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(20, 2),
        nullable=True,
        comment="Guarantee amount (for guarantors)",
    )
    guarantee_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="PERSONAL, CORPORATE, LIMITED",
    )

    # Additional info
    effective_from: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment="Relationship effective from",
    )
    effective_to: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment="Relationship effective until",
    )
    remarks: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Remarks/notes",
    )

    # Relationships
    entity: Mapped["Entity"] = relationship(
        "Entity",
        back_populates="relations",
        foreign_keys=[entity_id],
    )
    related_entity: Mapped[Optional["Entity"]] = relationship(
        "Entity",
        foreign_keys=[related_entity_id],
        lazy="selectin",
    )

    __table_args__ = (Index("ix_los_entity_relation_type", "entity_id", "relation_type"),)

    def __repr__(self) -> str:
        return f"<EntityRelation(entity={self.entity_id}, type={self.relation_type})>"


class EntityFinancial(BaseModel):
    """Annual financial data for an entity."""

    __tablename__ = "los_entity_financial"

    # Parent entity
    entity_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("los_entity.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent entity",
    )

    # Financial year
    financial_year: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment="Financial year e.g., '2024-25'",
    )
    is_audited: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Is this audited data?",
    )
    audit_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment="Date of audit report",
    )
    auditor_name: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        comment="Auditor firm name",
    )

    # Income statement
    revenue: Mapped[Decimal | None] = mapped_column(
        Numeric(20, 2),
        nullable=True,
        comment="Total revenue/turnover",
    )
    other_income: Mapped[Decimal | None] = mapped_column(
        Numeric(20, 2),
        nullable=True,
        comment="Other income",
    )
    total_income: Mapped[Decimal | None] = mapped_column(
        Numeric(20, 2),
        nullable=True,
        comment="Total income",
    )
    cost_of_goods_sold: Mapped[Decimal | None] = mapped_column(
        Numeric(20, 2),
        nullable=True,
        comment="Cost of goods sold",
    )
    gross_profit: Mapped[Decimal | None] = mapped_column(
        Numeric(20, 2),
        nullable=True,
        comment="Gross profit",
    )
    operating_expenses: Mapped[Decimal | None] = mapped_column(
        Numeric(20, 2),
        nullable=True,
        comment="Operating expenses",
    )
    ebitda: Mapped[Decimal | None] = mapped_column(
        Numeric(20, 2),
        nullable=True,
        comment="EBITDA",
    )
    depreciation: Mapped[Decimal | None] = mapped_column(
        Numeric(20, 2),
        nullable=True,
        comment="Depreciation and amortization",
    )
    interest_expense: Mapped[Decimal | None] = mapped_column(
        Numeric(20, 2),
        nullable=True,
        comment="Interest expense",
    )
    profit_before_tax: Mapped[Decimal | None] = mapped_column(
        Numeric(20, 2),
        nullable=True,
        comment="Profit before tax",
    )
    tax_expense: Mapped[Decimal | None] = mapped_column(
        Numeric(20, 2),
        nullable=True,
        comment="Tax expense",
    )
    net_profit: Mapped[Decimal | None] = mapped_column(
        Numeric(20, 2),
        nullable=True,
        comment="Net profit after tax",
    )

    # Balance sheet - Assets
    total_assets: Mapped[Decimal | None] = mapped_column(
        Numeric(20, 2),
        nullable=True,
        comment="Total assets",
    )
    fixed_assets: Mapped[Decimal | None] = mapped_column(
        Numeric(20, 2),
        nullable=True,
        comment="Fixed assets (net)",
    )
    current_assets: Mapped[Decimal | None] = mapped_column(
        Numeric(20, 2),
        nullable=True,
        comment="Current assets",
    )
    inventory: Mapped[Decimal | None] = mapped_column(
        Numeric(20, 2),
        nullable=True,
        comment="Inventory",
    )
    receivables: Mapped[Decimal | None] = mapped_column(
        Numeric(20, 2),
        nullable=True,
        comment="Trade receivables",
    )
    cash_and_equivalents: Mapped[Decimal | None] = mapped_column(
        Numeric(20, 2),
        nullable=True,
        comment="Cash and cash equivalents",
    )

    # Balance sheet - Liabilities
    total_liabilities: Mapped[Decimal | None] = mapped_column(
        Numeric(20, 2),
        nullable=True,
        comment="Total liabilities",
    )
    share_capital: Mapped[Decimal | None] = mapped_column(
        Numeric(20, 2),
        nullable=True,
        comment="Share capital",
    )
    reserves_surplus: Mapped[Decimal | None] = mapped_column(
        Numeric(20, 2),
        nullable=True,
        comment="Reserves and surplus",
    )
    net_worth: Mapped[Decimal | None] = mapped_column(
        Numeric(20, 2),
        nullable=True,
        comment="Net worth (equity)",
    )
    long_term_debt: Mapped[Decimal | None] = mapped_column(
        Numeric(20, 2),
        nullable=True,
        comment="Long term debt",
    )
    short_term_debt: Mapped[Decimal | None] = mapped_column(
        Numeric(20, 2),
        nullable=True,
        comment="Short term debt",
    )
    total_debt: Mapped[Decimal | None] = mapped_column(
        Numeric(20, 2),
        nullable=True,
        comment="Total debt",
    )
    current_liabilities: Mapped[Decimal | None] = mapped_column(
        Numeric(20, 2),
        nullable=True,
        comment="Current liabilities",
    )
    payables: Mapped[Decimal | None] = mapped_column(
        Numeric(20, 2),
        nullable=True,
        comment="Trade payables",
    )

    # Cash flow
    operating_cash_flow: Mapped[Decimal | None] = mapped_column(
        Numeric(20, 2),
        nullable=True,
        comment="Cash flow from operations",
    )
    investing_cash_flow: Mapped[Decimal | None] = mapped_column(
        Numeric(20, 2),
        nullable=True,
        comment="Cash flow from investing",
    )
    financing_cash_flow: Mapped[Decimal | None] = mapped_column(
        Numeric(20, 2),
        nullable=True,
        comment="Cash flow from financing",
    )
    net_cash_flow: Mapped[Decimal | None] = mapped_column(
        Numeric(20, 2),
        nullable=True,
        comment="Net cash flow",
    )

    # Key ratios (computed)
    current_ratio: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Current ratio",
    )
    debt_equity_ratio: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Debt to equity ratio",
    )
    interest_coverage_ratio: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Interest coverage ratio",
    )
    dscr: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Debt service coverage ratio",
    )
    net_profit_margin: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Net profit margin %",
    )
    return_on_equity: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Return on equity %",
    )
    return_on_assets: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Return on assets %",
    )

    # Additional data
    remarks: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Remarks/notes",
    )
    raw_data: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Additional financial data as JSON",
    )

    # Relationships
    entity: Mapped["Entity"] = relationship(
        "Entity",
        back_populates="financials",
    )

    __table_args__ = (
        UniqueConstraint("entity_id", "financial_year", name="uq_entity_financial_year"),
        Index("ix_los_entity_financial_year", "entity_id", "financial_year"),
    )

    def __repr__(self) -> str:
        return f"<EntityFinancial(entity={self.entity_id}, year={self.financial_year})>"
