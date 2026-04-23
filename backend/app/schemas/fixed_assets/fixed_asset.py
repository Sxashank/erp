"""Fixed Asset schemas."""

from datetime import date
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import Field, field_validator

from app.schemas.base import BaseSchema, AuditSchema
from app.core.constants import (
    AssetStatus,
    AssetAcquisitionType,
    AssetDisposalType,
    DepreciationMethod,
    RevaluationType,
    ITActAssetBlock,
)


class FixedAssetCreate(BaseSchema):
    """Schema for creating a fixed asset."""

    asset_name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    category_id: UUID
    location_id: Optional[UUID] = None
    department_id: Optional[UUID] = None
    custodian_employee_id: Optional[UUID] = None
    acquisition_date: date
    put_to_use_date: Optional[date] = None
    acquisition_type: AssetAcquisitionType = AssetAcquisitionType.PURCHASE
    vendor_id: Optional[UUID] = None
    invoice_number: Optional[str] = Field(None, max_length=50)
    invoice_date: Optional[date] = None
    po_number: Optional[str] = Field(None, max_length=50)
    acquisition_cost: Decimal = Field(Decimal("0.00"), ge=0)
    installation_cost: Decimal = Field(Decimal("0.00"), ge=0)
    other_costs: Decimal = Field(Decimal("0.00"), ge=0)
    residual_value: Optional[Decimal] = Field(None, ge=0)
    useful_life_months: Optional[int] = Field(None, ge=1)
    depreciation_method: Optional[DepreciationMethod] = None
    depreciation_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    make: Optional[str] = Field(None, max_length=100)
    model: Optional[str] = Field(None, max_length=100)
    serial_number: Optional[str] = Field(None, max_length=100)
    quantity: int = Field(1, ge=1)
    warranty_start_date: Optional[date] = None
    warranty_expiry_date: Optional[date] = None
    insurance_policy_number: Optional[str] = Field(None, max_length=50)
    insurance_provider: Optional[str] = Field(None, max_length=100)
    insurance_expiry_date: Optional[date] = None
    insured_value: Optional[Decimal] = Field(None, ge=0)
    amc_vendor_id: Optional[UUID] = None
    amc_start_date: Optional[date] = None
    amc_expiry_date: Optional[date] = None
    amc_value: Optional[Decimal] = Field(None, ge=0)
    parent_asset_id: Optional[UUID] = None
    is_component: bool = False
    tags: Optional[dict] = None
    organization_id: UUID
    # IT Act fields
    it_act_block: Optional[ITActAssetBlock] = None
    it_act_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    is_additional_depreciation_eligible: bool = False


class FixedAssetUpdate(BaseSchema):
    """Schema for updating a fixed asset."""

    asset_name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    category_id: Optional[UUID] = None
    location_id: Optional[UUID] = None
    department_id: Optional[UUID] = None
    custodian_employee_id: Optional[UUID] = None
    put_to_use_date: Optional[date] = None
    vendor_id: Optional[UUID] = None
    invoice_number: Optional[str] = Field(None, max_length=50)
    invoice_date: Optional[date] = None
    po_number: Optional[str] = Field(None, max_length=50)
    make: Optional[str] = Field(None, max_length=100)
    model: Optional[str] = Field(None, max_length=100)
    serial_number: Optional[str] = Field(None, max_length=100)
    warranty_start_date: Optional[date] = None
    warranty_expiry_date: Optional[date] = None
    insurance_policy_number: Optional[str] = Field(None, max_length=50)
    insurance_provider: Optional[str] = Field(None, max_length=100)
    insurance_expiry_date: Optional[date] = None
    insured_value: Optional[Decimal] = Field(None, ge=0)
    amc_vendor_id: Optional[UUID] = None
    amc_start_date: Optional[date] = None
    amc_expiry_date: Optional[date] = None
    amc_value: Optional[Decimal] = Field(None, ge=0)
    tags: Optional[dict] = None
    # IT Act fields
    it_act_block: Optional[ITActAssetBlock] = None
    it_act_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    is_additional_depreciation_eligible: Optional[bool] = None


class FixedAssetResponse(AuditSchema):
    """Fixed asset response schema."""

    id: UUID
    organization_id: UUID
    asset_code: str
    asset_name: str
    description: Optional[str] = None
    category_id: UUID
    category_code: Optional[str] = None
    category_name: Optional[str] = None
    location_id: Optional[UUID] = None
    location_name: Optional[str] = None
    department_id: Optional[UUID] = None
    department_name: Optional[str] = None
    custodian_employee_id: Optional[UUID] = None
    custodian_name: Optional[str] = None
    acquisition_date: date
    put_to_use_date: Optional[date] = None
    acquisition_type: AssetAcquisitionType
    vendor_id: Optional[UUID] = None
    vendor_name: Optional[str] = None
    invoice_number: Optional[str] = None
    invoice_date: Optional[date] = None
    po_number: Optional[str] = None
    acquisition_cost: Decimal
    installation_cost: Decimal
    other_costs: Decimal
    total_cost: Decimal
    residual_value: Decimal
    depreciable_value: Decimal
    useful_life_months: int
    depreciation_method: DepreciationMethod
    depreciation_rate: Decimal
    accumulated_depreciation: Decimal
    wdv_value: Decimal
    last_depreciation_date: Optional[date] = None
    depreciation_start_date: Optional[date] = None
    revaluation_amount: Decimal
    impairment_amount: Decimal
    make: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    quantity: int
    warranty_start_date: Optional[date] = None
    warranty_expiry_date: Optional[date] = None
    insurance_policy_number: Optional[str] = None
    insurance_provider: Optional[str] = None
    insurance_expiry_date: Optional[date] = None
    insured_value: Optional[Decimal] = None
    amc_vendor_id: Optional[UUID] = None
    amc_vendor_name: Optional[str] = None
    amc_start_date: Optional[date] = None
    amc_expiry_date: Optional[date] = None
    amc_value: Optional[Decimal] = None
    parent_asset_id: Optional[UUID] = None
    is_component: bool
    disposal_date: Optional[date] = None
    disposal_type: Optional[AssetDisposalType] = None
    disposal_value: Optional[Decimal] = None
    disposal_gain_loss: Optional[Decimal] = None
    disposal_remarks: Optional[str] = None
    status: AssetStatus
    tags: Optional[dict] = None
    is_fully_depreciated: bool = False
    # IT Act depreciation fields
    it_act_block: Optional[ITActAssetBlock] = None
    it_act_rate: Decimal = Decimal("0.00")
    it_accumulated_depreciation: Decimal = Decimal("0.00")
    it_wdv_value: Decimal = Decimal("0.00")
    it_last_depreciation_date: Optional[date] = None
    it_last_depreciation_fy: Optional[str] = None
    is_additional_depreciation_eligible: bool = False
    additional_depreciation_claimed: Decimal = Decimal("0.00")
    # Computed: difference between Companies Act and IT Act
    depreciation_difference: Optional[Decimal] = None


class AssetCapitalizeRequest(BaseSchema):
    """Request to capitalize an asset."""

    capitalization_date: date
    put_to_use_date: Optional[date] = None
    depreciation_start_date: Optional[date] = None
    remarks: Optional[str] = Field(None, max_length=500)


class AssetDisposeRequest(BaseSchema):
    """Request to dispose an asset."""

    disposal_date: date
    disposal_type: AssetDisposalType
    disposal_value: Decimal = Field(Decimal("0.00"), ge=0)
    disposal_remarks: Optional[str] = Field(None, max_length=500)
    buyer_name: Optional[str] = Field(None, max_length=200)
    buyer_address: Optional[str] = Field(None, max_length=500)


class AssetTransferRequest(BaseSchema):
    """Request to transfer an asset."""

    transfer_date: date
    to_location_id: Optional[UUID] = None
    to_department_id: Optional[UUID] = None
    to_custodian_id: Optional[UUID] = None
    reason: Optional[str] = Field(None, max_length=500)


class AssetRevalueRequest(BaseSchema):
    """Request to revalue an asset."""

    revaluation_date: date
    new_value: Decimal = Field(..., ge=0)
    valuer_name: Optional[str] = Field(None, max_length=200)
    valuation_report_number: Optional[str] = Field(None, max_length=100)
    valuation_report_date: Optional[date] = None
    valuation_method: Optional[str] = Field(None, max_length=100)
    reason: Optional[str] = Field(None, max_length=500)


class AssetImpairRequest(BaseSchema):
    """Request to record impairment on an asset."""

    impairment_date: date
    impairment_amount: Decimal = Field(..., ge=0)
    reason: Optional[str] = Field(None, max_length=500)


class AssetTransferResponse(AuditSchema):
    """Asset transfer response schema."""

    id: UUID
    asset_id: UUID
    asset_code: Optional[str] = None
    asset_name: Optional[str] = None
    transfer_date: date
    transfer_reference: Optional[str] = None
    from_location_id: Optional[UUID] = None
    from_location_name: Optional[str] = None
    from_department_id: Optional[UUID] = None
    from_department_name: Optional[str] = None
    from_custodian_id: Optional[UUID] = None
    to_location_id: Optional[UUID] = None
    to_location_name: Optional[str] = None
    to_department_id: Optional[UUID] = None
    to_department_name: Optional[str] = None
    to_custodian_id: Optional[UUID] = None
    reason: Optional[str] = None
    status: str
    remarks: Optional[str] = None


class AssetRevaluationResponse(AuditSchema):
    """Asset revaluation response schema."""

    id: UUID
    asset_id: UUID
    asset_code: Optional[str] = None
    asset_name: Optional[str] = None
    revaluation_date: date
    revaluation_type: RevaluationType
    previous_value: Decimal
    new_value: Decimal
    revaluation_amount: Decimal
    valuer_name: Optional[str] = None
    valuation_report_number: Optional[str] = None
    valuation_report_date: Optional[date] = None
    valuation_method: Optional[str] = None
    reason: Optional[str] = None
    voucher_id: Optional[UUID] = None
