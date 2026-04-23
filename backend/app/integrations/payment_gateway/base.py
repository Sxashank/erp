"""Base Payment Gateway Interface.

Abstract base class for payment gateway integrations.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, Dict, Any, List


class PaymentStatus(str, Enum):
    """Payment status enum."""

    CREATED = "created"
    AUTHORIZED = "authorized"
    CAPTURED = "captured"
    REFUNDED = "refunded"
    FAILED = "failed"


class RefundStatus(str, Enum):
    """Refund status enum."""

    PENDING = "pending"
    PROCESSED = "processed"
    FAILED = "failed"


class PaymentMethod(str, Enum):
    """Payment method enum."""

    UPI = "upi"
    NETBANKING = "netbanking"
    CARD = "card"
    WALLET = "wallet"
    EMANDATE = "emandate"
    NACH = "nach"
    BANK_TRANSFER = "bank_transfer"


@dataclass
class PaymentOrder:
    """Payment order details."""

    order_id: str
    amount: Decimal  # In base currency (e.g., INR)
    currency: str = "INR"
    receipt: Optional[str] = None
    notes: Optional[Dict[str, str]] = None

    # Customer details
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None

    # Product details
    description: Optional[str] = None

    # Gateway specific
    gateway_order_id: Optional[str] = None
    checkout_url: Optional[str] = None
    checkout_data: Optional[Dict[str, Any]] = None

    # Timestamps
    created_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None


@dataclass
class PaymentResult:
    """Payment result after callback/verification."""

    success: bool
    order_id: str
    gateway_order_id: str
    gateway_payment_id: Optional[str] = None
    amount: Optional[Decimal] = None
    currency: str = "INR"
    status: PaymentStatus = PaymentStatus.CREATED

    # Payment details
    payment_method: Optional[str] = None  # card, upi, netbanking, wallet
    bank_name: Optional[str] = None
    bank_reference: Optional[str] = None

    # Card details (masked)
    card_last4: Optional[str] = None
    card_network: Optional[str] = None
    card_type: Optional[str] = None
    card_issuer: Optional[str] = None

    # UPI details
    upi_vpa: Optional[str] = None

    # Error details
    error_code: Optional[str] = None
    error_description: Optional[str] = None
    error_source: Optional[str] = None
    error_reason: Optional[str] = None

    # Raw response
    raw_response: Optional[Dict[str, Any]] = None


@dataclass
class RefundResult:
    """Refund result."""

    success: bool
    payment_id: str
    refund_id: Optional[str] = None
    amount: Optional[Decimal] = None
    status: RefundStatus = RefundStatus.PENDING

    # Error details
    error_code: Optional[str] = None
    error_description: Optional[str] = None

    # Raw response
    raw_response: Optional[Dict[str, Any]] = None


class GatewayError(Exception):
    """Payment gateway error."""

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        source: Optional[str] = None,
        raw_error: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.code = code
        self.source = source
        self.raw_error = raw_error
        super().__init__(self.message)


class PaymentGateway(ABC):
    """Abstract base class for payment gateways."""

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        webhook_secret: Optional[str] = None,
        sandbox: bool = False,
    ):
        self.api_key = api_key
        self.api_secret = api_secret
        self.webhook_secret = webhook_secret
        self.sandbox = sandbox

    @property
    @abstractmethod
    def name(self) -> str:
        """Gateway name."""
        pass

    @abstractmethod
    async def create_order(
        self,
        amount: Decimal,
        currency: str,
        receipt: Optional[str] = None,
        notes: Optional[Dict[str, str]] = None,
        customer_name: Optional[str] = None,
        customer_email: Optional[str] = None,
        customer_phone: Optional[str] = None,
        description: Optional[str] = None,
    ) -> PaymentOrder:
        """
        Create a payment order.

        Args:
            amount: Payment amount in base currency
            currency: Currency code (default INR)
            receipt: Unique receipt number
            notes: Additional notes
            customer_name: Customer name
            customer_email: Customer email
            customer_phone: Customer phone
            description: Payment description

        Returns:
            PaymentOrder with gateway order ID
        """
        pass

    @abstractmethod
    async def verify_payment(
        self,
        order_id: str,
        payment_id: str,
        signature: str,
    ) -> PaymentResult:
        """
        Verify payment signature and fetch payment details.

        Args:
            order_id: Gateway order ID
            payment_id: Gateway payment ID
            signature: Payment signature

        Returns:
            PaymentResult with verification status
        """
        pass

    @abstractmethod
    async def fetch_payment(
        self,
        payment_id: str,
    ) -> PaymentResult:
        """
        Fetch payment details by payment ID.

        Args:
            payment_id: Gateway payment ID

        Returns:
            PaymentResult with payment details
        """
        pass

    @abstractmethod
    async def capture_payment(
        self,
        payment_id: str,
        amount: Optional[Decimal] = None,
    ) -> PaymentResult:
        """
        Capture an authorized payment.

        Args:
            payment_id: Gateway payment ID
            amount: Amount to capture (optional, captures full amount if not provided)

        Returns:
            PaymentResult with capture status
        """
        pass

    @abstractmethod
    async def refund_payment(
        self,
        payment_id: str,
        amount: Optional[Decimal] = None,
        notes: Optional[Dict[str, str]] = None,
    ) -> RefundResult:
        """
        Refund a payment.

        Args:
            payment_id: Gateway payment ID
            amount: Amount to refund (optional, refunds full amount if not provided)
            notes: Refund notes

        Returns:
            RefundResult with refund status
        """
        pass

    @abstractmethod
    def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str,
    ) -> bool:
        """
        Verify webhook signature.

        Args:
            payload: Raw webhook payload
            signature: Webhook signature

        Returns:
            True if signature is valid
        """
        pass

    @abstractmethod
    def parse_webhook_event(
        self,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Parse webhook event.

        Args:
            payload: Webhook payload

        Returns:
            Parsed event with type and data
        """
        pass

    @abstractmethod
    async def get_checkout_data(
        self,
        order: PaymentOrder,
        callback_url: Optional[str] = None,
        prefill: Optional[Dict[str, str]] = None,
        theme: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Get checkout data for frontend.

        Args:
            order: Payment order
            callback_url: Callback URL after payment
            prefill: Prefill customer details
            theme: Checkout theme

        Returns:
            Checkout configuration for frontend
        """
        pass

    def _convert_to_paise(self, amount: Decimal) -> int:
        """Convert INR to paise."""
        return int(amount * 100)

    def _convert_from_paise(self, amount: int) -> Decimal:
        """Convert paise to INR."""
        return Decimal(str(amount)) / 100
