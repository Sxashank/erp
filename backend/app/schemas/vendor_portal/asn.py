"""Advanced Shipping Notice Schemas."""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import Field

from app.schemas.base import BaseSchema
from app.models.vendor_portal.enums import ASNStatus


class ASNLineCreate(BaseSchema):
    """Create ASN line item."""

    po_line_id: UUID
    po_line_number: Optional[int] = None

    item_code: str = Field(..., max_length=50)
    item_description: str = Field(..., max_length=500)
    hsn_sac_code: Optional[str] = Field(None, max_length=10)
    uom: str = Field(..., max_length=20)

    ordered_quantity: Decimal = Field(..., gt=0)
    shipped_quantity: Decimal = Field(..., gt=0)

    batch_number: Optional[str] = Field(None, max_length=50)
    serial_numbers: Optional[List[str]] = None
    manufacturing_date: Optional[date] = None
    expiry_date: Optional[date] = None

    package_count: Optional[int] = Field(None, ge=1)
    package_type: Optional[str] = Field(None, max_length=50)
    weight: Optional[Decimal] = Field(None, ge=0)

    unit_price: Optional[Decimal] = Field(None, ge=0)
    remarks: Optional[str] = None


class ASNLineUpdate(BaseSchema):
    """Update ASN line item."""

    shipped_quantity: Optional[Decimal] = Field(None, gt=0)
    batch_number: Optional[str] = Field(None, max_length=50)
    serial_numbers: Optional[List[str]] = None
    manufacturing_date: Optional[date] = None
    expiry_date: Optional[date] = None
    package_count: Optional[int] = Field(None, ge=1)
    package_type: Optional[str] = Field(None, max_length=50)
    weight: Optional[Decimal] = Field(None, ge=0)
    remarks: Optional[str] = None


class ASNLineResponse(BaseSchema):
    """ASN line item response."""

    id: UUID
    line_number: int
    po_line_id: UUID
    po_line_number: Optional[int] = None

    item_code: str
    item_description: str
    hsn_sac_code: Optional[str] = None
    uom: str

    ordered_quantity: Decimal
    shipped_quantity: Decimal
    received_quantity: Optional[Decimal] = None
    rejected_quantity: Optional[Decimal] = None
    accepted_quantity: Optional[Decimal] = None

    batch_number: Optional[str] = None
    serial_numbers: Optional[List[str]] = None
    manufacturing_date: Optional[date] = None
    expiry_date: Optional[date] = None

    quality_check_required: bool
    quality_check_status: Optional[str] = None
    quality_remarks: Optional[str] = None

    package_count: Optional[int] = None
    package_type: Optional[str] = None
    weight: Optional[Decimal] = None

    unit_price: Optional[Decimal] = None
    line_total: Optional[Decimal] = None
    remarks: Optional[str] = None


class ASNCreate(BaseSchema):
    """Create ASN."""

    purchase_order_id: UUID
    purchase_order_number: str = Field(..., max_length=50)

    asn_date: date
    ship_date: date
    expected_delivery_date: date

    # Carrier Info
    carrier_name: Optional[str] = Field(None, max_length=100)
    carrier_code: Optional[str] = Field(None, max_length=50)
    tracking_number: Optional[str] = Field(None, max_length=100)
    tracking_url: Optional[str] = Field(None, max_length=500)

    # Vehicle Details
    vehicle_number: Optional[str] = Field(None, max_length=20)
    vehicle_type: Optional[str] = Field(None, max_length=50)
    driver_name: Optional[str] = Field(None, max_length=100)
    driver_phone: Optional[str] = Field(None, max_length=15)

    # Packaging
    total_packages: int = Field(default=1, ge=1)
    total_weight: Optional[Decimal] = Field(None, ge=0)
    weight_uom: Optional[str] = Field(None, max_length=10)
    total_volume: Optional[Decimal] = Field(None, ge=0)
    volume_uom: Optional[str] = Field(None, max_length=10)

    # Addresses
    ship_from_address: Optional[str] = None
    delivery_location: Optional[str] = Field(None, max_length=200)

    # E-Way Bill
    e_way_bill_number: Optional[str] = Field(None, max_length=20)
    e_way_bill_date: Optional[date] = None

    # LR
    lr_number: Optional[str] = Field(None, max_length=50)
    lr_date: Optional[date] = None

    # Lines
    lines: List[ASNLineCreate] = []

    # Remarks
    vendor_remarks: Optional[str] = None
    delivery_instructions: Optional[str] = None


class ASNUpdate(BaseSchema):
    """Update ASN."""

    ship_date: Optional[date] = None
    expected_delivery_date: Optional[date] = None

    carrier_name: Optional[str] = Field(None, max_length=100)
    carrier_code: Optional[str] = Field(None, max_length=50)
    tracking_number: Optional[str] = Field(None, max_length=100)
    tracking_url: Optional[str] = Field(None, max_length=500)

    vehicle_number: Optional[str] = Field(None, max_length=20)
    vehicle_type: Optional[str] = Field(None, max_length=50)
    driver_name: Optional[str] = Field(None, max_length=100)
    driver_phone: Optional[str] = Field(None, max_length=15)

    total_packages: Optional[int] = Field(None, ge=1)
    total_weight: Optional[Decimal] = Field(None, ge=0)
    weight_uom: Optional[str] = Field(None, max_length=10)

    ship_from_address: Optional[str] = None
    delivery_location: Optional[str] = Field(None, max_length=200)

    e_way_bill_number: Optional[str] = Field(None, max_length=20)
    e_way_bill_date: Optional[date] = None
    lr_number: Optional[str] = Field(None, max_length=50)
    lr_date: Optional[date] = None

    vendor_remarks: Optional[str] = None
    delivery_instructions: Optional[str] = None


class ASNDispatchRequest(BaseSchema):
    """Mark ASN as dispatched."""

    tracking_number: Optional[str] = Field(None, max_length=100)
    vehicle_number: Optional[str] = Field(None, max_length=20)
    driver_name: Optional[str] = Field(None, max_length=100)
    driver_phone: Optional[str] = Field(None, max_length=15)
    e_way_bill_number: Optional[str] = Field(None, max_length=20)
    lr_number: Optional[str] = Field(None, max_length=50)
    dispatch_remarks: Optional[str] = None


class ASNTrackingUpdate(BaseSchema):
    """Update ASN tracking info."""

    tracking_number: Optional[str] = Field(None, max_length=100)
    tracking_url: Optional[str] = Field(None, max_length=500)
    current_location: Optional[str] = Field(None, max_length=200)
    expected_delivery_date: Optional[date] = None
    tracking_remarks: Optional[str] = None


class ASNResponse(BaseSchema):
    """ASN response."""

    id: UUID
    vendor_id: UUID
    organization_id: UUID

    asn_number: str
    asn_date: date
    purchase_order_id: UUID
    purchase_order_number: str

    ship_date: date
    expected_delivery_date: date
    actual_delivery_date: Optional[date] = None

    # Carrier
    carrier_name: Optional[str] = None
    carrier_code: Optional[str] = None
    tracking_number: Optional[str] = None
    tracking_url: Optional[str] = None

    # Vehicle
    vehicle_number: Optional[str] = None
    vehicle_type: Optional[str] = None
    driver_name: Optional[str] = None
    driver_phone: Optional[str] = None

    # Packaging
    total_packages: int
    total_weight: Optional[Decimal] = None
    weight_uom: Optional[str] = None
    total_volume: Optional[Decimal] = None
    volume_uom: Optional[str] = None

    # Addresses
    ship_from_address: Optional[str] = None
    ship_to_address: Optional[str] = None
    delivery_location: Optional[str] = None

    # E-Way Bill & LR
    e_way_bill_number: Optional[str] = None
    e_way_bill_date: Optional[date] = None
    lr_number: Optional[str] = None
    lr_date: Optional[date] = None

    # Status
    status: ASNStatus
    dispatched_at: Optional[datetime] = None
    in_transit_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None

    # Receipt
    grn_id: Optional[UUID] = None
    grn_number: Optional[str] = None
    received_by: Optional[str] = None
    received_at: Optional[datetime] = None

    vendor_remarks: Optional[str] = None
    delivery_instructions: Optional[str] = None

    lines: List[ASNLineResponse] = []

    created_at: datetime
    updated_at: Optional[datetime] = None


class ASNListResponse(BaseSchema):
    """ASN list item response."""

    id: UUID
    asn_number: str
    asn_date: date
    purchase_order_number: str
    ship_date: date
    expected_delivery_date: date
    carrier_name: Optional[str] = None
    tracking_number: Optional[str] = None
    status: ASNStatus
    total_packages: int
    line_count: int = 0
    created_at: datetime


class ASNSummary(BaseSchema):
    """ASN summary for dashboard."""

    total_asns: int = 0
    draft_count: int = 0
    dispatched_count: int = 0
    in_transit_count: int = 0
    delivered_count: int = 0
    partially_received_count: int = 0


# Aliases for backward compatibility
ASNDispatch = ASNDispatchRequest
