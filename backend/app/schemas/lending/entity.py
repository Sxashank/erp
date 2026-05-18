"""Entity/Borrower schemas for the lending module."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import Field, field_validator

from app.core.pii import MaskedPIIModel
from app.models.lending.enums import (
    AddressType,
    ContactType,
    EntityStatus,
    EntityType,
    IndustrySector,
    RelationType,
    RiskCategory,
)
from app.schemas.base import CamelSchema

# =============================================================================
# Entity Contact Schemas
# =============================================================================


class EntityContactBase(CamelSchema):
    """Base schema for entity contact."""

    contact_type: ContactType
    name: str = Field(..., min_length=1, max_length=200)
    designation: str | None = Field(None, max_length=100)
    is_primary: bool = False
    din: str | None = Field(None, max_length=20, description="Director Identification Number")
    pan: str | None = Field(None, max_length=10)
    aadhaar_masked: str | None = Field(None, max_length=16, description="Masked Aadhaar")
    email: str | None = Field(None, max_length=100)
    phone: str | None = Field(None, max_length=20)
    mobile: str | None = Field(None, max_length=20)
    shareholding_percentage: Decimal | None = Field(None, ge=0, le=100)
    is_authorized_signatory: bool = False
    kyc_verified: bool = False
    date_of_birth: date | None = None

    @field_validator("pan")
    @classmethod
    def validate_pan(cls, v: str | None) -> str | None:
        if v:
            v = v.upper().strip()
            if len(v) != 10:
                raise ValueError("PAN must be 10 characters")
        return v


class EntityContactCreate(EntityContactBase):
    """Schema for creating an entity contact."""

    entity_id: UUID | None = None


class EntityContactUpdate(CamelSchema):
    """Schema for updating an entity contact."""

    contact_type: ContactType | None = None
    name: str | None = Field(None, min_length=1, max_length=200)
    designation: str | None = Field(None, max_length=100)
    is_primary: bool | None = None
    din: str | None = Field(None, max_length=20)
    pan: str | None = Field(None, max_length=10)
    aadhaar_masked: str | None = Field(None, max_length=16)
    email: str | None = Field(None, max_length=100)
    phone: str | None = Field(None, max_length=20)
    mobile: str | None = Field(None, max_length=20)
    shareholding_percentage: Decimal | None = Field(None, ge=0, le=100)
    is_authorized_signatory: bool | None = None
    kyc_verified: bool | None = None
    date_of_birth: date | None = None
    is_active: bool | None = None


class EntityContactResponse(EntityContactBase):
    """Schema for entity contact response."""

    id: UUID
    entity_id: UUID
    created_at: datetime
    updated_at: datetime | None = None
    is_active: bool = True


# =============================================================================
# Entity Address Schemas
# =============================================================================


class EntityAddressBase(CamelSchema):
    """Base schema for entity address."""

    address_type: AddressType
    address_line1: str = Field(..., min_length=1, max_length=200)
    address_line2: str | None = Field(None, max_length=200)
    address_line3: str | None = Field(None, max_length=200)
    city: str = Field(..., min_length=1, max_length=100)
    district: str | None = Field(None, max_length=100)
    state: str = Field(..., min_length=1, max_length=100)
    state_code: str | None = Field(None, min_length=2, max_length=2)
    pincode: str = Field(..., min_length=6, max_length=6)
    country: str = Field(default="India", max_length=50)
    is_primary: bool = False
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    is_verified: bool = False

    @field_validator("pincode")
    @classmethod
    def validate_pincode(cls, v: str) -> str:
        v = v.strip()
        if not v.isdigit() or len(v) != 6:
            raise ValueError("Pincode must be 6 digits")
        return v


class EntityAddressCreate(EntityAddressBase):
    """Schema for creating an entity address."""

    entity_id: UUID | None = None


class EntityAddressUpdate(CamelSchema):
    """Schema for updating an entity address."""

    address_type: AddressType | None = None
    address_line1: str | None = Field(None, min_length=1, max_length=200)
    address_line2: str | None = Field(None, max_length=200)
    address_line3: str | None = Field(None, max_length=200)
    city: str | None = Field(None, min_length=1, max_length=100)
    district: str | None = Field(None, max_length=100)
    state: str | None = Field(None, min_length=1, max_length=100)
    state_code: str | None = Field(None, min_length=2, max_length=2)
    pincode: str | None = Field(None, min_length=6, max_length=6)
    country: str | None = Field(None, max_length=50)
    is_primary: bool | None = None
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    is_verified: bool | None = None
    is_active: bool | None = None


class EntityAddressResponse(EntityAddressBase):
    """Schema for entity address response."""

    id: UUID
    entity_id: UUID
    created_at: datetime
    updated_at: datetime | None = None
    is_active: bool = True


# =============================================================================
# Entity Bank Account Schemas
# =============================================================================


class EntityBankAccountBase(CamelSchema):
    """Base schema for entity bank account."""

    bank_name: str = Field(..., min_length=1, max_length=100)
    branch_name: str | None = Field(None, max_length=100)
    account_number: str = Field(..., min_length=1, max_length=50)
    account_type: str = Field(default="CURRENT", max_length=20)
    account_holder_name: str = Field(..., min_length=1, max_length=200)
    ifsc_code: str = Field(..., min_length=11, max_length=11)
    micr_code: str | None = Field(None, max_length=10)
    is_primary: bool = False
    is_disbursement_account: bool = False
    is_collection_account: bool = False
    is_verified: bool = False
    verification_method: str | None = Field(None, max_length=50)

    @field_validator("ifsc_code")
    @classmethod
    def validate_ifsc(cls, v: str) -> str:
        v = v.upper().strip()
        if len(v) != 11:
            raise ValueError("IFSC code must be 11 characters")
        return v


class EntityBankAccountCreate(EntityBankAccountBase):
    """Schema for creating an entity bank account."""

    entity_id: UUID | None = None


class EntityBankAccountUpdate(CamelSchema):
    """Schema for updating an entity bank account."""

    bank_name: str | None = Field(None, min_length=1, max_length=100)
    branch_name: str | None = Field(None, max_length=100)
    account_number: str | None = Field(None, min_length=1, max_length=50)
    account_type: str | None = Field(None, max_length=20)
    account_holder_name: str | None = Field(None, min_length=1, max_length=200)
    ifsc_code: str | None = Field(None, min_length=11, max_length=11)
    micr_code: str | None = Field(None, max_length=10)
    is_primary: bool | None = None
    is_disbursement_account: bool | None = None
    is_collection_account: bool | None = None
    is_verified: bool | None = None
    verification_method: str | None = Field(None, max_length=50)
    is_active: bool | None = None


class EntityBankAccountResponse(EntityBankAccountBase):
    """Schema for entity bank account response."""

    id: UUID
    entity_id: UUID
    created_at: datetime
    updated_at: datetime | None = None
    is_active: bool = True


# =============================================================================
# Entity Relation Schemas
# =============================================================================


class EntityRelationBase(CamelSchema):
    """Base schema for entity relation."""

    relation_type: RelationType
    related_entity_id: UUID | None = None
    related_entity_name: str | None = Field(None, max_length=200)
    related_entity_pan: str | None = Field(None, max_length=10)
    stake_percentage: Decimal | None = Field(None, ge=0, le=100)
    effective_from: date | None = None
    effective_to: date | None = None
    remarks: str | None = None


class EntityRelationCreate(EntityRelationBase):
    """Schema for creating an entity relation."""

    entity_id: UUID | None = None


class EntityRelationUpdate(CamelSchema):
    """Schema for updating an entity relation."""

    relation_type: RelationType | None = None
    related_entity_id: UUID | None = None
    related_entity_name: str | None = Field(None, max_length=200)
    related_entity_pan: str | None = Field(None, max_length=10)
    stake_percentage: Decimal | None = Field(None, ge=0, le=100)
    effective_from: date | None = None
    effective_to: date | None = None
    remarks: str | None = None
    is_active: bool | None = None


class EntityRelationResponse(EntityRelationBase):
    """Schema for entity relation response."""

    id: UUID
    entity_id: UUID
    created_at: datetime
    updated_at: datetime | None = None
    is_active: bool = True


# =============================================================================
# Entity Financial Schemas
# =============================================================================


class EntityFinancialBase(CamelSchema):
    """Base schema for entity financial."""

    financial_year: str = Field(..., min_length=7, max_length=7, description="FY format: 2023-24")
    is_audited: bool = False
    auditor_name: str | None = Field(None, max_length=200)
    audit_date: date | None = None

    # Income Statement
    revenue: Decimal | None = Field(None, ge=0)
    other_income: Decimal | None = Field(None, ge=0)
    total_income: Decimal | None = Field(None, ge=0)
    cost_of_goods_sold: Decimal | None = Field(None, ge=0)
    gross_profit: Decimal | None = None
    operating_expenses: Decimal | None = Field(None, ge=0)
    ebitda: Decimal | None = None
    depreciation: Decimal | None = Field(None, ge=0)
    interest_expense: Decimal | None = Field(None, ge=0)
    profit_before_tax: Decimal | None = None
    tax_expense: Decimal | None = None
    net_profit: Decimal | None = None

    # Balance Sheet - Assets
    total_assets: Decimal | None = Field(None, ge=0)
    fixed_assets: Decimal | None = Field(None, ge=0)
    current_assets: Decimal | None = Field(None, ge=0)
    inventory: Decimal | None = Field(None, ge=0)
    receivables: Decimal | None = Field(None, ge=0)
    cash_and_equivalents: Decimal | None = Field(None, ge=0)

    # Balance Sheet - Liabilities
    total_liabilities: Decimal | None = Field(None, ge=0)
    share_capital: Decimal | None = Field(None, ge=0)
    reserves_surplus: Decimal | None = None
    net_worth: Decimal | None = None
    long_term_debt: Decimal | None = Field(None, ge=0)
    short_term_debt: Decimal | None = Field(None, ge=0)
    total_debt: Decimal | None = Field(None, ge=0)
    current_liabilities: Decimal | None = Field(None, ge=0)
    payables: Decimal | None = Field(None, ge=0)

    # Cash Flow
    operating_cash_flow: Decimal | None = None
    investing_cash_flow: Decimal | None = None
    financing_cash_flow: Decimal | None = None
    net_cash_flow: Decimal | None = None

    # Key Ratios (computed or overridden)
    current_ratio: Decimal | None = None
    debt_equity_ratio: Decimal | None = None
    interest_coverage_ratio: Decimal | None = None
    dscr: Decimal | None = None
    net_profit_margin: Decimal | None = None
    return_on_equity: Decimal | None = None
    return_on_assets: Decimal | None = None
    remarks: str | None = None
    raw_data: dict[str, Any] | None = None


class EntityFinancialCreate(EntityFinancialBase):
    """Schema for creating entity financial."""

    entity_id: UUID | None = None


class EntityFinancialUpdate(CamelSchema):
    """Schema for updating entity financial."""

    financial_year: str | None = Field(None, min_length=7, max_length=7)
    is_audited: bool | None = None
    auditor_name: str | None = Field(None, max_length=200)
    audit_date: date | None = None

    # All financial fields optional for update
    revenue: Decimal | None = None
    other_income: Decimal | None = None
    total_income: Decimal | None = None
    cost_of_goods_sold: Decimal | None = None
    gross_profit: Decimal | None = None
    operating_expenses: Decimal | None = None
    ebitda: Decimal | None = None
    depreciation: Decimal | None = None
    interest_expense: Decimal | None = None
    profit_before_tax: Decimal | None = None
    tax_expense: Decimal | None = None
    net_profit: Decimal | None = None

    total_assets: Decimal | None = None
    fixed_assets: Decimal | None = None
    current_assets: Decimal | None = None
    inventory: Decimal | None = None
    receivables: Decimal | None = None
    cash_and_equivalents: Decimal | None = None

    total_liabilities: Decimal | None = None
    share_capital: Decimal | None = None
    reserves_surplus: Decimal | None = None
    net_worth: Decimal | None = None
    long_term_debt: Decimal | None = None
    short_term_debt: Decimal | None = None
    total_debt: Decimal | None = None
    current_liabilities: Decimal | None = None
    payables: Decimal | None = None

    operating_cash_flow: Decimal | None = None
    investing_cash_flow: Decimal | None = None
    financing_cash_flow: Decimal | None = None
    net_cash_flow: Decimal | None = None

    current_ratio: Decimal | None = None
    debt_equity_ratio: Decimal | None = None
    interest_coverage_ratio: Decimal | None = None
    dscr: Decimal | None = None
    net_profit_margin: Decimal | None = None
    return_on_equity: Decimal | None = None
    return_on_assets: Decimal | None = None
    remarks: str | None = None
    raw_data: dict[str, Any] | None = None

    is_active: bool | None = None


class EntityFinancialResponse(EntityFinancialBase):
    """Schema for entity financial response."""

    id: UUID
    entity_id: UUID
    created_at: datetime
    updated_at: datetime | None = None
    is_active: bool = True


# =============================================================================
# Entity Schemas
# =============================================================================


class EntityBase(CamelSchema):
    """Base schema for Entity/Borrower."""

    entity_type: EntityType
    legal_name: str = Field(..., min_length=1, max_length=500)
    trade_name: str | None = Field(None, max_length=500)

    # Registration Details
    cin: str | None = Field(None, max_length=21, description="Corporate Identity Number")
    llpin: str | None = Field(None, max_length=20, description="LLP Identification Number")
    date_of_incorporation: date | None = None
    date_of_birth: date | None = None
    place_of_incorporation: str | None = Field(None, max_length=200)
    country_of_incorporation: str = Field(default="IND", max_length=3)

    # Tax Identifiers
    pan: str = Field(..., min_length=10, max_length=10)
    tan: str | None = Field(None, max_length=10)
    gstin: str | None = Field(None, max_length=15)
    udyam_number: str | None = Field(None, max_length=25)

    # KYC
    ckyc_number: str | None = Field(None, max_length=14)
    kyc_verified: bool = False
    kyc_verified_date: date | None = None

    # Classification
    industry_sector: IndustrySector | None = None
    industry_sub_sector: str | None = Field(None, max_length=200)
    nic_code: str | None = Field(None, max_length=10, description="NIC Industry Code")

    # Risk & Rating
    risk_category: RiskCategory = RiskCategory.MEDIUM
    internal_rating: str | None = Field(None, max_length=10)
    external_rating: str | None = Field(None, max_length=50)
    external_rating_agency: str | None = Field(None, max_length=50)

    # Business Details
    authorized_capital: Decimal | None = Field(None, ge=0)
    paid_up_capital: Decimal | None = Field(None, ge=0)
    net_worth: Decimal | None = Field(None, ge=0)
    turnover: Decimal | None = Field(None, ge=0)
    employee_count: int | None = Field(None, ge=0)

    # Contact
    primary_email: str | None = Field(None, max_length=255)
    primary_phone: str | None = Field(None, max_length=20)
    website: str | None = Field(None, max_length=255)

    # Relationship
    relationship_manager_id: UUID | None = None
    branch_id: UUID | None = None
    region: str | None = Field(None, max_length=100)

    # Status
    status: EntityStatus = EntityStatus.PROSPECT
    onboarding_date: date | None = None
    blacklist_reason: str | None = None
    remarks: str | None = None
    extra_data: dict[str, Any] | None = None

    @field_validator("pan")
    @classmethod
    def validate_pan(cls, v: str) -> str:
        v = v.upper().strip()
        if len(v) != 10:
            raise ValueError("PAN must be 10 characters")
        return v

    @field_validator("gstin")
    @classmethod
    def validate_gstin(cls, v: str | None) -> str | None:
        if v:
            v = v.upper().strip()
            if len(v) != 15:
                raise ValueError("GSTIN must be 15 characters")
        return v

    @field_validator("cin")
    @classmethod
    def validate_cin(cls, v: str | None) -> str | None:
        if v:
            v = v.upper().strip()
            if len(v) != 21:
                raise ValueError("CIN must be 21 characters")
        return v


class EntityCreate(EntityBase):
    """Schema for creating an Entity/Borrower."""

    organization_id: UUID | None = None


class EntityUpdate(CamelSchema):
    """Schema for updating an Entity/Borrower."""

    entity_type: EntityType | None = None
    legal_name: str | None = Field(None, min_length=1, max_length=500)
    trade_name: str | None = Field(None, max_length=500)

    # Registration Details
    cin: str | None = Field(None, max_length=21)
    llpin: str | None = Field(None, max_length=20)
    date_of_incorporation: date | None = None
    date_of_birth: date | None = None
    place_of_incorporation: str | None = Field(None, max_length=200)
    country_of_incorporation: str | None = Field(None, max_length=3)

    # Tax Identifiers
    pan: str | None = Field(None, min_length=10, max_length=10)
    tan: str | None = Field(None, max_length=10)
    gstin: str | None = Field(None, max_length=15)
    udyam_number: str | None = Field(None, max_length=25)

    # KYC
    ckyc_number: str | None = Field(None, max_length=14)
    kyc_verified: bool | None = None
    kyc_verified_date: date | None = None

    # Classification
    industry_sector: IndustrySector | None = None
    industry_sub_sector: str | None = Field(None, max_length=200)
    nic_code: str | None = Field(None, max_length=10)

    # Risk & Rating
    risk_category: RiskCategory | None = None
    internal_rating: str | None = Field(None, max_length=10)
    external_rating: str | None = Field(None, max_length=50)
    external_rating_agency: str | None = Field(None, max_length=50)

    # Business Details
    authorized_capital: Decimal | None = None
    paid_up_capital: Decimal | None = None
    net_worth: Decimal | None = None
    turnover: Decimal | None = None
    employee_count: int | None = None

    # Contact
    primary_email: str | None = Field(None, max_length=255)
    primary_phone: str | None = Field(None, max_length=20)
    website: str | None = Field(None, max_length=255)

    # Relationship
    relationship_manager_id: UUID | None = None
    branch_id: UUID | None = None
    region: str | None = Field(None, max_length=100)

    # Status
    status: EntityStatus | None = None
    onboarding_date: date | None = None
    blacklist_reason: str | None = None
    remarks: str | None = None
    extra_data: dict[str, Any] | None = None
    is_active: bool | None = None


class EntityResponse(MaskedPIIModel, EntityBase):
    """Schema for Entity/Borrower response."""

    id: UUID
    entity_code: str
    organization_id: UUID
    created_at: datetime
    updated_at: datetime | None = None
    is_active: bool = True


class EntityListResponse(CamelSchema):
    """Slim list response for entities (camelCase wire format)."""

    id: UUID
    entity_code: str
    entity_type: EntityType
    legal_name: str
    trade_name: str | None = None
    pan: str
    gstin: str | None = None
    industry_sector: IndustrySector | None = None
    internal_rating: str | None = None
    risk_category: RiskCategory | None = None
    status: EntityStatus
    is_active: bool = True
    created_at: datetime | None = None


class EntityDetailResponse(EntityResponse):
    """Schema for detailed Entity response with related data."""

    contacts: list[EntityContactResponse] = []
    addresses: list[EntityAddressResponse] = []
    bank_accounts: list[EntityBankAccountResponse] = []
    relations: list[EntityRelationResponse] = []
    financials: list[EntityFinancialResponse] = []
