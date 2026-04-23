"""Purchase Order Schemas for Vendor Portal."""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import Field

from app.schemas.base import BaseSchema
from app.models.vendor_portal.enums import (
    POAcknowledgementStatus,
    ChangeRequestType,
    ChangeRequestStatus,
)


class POLineResponse(BaseSchema):
    """PO line item response."""

    id: UUID
    line_number: int
    item_code: Optional[str] = None
    item_description: str
    hsn_sac_code: Optional[str] = None
    uom: str
    quantity: Decimal
    unit_price: Decimal
    line_total: Decimal
    cgst_rate: Decimal
    cgst_amount: Decimal
    sgst_rate: Decimal
    sgst_amount: Decimal
    igst_rate: Decimal
    igst_amount: Decimal
    net_amount: Decimal
    delivery_date: Optional[date] = None
    received_quantity: Decimal = Decimal("0")
    pending_quantity: Decimal = Decimal("0")


class POListResponse(BaseSchema):
    """PO list item response."""

    id: UUID
    po_number: str
    po_date: date
    delivery_date: Optional[date] = None
    total_amount: Decimal
    status: str
    acknowledgement_status: Optional[POAcknowledgementStatus] = None
    line_count: int = 0
    currency: str = "INR"
    created_at: datetime


class PODetailResponse(BaseSchema):
    """PO detail response."""

    id: UUID
    po_number: str
    po_date: date
    delivery_date: Optional[date] = None

    # Buyer Info
    buyer_name: str
    buyer_address: Optional[str] = None
    ship_to_address: Optional[str] = None
    bill_to_address: Optional[str] = None

    # Payment Terms
    payment_terms: Optional[str] = None
    credit_days: int = 0

    # Amounts
    subtotal: Decimal
    discount_amount: Decimal = Decimal("0")
    cgst_amount: Decimal = Decimal("0")
    sgst_amount: Decimal = Decimal("0")
    igst_amount: Decimal = Decimal("0")
    total_amount: Decimal

    # Status
    status: str
    acknowledgement_status: Optional[POAcknowledgementStatus] = None
    acknowledged_at: Optional[datetime] = None
    committed_delivery_date: Optional[date] = None

    # Lines
    lines: List[POLineResponse] = []

    # Change Requests
    pending_change_requests: int = 0

    # Remarks
    terms_and_conditions: Optional[str] = None
    special_instructions: Optional[str] = None

    currency: str = "INR"
    created_at: datetime


class POAcknowledgeRequest(BaseSchema):
    """Acknowledge PO request."""

    committed_delivery_date: date
    delivery_remarks: Optional[str] = Field(None, max_length=500)


class PORejectRequest(BaseSchema):
    """Reject PO request."""

    rejection_reason: str = Field(..., min_length=10, max_length=1000)
    rejection_category: Optional[str] = Field(None, max_length=100)


class POChangeRequestCreate(BaseSchema):
    """Create PO change request."""

    change_type: ChangeRequestType
    change_description: str = Field(..., min_length=10, max_length=2000)

    # Line-specific change
    po_line_id: Optional[UUID] = None
    po_line_number: Optional[int] = None

    # Values
    original_value: Optional[str] = None  # JSON string
    requested_value: Optional[str] = None  # JSON string
    justification: Optional[str] = Field(None, max_length=1000)


class POChangeRequestResponse(BaseSchema):
    """Change request response."""

    id: UUID
    request_number: str
    change_type: ChangeRequestType
    change_description: str
    po_line_number: Optional[int] = None
    original_value: Optional[str] = None
    requested_value: Optional[str] = None
    justification: Optional[str] = None
    status: ChangeRequestStatus
    submitted_at: datetime
    reviewed_at: Optional[datetime] = None
    review_remarks: Optional[str] = None
    approved_value: Optional[str] = None
    buyer_response: Optional[str] = None


class POHistoryResponse(BaseSchema):
    """PO collaboration history response."""

    id: UUID
    action: str
    action_by: str
    action_at: datetime
    details: Optional[str] = None
    old_value: Optional[str] = None
    new_value: Optional[str] = None


class POAcknowledgementResponse(BaseSchema):
    """PO acknowledgement response."""

    id: UUID
    purchase_order_id: UUID
    status: POAcknowledgementStatus
    committed_delivery_date: Optional[date] = None
    delivery_remarks: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    rejected_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None


class POChangeRequestListResponse(BaseSchema):
    """Change request list response."""

    total: int
    change_requests: List[POChangeRequestResponse] = []


class POAcknowledgementSummary(BaseSchema):
    """Acknowledgement summary response."""

    pending_acknowledgement: int = 0
    acknowledged: int = 0
    rejected: int = 0
    change_requested: int = 0
    total: int = 0


class VendorPOListResponse(BaseSchema):
    """Paginated PO list response."""

    total: int
    purchase_orders: List[POListResponse] = []


# Aliases for backward compatibility with services and routes
POAcknowledgementCreate = POAcknowledgeRequest
VendorPODetailResponse = PODetailResponse
