"""Experian Credit Bureau Client.

Client for pulling credit reports from Experian.
"""

import logging
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Dict, Any, Optional

from app.integrations.bureau.base import (
    BaseBureauClient,
    BureauConfig,
    BureauReport,
    CustomerInfo,
    CreditAccount,
    CreditEnquiry,
)

logger = logging.getLogger(__name__)


class ExperianClient(BaseBureauClient):
    """Experian Credit Bureau Client.

    Integrates with Experian API for credit report pulls.
    """

    BUREAU_NAME = "EXPERIAN"

    # Experian API endpoints
    ENDPOINT_CONSUMER = "/credit-profile/consumer"
    ENDPOINT_COMMERCIAL = "/credit-profile/commercial"

    # Score versions
    SCORE_VERSION_ND = "EXPERIAN_ND"
    SCORE_VERSION_V4 = "EXPERIAN_V4"

    def __init__(self, config: BureauConfig):
        """Initialize Experian client."""
        super().__init__(config)

    def _get_headers(self) -> Dict[str, str]:
        """Get Experian-specific headers."""
        headers = super()._get_headers()
        headers.update({
            "clientCode": self.config.member_id,
            "clientSecret": self.config.password,
        })
        if self.config.api_key:
            headers["x-api-key"] = self.config.api_key
        return headers

    async def pull_report(
        self,
        customer: CustomerInfo,
        inquiry_type: str = "SOFT",
        purpose: str = "ACCOUNT_REVIEW",
    ) -> BureauReport:
        """Pull credit report from Experian.

        Args:
            customer: Customer information
            inquiry_type: SOFT or HARD inquiry
            purpose: Purpose code for the inquiry

        Returns:
            Parsed Experian report
        """
        request_ref = f"EXP{datetime.utcnow().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:8]}"

        # Build request payload
        payload = self._build_request_payload(customer, inquiry_type, purpose, request_ref)

        logger.info(f"Experian pull request: {request_ref} for PAN: {customer.pan}")

        try:
            response = await self._make_request("POST", self.ENDPOINT_CONSUMER, payload)
            report = self._parse_response(response)
            report.request_reference = request_ref
            return report

        except Exception as e:
            logger.error(f"Experian pull failed: {e}")
            return BureauReport(
                bureau=self.BUREAU_NAME,
                request_reference=request_ref,
                success=False,
                error_code="PULL_FAILED",
                error_message=str(e),
            )

    def _build_request_payload(
        self,
        customer: CustomerInfo,
        inquiry_type: str,
        purpose: str,
        request_ref: str,
    ) -> Dict[str, Any]:
        """Build Experian API request payload."""
        payload = {
            "header": {
                "clientCode": self.config.member_id,
                "requestId": request_ref,
                "requestDate": datetime.utcnow().isoformat(),
                "productCode": "CCRI",  # Consumer Credit Report
                "inquiryType": inquiry_type,
                "inquiryPurpose": purpose,
            },
            "consumer": {
                "name": customer.name,
            }
        }

        # Add PAN
        if customer.pan:
            payload["consumer"]["pan"] = customer.pan

        # Add DOB
        if customer.date_of_birth:
            payload["consumer"]["dateOfBirth"] = customer.date_of_birth.strftime("%Y-%m-%d")

        # Add mobile
        if customer.mobile:
            payload["consumer"]["mobile"] = customer.mobile

        # Add email
        if customer.email:
            payload["consumer"]["email"] = customer.email

        # Add address
        if customer.address_line1:
            payload["consumer"]["address"] = {
                "line1": customer.address_line1,
                "line2": customer.address_line2 or "",
                "city": customer.city or "",
                "state": customer.state or "",
                "pincode": customer.pincode or "",
            }

        return payload

    def _parse_response(self, response: Dict[str, Any]) -> BureauReport:
        """Parse Experian API response."""
        report = BureauReport(
            bureau=self.BUREAU_NAME,
            raw_response=response,
        )

        # Check for errors
        if response.get("success") is False:
            report.success = False
            report.error_code = response.get("error_code")
            report.error_message = response.get("error_message")
            return report

        # Parse response header
        header = response.get("header", {})
        report.bureau_reference = header.get("reportId")

        # Check status
        status = header.get("status", {})
        if status.get("code") == "SUCCESS":
            report.success = True
        elif status.get("code") == "NO_HIT":
            report.success = False
            report.error_code = "NO_HIT"
            report.error_message = "No credit record found"
            return report
        else:
            report.success = False
            report.error_code = status.get("code")
            report.error_message = status.get("message")
            return report

        # Parse credit profile
        profile = response.get("creditProfile", {})

        # Parse credit score
        score_info = profile.get("score", {})
        if score_info:
            report.credit_score = self._parse_int(score_info.get("value"))
            report.score_version = score_info.get("version", self.SCORE_VERSION_ND)
            report.score_date = self._parse_date(score_info.get("date"))

        # Parse summary
        summary = profile.get("summary", {})
        report.total_accounts = self._parse_int(summary.get("totalAccounts")) or 0
        report.active_accounts = self._parse_int(summary.get("activeAccounts")) or 0
        report.total_sanctioned = self._parse_decimal(summary.get("totalSanctioned")) or Decimal("0")
        report.total_outstanding = self._parse_decimal(summary.get("totalOutstanding")) or Decimal("0")
        report.total_overdue = self._parse_decimal(summary.get("totalOverdue")) or Decimal("0")

        # Parse DPD summary
        dpd_summary = profile.get("dpdSummary", {})
        report.max_dpd_last_12m = self._parse_int(dpd_summary.get("maxDpd12Months")) or 0
        report.max_dpd_last_24m = self._parse_int(dpd_summary.get("maxDpd24Months")) or 0

        # Parse accounts
        accounts_data = profile.get("accounts", [])
        report.accounts = [self._parse_account(acc) for acc in accounts_data]

        # Parse enquiries
        enquiries_data = profile.get("enquiries", [])
        report.enquiries = [self._parse_enquiry(enq) for enq in enquiries_data]

        # Count recent enquiries
        today = date.today()
        report.enquiries_last_30d = sum(
            1 for e in report.enquiries
            if e.enquiry_date and (today - e.enquiry_date).days <= 30
        )
        report.enquiries_last_12m = sum(
            1 for e in report.enquiries
            if e.enquiry_date and (today - e.enquiry_date).days <= 365
        )

        return report

    def _parse_account(self, data: Dict[str, Any]) -> CreditAccount:
        """Parse credit account from Experian response."""
        account = CreditAccount(
            bureau_account_id=data.get("accountId"),
            account_number_masked=data.get("accountNumberMasked"),
            institution_name=data.get("memberName"),
            institution_type=data.get("memberCategory"),
            account_type=self._map_experian_account_type(data.get("accountType", "")),
            account_status=self._map_experian_account_status(data.get("accountStatus", "")),
            ownership=self._map_ownership(data.get("ownershipType", "")),
            sanctioned_amount=self._parse_decimal(data.get("sanctionedAmount")),
            current_balance=self._parse_decimal(data.get("currentBalance")),
            overdue_amount=self._parse_decimal(data.get("overdueAmount")),
            emi_amount=self._parse_decimal(data.get("emiAmount")),
            credit_limit=self._parse_decimal(data.get("creditLimit")),
            high_credit=self._parse_decimal(data.get("highCredit")),
            write_off_amount=self._parse_decimal(data.get("writeOffAmount")),
            opened_date=self._parse_date(data.get("openDate")),
            closed_date=self._parse_date(data.get("closeDate")),
            last_payment_date=self._parse_date(data.get("lastPaymentDate")),
            reported_date=self._parse_date(data.get("reportedDate")),
            tenure_months=self._parse_int(data.get("tenure")),
            remaining_tenure=self._parse_int(data.get("remainingTenure")),
            max_dpd=self._parse_int(data.get("maxDpd")),
            raw_data=data,
        )

        # Parse payment history
        payment_history = data.get("paymentHistory", [])
        if payment_history:
            account.dpd_history = {}
            for entry in payment_history:
                month_key = entry.get("month")
                dpd_value = entry.get("dpd")
                if month_key and dpd_value is not None:
                    try:
                        account.dpd_history[month_key] = int(dpd_value)
                    except (ValueError, TypeError):
                        pass
            if account.dpd_history:
                account.max_dpd = max(account.dpd_history.values())

        # Determine if secured
        secured_types = ["HOME_LOAN", "AUTO_LOAN", "PROPERTY_LOAN", "GOLD_LOAN"]
        account.is_secured = account.account_type in secured_types

        return account

    def _parse_enquiry(self, data: Dict[str, Any]) -> CreditEnquiry:
        """Parse credit enquiry from Experian response."""
        return CreditEnquiry(
            enquiry_date=self._parse_date(data.get("enquiryDate")),
            institution_name=data.get("memberName"),
            enquiry_purpose=data.get("purpose"),
            enquiry_amount=self._parse_decimal(data.get("amount")),
            raw_data=data,
        )

    @staticmethod
    def _map_experian_account_type(account_type: str) -> str:
        """Map Experian account type to standard type."""
        mapping = {
            "01": "PERSONAL_LOAN",
            "02": "CREDIT_CARD",
            "03": "HOME_LOAN",
            "04": "AUTO_LOAN",
            "05": "CONSUMER_LOAN",
            "06": "BUSINESS_LOAN",
            "07": "GOLD_LOAN",
            "08": "EDUCATION_LOAN",
            "09": "TWO_WHEELER_LOAN",
            "10": "OVERDRAFT",
            "11": "PROPERTY_LOAN",
            "PERSONAL LOAN": "PERSONAL_LOAN",
            "CREDIT CARD": "CREDIT_CARD",
            "HOME LOAN": "HOME_LOAN",
            "HOUSING LOAN": "HOME_LOAN",
            "AUTO LOAN": "AUTO_LOAN",
            "VEHICLE LOAN": "AUTO_LOAN",
            "BUSINESS LOAN": "BUSINESS_LOAN",
            "GOLD LOAN": "GOLD_LOAN",
            "EDUCATION LOAN": "EDUCATION_LOAN",
        }
        return mapping.get(account_type.upper() if account_type else "", "OTHER")

    @staticmethod
    def _map_experian_account_status(status: str) -> str:
        """Map Experian account status to standard status."""
        mapping = {
            "ACTIVE": "ACTIVE",
            "OPEN": "ACTIVE",
            "CURRENT": "ACTIVE",
            "CLOSED": "CLOSED",
            "SETTLED": "SETTLED",
            "WRITTEN-OFF": "WRITTEN_OFF",
            "WRITEOFF": "WRITTEN_OFF",
            "SUIT-FILED": "SUIT_FILED",
            "WILLFUL-DEFAULT": "WILLFUL_DEFAULT",
        }
        return mapping.get(status.upper() if status else "", "ACTIVE")

    @staticmethod
    def _map_ownership(ownership: str) -> str:
        """Map Experian ownership type to standard type."""
        mapping = {
            "INDIVIDUAL": "INDIVIDUAL",
            "SINGLE": "INDIVIDUAL",
            "JOINT": "JOINT",
            "AUTHORIZED": "AUTHORIZED_USER",
            "GUARANTOR": "GUARANTOR",
        }
        return mapping.get(ownership.upper() if ownership else "", "INDIVIDUAL")

    @staticmethod
    def _parse_int(value: Any) -> Optional[int]:
        """Parse value to integer."""
        if value is None:
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None
