"""Fixed Assets Configuration schemas."""

from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import Field

from app.schemas.base import BaseSchema, AuditSchema


class FAConfigurationCreate(BaseSchema):
    """Schema for creating FA configuration."""

    organization_id: UUID

    # Asset Code Format
    asset_code_prefix: str = Field("FA", max_length=10)
    asset_code_format: str = Field(
        "{prefix}/{category}/{year}/{sequence:05d}",
        max_length=100,
    )
    asset_code_separator: str = Field("/", max_length=1)
    auto_generate_code: bool = True

    # Financial Year
    fy_start_month: int = Field(4, ge=1, le=12)
    fy_start_day: int = Field(1, ge=1, le=31)

    # Approval Thresholds
    creation_approval_threshold: Decimal = Field(Decimal("1000000.00"), ge=0)
    disposal_approval_threshold: Decimal = Field(Decimal("0.00"), ge=0)
    revaluation_approval_threshold: Decimal = Field(Decimal("0.00"), ge=0)
    transfer_requires_approval: bool = True

    # Depreciation
    days_in_year: int = Field(365, ge=360, le=366)
    pro_rata_method: str = Field("DAILY", pattern="^(DAILY|MONTHLY|HALF_YEARLY|FULL_MONTH)$")
    min_asset_value_for_depreciation: Decimal = Field(Decimal("5000.00"), ge=0)
    depreciation_posting_auto_approve: bool = False

    # Alerts
    amc_expiry_reminder_days: int = Field(30, ge=1, le=365)
    insurance_expiry_reminder_days: int = Field(30, ge=1, le=365)
    warranty_expiry_reminder_days: int = Field(30, ge=1, le=365)
    lease_expiry_reminder_days: int = Field(90, ge=1, le=365)
    lease_payment_reminder_days: int = Field(7, ge=1, le=30)

    # Physical Verification
    pv_frequency_months: int = Field(12, ge=1, le=36)
    pv_tolerance_percentage: Decimal = Field(Decimal("5.00"), ge=0, le=100)

    # GL Integration
    auto_post_capitalization: bool = True
    auto_post_disposal: bool = True
    auto_post_depreciation: bool = True

    # Pagination
    default_page_size: int = Field(50, ge=10, le=200)
    max_page_size: int = Field(200, ge=50, le=500)

    # Custom
    custom_settings: Optional[dict] = None
    notification_emails: Optional[List[str]] = None


class FAConfigurationUpdate(BaseSchema):
    """Schema for updating FA configuration."""

    # Asset Code Format
    asset_code_prefix: Optional[str] = Field(None, max_length=10)
    asset_code_format: Optional[str] = Field(None, max_length=100)
    asset_code_separator: Optional[str] = Field(None, max_length=1)
    auto_generate_code: Optional[bool] = None

    # Financial Year
    fy_start_month: Optional[int] = Field(None, ge=1, le=12)
    fy_start_day: Optional[int] = Field(None, ge=1, le=31)

    # Approval Thresholds
    creation_approval_threshold: Optional[Decimal] = Field(None, ge=0)
    disposal_approval_threshold: Optional[Decimal] = Field(None, ge=0)
    revaluation_approval_threshold: Optional[Decimal] = Field(None, ge=0)
    transfer_requires_approval: Optional[bool] = None

    # Depreciation
    days_in_year: Optional[int] = Field(None, ge=360, le=366)
    pro_rata_method: Optional[str] = Field(None, pattern="^(DAILY|MONTHLY|HALF_YEARLY|FULL_MONTH)$")
    min_asset_value_for_depreciation: Optional[Decimal] = Field(None, ge=0)
    depreciation_posting_auto_approve: Optional[bool] = None

    # Alerts
    amc_expiry_reminder_days: Optional[int] = Field(None, ge=1, le=365)
    insurance_expiry_reminder_days: Optional[int] = Field(None, ge=1, le=365)
    warranty_expiry_reminder_days: Optional[int] = Field(None, ge=1, le=365)
    lease_expiry_reminder_days: Optional[int] = Field(None, ge=1, le=365)
    lease_payment_reminder_days: Optional[int] = Field(None, ge=1, le=30)

    # Physical Verification
    pv_frequency_months: Optional[int] = Field(None, ge=1, le=36)
    pv_tolerance_percentage: Optional[Decimal] = Field(None, ge=0, le=100)

    # GL Integration
    auto_post_capitalization: Optional[bool] = None
    auto_post_disposal: Optional[bool] = None
    auto_post_depreciation: Optional[bool] = None

    # Pagination
    default_page_size: Optional[int] = Field(None, ge=10, le=200)
    max_page_size: Optional[int] = Field(None, ge=50, le=500)

    # Custom
    custom_settings: Optional[dict] = None
    notification_emails: Optional[List[str]] = None


class FAConfigurationResponse(AuditSchema):
    """Response schema for FA configuration."""

    id: UUID
    organization_id: UUID

    # Asset Code Format
    asset_code_prefix: str
    asset_code_format: str
    asset_code_separator: str
    auto_generate_code: bool

    # Financial Year
    fy_start_month: int
    fy_start_day: int

    # Approval Thresholds
    creation_approval_threshold: Decimal
    disposal_approval_threshold: Decimal
    revaluation_approval_threshold: Decimal
    transfer_requires_approval: bool

    # Depreciation
    days_in_year: int
    pro_rata_method: str
    min_asset_value_for_depreciation: Decimal
    depreciation_posting_auto_approve: bool

    # Alerts
    amc_expiry_reminder_days: int
    insurance_expiry_reminder_days: int
    warranty_expiry_reminder_days: int
    lease_expiry_reminder_days: int
    lease_payment_reminder_days: int

    # Physical Verification
    pv_frequency_months: int
    pv_tolerance_percentage: Decimal

    # GL Integration
    auto_post_capitalization: bool
    auto_post_disposal: bool
    auto_post_depreciation: bool

    # Pagination
    default_page_size: int
    max_page_size: int

    # Custom
    custom_settings: Optional[dict] = None
    notification_emails: Optional[List[str]] = None
