"""Base Credit Bureau Client.

Abstract base class for credit bureau integrations.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Dict, Any, Optional, List

import httpx

logger = logging.getLogger(__name__)


@dataclass
class BureauConfig:
    """Configuration for bureau API connection."""

    member_id: str
    password: str
    base_url: str
    sandbox_url: Optional[str] = None
    sandbox_mode: bool = True
    timeout: int = 60
    # Additional credentials
    api_key: Optional[str] = None
    secret_key: Optional[str] = None
    certificate_path: Optional[str] = None
    private_key_path: Optional[str] = None

    @property
    def active_url(self) -> str:
        """Get the active URL based on sandbox mode."""
        if self.sandbox_mode and self.sandbox_url:
            return self.sandbox_url
        return self.base_url


@dataclass
class CustomerInfo:
    """Customer information for bureau inquiry."""

    name: str
    pan: Optional[str] = None
    aadhaar_last4: Optional[str] = None
    mobile: Optional[str] = None
    email: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    # Address
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None


@dataclass
class CreditAccount:
    """Credit account from bureau report."""

    account_number_masked: Optional[str] = None
    bureau_account_id: Optional[str] = None
    institution_name: Optional[str] = None
    institution_type: Optional[str] = None
    account_type: str = "OTHER"
    account_status: str = "ACTIVE"
    ownership: str = "INDIVIDUAL"
    sanctioned_amount: Optional[Decimal] = None
    current_balance: Optional[Decimal] = None
    overdue_amount: Optional[Decimal] = None
    emi_amount: Optional[Decimal] = None
    credit_limit: Optional[Decimal] = None
    high_credit: Optional[Decimal] = None
    write_off_amount: Optional[Decimal] = None
    opened_date: Optional[date] = None
    closed_date: Optional[date] = None
    last_payment_date: Optional[date] = None
    reported_date: Optional[date] = None
    tenure_months: Optional[int] = None
    remaining_tenure: Optional[int] = None
    dpd_history: Optional[Dict[str, int]] = None
    max_dpd: Optional[int] = None
    is_secured: bool = False
    has_dispute: bool = False
    raw_data: Optional[Dict[str, Any]] = None


@dataclass
class CreditEnquiry:
    """Credit enquiry from bureau report."""

    enquiry_date: Optional[date] = None
    institution_name: Optional[str] = None
    enquiry_purpose: Optional[str] = None
    enquiry_amount: Optional[Decimal] = None
    raw_data: Optional[Dict[str, Any]] = None


@dataclass
class BureauReport:
    """Parsed credit bureau report."""

    # Reference
    bureau: str
    request_reference: Optional[str] = None
    bureau_reference: Optional[str] = None

    # Status
    success: bool = False
    error_code: Optional[str] = None
    error_message: Optional[str] = None

    # Score
    credit_score: Optional[int] = None
    score_version: Optional[str] = None
    score_date: Optional[date] = None

    # Summary
    total_accounts: int = 0
    active_accounts: int = 0
    total_sanctioned: Decimal = Decimal("0")
    total_outstanding: Decimal = Decimal("0")
    total_overdue: Decimal = Decimal("0")
    max_dpd_last_12m: int = 0
    max_dpd_last_24m: int = 0
    enquiries_last_30d: int = 0
    enquiries_last_12m: int = 0

    # Details
    accounts: List[CreditAccount] = None
    enquiries: List[CreditEnquiry] = None

    # Raw data
    raw_response: Optional[Dict[str, Any]] = None
    raw_xml: Optional[str] = None

    def __post_init__(self):
        if self.accounts is None:
            self.accounts = []
        if self.enquiries is None:
            self.enquiries = []


class BaseBureauClient(ABC):
    """Abstract base class for credit bureau clients."""

    BUREAU_NAME: str = "UNKNOWN"

    def __init__(self, config: BureauConfig):
        """Initialize bureau client.

        Args:
            config: Bureau API configuration
        """
        self.config = config
        self._client = httpx.AsyncClient(timeout=config.timeout)

    async def close(self):
        """Close HTTP client."""
        await self._client.aclose()

    @abstractmethod
    async def pull_report(
        self,
        customer: CustomerInfo,
        inquiry_type: str = "SOFT",
        purpose: str = "ACCOUNT_REVIEW",
    ) -> BureauReport:
        """Pull credit report for a customer.

        Args:
            customer: Customer information
            inquiry_type: SOFT or HARD inquiry
            purpose: Purpose of inquiry

        Returns:
            Parsed bureau report
        """
        pass

    @abstractmethod
    def _parse_response(self, response: Dict[str, Any]) -> BureauReport:
        """Parse bureau API response into standard format.

        Args:
            response: Raw API response

        Returns:
            Parsed bureau report
        """
        pass

    def _get_headers(self) -> Dict[str, str]:
        """Get default headers for API requests."""
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Make HTTP request to bureau API.

        Args:
            method: HTTP method
            endpoint: API endpoint
            data: Request payload
            headers: Additional headers

        Returns:
            API response
        """
        url = f"{self.config.active_url}{endpoint}"
        request_headers = self._get_headers()
        if headers:
            request_headers.update(headers)

        try:
            if method == "GET":
                response = await self._client.get(url, headers=request_headers)
            else:
                response = await self._client.request(
                    method, url, headers=request_headers, json=data
                )

            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            logger.error(f"{self.BUREAU_NAME} API error: {e.response.status_code}")
            return {
                "success": False,
                "error_code": str(e.response.status_code),
                "error_message": str(e),
            }
        except Exception as e:
            logger.error(f"{self.BUREAU_NAME} API error: {e}")
            return {
                "success": False,
                "error_code": "CONNECTION_ERROR",
                "error_message": str(e),
            }

    @staticmethod
    def _parse_date(date_str: Optional[str], formats: List[str] = None) -> Optional[date]:
        """Parse date string to date object.

        Args:
            date_str: Date string
            formats: List of date formats to try

        Returns:
            Parsed date or None
        """
        if not date_str:
            return None

        if formats is None:
            formats = ["%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y%m%d", "%d%m%Y"]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        return None

    @staticmethod
    def _parse_decimal(value: Any) -> Optional[Decimal]:
        """Parse value to Decimal.

        Args:
            value: Value to parse

        Returns:
            Decimal or None
        """
        if value is None:
            return None
        try:
            return Decimal(str(value))
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _map_account_type(bureau_type: str) -> str:
        """Map bureau-specific account type to standard type."""
        # Override in subclasses for bureau-specific mapping
        type_map = {
            "HOUSING LOAN": "HOME_LOAN",
            "HOME LOAN": "HOME_LOAN",
            "MORTGAGE": "HOME_LOAN",
            "AUTO LOAN": "AUTO_LOAN",
            "CAR LOAN": "AUTO_LOAN",
            "VEHICLE LOAN": "AUTO_LOAN",
            "PERSONAL LOAN": "PERSONAL_LOAN",
            "CONSUMER LOAN": "CONSUMER_LOAN",
            "CREDIT CARD": "CREDIT_CARD",
            "BUSINESS LOAN": "BUSINESS_LOAN",
            "COMMERCIAL LOAN": "BUSINESS_LOAN",
            "GOLD LOAN": "GOLD_LOAN",
            "EDUCATION LOAN": "EDUCATION_LOAN",
            "PROPERTY LOAN": "PROPERTY_LOAN",
            "TWO WHEELER": "TWO_WHEELER_LOAN",
            "TWO-WHEELER": "TWO_WHEELER_LOAN",
            "OVERDRAFT": "OVERDRAFT",
            "OD": "OVERDRAFT",
        }
        return type_map.get(bureau_type.upper(), "OTHER")

    @staticmethod
    def _map_account_status(bureau_status: str) -> str:
        """Map bureau-specific account status to standard status."""
        status_map = {
            "ACTIVE": "ACTIVE",
            "OPEN": "ACTIVE",
            "CURRENT": "ACTIVE",
            "CLOSED": "CLOSED",
            "PAID": "CLOSED",
            "SETTLED": "SETTLED",
            "WRITTEN OFF": "WRITTEN_OFF",
            "WRITEOFF": "WRITTEN_OFF",
            "SUIT FILED": "SUIT_FILED",
            "WILLFUL DEFAULT": "WILLFUL_DEFAULT",
        }
        return status_map.get(bureau_status.upper(), "ACTIVE")
