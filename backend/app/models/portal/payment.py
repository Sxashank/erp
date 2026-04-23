"""Portal Payment Models.

Handles payment requests, transactions, saved methods, and auto-debit mandates.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import (
    String,
    Boolean,
    ForeignKey,
    Text,
    DateTime,
    Date,
    Numeric,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel
from app.models.portal.enums import (
    PaymentMode,
    PaymentStatus,
    MandateStatus,
    MandateFrequency,
)


class PortalPaymentRequest(BaseModel):
    """Payment request initiated from portal.

    Created when customer initiates a payment.
    """

    __tablename__ = "portal_payment_request"

    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("mst_organization.id"),
        nullable=False,
        index=True,
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("portal_user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    loan_account_id: Mapped[UUID] = mapped_column(
        ForeignKey("lms_loan_account.id"),
        nullable=False,
        index=True,
    )

    # Request Details
    request_number: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False
    )
    request_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # EMI, PREPAYMENT, FORECLOSURE, CHARGES

    # Amount
    requested_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False
    )
    principal_component: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    interest_component: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    charges_component: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    penalty_component: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))

    # Payment Mode
    payment_mode: Mapped[Optional[PaymentMode]] = mapped_column()
    saved_method_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("portal_saved_payment_method.id")
    )

    # Expiry
    valid_until: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # Status
    status: Mapped[PaymentStatus] = mapped_column(default=PaymentStatus.INITIATED)
    status_message: Mapped[Optional[str]] = mapped_column(String(500))

    # Gateway
    gateway_name: Mapped[Optional[str]] = mapped_column(String(50))
    gateway_order_id: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    gateway_checkout_url: Mapped[Optional[str]] = mapped_column(Text)

    # Timestamps
    initiated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    __table_args__ = (
        Index("ix_portal_payment_req_user", "user_id", "status"),
        Index("ix_portal_payment_req_loan", "loan_account_id", "status"),
    )


class PortalPaymentTransaction(BaseModel):
    """Payment transaction log.

    Records each payment attempt with gateway details.
    """

    __tablename__ = "portal_payment_transaction"

    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("mst_organization.id"),
        nullable=False,
        index=True,
    )

    payment_request_id: Mapped[UUID] = mapped_column(
        ForeignKey("portal_payment_request.id"),
        nullable=False,
        index=True,
    )

    # Transaction Details
    transaction_id: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False
    )
    transaction_date: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )

    # Amount
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR")

    # Payment Info
    payment_mode: Mapped[PaymentMode] = mapped_column(nullable=False)
    bank_name: Mapped[Optional[str]] = mapped_column(String(100))
    bank_reference: Mapped[Optional[str]] = mapped_column(String(100))

    # Card Details (masked)
    card_last4: Mapped[Optional[str]] = mapped_column(String(4))
    card_network: Mapped[Optional[str]] = mapped_column(String(20))
    card_type: Mapped[Optional[str]] = mapped_column(String(20))

    # UPI Details
    upi_vpa: Mapped[Optional[str]] = mapped_column(String(100))

    # Gateway Response
    gateway_name: Mapped[str] = mapped_column(String(50), nullable=False)
    gateway_transaction_id: Mapped[Optional[str]] = mapped_column(
        String(100), index=True
    )
    gateway_order_id: Mapped[Optional[str]] = mapped_column(String(100))
    gateway_status: Mapped[Optional[str]] = mapped_column(String(50))
    gateway_response_code: Mapped[Optional[str]] = mapped_column(String(50))
    gateway_response_message: Mapped[Optional[str]] = mapped_column(Text)
    gateway_response_raw: Mapped[Optional[str]] = mapped_column(Text)  # JSON

    # Status
    status: Mapped[PaymentStatus] = mapped_column(nullable=False)
    failure_reason: Mapped[Optional[str]] = mapped_column(String(500))

    # ERP Integration
    is_posted_to_erp: Mapped[bool] = mapped_column(Boolean, default=False)
    erp_receipt_id: Mapped[Optional[UUID]] = mapped_column()
    posted_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    posting_error: Mapped[Optional[str]] = mapped_column(Text)

    # Refund
    is_refunded: Mapped[bool] = mapped_column(Boolean, default=False)
    refund_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    refund_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    refund_reference: Mapped[Optional[str]] = mapped_column(String(100))

    __table_args__ = (
        Index("ix_portal_txn_gateway", "gateway_name", "gateway_transaction_id"),
        Index("ix_portal_txn_date", "organization_id", "transaction_date"),
    )


class PortalSavedPaymentMethod(BaseModel):
    """Saved payment methods.

    Stores tokenized cards and UPI IDs for quick payments.
    """

    __tablename__ = "portal_saved_payment_method"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("portal_user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Method Info
    method_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # CARD, UPI, NETBANKING

    # Display Name
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)

    # Card Details (tokenized)
    card_token: Mapped[Optional[str]] = mapped_column(String(255))
    card_last4: Mapped[Optional[str]] = mapped_column(String(4))
    card_network: Mapped[Optional[str]] = mapped_column(String(20))  # VISA, MC, RUPAY
    card_type: Mapped[Optional[str]] = mapped_column(String(20))  # CREDIT, DEBIT
    card_issuer: Mapped[Optional[str]] = mapped_column(String(100))
    card_expiry_month: Mapped[Optional[int]] = mapped_column()
    card_expiry_year: Mapped[Optional[int]] = mapped_column()

    # UPI Details
    upi_vpa: Mapped[Optional[str]] = mapped_column(String(100))
    upi_provider: Mapped[Optional[str]] = mapped_column(String(50))

    # Bank Details (for net banking)
    bank_code: Mapped[Optional[str]] = mapped_column(String(20))
    bank_name: Mapped[Optional[str]] = mapped_column(String(100))

    # Gateway
    gateway_name: Mapped[str] = mapped_column(String(50), nullable=False)
    gateway_customer_id: Mapped[Optional[str]] = mapped_column(String(100))

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Usage
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    usage_count: Mapped[int] = mapped_column(default=0)

    __table_args__ = (
        Index("ix_portal_saved_method_user", "user_id", "is_active"),
    )


class PortalAutoDebitMandate(BaseModel):
    """Auto-debit mandate (NACH/UPI Autopay).

    Manages recurring payment mandates.
    """

    __tablename__ = "portal_auto_debit_mandate"

    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("mst_organization.id"),
        nullable=False,
        index=True,
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("portal_user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    loan_account_id: Mapped[UUID] = mapped_column(
        ForeignKey("lms_loan_account.id"),
        nullable=False,
        index=True,
    )

    # Mandate Info
    mandate_id: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False
    )
    mandate_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # NACH, UPI_AUTOPAY, EMANDATE

    # Bank Details
    bank_account_number: Mapped[Optional[str]] = mapped_column(
        String(30)
    )  # Masked
    bank_ifsc: Mapped[Optional[str]] = mapped_column(String(15))
    bank_name: Mapped[Optional[str]] = mapped_column(String(100))
    account_holder_name: Mapped[Optional[str]] = mapped_column(String(200))

    # UPI Details (for UPI Autopay)
    upi_vpa: Mapped[Optional[str]] = mapped_column(String(100))

    # Mandate Parameters
    max_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    frequency: Mapped[MandateFrequency] = mapped_column(
        default=MandateFrequency.MONTHLY
    )
    debit_day: Mapped[Optional[int]] = mapped_column()  # Day of month (1-28)

    # Validity
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Status
    status: Mapped[MandateStatus] = mapped_column(default=MandateStatus.PENDING)
    status_message: Mapped[Optional[str]] = mapped_column(String(500))
    registered_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    activated_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    cancellation_reason: Mapped[Optional[str]] = mapped_column(String(500))

    # Gateway/Sponsor Bank
    gateway_name: Mapped[Optional[str]] = mapped_column(String(50))
    gateway_mandate_id: Mapped[Optional[str]] = mapped_column(String(100))
    sponsor_bank: Mapped[Optional[str]] = mapped_column(String(100))
    umrn: Mapped[Optional[str]] = mapped_column(String(50))  # NACH UMRN

    # Last Execution
    last_execution_date: Mapped[Optional[date]] = mapped_column(Date)
    last_execution_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    last_execution_status: Mapped[Optional[str]] = mapped_column(String(50))
    consecutive_failures: Mapped[int] = mapped_column(default=0)

    __table_args__ = (
        Index("ix_portal_mandate_user", "user_id", "status"),
        Index("ix_portal_mandate_loan", "loan_account_id", "status"),
    )
