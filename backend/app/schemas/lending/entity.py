"""Entity/Borrower schemas for the lending module."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import Field, field_validator

from app.schemas.base import BaseSchema
from app.core.pii import MaskedPIIModel
from app.models.lending.enums import (
    EntityType,
    EntityStatus,
    ContactType,
    AddressType,
    RelationType,
    RiskCategory,
    IndustrySector,
)


# =============================================================================
# Entity Contact Schemas
# =============================================================================


class EntityContactBase(BaseSchema):
    """Base schema for entity contact."""

    contact_type: ContactType
    name: str = Field(..., min_length=1, max_length=200)
    designation: Optional[str] = Field(None, max_length=100)
    din: Optional[str] = Field(None, max_length=20, description="Director Identification Number")
    pan: Optional[str] = Field(None, max_length=10)
    aadhaar_masked: Optional[str] = Field(None, max_length=16, description="Masked Aadhaar")
    email: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    mobile: Optional[str] = Field(None, max_length=20)
    shareholding_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    is_authorized_signatory: bool = False
    is_kyc_verified: bool = False
    date_of_birth: Optional[date] = None
    address: Optional[str] = Field(None, max_length=500)

    @field_validator("pan")
    @classmethod
    def validate_pan(cls, v: Optional[str]) -> Optional[str]:
        if v:
            v = v.upper().strip()
            if len(v) != 10:
                raise ValueError("PAN must be 10 characters")
        return v


class EntityContactCreate(EntityContactBase):
    """Schema for creating an entity contact."""

    entity_id: UUID


class EntityContactUpdate(BaseSchema):
    """Schema for updating an entity contact."""

    contact_type: Optional[ContactType] = None
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    designation: Optional[str] = Field(None, max_length=100)
    din: Optional[str] = Field(None, max_length=20)
    pan: Optional[str] = Field(None, max_length=10)
    aadhaar_masked: Optional[str] = Field(None, max_length=16)
    email: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    mobile: Optional[str] = Field(None, max_length=20)
    shareholding_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    is_authorized_signatory: Optional[bool] = None
    is_kyc_verified: Optional[bool] = None
    date_of_birth: Optional[date] = None
    address: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None


class EntityContactResponse(EntityContactBase):
    """Schema for entity contact response."""

    id: UUID
    entity_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = True


# =============================================================================
# Entity Address Schemas
# =============================================================================


class EntityAddressBase(BaseSchema):
    """Base schema for entity address."""

    address_type: AddressType
    address_line1: str = Field(..., min_length=1, max_length=200)
    address_line2: Optional[str] = Field(None, max_length=200)
    address_line3: Optional[str] = Field(None, max_length=200)
    landmark: Optional[str] = Field(None, max_length=100)
    city: str = Field(..., min_length=1, max_length=100)
    district: Optional[str] = Field(None, max_length=100)
    state_code: str = Field(..., min_length=2, max_length=2)
    state_name: Optional[str] = Field(None, max_length=100)
    pincode: str = Field(..., min_length=6, max_length=6)
    country: str = Field(default="India", max_length=50)
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
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

    entity_id: UUID


class EntityAddressUpdate(BaseSchema):
    """Schema for updating an entity address."""

    address_type: Optional[AddressType] = None
    address_line1: Optional[str] = Field(None, min_length=1, max_length=200)
    address_line2: Optional[str] = Field(None, max_length=200)
    address_line3: Optional[str] = Field(None, max_length=200)
    landmark: Optional[str] = Field(None, max_length=100)
    city: Optional[str] = Field(None, min_length=1, max_length=100)
    district: Optional[str] = Field(None, max_length=100)
    state_code: Optional[str] = Field(None, min_length=2, max_length=2)
    state_name: Optional[str] = Field(None, max_length=100)
    pincode: Optional[str] = Field(None, min_length=6, max_length=6)
    country: Optional[str] = Field(None, max_length=50)
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    is_verified: Optional[bool] = None
    is_active: Optional[bool] = None


class EntityAddressResponse(EntityAddressBase):
    """Schema for entity address response."""

    id: UUID
    entity_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = True


# =============================================================================
# Entity Bank Account Schemas
# =============================================================================


class EntityBankAccountBase(BaseSchema):
    """Base schema for entity bank account."""

    bank_name: str = Field(..., min_length=1, max_length=100)
    branch_name: Optional[str] = Field(None, max_length=100)
    account_number: str = Field(..., min_length=1, max_length=50)
    account_type: str = Field(default="CURRENT", max_length=20)
    ifsc_code: str = Field(..., min_length=11, max_length=11)
    micr_code: Optional[str] = Field(None, max_length=10)
    is_primary: bool = False
    is_disbursement_account: bool = False
    is_collection_account: bool = False
    is_verified: bool = False
    verified_via: Optional[str] = Field(None, max_length=50)

    @field_validator("ifsc_code")
    @classmethod
    def validate_ifsc(cls, v: str) -> str:
        v = v.upper().strip()
        if len(v) != 11:
            raise ValueError("IFSC code must be 11 characters")
        return v


class EntityBankAccountCreate(EntityBankAccountBase):
    """Schema for creating an entity bank account."""

    entity_id: UUID


class EntityBankAccountUpdate(BaseSchema):
    """Schema for updating an entity bank account."""

    bank_name: Optional[str] = Field(None, min_length=1, max_length=100)
    branch_name: Optional[str] = Field(None, max_length=100)
    account_number: Optional[str] = Field(None, min_length=1, max_length=50)
    account_type: Optional[str] = Field(None, max_length=20)
    ifsc_code: Optional[str] = Field(None, min_length=11, max_length=11)
    micr_code: Optional[str] = Field(None, max_length=10)
    is_primary: Optional[bool] = None
    is_disbursement_account: Optional[bool] = None
    is_collection_account: Optional[bool] = None
    is_verified: Optional[bool] = None
    verified_via: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None


class EntityBankAccountResponse(EntityBankAccountBase):
    """Schema for entity bank account response."""

    id: UUID
    entity_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = True


# =============================================================================
# Entity Relation Schemas
# =============================================================================


class EntityRelationBase(BaseSchema):
    """Base schema for entity relation."""

    relation_type: RelationType
    related_entity_id: Optional[UUID] = None
    related_entity_name: Optional[str] = Field(None, max_length=200)
    related_entity_pan: Optional[str] = Field(None, max_length=10)
    stake_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    remarks: Optional[str] = None


class EntityRelationCreate(EntityRelationBase):
    """Schema for creating an entity relation."""

    entity_id: UUID


class EntityRelationUpdate(BaseSchema):
    """Schema for updating an entity relation."""

    relation_type: Optional[RelationType] = None
    related_entity_id: Optional[UUID] = None
    related_entity_name: Optional[str] = Field(None, max_length=200)
    related_entity_pan: Optional[str] = Field(None, max_length=10)
    stake_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    remarks: Optional[str] = None
    is_active: Optional[bool] = None


class EntityRelationResponse(EntityRelationBase):
    """Schema for entity relation response."""

    id: UUID
    entity_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = True


# =============================================================================
# Entity Financial Schemas
# =============================================================================


class EntityFinancialBase(BaseSchema):
    """Base schema for entity financial."""

    financial_year: str = Field(..., min_length=7, max_length=7, description="FY format: 2023-24")
    audit_status: str = Field(default="UNAUDITED", max_length=20)
    auditor_name: Optional[str] = Field(None, max_length=200)
    audit_date: Optional[date] = None

    # Income Statement
    revenue: Optional[Decimal] = Field(None, ge=0)
    other_income: Optional[Decimal] = Field(None, ge=0)
    total_income: Optional[Decimal] = Field(None, ge=0)
    cost_of_materials: Optional[Decimal] = Field(None, ge=0)
    employee_cost: Optional[Decimal] = Field(None, ge=0)
    other_expenses: Optional[Decimal] = Field(None, ge=0)
    ebitda: Optional[Decimal] = None
    depreciation: Optional[Decimal] = Field(None, ge=0)
    interest_expense: Optional[Decimal] = Field(None, ge=0)
    pbt: Optional[Decimal] = None
    tax_expense: Optional[Decimal] = None
    pat: Optional[Decimal] = None

    # Balance Sheet - Assets
    fixed_assets_gross: Optional[Decimal] = Field(None, ge=0)
    accumulated_depreciation: Optional[Decimal] = Field(None, ge=0)
    fixed_assets_net: Optional[Decimal] = Field(None, ge=0)
    cwip: Optional[Decimal] = Field(None, ge=0)
    investments: Optional[Decimal] = Field(None, ge=0)
    inventory: Optional[Decimal] = Field(None, ge=0)
    receivables: Optional[Decimal] = Field(None, ge=0)
    cash_and_bank: Optional[Decimal] = Field(None, ge=0)
    other_current_assets: Optional[Decimal] = Field(None, ge=0)
    total_current_assets: Optional[Decimal] = Field(None, ge=0)
    total_assets: Optional[Decimal] = Field(None, ge=0)

    # Balance Sheet - Liabilities
    share_capital: Optional[Decimal] = Field(None, ge=0)
    reserves: Optional[Decimal] = None
    net_worth: Optional[Decimal] = None
    long_term_debt: Optional[Decimal] = Field(None, ge=0)
    short_term_debt: Optional[Decimal] = Field(None, ge=0)
    total_debt: Optional[Decimal] = Field(None, ge=0)
    payables: Optional[Decimal] = Field(None, ge=0)
    other_current_liabilities: Optional[Decimal] = Field(None, ge=0)
    total_current_liabilities: Optional[Decimal] = Field(None, ge=0)
    total_liabilities: Optional[Decimal] = Field(None, ge=0)

    # Cash Flow
    cfo: Optional[Decimal] = None
    cfi: Optional[Decimal] = None
    cff: Optional[Decimal] = None
    net_cash_flow: Optional[Decimal] = None

    # Key Ratios (computed or overridden)
    current_ratio: Optional[Decimal] = None
    debt_equity_ratio: Optional[Decimal] = None
    interest_coverage: Optional[Decimal] = None
    dscr: Optional[Decimal] = None
    roce: Optional[Decimal] = None
    roe: Optional[Decimal] = None
    net_profit_margin: Optional[Decimal] = None


class EntityFinancialCreate(EntityFinancialBase):
    """Schema for creating entity financial."""

    entity_id: UUID


class EntityFinancialUpdate(BaseSchema):
    """Schema for updating entity financial."""

    audit_status: Optional[str] = Field(None, max_length=20)
    auditor_name: Optional[str] = Field(None, max_length=200)
    audit_date: Optional[date] = None

    # All financial fields optional for update
    revenue: Optional[Decimal] = None
    other_income: Optional[Decimal] = None
    total_income: Optional[Decimal] = None
    cost_of_materials: Optional[Decimal] = None
    employee_cost: Optional[Decimal] = None
    other_expenses: Optional[Decimal] = None
    ebitda: Optional[Decimal] = None
    depreciation: Optional[Decimal] = None
    interest_expense: Optional[Decimal] = None
    pbt: Optional[Decimal] = None
    tax_expense: Optional[Decimal] = None
    pat: Optional[Decimal] = None

    fixed_assets_gross: Optional[Decimal] = None
    accumulated_depreciation: Optional[Decimal] = None
    fixed_assets_net: Optional[Decimal] = None
    cwip: Optional[Decimal] = None
    investments: Optional[Decimal] = None
    inventory: Optional[Decimal] = None
    receivables: Optional[Decimal] = None
    cash_and_bank: Optional[Decimal] = None
    other_current_assets: Optional[Decimal] = None
    total_current_assets: Optional[Decimal] = None
    total_assets: Optional[Decimal] = None

    share_capital: Optional[Decimal] = None
    reserves: Optional[Decimal] = None
    net_worth: Optional[Decimal] = None
    long_term_debt: Optional[Decimal] = None
    short_term_debt: Optional[Decimal] = None
    total_debt: Optional[Decimal] = None
    payables: Optional[Decimal] = None
    other_current_liabilities: Optional[Decimal] = None
    total_current_liabilities: Optional[Decimal] = None
    total_liabilities: Optional[Decimal] = None

    cfo: Optional[Decimal] = None
    cfi: Optional[Decimal] = None
    cff: Optional[Decimal] = None
    net_cash_flow: Optional[Decimal] = None

    current_ratio: Optional[Decimal] = None
    debt_equity_ratio: Optional[Decimal] = None
    interest_coverage: Optional[Decimal] = None
    dscr: Optional[Decimal] = None
    roce: Optional[Decimal] = None
    roe: Optional[Decimal] = None
    net_profit_margin: Optional[Decimal] = None

    is_active: Optional[bool] = None


class EntityFinancialResponse(EntityFinancialBase):
    """Schema for entity financial response."""

    id: UUID
    entity_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = True


# =============================================================================
# Entity Schemas
# =============================================================================


class EntityBase(BaseSchema):
    """Base schema for Entity/Borrower."""

    entity_type: EntityType
    legal_name: str = Field(..., min_length=1, max_length=500)
    trade_name: Optional[str] = Field(None, max_length=500)

    # Registration Details
    cin: Optional[str] = Field(None, max_length=21, description="Corporate Identity Number")
    llpin: Optional[str] = Field(None, max_length=20, description="LLP Identification Number")
    date_of_incorporation: Optional[date] = None
    date_of_birth: Optional[date] = None
    place_of_incorporation: Optional[str] = Field(None, max_length=200)
    country_of_incorporation: str = Field(default="IND", max_length=3)

    # Tax Identifiers
    pan: str = Field(..., min_length=10, max_length=10)
    tan: Optional[str] = Field(None, max_length=10)
    gstin: Optional[str] = Field(None, max_length=15)
    udyam_number: Optional[str] = Field(None, max_length=25)

    # KYC
    ckyc_number: Optional[str] = Field(None, max_length=14)
    kyc_verified: bool = False
    kyc_verified_date: Optional[date] = None

    # Classification
    industry_sector: Optional[IndustrySector] = None
    industry_sub_sector: Optional[str] = Field(None, max_length=200)
    nic_code: Optional[str] = Field(None, max_length=10, description="NIC Industry Code")

    # Risk & Rating
    risk_category: RiskCategory = RiskCategory.MEDIUM
    internal_rating: Optional[str] = Field(None, max_length=10)
    external_rating: Optional[str] = Field(None, max_length=50)
    external_rating_agency: Optional[str] = Field(None, max_length=50)

    # Business Details
    authorized_capital: Optional[Decimal] = Field(None, ge=0)
    paid_up_capital: Optional[Decimal] = Field(None, ge=0)
    net_worth: Optional[Decimal] = Field(None, ge=0)
    turnover: Optional[Decimal] = Field(None, ge=0)
    employee_count: Optional[int] = Field(None, ge=0)

    # Contact
    primary_email: Optional[str] = Field(None, max_length=255)
    primary_phone: Optional[str] = Field(None, max_length=20)
    website: Optional[str] = Field(None, max_length=255)

    # Relationship
    relationship_manager_id: Optional[UUID] = None
    branch_id: Optional[UUID] = None
    region: Optional[str] = Field(None, max_length=100)

    # Status
    status: EntityStatus = EntityStatus.PROSPECT
    onboarding_date: Optional[date] = None
    blacklist_reason: Optional[str] = None
    remarks: Optional[str] = None
    extra_data: Optional[Dict[str, Any]] = None

    @field_validator("pan")
    @classmethod
    def validate_pan(cls, v: str) -> str:
        v = v.upper().strip()
        if len(v) != 10:
            raise ValueError("PAN must be 10 characters")
        return v

    @field_validator("gstin")
    @classmethod
    def validate_gstin(cls, v: Optional[str]) -> Optional[str]:
        if v:
            v = v.upper().strip()
            if len(v) != 15:
                raise ValueError("GSTIN must be 15 characters")
        return v

    @field_validator("cin")
    @classmethod
    def validate_cin(cls, v: Optional[str]) -> Optional[str]:
        if v:
            v = v.upper().strip()
            if len(v) != 21:
                raise ValueError("CIN must be 21 characters")
        return v


class EntityCreate(EntityBase):
    """Schema for creating an Entity/Borrower."""

    organization_id: UUID


class EntityUpdate(BaseSchema):
    """Schema for updating an Entity/Borrower."""

    entity_type: Optional[EntityType] = None
    legal_name: Optional[str] = Field(None, min_length=1, max_length=500)
    trade_name: Optional[str] = Field(None, max_length=500)

    # Registration Details
    cin: Optional[str] = Field(None, max_length=21)
    llpin: Optional[str] = Field(None, max_length=20)
    date_of_incorporation: Optional[date] = None
    date_of_birth: Optional[date] = None
    place_of_incorporation: Optional[str] = Field(None, max_length=200)
    country_of_incorporation: Optional[str] = Field(None, max_length=3)

    # Tax Identifiers
    pan: Optional[str] = Field(None, min_length=10, max_length=10)
    tan: Optional[str] = Field(None, max_length=10)
    gstin: Optional[str] = Field(None, max_length=15)
    udyam_number: Optional[str] = Field(None, max_length=25)

    # KYC
    ckyc_number: Optional[str] = Field(None, max_length=14)
    kyc_verified: Optional[bool] = None
    kyc_verified_date: Optional[date] = None

    # Classification
    industry_sector: Optional[IndustrySector] = None
    industry_sub_sector: Optional[str] = Field(None, max_length=200)
    nic_code: Optional[str] = Field(None, max_length=10)

    # Risk & Rating
    risk_category: Optional[RiskCategory] = None
    internal_rating: Optional[str] = Field(None, max_length=10)
    external_rating: Optional[str] = Field(None, max_length=50)
    external_rating_agency: Optional[str] = Field(None, max_length=50)

    # Business Details
    authorized_capital: Optional[Decimal] = None
    paid_up_capital: Optional[Decimal] = None
    net_worth: Optional[Decimal] = None
    turnover: Optional[Decimal] = None
    employee_count: Optional[int] = None

    # Contact
    primary_email: Optional[str] = Field(None, max_length=255)
    primary_phone: Optional[str] = Field(None, max_length=20)
    website: Optional[str] = Field(None, max_length=255)

    # Relationship
    relationship_manager_id: Optional[UUID] = None
    branch_id: Optional[UUID] = None
    region: Optional[str] = Field(None, max_length=100)

    # Status
    status: Optional[EntityStatus] = None
    onboarding_date: Optional[date] = None
    blacklist_reason: Optional[str] = None
    remarks: Optional[str] = None
    extra_data: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class EntityResponse(MaskedPIIModel, EntityBase):
    """Schema for Entity/Borrower response."""

    id: UUID
    entity_code: str
    organization_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = True


class EntityListResponse(BaseSchema):
    """Schema for Entity list response (lightweight)."""

    id: UUID
    entity_code: str
    entity_type: EntityType
    legal_name: str
    trade_name: Optional[str] = None
    pan: str
    gstin: Optional[str] = None
    industry_sector: Optional[IndustrySector] = None
    internal_rating: Optional[str] = None
    risk_category: Optional[RiskCategory] = None
    status: EntityStatus
    is_active: bool = True


class EntityDetailResponse(EntityResponse):
    """Schema for detailed Entity response with related data."""

    contacts: List[EntityContactResponse] = []
    addresses: List[EntityAddressResponse] = []
    bank_accounts: List[EntityBankAccountResponse] = []
    relations: List[EntityRelationResponse] = []
    financials: List[EntityFinancialResponse] = []
