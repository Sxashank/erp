"""NACH API client for interacting with NPCI/provider APIs."""

import hashlib
import hmac
import json
import logging
from abc import ABC, abstractmethod
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

import httpx

from app.integrations.nach.schemas import (
    NachApiResponse,
    MandateStatusResponse,
    MandateRegistrationData,
)

logger = logging.getLogger(__name__)


class NachClientBase(ABC):
    """Abstract base class for NACH provider clients."""

    def __init__(
        self,
        config: Dict[str, Any],
        sandbox_mode: bool = True,
    ):
        """Initialize the NACH client.

        Args:
            config: Provider-specific configuration
            sandbox_mode: Whether to use sandbox/test environment
        """
        self.config = config
        self.sandbox_mode = sandbox_mode
        self.base_url = config.get("sandbox_url" if sandbox_mode else "base_url", "")

    @abstractmethod
    async def register_mandate(
        self,
        mandate_data: MandateRegistrationData,
    ) -> NachApiResponse:
        """Register a new mandate with the provider."""
        pass

    @abstractmethod
    async def check_mandate_status(
        self,
        mandate_reference: str,
        umrn: Optional[str] = None,
    ) -> MandateStatusResponse:
        """Check mandate registration status."""
        pass

    @abstractmethod
    async def cancel_mandate(
        self,
        umrn: str,
        reason: str,
    ) -> NachApiResponse:
        """Cancel/revoke a mandate."""
        pass

    @abstractmethod
    async def submit_debit_batch(
        self,
        batch_reference: str,
        file_path: str,
    ) -> NachApiResponse:
        """Submit debit batch file to provider."""
        pass

    @abstractmethod
    async def get_batch_status(
        self,
        batch_reference: str,
    ) -> NachApiResponse:
        """Get status of submitted batch."""
        pass

    @abstractmethod
    async def download_response_file(
        self,
        batch_reference: str,
        output_path: str,
    ) -> Tuple[bool, str]:
        """Download response file for a batch."""
        pass

    async def health_check(self) -> Tuple[bool, str]:
        """Check provider API health."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/health")
                if response.status_code == 200:
                    return True, "Healthy"
                return False, f"Status code: {response.status_code}"
        except Exception as e:
            return False, str(e)


class RazorpayNachClient(NachClientBase):
    """Razorpay NACH/Auto-debit client."""

    def __init__(self, config: Dict[str, Any], sandbox_mode: bool = True):
        super().__init__(config, sandbox_mode)
        self.key_id = config.get("key_id", "")
        self.key_secret = config.get("key_secret", "")
        self.base_url = (
            "https://api.razorpay.com/v1"
            if not sandbox_mode
            else "https://api.razorpay.com/v1"  # Razorpay uses same URL with test keys
        )

    def _get_auth(self) -> Tuple[str, str]:
        """Get basic auth credentials."""
        return (self.key_id, self.key_secret)

    async def register_mandate(
        self,
        mandate_data: MandateRegistrationData,
    ) -> NachApiResponse:
        """Register a new mandate via Razorpay."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                payload = {
                    "type": "nach",
                    "bank_account": {
                        "beneficiary_name": mandate_data.account_holder_name,
                        "account_number": mandate_data.account_number,
                        "ifsc_code": mandate_data.ifsc_code,
                    },
                    "max_amount": int(mandate_data.max_amount * 100),  # In paise
                    "first_payment_amount": int(mandate_data.max_amount * 100),
                    "frequency": self._map_frequency(mandate_data.frequency),
                    "auth_type": "netbanking" if mandate_data.mandate_type == "E" else "physical",
                    "notes": {
                        "mandate_reference": mandate_data.mandate_reference,
                    },
                }

                response = await client.post(
                    f"{self.base_url}/tokens",
                    json=payload,
                    auth=self._get_auth(),
                )

                data = response.json()

                if response.status_code in (200, 201):
                    return NachApiResponse(
                        success=True,
                        request_id=data.get("id", ""),
                        message="Mandate registration initiated",
                        data=data,
                    )
                else:
                    return NachApiResponse(
                        success=False,
                        request_id="",
                        message=data.get("error", {}).get("description", "Registration failed"),
                        error_code=data.get("error", {}).get("code"),
                        error_details=json.dumps(data.get("error", {})),
                    )

        except Exception as e:
            logger.error(f"Razorpay mandate registration error: {e}")
            return NachApiResponse(
                success=False,
                request_id="",
                message=str(e),
                error_code="EXCEPTION",
            )

    async def check_mandate_status(
        self,
        mandate_reference: str,
        umrn: Optional[str] = None,
    ) -> MandateStatusResponse:
        """Check mandate status via Razorpay."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Razorpay uses token_id for mandate lookup
                response = await client.get(
                    f"{self.base_url}/tokens/{mandate_reference}",
                    auth=self._get_auth(),
                )

                data = response.json()

                if response.status_code == 200:
                    return MandateStatusResponse(
                        umrn=data.get("umrn"),
                        mandate_reference=mandate_reference,
                        status=self._map_status(data.get("status", "")),
                        registration_date=datetime.fromtimestamp(data.get("created_at", 0)).date()
                        if data.get("created_at")
                        else None,
                    )
                else:
                    return MandateStatusResponse(
                        mandate_reference=mandate_reference,
                        status="UNKNOWN",
                        status_reason=data.get("error", {}).get("description"),
                    )

        except Exception as e:
            logger.error(f"Razorpay status check error: {e}")
            return MandateStatusResponse(
                mandate_reference=mandate_reference,
                status="ERROR",
                status_reason=str(e),
            )

    async def cancel_mandate(
        self,
        umrn: str,
        reason: str,
    ) -> NachApiResponse:
        """Cancel mandate via Razorpay."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.delete(
                    f"{self.base_url}/tokens/{umrn}",
                    auth=self._get_auth(),
                )

                if response.status_code in (200, 204):
                    return NachApiResponse(
                        success=True,
                        request_id=umrn,
                        message="Mandate cancellation initiated",
                    )
                else:
                    data = response.json()
                    return NachApiResponse(
                        success=False,
                        request_id=umrn,
                        message=data.get("error", {}).get("description", "Cancellation failed"),
                        error_code=data.get("error", {}).get("code"),
                    )

        except Exception as e:
            logger.error(f"Razorpay mandate cancellation error: {e}")
            return NachApiResponse(
                success=False,
                request_id=umrn,
                message=str(e),
                error_code="EXCEPTION",
            )

    async def submit_debit_batch(
        self,
        batch_reference: str,
        file_path: str,
    ) -> NachApiResponse:
        """Submit debit batch - Razorpay uses individual API calls."""
        # Note: Razorpay doesn't use file upload, each debit is an API call
        return NachApiResponse(
            success=True,
            request_id=batch_reference,
            message="Razorpay uses individual debit API calls, not batch files",
        )

    async def create_debit(
        self,
        token_id: str,
        amount: Decimal,
        order_id: str,
        receipt: str,
    ) -> NachApiResponse:
        """Create a debit/charge on a token."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                payload = {
                    "amount": int(amount * 100),  # In paise
                    "currency": "INR",
                    "receipt": receipt,
                    "token": token_id,
                    "recurring": "1",
                }

                response = await client.post(
                    f"{self.base_url}/payments/create/recurring",
                    json=payload,
                    auth=self._get_auth(),
                )

                data = response.json()

                if response.status_code in (200, 201):
                    return NachApiResponse(
                        success=True,
                        request_id=data.get("razorpay_payment_id", ""),
                        message="Debit initiated",
                        data=data,
                    )
                else:
                    return NachApiResponse(
                        success=False,
                        request_id="",
                        message=data.get("error", {}).get("description", "Debit failed"),
                        error_code=data.get("error", {}).get("code"),
                    )

        except Exception as e:
            logger.error(f"Razorpay debit error: {e}")
            return NachApiResponse(
                success=False,
                request_id="",
                message=str(e),
                error_code="EXCEPTION",
            )

    async def get_batch_status(self, batch_reference: str) -> NachApiResponse:
        """Get batch status - N/A for Razorpay."""
        return NachApiResponse(
            success=True,
            request_id=batch_reference,
            message="Razorpay uses individual payment status checks",
        )

    async def download_response_file(
        self,
        batch_reference: str,
        output_path: str,
    ) -> Tuple[bool, str]:
        """Download response file - N/A for Razorpay."""
        return True, "Razorpay uses webhooks for payment status updates"

    def _map_frequency(self, frequency: str) -> str:
        """Map frequency code to Razorpay format."""
        mapping = {
            "M": "monthly",
            "Q": "quarterly",
            "Y": "yearly",
            "AS_PRESENTED": "as_presented",
        }
        return mapping.get(frequency, "monthly")

    def _map_status(self, status: str) -> str:
        """Map Razorpay status to internal status."""
        mapping = {
            "created": "PENDING",
            "active": "ACTIVE",
            "cancelled": "CANCELLED",
            "expired": "EXPIRED",
        }
        return mapping.get(status.lower(), "UNKNOWN")


class CashfreeNachClient(NachClientBase):
    """Cashfree NACH/Auto-collect client."""

    def __init__(self, config: Dict[str, Any], sandbox_mode: bool = True):
        super().__init__(config, sandbox_mode)
        self.app_id = config.get("app_id", "")
        self.secret_key = config.get("secret_key", "")
        self.base_url = (
            "https://sandbox.cashfree.com/pg/recurring"
            if sandbox_mode
            else "https://api.cashfree.com/pg/recurring"
        )

    def _get_headers(self) -> Dict[str, str]:
        """Get API headers."""
        return {
            "x-client-id": self.app_id,
            "x-client-secret": self.secret_key,
            "x-api-version": "2022-09-01",
            "Content-Type": "application/json",
        }

    async def register_mandate(
        self,
        mandate_data: MandateRegistrationData,
    ) -> NachApiResponse:
        """Register mandate via Cashfree."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                payload = {
                    "subscription_id": mandate_data.mandate_reference,
                    "customer_details": {
                        "customer_name": mandate_data.account_holder_name,
                        "customer_email": mandate_data.email or "na@example.com",
                        "customer_phone": mandate_data.phone_number or "9999999999",
                    },
                    "plan_info": {
                        "type": "NACH",
                        "max_amount": float(mandate_data.max_amount),
                        "recurring_amount": float(mandate_data.max_amount),
                    },
                    "authorization_details": {
                        "authorization_type": "NACH",
                        "account_number": mandate_data.account_number,
                        "ifsc_code": mandate_data.ifsc_code,
                        "account_holder_name": mandate_data.account_holder_name,
                    },
                    "first_charge_date": mandate_data.first_collection_date.isoformat(),
                    "expiry_date": mandate_data.final_collection_date.isoformat(),
                }

                response = await client.post(
                    f"{self.base_url}/subscriptions",
                    json=payload,
                    headers=self._get_headers(),
                )

                data = response.json()

                if response.status_code in (200, 201):
                    return NachApiResponse(
                        success=True,
                        request_id=data.get("cf_subscription_id", ""),
                        message="Mandate registration initiated",
                        data=data,
                    )
                else:
                    return NachApiResponse(
                        success=False,
                        request_id="",
                        message=data.get("message", "Registration failed"),
                        error_code=data.get("code"),
                    )

        except Exception as e:
            logger.error(f"Cashfree mandate registration error: {e}")
            return NachApiResponse(
                success=False,
                request_id="",
                message=str(e),
                error_code="EXCEPTION",
            )

    async def check_mandate_status(
        self,
        mandate_reference: str,
        umrn: Optional[str] = None,
    ) -> MandateStatusResponse:
        """Check mandate status via Cashfree."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/subscriptions/{mandate_reference}",
                    headers=self._get_headers(),
                )

                data = response.json()

                if response.status_code == 200:
                    return MandateStatusResponse(
                        umrn=data.get("umrn"),
                        mandate_reference=mandate_reference,
                        status=data.get("status", "UNKNOWN"),
                    )
                else:
                    return MandateStatusResponse(
                        mandate_reference=mandate_reference,
                        status="UNKNOWN",
                        status_reason=data.get("message"),
                    )

        except Exception as e:
            logger.error(f"Cashfree status check error: {e}")
            return MandateStatusResponse(
                mandate_reference=mandate_reference,
                status="ERROR",
                status_reason=str(e),
            )

    async def cancel_mandate(
        self,
        umrn: str,
        reason: str,
    ) -> NachApiResponse:
        """Cancel mandate via Cashfree."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/subscriptions/{umrn}/cancel",
                    json={"cancellation_reason": reason},
                    headers=self._get_headers(),
                )

                if response.status_code in (200, 204):
                    return NachApiResponse(
                        success=True,
                        request_id=umrn,
                        message="Mandate cancellation initiated",
                    )
                else:
                    data = response.json()
                    return NachApiResponse(
                        success=False,
                        request_id=umrn,
                        message=data.get("message", "Cancellation failed"),
                        error_code=data.get("code"),
                    )

        except Exception as e:
            logger.error(f"Cashfree cancellation error: {e}")
            return NachApiResponse(
                success=False,
                request_id=umrn,
                message=str(e),
                error_code="EXCEPTION",
            )

    async def submit_debit_batch(
        self,
        batch_reference: str,
        file_path: str,
    ) -> NachApiResponse:
        """Submit debit batch - Cashfree uses charge API."""
        return NachApiResponse(
            success=True,
            request_id=batch_reference,
            message="Cashfree uses subscription charge API",
        )

    async def get_batch_status(self, batch_reference: str) -> NachApiResponse:
        """Get batch status."""
        return NachApiResponse(
            success=True,
            request_id=batch_reference,
            message="Use individual payment status checks",
        )

    async def download_response_file(
        self,
        batch_reference: str,
        output_path: str,
    ) -> Tuple[bool, str]:
        """Download response file - N/A for Cashfree."""
        return True, "Cashfree uses webhooks for payment status updates"


class NachClientFactory:
    """Factory for creating NACH clients based on provider."""

    CLIENTS = {
        "RAZORPAY_NACH": RazorpayNachClient,
        "CASHFREE_NACH": CashfreeNachClient,
        # Add more providers as needed
    }

    @classmethod
    def create(
        cls,
        provider: str,
        config: Dict[str, Any],
        sandbox_mode: bool = True,
    ) -> NachClientBase:
        """Create a NACH client for the given provider.

        Args:
            provider: Provider identifier
            config: Provider-specific configuration
            sandbox_mode: Whether to use sandbox environment

        Returns:
            NachClientBase implementation

        Raises:
            ValueError: If provider is not supported
        """
        client_class = cls.CLIENTS.get(provider)
        if not client_class:
            raise ValueError(f"Unsupported NACH provider: {provider}")

        return client_class(config, sandbox_mode)

    @classmethod
    def get_supported_providers(cls) -> List[str]:
        """Get list of supported NACH providers."""
        return list(cls.CLIENTS.keys())
