"""TDS Entry schemas."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import Field, field_validator
import re

from app.schemas.base import BaseSchema, CamelSchema
from app.core.constants import TDSDeducteeType, TDSChallanStatus


class TDSEntryBase(CamelSchema):
    """Base TDS Entry schema."""

    tds_section_id: UUID
    voucher_id: Optional[UUID] = None
    organization_id: UUID
    vendor_id: Optional[UUID] = None  # For aggregate threshold tracking
    deductee_name: str = Field(..., min_length=1, max_length=200)
    deductee_pan: Optional[str] = Field(None, min_length=10, max_length=10)
    deductee_type: TDSDeducteeType = TDSDeducteeType.COMPANY
    deductee_address: Optional[str] = None
    deduction_date: date
    base_amount: Decimal = Field(..., ge=0)
    tds_rate: Decimal = Field(..., ge=0, le=100)
    tds_amount: Decimal = Field(..., ge=0)
    surcharge: Decimal = Field(default=Decimal("0.00"), ge=0)
    cess: Decimal = Field(default=Decimal("0.00"), ge=0)
    total_tds: Decimal = Field(..., ge=0)
    lower_deduction_cert_no: Optional[str] = Field(None, max_length=50)
    remarks: Optional[str] = None

    @field_validator("deductee_pan")
    @classmethod
    def validate_pan(cls, v: Optional[str]) -> Optional[str]:
        """Validate PAN format."""
        if v is None:
            return v
        pattern = r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$"
        if not re.match(pattern, v.upper()):
            raise ValueError("Invalid PAN format")
        return v.upper()


class TDSEntryCreate(TDSEntryBase):
    """Schema for creating a TDS entry."""

    pass


class TDSEntryUpdate(CamelSchema):
    """Schema for updating a TDS entry."""

    deductee_name: Optional[str] = Field(None, min_length=1, max_length=200)
    deductee_pan: Optional[str] = Field(None, min_length=10, max_length=10)
    deductee_type: Optional[TDSDeducteeType] = None
    deductee_address: Optional[str] = None
    base_amount: Optional[Decimal] = Field(None, ge=0)
    tds_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    tds_amount: Optional[Decimal] = Field(None, ge=0)
    surcharge: Optional[Decimal] = Field(None, ge=0)
    cess: Optional[Decimal] = Field(None, ge=0)
    total_tds: Optional[Decimal] = Field(None, ge=0)
    lower_deduction_cert_no: Optional[str] = Field(None, max_length=50)
    challan_status: Optional[TDSChallanStatus] = None
    challan_number: Optional[str] = Field(None, max_length=50)
    challan_date: Optional[date] = None
    bank_name: Optional[str] = Field(None, max_length=100)
    bsr_code: Optional[str] = Field(None, max_length=10)
    certificate_number: Optional[str] = Field(None, max_length=50)
    certificate_date: Optional[date] = None
    return_quarter: Optional[str] = Field(None, max_length=10)
    return_filed: Optional[bool] = None
    acknowledgment_number: Optional[str] = Field(None, max_length=50)
    remarks: Optional[str] = None
    is_active: Optional[bool] = None


class TDSEntryResponse(CamelSchema):
    """TDS Entry response schema."""

    id: UUID
    tds_section_id: UUID
    tds_section_code: Optional[str] = None
    tds_section_name: Optional[str] = None
    voucher_id: Optional[UUID] = None
    voucher_number: Optional[str] = None
    organization_id: UUID
    vendor_id: Optional[UUID] = None
    financial_year_id: Optional[UUID] = None
    deductee_name: str
    deductee_pan: Optional[str] = None
    deductee_type: TDSDeducteeType
    deductee_address: Optional[str] = None
    deduction_date: date
    base_amount: Decimal
    tds_rate: Decimal
    tds_amount: Decimal
    surcharge: Decimal
    cess: Decimal
    total_tds: Decimal
    lower_deduction_cert_no: Optional[str] = None
    # Threshold tracking fields
    is_threshold_crossed: bool = True
    aggregate_amount_ytd: Decimal = Decimal("0.00")
    threshold_reason: Optional[str] = None
    # Challan fields
    challan_status: TDSChallanStatus
    challan_number: Optional[str] = None
    challan_date: Optional[date] = None
    bank_name: Optional[str] = None
    bsr_code: Optional[str] = None
    certificate_number: Optional[str] = None
    certificate_date: Optional[date] = None
    return_quarter: Optional[str] = None
    return_filed: bool
    acknowledgment_number: Optional[str] = None
    remarks: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = True


class ThresholdValidationRequest(CamelSchema):
    """Request schema for TDS threshold validation."""

    organization_id: UUID
    vendor_id: Optional[UUID] = None
    tds_section_id: UUID
    base_amount: Decimal = Field(..., ge=0)
    deduction_date: date
    deductee_type: TDSDeducteeType = TDSDeducteeType.COMPANY
    deductee_pan: Optional[str] = None


class ThresholdValidationResponse(CamelSchema):
    """Response schema for TDS threshold validation."""

    tds_applicable: bool
    reason: str  # SINGLE_THRESHOLD, AGGREGATE_THRESHOLD, BELOW_THRESHOLD, NO_THRESHOLD
    single_threshold: Decimal
    annual_threshold: Decimal
    current_aggregate: Decimal
    new_aggregate: Decimal
    tds_rate: Decimal
    estimated_tds: Decimal
    estimated_surcharge: Decimal
    estimated_cess: Decimal
    estimated_total_tds: Decimal
