"""Razorpay Payment Gateway Integration.

Implements Razorpay API for payment processing.
Documentation: https://razorpay.com/docs/api/
"""

import hashlib
import hmac
import json
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, Dict, Any

import httpx

from app.integrations.payment_gateway.base import (
    PaymentGateway,
    PaymentOrder,
    PaymentResult,
    RefundResult,
    PaymentStatus,
    RefundStatus,
    GatewayError,
)


class RazorpayGateway(PaymentGateway):
    """Razorpay payment gateway implementation."""

    BASE_URL = "https://api.razorpay.com/v1"
    SANDBOX_URL = "https://api.razorpay.com/v1"  # Razorpay uses same URL with test keys

    @property
    def name(self) -> str:
        return "RAZORPAY"

    @property
    def _base_url(self) -> str:
        return self.SANDBOX_URL if self.sandbox else self.BASE_URL

    async def create_order(
        self,
        amount: Decimal,
        currency: str = "INR",
        receipt: Optional[str] = None,
        notes: Optional[Dict[str, str]] = None,
        customer_name: Optional[str] = None,
        customer_email: Optional[str] = None,
        customer_phone: Optional[str] = None,
        description: Optional[str] = None,
    ) -> PaymentOrder:
        """Create a Razorpay order."""
        payload = {
            "amount": self._convert_to_paise(amount),
            "currency": currency,
            "receipt": receipt,
            "notes": notes or {},
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self._base_url}/orders",
                    json=payload,
                    auth=(self.api_key, self.api_secret),
                    timeout=30.0,
                )

                if response.status_code != 200:
                    error_data = response.json()
                    raise GatewayError(
                        message=error_data.get("error", {}).get("description", "Order creation failed"),
                        code=error_data.get("error", {}).get("code"),
                        source="razorpay",
                        raw_error=error_data,
                    )

                data = response.json()

        except httpx.RequestError as e:
            raise GatewayError(
                message=f"Network error: {str(e)}",
                source="razorpay",
            )

        return PaymentOrder(
            order_id=receipt or data["receipt"],
            amount=amount,
            currency=currency,
            receipt=receipt,
            notes=notes,
            customer_name=customer_name,
            customer_email=customer_email,
            customer_phone=customer_phone,
            description=description,
            gateway_order_id=data["id"],
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(minutes=30),
        )

    async def verify_payment(
        self,
        order_id: str,
        payment_id: str,
        signature: str,
    ) -> PaymentResult:
        """Verify Razorpay payment signature."""
        # Verify signature
        message = f"{order_id}|{payment_id}"
        expected_signature = hmac.new(
            self.api_secret.encode(),
            message.encode(),
            hashlib.sha256,
        ).hexdigest()

        if signature != expected_signature:
            return PaymentResult(
                success=False,
                order_id=order_id,
                gateway_order_id=order_id,
                gateway_payment_id=payment_id,
                status=PaymentStatus.FAILED,
                error_code="SIGNATURE_MISMATCH",
                error_description="Payment signature verification failed",
            )

        # Fetch payment details
        return await self.fetch_payment(payment_id)

    async def fetch_payment(
        self,
        payment_id: str,
    ) -> PaymentResult:
        """Fetch payment details from Razorpay."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self._base_url}/payments/{payment_id}",
                    auth=(self.api_key, self.api_secret),
                    timeout=30.0,
                )

                if response.status_code != 200:
                    error_data = response.json()
                    return PaymentResult(
                        success=False,
                        order_id="",
                        gateway_order_id="",
                        gateway_payment_id=payment_id,
                        status=PaymentStatus.FAILED,
                        error_code=error_data.get("error", {}).get("code"),
                        error_description=error_data.get("error", {}).get("description"),
                        raw_response=error_data,
                    )

                data = response.json()

        except httpx.RequestError as e:
            return PaymentResult(
                success=False,
                order_id="",
                gateway_order_id="",
                gateway_payment_id=payment_id,
                status=PaymentStatus.FAILED,
                error_description=f"Network error: {str(e)}",
            )

        # Parse status
        status_map = {
            "created": PaymentStatus.CREATED,
            "authorized": PaymentStatus.AUTHORIZED,
            "captured": PaymentStatus.CAPTURED,
            "refunded": PaymentStatus.REFUNDED,
            "failed": PaymentStatus.FAILED,
        }

        return PaymentResult(
            success=data["status"] in ["captured", "authorized"],
            order_id=data.get("order_id", ""),
            gateway_order_id=data.get("order_id", ""),
            gateway_payment_id=data["id"],
            amount=self._convert_from_paise(data["amount"]),
            currency=data["currency"],
            status=status_map.get(data["status"], PaymentStatus.FAILED),
            payment_method=data.get("method"),
            bank_name=data.get("bank"),
            bank_reference=data.get("acquirer_data", {}).get("bank_transaction_id"),
            card_last4=data.get("card", {}).get("last4"),
            card_network=data.get("card", {}).get("network"),
            card_type=data.get("card", {}).get("type"),
            card_issuer=data.get("card", {}).get("issuer"),
            upi_vpa=data.get("vpa"),
            error_code=data.get("error_code"),
            error_description=data.get("error_description"),
            error_source=data.get("error_source"),
            error_reason=data.get("error_reason"),
            raw_response=data,
        )

    async def capture_payment(
        self,
        payment_id: str,
        amount: Optional[Decimal] = None,
    ) -> PaymentResult:
        """Capture an authorized payment."""
        # First fetch the payment to get the amount if not provided
        if amount is None:
            payment = await self.fetch_payment(payment_id)
            if not payment.success:
                return payment
            amount = payment.amount

        payload = {
            "amount": self._convert_to_paise(amount),
            "currency": "INR",
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self._base_url}/payments/{payment_id}/capture",
                    json=payload,
                    auth=(self.api_key, self.api_secret),
                    timeout=30.0,
                )

                if response.status_code != 200:
                    error_data = response.json()
                    return PaymentResult(
                        success=False,
                        order_id="",
                        gateway_order_id="",
                        gateway_payment_id=payment_id,
                        status=PaymentStatus.FAILED,
                        error_code=error_data.get("error", {}).get("code"),
                        error_description=error_data.get("error", {}).get("description"),
                        raw_response=error_data,
                    )

                data = response.json()

        except httpx.RequestError as e:
            return PaymentResult(
                success=False,
                order_id="",
                gateway_order_id="",
                gateway_payment_id=payment_id,
                status=PaymentStatus.FAILED,
                error_description=f"Network error: {str(e)}",
            )

        return PaymentResult(
            success=True,
            order_id=data.get("order_id", ""),
            gateway_order_id=data.get("order_id", ""),
            gateway_payment_id=data["id"],
            amount=self._convert_from_paise(data["amount"]),
            status=PaymentStatus.CAPTURED,
            raw_response=data,
        )

    async def refund_payment(
        self,
        payment_id: str,
        amount: Optional[Decimal] = None,
        notes: Optional[Dict[str, str]] = None,
    ) -> RefundResult:
        """Refund a payment."""
        payload = {
            "notes": notes or {},
        }

        if amount is not None:
            payload["amount"] = self._convert_to_paise(amount)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self._base_url}/payments/{payment_id}/refund",
                    json=payload,
                    auth=(self.api_key, self.api_secret),
                    timeout=30.0,
                )

                if response.status_code != 200:
                    error_data = response.json()
                    return RefundResult(
                        success=False,
                        payment_id=payment_id,
                        status=RefundStatus.FAILED,
                        error_code=error_data.get("error", {}).get("code"),
                        error_description=error_data.get("error", {}).get("description"),
                        raw_response=error_data,
                    )

                data = response.json()

        except httpx.RequestError as e:
            return RefundResult(
                success=False,
                payment_id=payment_id,
                status=RefundStatus.FAILED,
                error_description=f"Network error: {str(e)}",
            )

        status_map = {
            "pending": RefundStatus.PENDING,
            "processed": RefundStatus.PROCESSED,
            "failed": RefundStatus.FAILED,
        }

        return RefundResult(
            success=True,
            payment_id=payment_id,
            refund_id=data["id"],
            amount=self._convert_from_paise(data["amount"]),
            status=status_map.get(data["status"], RefundStatus.PENDING),
            raw_response=data,
        )

    def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str,
    ) -> bool:
        """Verify Razorpay webhook signature."""
        if not self.webhook_secret:
            return False

        expected_signature = hmac.new(
            self.webhook_secret.encode(),
            payload,
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(signature, expected_signature)

    def parse_webhook_event(
        self,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Parse Razorpay webhook event."""
        event_type = payload.get("event")
        event_data = payload.get("payload", {})

        # Extract entity based on event type
        entity = None
        if "payment" in event_data:
            entity = event_data["payment"].get("entity")
        elif "order" in event_data:
            entity = event_data["order"].get("entity")
        elif "refund" in event_data:
            entity = event_data["refund"].get("entity")

        return {
            "event_type": event_type,
            "entity_type": event_type.split(".")[0] if event_type else None,
            "action": event_type.split(".")[-1] if event_type else None,
            "entity": entity,
            "created_at": datetime.fromtimestamp(payload.get("created_at", 0)),
            "account_id": payload.get("account_id"),
        }

    async def get_checkout_data(
        self,
        order: PaymentOrder,
        callback_url: Optional[str] = None,
        prefill: Optional[Dict[str, str]] = None,
        theme: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Get Razorpay checkout configuration."""
        checkout_data = {
            "key": self.api_key,
            "amount": self._convert_to_paise(order.amount),
            "currency": order.currency,
            "name": "Loan Payment",
            "description": order.description or "EMI Payment",
            "order_id": order.gateway_order_id,
            "prefill": {
                "name": prefill.get("name") if prefill else order.customer_name,
                "email": prefill.get("email") if prefill else order.customer_email,
                "contact": prefill.get("contact") if prefill else order.customer_phone,
            },
            "notes": order.notes or {},
            "theme": theme or {
                "color": "#3399cc",
            },
        }

        if callback_url:
            checkout_data["callback_url"] = callback_url

        return checkout_data

    # ==========================================================================
    # Additional Razorpay-specific methods
    # ==========================================================================

    async def create_customer(
        self,
        name: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        notes: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Create a Razorpay customer."""
        payload = {
            "name": name,
            "email": email,
            "contact": phone,
            "notes": notes or {},
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self._base_url}/customers",
                json=payload,
                auth=(self.api_key, self.api_secret),
                timeout=30.0,
            )

            if response.status_code != 200:
                error_data = response.json()
                raise GatewayError(
                    message=error_data.get("error", {}).get("description", "Customer creation failed"),
                    code=error_data.get("error", {}).get("code"),
                    source="razorpay",
                    raw_error=error_data,
                )

            return response.json()

    async def create_subscription(
        self,
        plan_id: str,
        customer_id: str,
        total_count: int,
        quantity: int = 1,
        start_at: Optional[datetime] = None,
        notes: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Create a Razorpay subscription (for recurring payments)."""
        payload = {
            "plan_id": plan_id,
            "customer_id": customer_id,
            "total_count": total_count,
            "quantity": quantity,
            "customer_notify": 1,
            "notes": notes or {},
        }

        if start_at:
            payload["start_at"] = int(start_at.timestamp())

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self._base_url}/subscriptions",
                json=payload,
                auth=(self.api_key, self.api_secret),
                timeout=30.0,
            )

            if response.status_code != 200:
                error_data = response.json()
                raise GatewayError(
                    message=error_data.get("error", {}).get("description", "Subscription creation failed"),
                    code=error_data.get("error", {}).get("code"),
                    source="razorpay",
                    raw_error=error_data,
                )

            return response.json()

    async def create_qr_code(
        self,
        amount: Decimal,
        name: str,
        description: Optional[str] = None,
        customer_id: Optional[str] = None,
        close_by: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Create a Razorpay QR code for UPI payments."""
        payload = {
            "type": "upi_qr",
            "name": name,
            "usage": "single_use",
            "fixed_amount": True,
            "payment_amount": self._convert_to_paise(amount),
            "description": description or "Payment",
        }

        if customer_id:
            payload["customer_id"] = customer_id

        if close_by:
            payload["close_by"] = int(close_by.timestamp())

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self._base_url}/payments/qr_codes",
                json=payload,
                auth=(self.api_key, self.api_secret),
                timeout=30.0,
            )

            if response.status_code != 200:
                error_data = response.json()
                raise GatewayError(
                    message=error_data.get("error", {}).get("description", "QR code creation failed"),
                    code=error_data.get("error", {}).get("code"),
                    source="razorpay",
                    raw_error=error_data,
                )

            return response.json()

    async def fetch_settlement(
        self,
        settlement_id: str,
    ) -> Dict[str, Any]:
        """Fetch settlement details."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self._base_url}/settlements/{settlement_id}",
                auth=(self.api_key, self.api_secret),
                timeout=30.0,
            )

            if response.status_code != 200:
                error_data = response.json()
                raise GatewayError(
                    message=error_data.get("error", {}).get("description", "Settlement fetch failed"),
                    code=error_data.get("error", {}).get("code"),
                    source="razorpay",
                    raw_error=error_data,
                )

            return response.json()

    async def list_settlements(
        self,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        count: int = 10,
        skip: int = 0,
    ) -> Dict[str, Any]:
        """List settlements."""
        params = {
            "count": count,
            "skip": skip,
        }

        if from_date:
            params["from"] = int(from_date.timestamp())
        if to_date:
            params["to"] = int(to_date.timestamp())

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self._base_url}/settlements",
                params=params,
                auth=(self.api_key, self.api_secret),
                timeout=30.0,
            )

            if response.status_code != 200:
                error_data = response.json()
                raise GatewayError(
                    message=error_data.get("error", {}).get("description", "Settlements list failed"),
                    code=error_data.get("error", {}).get("code"),
                    source="razorpay",
                    raw_error=error_data,
                )

            return response.json()
