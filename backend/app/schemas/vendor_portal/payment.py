"""Vendor Payment Schemas."""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import Field

from app.schemas.base import BaseSchema


class PaymentAllocationResponse(BaseSchema):
    """Payment allocation to invoice."""

    invoice_id: UUID
    invoice_number: str
    invoice_date: date
    invoice_amount: Decimal
    allocated_amount: Decimal


class PaymentListResponse(BaseSchema):
    """Payment list item response."""

    id: UUID
    payment_number: str
    payment_date: date
    payment_mode: str
    amount: Decimal
    currency: str = "INR"
    status: str
    reference_number: Optional[str] = None
    utr_number: Optional[str] = None
    invoices_count: int = 0
    created_at: datetime


class PaymentDetailResponse(BaseSchema):
    """Payment detail response."""

    id: UUID
    payment_number: str
    payment_date: date
    payment_mode: str
    amount: Decimal
    currency: str = "INR"
    status: str

    # Bank Details
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    reference_number: Optional[str] = None
    utr_number: Optional[str] = None
    cheque_number: Optional[str] = None
    cheque_date: Optional[date] = None

    # Deductions
    tds_amount: Decimal = Decimal("0")
    other_deductions: Decimal = Decimal("0")
    net_amount: Decimal

    # Remarks
    remarks: Optional[str] = None

    # Allocations
    allocations: List[PaymentAllocationResponse] = []

    # Remittance
    remittance_available: bool = False

    created_at: datetime


class AgingBucket(BaseSchema):
    """Aging bucket details."""

    bucket: str  # 0-30, 31-60, 61-90, 91-120, 120+
    invoice_count: int
    amount: Decimal


class PaymentAgingResponse(BaseSchema):
    """Payment aging report response."""

    vendor_id: UUID
    vendor_name: str
    as_of_date: date

    total_outstanding: Decimal
    total_overdue: Decimal

    buckets: List[AgingBucket] = []

    oldest_invoice_date: Optional[date] = None
    oldest_invoice_days: int = 0

    overdue_invoices: List["OverdueInvoice"] = []


class OverdueInvoice(BaseSchema):
    """Overdue invoice details."""

    id: UUID
    invoice_number: str
    invoice_date: date
    due_date: date
    days_overdue: int
    original_amount: Decimal
    balance_amount: Decimal


class ScheduledPayment(BaseSchema):
    """Scheduled payment details."""

    id: UUID
    invoice_number: str
    invoice_date: date
    due_date: date
    amount: Decimal
    scheduled_date: Optional[date] = None
    status: str


class ScheduledPaymentsResponse(BaseSchema):
    """Scheduled payments response."""

    vendor_id: UUID
    total_scheduled: Decimal
    payments: List[ScheduledPayment] = []


class AccountStatementRequest(BaseSchema):
    """Account statement request."""

    from_date: date
    to_date: date
    include_pending: bool = True


class StatementLine(BaseSchema):
    """Account statement line."""

    date: date
    document_type: str  # INVOICE, PAYMENT, DEBIT_NOTE, CREDIT_NOTE
    document_number: str
    description: str
    debit: Decimal = Decimal("0")
    credit: Decimal = Decimal("0")
    balance: Decimal


class AccountStatementResponse(BaseSchema):
    """Account statement response."""

    vendor_id: UUID
    vendor_name: str
    vendor_code: str

    from_date: date
    to_date: date
    generated_at: datetime

    opening_balance: Decimal
    opening_balance_type: str  # DR, CR

    total_invoices: Decimal
    total_payments: Decimal
    total_debit_notes: Decimal
    total_credit_notes: Decimal

    closing_balance: Decimal
    closing_balance_type: str  # DR, CR

    lines: List[StatementLine] = []


class RemittanceAdviceResponse(BaseSchema):
    """Remittance advice details."""

    payment_id: UUID
    payment_number: str
    payment_date: date
    payment_mode: str
    amount: Decimal

    # Payer Details
    payer_name: str
    payer_address: Optional[str] = None

    # Bank Details
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    utr_number: Optional[str] = None

    # Invoice Details
    invoices: List["RemittanceInvoice"] = []

    # Deductions
    tds_amount: Decimal = Decimal("0")
    tds_details: Optional[str] = None
    other_deductions: Decimal = Decimal("0")
    deduction_details: Optional[str] = None

    net_amount: Decimal


class RemittanceInvoice(BaseSchema):
    """Invoice in remittance advice."""

    invoice_number: str
    invoice_date: date
    invoice_amount: Decimal
    allocated_amount: Decimal
    tds_deducted: Decimal = Decimal("0")


class VendorPaymentFilter(BaseSchema):
    """Filter for vendor payments."""

    from_date: Optional[date] = None
    to_date: Optional[date] = None
    payment_mode: Optional[str] = None
    status: Optional[str] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None


class VendorAgingFilter(BaseSchema):
    """Filter for vendor aging report."""

    as_of_date: Optional[date] = None
    include_future: bool = False


class VendorStatementFilter(BaseSchema):
    """Filter for vendor statement."""

    from_date: date
    to_date: date
    include_pending: bool = True
    document_types: Optional[List[str]] = None


class VendorPaymentSummary(BaseSchema):
    """Vendor payment summary for dashboard."""

    total_received: Decimal = Decimal("0")
    total_pending: Decimal = Decimal("0")
    overdue_amount: Decimal = Decimal("0")
    last_payment_date: Optional[date] = None
    last_payment_amount: Decimal = Decimal("0")
    next_scheduled_date: Optional[date] = None
    next_scheduled_amount: Decimal = Decimal("0")


class UpcomingPayment(BaseSchema):
    """Upcoming payment details."""

    invoice_id: UUID
    invoice_number: str
    invoice_date: date
    due_date: date
    amount: Decimal
    scheduled_date: Optional[date] = None


class VendorPaymentListResponse(BaseSchema):
    """Paginated payment list response."""

    total: int
    payments: List[PaymentListResponse] = []


# Aliases for service compatibility
VendorPaymentResponse = PaymentDetailResponse
VendorAgingReport = PaymentAgingResponse
VendorStatement = AccountStatementResponse
VendorStatementLine = StatementLine
