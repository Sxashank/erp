"""Portal Payment Service.

Handles payment initiation, gateway integration, and mandate management.
"""

import secrets
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Optional, Dict, Any, List, Tuple
from uuid import UUID

from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.portal.payment import (
    PortalPaymentRequest,
    PortalPaymentTransaction,
    PortalSavedPaymentMethod,
    PortalAutoDebitMandate,
)
from app.models.portal.enums import (
    PaymentMode,
    PaymentStatus,
    MandateStatus,
    MandateFrequency,
)


class PortalPaymentService:
    """Portal payment service."""

    PAYMENT_VALIDITY_MINUTES = 30
    SUPPORTED_GATEWAYS = ["RAZORPAY", "PAYU", "CCAVENUE"]

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # Payment Initiation
    # =========================================================================

    async def initiate_payment(
        self,
        organization_id: UUID,
        user_id: UUID,
        loan_account_id: UUID,
        amount: Decimal,
        request_type: str,  # EMI, PREPAYMENT, FORECLOSURE, CHARGES
        payment_mode: Optional[PaymentMode] = None,
        saved_method_id: Optional[UUID] = None,
        gateway_name: str = "RAZORPAY",
        principal_component: Optional[Decimal] = None,
        interest_component: Optional[Decimal] = None,
        charges_component: Optional[Decimal] = None,
    ) -> Dict[str, Any]:
        """Initiate a payment request."""
        # Validate gateway
        if gateway_name not in self.SUPPORTED_GATEWAYS:
            raise ValueError(f"Unsupported gateway: {gateway_name}")

        # Generate request number
        request_number = self._generate_request_number()

        # Create payment request
        payment_request = PortalPaymentRequest(
            organization_id=organization_id,
            user_id=user_id,
            loan_account_id=loan_account_id,
            request_number=request_number,
            request_type=request_type,
            requested_amount=amount,
            principal_component=principal_component,
            interest_component=interest_component,
            charges_component=charges_component,
            payment_mode=payment_mode,
            saved_method_id=saved_method_id,
            valid_until=datetime.utcnow() + timedelta(minutes=self.PAYMENT_VALIDITY_MINUTES),
            gateway_name=gateway_name,
            status=PaymentStatus.INITIATED,
        )
        self.db.add(payment_request)
        await self.db.flush()

        # Create gateway order
        gateway_response = await self._create_gateway_order(
            payment_request, gateway_name
        )

        payment_request.gateway_order_id = gateway_response.get("order_id")
        payment_request.gateway_checkout_url = gateway_response.get("checkout_url")

        return {
            "request_id": str(payment_request.id),
            "request_number": request_number,
            "amount": float(amount),
            "gateway": gateway_name,
            "order_id": gateway_response.get("order_id"),
            "checkout_url": gateway_response.get("checkout_url"),
            "checkout_data": gateway_response.get("checkout_data"),
            "valid_until": payment_request.valid_until.isoformat(),
        }

    async def process_gateway_callback(
        self,
        gateway_name: str,
        callback_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Process payment gateway callback."""
        # Extract order ID from callback
        order_id = self._extract_order_id(gateway_name, callback_data)

        # Find payment request
        stmt = select(PortalPaymentRequest).where(
            PortalPaymentRequest.gateway_order_id == order_id
        )
        result = await self.db.execute(stmt)
        payment_request = result.scalar_one_or_none()

        if not payment_request:
            return {"success": False, "error": "Payment request not found"}

        # Verify and parse callback
        verification = await self._verify_gateway_callback(
            gateway_name, callback_data, payment_request
        )

        if not verification.get("verified"):
            return {"success": False, "error": "Callback verification failed"}

        # Create transaction record
        transaction = PortalPaymentTransaction(
            organization_id=payment_request.organization_id,
            payment_request_id=payment_request.id,
            transaction_id=self._generate_transaction_id(),
            amount=payment_request.requested_amount,
            payment_mode=PaymentMode(verification.get("payment_mode", "UPI")),
            gateway_name=gateway_name,
            gateway_transaction_id=verification.get("gateway_txn_id"),
            gateway_order_id=order_id,
            gateway_status=verification.get("gateway_status"),
            gateway_response_raw=str(callback_data),
            status=PaymentStatus.SUCCESS if verification.get("success") else PaymentStatus.FAILED,
            failure_reason=verification.get("failure_reason"),
            bank_name=verification.get("bank_name"),
            bank_reference=verification.get("bank_reference"),
        )
        self.db.add(transaction)

        # Update payment request status
        if verification.get("success"):
            payment_request.status = PaymentStatus.SUCCESS
            payment_request.completed_at = datetime.utcnow()

            # Post to ERP
            erp_result = await self._post_payment_to_erp(payment_request, transaction)
            transaction.is_posted_to_erp = erp_result.get("success", False)
            transaction.erp_receipt_id = erp_result.get("receipt_id")
            transaction.posted_at = datetime.utcnow() if transaction.is_posted_to_erp else None
            transaction.posting_error = erp_result.get("error")
        else:
            payment_request.status = PaymentStatus.FAILED
            payment_request.status_message = verification.get("failure_reason")

        return {
            "success": verification.get("success"),
            "transaction_id": str(transaction.id),
            "status": payment_request.status.value,
            "amount": float(payment_request.requested_amount),
            "receipt_id": str(transaction.erp_receipt_id) if transaction.erp_receipt_id else None,
        }

    async def get_payment_status(
        self,
        request_id: UUID,
        user_id: UUID,
    ) -> Optional[Dict[str, Any]]:
        """Get payment request status."""
        stmt = select(PortalPaymentRequest).where(
            and_(
                PortalPaymentRequest.id == request_id,
                PortalPaymentRequest.user_id == user_id,
            )
        )
        result = await self.db.execute(stmt)
        payment_request = result.scalar_one_or_none()

        if not payment_request:
            return None

        # Get transaction if exists
        transaction = None
        if payment_request.status in [PaymentStatus.SUCCESS, PaymentStatus.FAILED]:
            stmt = select(PortalPaymentTransaction).where(
                PortalPaymentTransaction.payment_request_id == request_id
            )
            result = await self.db.execute(stmt)
            transaction = result.scalar_one_or_none()

        return {
            "request_id": str(payment_request.id),
            "request_number": payment_request.request_number,
            "amount": float(payment_request.requested_amount),
            "status": payment_request.status.value,
            "status_message": payment_request.status_message,
            "initiated_at": payment_request.initiated_at.isoformat(),
            "completed_at": payment_request.completed_at.isoformat() if payment_request.completed_at else None,
            "transaction": {
                "transaction_id": str(transaction.id) if transaction else None,
                "gateway_txn_id": transaction.gateway_transaction_id if transaction else None,
                "payment_mode": transaction.payment_mode.value if transaction else None,
                "bank_name": transaction.bank_name if transaction else None,
                "receipt_id": str(transaction.erp_receipt_id) if transaction and transaction.erp_receipt_id else None,
            } if transaction else None,
        }

    # =========================================================================
    # Payment History
    # =========================================================================

    async def get_payment_history(
        self,
        user_id: UUID,
        loan_account_id: Optional[UUID] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Get payment transaction history."""
        stmt = (
            select(PortalPaymentTransaction)
            .join(PortalPaymentRequest)
            .where(PortalPaymentRequest.user_id == user_id)
        )

        if loan_account_id:
            stmt = stmt.where(PortalPaymentRequest.loan_account_id == loan_account_id)

        if from_date:
            stmt = stmt.where(PortalPaymentTransaction.transaction_date >= from_date)

        if to_date:
            stmt = stmt.where(PortalPaymentTransaction.transaction_date <= to_date)

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar()

        # Get paginated results
        stmt = stmt.order_by(PortalPaymentTransaction.transaction_date.desc())
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(stmt)
        transactions = list(result.scalars().all())

        items = [
            {
                "transaction_id": str(txn.id),
                "transaction_date": txn.transaction_date.isoformat(),
                "amount": float(txn.amount),
                "payment_mode": txn.payment_mode.value,
                "status": txn.status.value,
                "gateway_txn_id": txn.gateway_transaction_id,
                "bank_name": txn.bank_name,
            }
            for txn in transactions
        ]

        return items, total

    # =========================================================================
    # Saved Payment Methods
    # =========================================================================

    async def get_saved_methods(
        self,
        user_id: UUID,
    ) -> List[Dict[str, Any]]:
        """Get saved payment methods for a user."""
        stmt = (
            select(PortalSavedPaymentMethod)
            .where(
                and_(
                    PortalSavedPaymentMethod.user_id == user_id,
                    PortalSavedPaymentMethod.is_active == True,
                )
            )
            .order_by(PortalSavedPaymentMethod.is_default.desc())
        )
        result = await self.db.execute(stmt)
        methods = list(result.scalars().all())

        return [
            {
                "id": str(method.id),
                "method_type": method.method_type,
                "display_name": method.display_name,
                "is_default": method.is_default,
                "card_last4": method.card_last4,
                "card_network": method.card_network,
                "upi_vpa": method.upi_vpa,
                "bank_name": method.bank_name,
                "last_used_at": method.last_used_at.isoformat() if method.last_used_at else None,
            }
            for method in methods
        ]

    async def save_payment_method(
        self,
        user_id: UUID,
        method_type: str,
        gateway_name: str,
        card_token: Optional[str] = None,
        card_last4: Optional[str] = None,
        card_network: Optional[str] = None,
        card_type: Optional[str] = None,
        upi_vpa: Optional[str] = None,
        display_name: Optional[str] = None,
        set_as_default: bool = False,
    ) -> PortalSavedPaymentMethod:
        """Save a payment method."""
        # Generate display name if not provided
        if not display_name:
            if method_type == "CARD":
                display_name = f"{card_network} •••• {card_last4}"
            elif method_type == "UPI":
                display_name = upi_vpa
            else:
                display_name = method_type

        method = PortalSavedPaymentMethod(
            user_id=user_id,
            method_type=method_type,
            display_name=display_name,
            card_token=card_token,
            card_last4=card_last4,
            card_network=card_network,
            card_type=card_type,
            upi_vpa=upi_vpa,
            gateway_name=gateway_name,
            is_default=set_as_default,
        )
        self.db.add(method)

        if set_as_default:
            await self._clear_default_method(user_id, method.id)

        return method

    async def delete_saved_method(
        self,
        method_id: UUID,
        user_id: UUID,
    ) -> bool:
        """Delete a saved payment method."""
        stmt = select(PortalSavedPaymentMethod).where(
            and_(
                PortalSavedPaymentMethod.id == method_id,
                PortalSavedPaymentMethod.user_id == user_id,
            )
        )
        result = await self.db.execute(stmt)
        method = result.scalar_one_or_none()

        if method:
            method.is_active = False
            return True
        return False

    # =========================================================================
    # Auto-Debit Mandate (NACH/UPI Autopay)
    # =========================================================================

    async def setup_mandate(
        self,
        organization_id: UUID,
        user_id: UUID,
        loan_account_id: UUID,
        mandate_type: str,  # NACH, UPI_AUTOPAY
        max_amount: Decimal,
        frequency: MandateFrequency,
        debit_day: int,
        start_date: date,
        end_date: date,
        bank_account_number: Optional[str] = None,
        bank_ifsc: Optional[str] = None,
        account_holder_name: Optional[str] = None,
        upi_vpa: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Setup auto-debit mandate."""
        mandate_id = self._generate_mandate_id()

        mandate = PortalAutoDebitMandate(
            organization_id=organization_id,
            user_id=user_id,
            loan_account_id=loan_account_id,
            mandate_id=mandate_id,
            mandate_type=mandate_type,
            bank_account_number=self._mask_account_number(bank_account_number) if bank_account_number else None,
            bank_ifsc=bank_ifsc,
            account_holder_name=account_holder_name,
            upi_vpa=upi_vpa,
            max_amount=max_amount,
            frequency=frequency,
            debit_day=debit_day,
            start_date=start_date,
            end_date=end_date,
            status=MandateStatus.PENDING,
        )
        self.db.add(mandate)
        await self.db.flush()

        # Initiate mandate registration with bank/NPCI
        registration_result = await self._initiate_mandate_registration(mandate)

        mandate.gateway_name = registration_result.get("gateway")
        mandate.gateway_mandate_id = registration_result.get("gateway_mandate_id")

        return {
            "mandate_id": str(mandate.id),
            "internal_mandate_id": mandate_id,
            "status": mandate.status.value,
            "registration_url": registration_result.get("registration_url"),
            "registration_data": registration_result.get("registration_data"),
        }

    async def get_mandate_status(
        self,
        mandate_id: UUID,
        user_id: UUID,
    ) -> Optional[Dict[str, Any]]:
        """Get mandate status."""
        stmt = select(PortalAutoDebitMandate).where(
            and_(
                PortalAutoDebitMandate.id == mandate_id,
                PortalAutoDebitMandate.user_id == user_id,
            )
        )
        result = await self.db.execute(stmt)
        mandate = result.scalar_one_or_none()

        if not mandate:
            return None

        return {
            "mandate_id": str(mandate.id),
            "internal_mandate_id": mandate.mandate_id,
            "mandate_type": mandate.mandate_type,
            "status": mandate.status.value,
            "max_amount": float(mandate.max_amount),
            "frequency": mandate.frequency.value,
            "debit_day": mandate.debit_day,
            "start_date": mandate.start_date.isoformat(),
            "end_date": mandate.end_date.isoformat(),
            "bank_name": mandate.bank_name,
            "umrn": mandate.umrn,
            "last_execution": {
                "date": mandate.last_execution_date.isoformat() if mandate.last_execution_date else None,
                "amount": float(mandate.last_execution_amount) if mandate.last_execution_amount else None,
                "status": mandate.last_execution_status,
            },
        }

    async def cancel_mandate(
        self,
        mandate_id: UUID,
        user_id: UUID,
        reason: str,
    ) -> bool:
        """Cancel an active mandate."""
        stmt = select(PortalAutoDebitMandate).where(
            and_(
                PortalAutoDebitMandate.id == mandate_id,
                PortalAutoDebitMandate.user_id == user_id,
                PortalAutoDebitMandate.status.in_([
                    MandateStatus.REGISTERED,
                    MandateStatus.ACTIVE,
                ]),
            )
        )
        result = await self.db.execute(stmt)
        mandate = result.scalar_one_or_none()

        if not mandate:
            return False

        # Cancel with bank/NPCI
        await self._cancel_mandate_with_bank(mandate)

        mandate.status = MandateStatus.CANCELLED
        mandate.cancelled_at = datetime.utcnow()
        mandate.cancellation_reason = reason

        return True

    async def get_user_mandates(
        self,
        user_id: UUID,
        loan_account_id: Optional[UUID] = None,
    ) -> List[Dict[str, Any]]:
        """Get all mandates for a user."""
        stmt = select(PortalAutoDebitMandate).where(
            PortalAutoDebitMandate.user_id == user_id
        )

        if loan_account_id:
            stmt = stmt.where(PortalAutoDebitMandate.loan_account_id == loan_account_id)

        stmt = stmt.order_by(PortalAutoDebitMandate.created_at.desc())

        result = await self.db.execute(stmt)
        mandates = list(result.scalars().all())

        return [
            {
                "mandate_id": str(m.id),
                "mandate_type": m.mandate_type,
                "status": m.status.value,
                "max_amount": float(m.max_amount),
                "frequency": m.frequency.value,
                "bank_name": m.bank_name,
                "umrn": m.umrn,
            }
            for m in mandates
        ]

    # =========================================================================
    # Private Methods
    # =========================================================================

    def _generate_request_number(self) -> str:
        """Generate unique payment request number."""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        random_suffix = secrets.token_hex(3).upper()
        return f"PAY{timestamp}{random_suffix}"

    def _generate_transaction_id(self) -> str:
        """Generate unique transaction ID."""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        random_suffix = secrets.token_hex(4).upper()
        return f"TXN{timestamp}{random_suffix}"

    def _generate_mandate_id(self) -> str:
        """Generate unique mandate ID."""
        timestamp = datetime.utcnow().strftime("%Y%m%d")
        random_suffix = secrets.token_hex(4).upper()
        return f"MND{timestamp}{random_suffix}"

    def _mask_account_number(self, account_number: str) -> str:
        """Mask account number for storage."""
        if len(account_number) <= 4:
            return account_number
        return "X" * (len(account_number) - 4) + account_number[-4:]

    def _extract_order_id(self, gateway_name: str, callback_data: Dict) -> str:
        """Extract order ID from gateway callback."""
        if gateway_name == "RAZORPAY":
            return callback_data.get("razorpay_order_id", "")
        elif gateway_name == "PAYU":
            return callback_data.get("txnid", "")
        return callback_data.get("order_id", "")

    async def _create_gateway_order(
        self,
        payment_request: PortalPaymentRequest,
        gateway_name: str,
    ) -> Dict[str, Any]:
        """Create order with payment gateway."""
        # This would integrate with actual payment gateway
        # Placeholder implementation
        return {
            "order_id": f"{gateway_name}_{secrets.token_hex(8)}",
            "checkout_url": None,
            "checkout_data": {
                "key": "test_key",
                "amount": int(payment_request.requested_amount * 100),
                "currency": "INR",
                "name": "Loan Payment",
                "order_id": "",
            },
        }

    async def _verify_gateway_callback(
        self,
        gateway_name: str,
        callback_data: Dict[str, Any],
        payment_request: PortalPaymentRequest,
    ) -> Dict[str, Any]:
        """Verify payment gateway callback."""
        # This would verify callback signature with gateway
        # Placeholder implementation
        return {
            "verified": True,
            "success": True,
            "gateway_txn_id": callback_data.get("gateway_transaction_id"),
            "gateway_status": "SUCCESS",
            "payment_mode": "UPI",
        }

    async def _post_payment_to_erp(
        self,
        payment_request: PortalPaymentRequest,
        transaction: PortalPaymentTransaction,
    ) -> Dict[str, Any]:
        """Post successful payment to ERP lending module."""
        # This would create receipt in lending module
        # Placeholder implementation
        return {
            "success": True,
            "receipt_id": None,
        }

    async def _clear_default_method(
        self,
        user_id: UUID,
        except_id: UUID,
    ):
        """Clear default flag from other payment methods."""
        stmt = select(PortalSavedPaymentMethod).where(
            and_(
                PortalSavedPaymentMethod.user_id == user_id,
                PortalSavedPaymentMethod.id != except_id,
                PortalSavedPaymentMethod.is_default == True,
            )
        )
        result = await self.db.execute(stmt)
        methods = list(result.scalars().all())

        for method in methods:
            method.is_default = False

    async def _initiate_mandate_registration(
        self,
        mandate: PortalAutoDebitMandate,
    ) -> Dict[str, Any]:
        """Initiate mandate registration with bank."""
        # This would integrate with NACH/UPI Autopay systems
        # Placeholder implementation
        return {
            "gateway": "RAZORPAY",
            "gateway_mandate_id": f"MND_{secrets.token_hex(8)}",
            "registration_url": None,
            "registration_data": {},
        }

    async def _cancel_mandate_with_bank(
        self,
        mandate: PortalAutoDebitMandate,
    ):
        """Cancel mandate with bank/NPCI."""
        # This would cancel mandate via gateway
        # Placeholder implementation
        pass
