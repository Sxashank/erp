"""Asset Category schemas."""

from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import Field

from app.schemas.base import BaseSchema, AuditSchema
from app.core.constants import AssetType, DepreciationMethod


class AssetCategoryCreate(BaseSchema):
    """Schema for creating an asset category."""

    category_code: str = Field(..., min_length=1, max_length=20)
    category_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    parent_category_id: Optional[UUID] = None
    asset_type: AssetType = AssetType.TANGIBLE
    depreciation_method: DepreciationMethod = DepreciationMethod.SLM
    useful_life_years: int = Field(5, ge=1, le=100)
    residual_value_pct: Decimal = Field(Decimal("5.00"), ge=0, le=100)
    depreciation_rate_slm: Decimal = Field(Decimal("0.00"), ge=0, le=100)
    depreciation_rate_wdv: Decimal = Field(Decimal("0.00"), ge=0, le=100)
    it_act_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    it_act_block: Optional[str] = Field(None, max_length=10)
    capitalization_threshold: Decimal = Field(Decimal("5000.00"), ge=0)
    gl_asset_account_id: Optional[UUID] = None
    gl_accum_dep_account_id: Optional[UUID] = None
    gl_dep_expense_account_id: Optional[UUID] = None
    gl_disposal_gain_account_id: Optional[UUID] = None
    gl_disposal_loss_account_id: Optional[UUID] = None
    gl_revaluation_reserve_account_id: Optional[UUID] = None
    gl_impairment_account_id: Optional[UUID] = None
    requires_insurance: bool = False
    requires_amc: bool = False
    organization_id: UUID


class AssetCategoryUpdate(BaseSchema):
    """Schema for updating an asset category."""

    category_code: Optional[str] = Field(None, min_length=1, max_length=20)
    category_name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    parent_category_id: Optional[UUID] = None
    asset_type: Optional[AssetType] = None
    depreciation_method: Optional[DepreciationMethod] = None
    useful_life_years: Optional[int] = Field(None, ge=1, le=100)
    residual_value_pct: Optional[Decimal] = Field(None, ge=0, le=100)
    depreciation_rate_slm: Optional[Decimal] = Field(None, ge=0, le=100)
    depreciation_rate_wdv: Optional[Decimal] = Field(None, ge=0, le=100)
    it_act_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    it_act_block: Optional[str] = Field(None, max_length=10)
    capitalization_threshold: Optional[Decimal] = Field(None, ge=0)
    gl_asset_account_id: Optional[UUID] = None
    gl_accum_dep_account_id: Optional[UUID] = None
    gl_dep_expense_account_id: Optional[UUID] = None
    gl_disposal_gain_account_id: Optional[UUID] = None
    gl_disposal_loss_account_id: Optional[UUID] = None
    gl_revaluation_reserve_account_id: Optional[UUID] = None
    gl_impairment_account_id: Optional[UUID] = None
    requires_insurance: Optional[bool] = None
    requires_amc: Optional[bool] = None


class AssetCategoryResponse(AuditSchema):
    """Asset category response schema."""

    id: UUID
    organization_id: UUID
    category_code: str
    category_name: str
    description: Optional[str] = None
    parent_category_id: Optional[UUID] = None
    parent_category_name: Optional[str] = None
    asset_type: AssetType
    depreciation_method: DepreciationMethod
    useful_life_years: int
    residual_value_pct: Decimal
    depreciation_rate_slm: Decimal
    depreciation_rate_wdv: Decimal
    it_act_rate: Optional[Decimal] = None
    it_act_block: Optional[str] = None
    capitalization_threshold: Decimal
    gl_asset_account_id: Optional[UUID] = None
    gl_asset_account_name: Optional[str] = None
    gl_accum_dep_account_id: Optional[UUID] = None
    gl_accum_dep_account_name: Optional[str] = None
    gl_dep_expense_account_id: Optional[UUID] = None
    gl_dep_expense_account_name: Optional[str] = None
    gl_disposal_gain_account_id: Optional[UUID] = None
    gl_disposal_loss_account_id: Optional[UUID] = None
    gl_revaluation_reserve_account_id: Optional[UUID] = None
    gl_impairment_account_id: Optional[UUID] = None
    requires_insurance: bool
    requires_amc: bool
    asset_count: int = 0


class AssetCategoryTreeResponse(BaseSchema):
    """Asset category tree node for hierarchical display."""

    id: UUID
    category_code: str
    category_name: str
    asset_type: AssetType
    depreciation_method: DepreciationMethod
    useful_life_years: int
    asset_count: int = 0
    children: List["AssetCategoryTreeResponse"] = []


# Update forward reference
AssetCategoryTreeResponse.model_rebuild()
