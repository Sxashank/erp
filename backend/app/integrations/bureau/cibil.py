"""CIBIL (TransUnion) Credit Bureau Client.

Client for pulling credit reports from CIBIL.
"""

import logging
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Dict, Any, Optional, List

from app.integrations.bureau.base import (
    BaseBureauClient,
    BureauConfig,
    BureauReport,
    CustomerInfo,
    CreditAccount,
    CreditEnquiry,
)

logger = logging.getLogger(__name__)


class CIBILClient(BaseBureauClient):
    """CIBIL Credit Bureau Client.

    Integrates with CIBIL (TransUnion) API for credit report pulls.
    """

    BUREAU_NAME = "CIBIL"

    # CIBIL API endpoints
    ENDPOINT_CONSUMER = "/consumer/credit-report"
    ENDPOINT_COMMERCIAL = "/commercial/credit-report"

    # Score versions
    SCORE_VERSION_V2 = "CIBIL_V2"
    SCORE_VERSION_V3 = "CIBIL_V3"

    def __init__(self, config: BureauConfig):
        """Initialize CIBIL client."""
        super().__init__(config)

    def _get_headers(self) -> Dict[str, str]:
        """Get CIBIL-specific headers."""
        headers = super()._get_headers()
        headers.update({
            "memberId": self.config.member_id,
            "password": self.config.password,
            "userId": self.config.member_id,
        })
        if self.config.api_key:
            headers["apiKey"] = self.config.api_key
        return headers

    async def pull_report(
        self,
        customer: CustomerInfo,
        inquiry_type: str = "SOFT",
        purpose: str = "ACCOUNT_REVIEW",
    ) -> BureauReport:
        """Pull credit report from CIBIL.

        Args:
            customer: Customer information
            inquiry_type: SOFT or HARD inquiry
            purpose: Purpose code for the inquiry

        Returns:
            Parsed CIBIL report
        """
        request_ref = f"REQ{datetime.utcnow().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:8]}"

        # Build request payload
        payload = self._build_request_payload(customer, inquiry_type, purpose, request_ref)

        logger.info(f"CIBIL pull request: {request_ref} for PAN: {customer.pan}")

        try:
            response = await self._make_request("POST", self.ENDPOINT_CONSUMER, payload)
            report = self._parse_response(response)
            report.request_reference = request_ref
            return report

        except Exception as e:
            logger.error(f"CIBIL pull failed: {e}")
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
        """Build CIBIL API request payload."""
        payload = {
            "requestHeader": {
                "memberId": self.config.member_id,
                "userId": self.config.member_id,
                "password": self.config.password,
                "requestRefNo": request_ref,
                "requestDt": datetime.utcnow().strftime("%Y-%m-%d"),
                "inquiryPurpose": self._map_inquiry_purpose(purpose),
                "inquiryType": "01" if inquiry_type == "SOFT" else "02",
            },
            "requestBody": {
                "applicantDetails": {
                    "applicantType": "Main",
                    "applicantName": {
                        "name1": customer.name,
                    },
                }
            }
        }

        # Add identification
        if customer.pan:
            payload["requestBody"]["applicantDetails"]["identifiers"] = [{
                "idType": "T",  # PAN
                "idValue": customer.pan,
            }]

        # Add DOB
        if customer.date_of_birth:
            payload["requestBody"]["applicantDetails"]["dateOfBirth"] = (
                customer.date_of_birth.strftime("%Y-%m-%d")
            )

        # Add phone
        if customer.mobile:
            payload["requestBody"]["applicantDetails"]["phoneNumbers"] = [{
                "phoneType": "M",
                "phoneNumber": customer.mobile,
            }]

        # Add address
        if customer.address_line1:
            payload["requestBody"]["applicantDetails"]["addresses"] = [{
                "addressType": "P",  # Permanent
                "addressLine1": customer.address_line1,
                "addressLine2": customer.address_line2 or "",
                "city": customer.city or "",
                "state": customer.state or "",
                "pincode": customer.pincode or "",
            }]

        return payload

    def _parse_response(self, response: Dict[str, Any]) -> BureauReport:
        """Parse CIBIL API response."""
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
        header = response.get("responseHeader", {})
        report.bureau_reference = header.get("reportNo")

        # Check status
        status = header.get("status")
        if status == "0":
            report.success = True
        elif status == "1":
            report.success = False
            report.error_code = "NO_HIT"
            report.error_message = "No credit record found"
            return report
        else:
            report.success = False
            report.error_code = header.get("errorCode")
            report.error_message = header.get("errorMessage")
            return report

        # Parse response body
        body = response.get("responseBody", {})

        # Parse credit score
        score_info = body.get("scoreDetails", {})
        if score_info:
            report.credit_score = self._parse_int(score_info.get("score"))
            report.score_version = score_info.get("scoreVersion", self.SCORE_VERSION_V2)
            report.score_date = self._parse_date(score_info.get("scoreDate"))

        # Parse accounts
        accounts_data = body.get("creditAccounts", [])
        report.accounts = [self._parse_account(acc) for acc in accounts_data]

        # Calculate summary
        report.total_accounts = len(report.accounts)
        report.active_accounts = sum(1 for a in report.accounts if a.account_status == "ACTIVE")
        report.total_sanctioned = sum(a.sanctioned_amount or Decimal("0") for a in report.accounts)
        report.total_outstanding = sum(a.current_balance or Decimal("0") for a in report.accounts)
        report.total_overdue = sum(a.overdue_amount or Decimal("0") for a in report.accounts)

        # Calculate max DPD
        all_dpd = []
        for acc in report.accounts:
            if acc.max_dpd:
                all_dpd.append(acc.max_dpd)
        if all_dpd:
            report.max_dpd_last_12m = max(all_dpd)
            report.max_dpd_last_24m = max(all_dpd)

        # Parse enquiries
        enquiries_data = body.get("enquiries", [])
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
        """Parse credit account from CIBIL response."""
        account = CreditAccount(
            bureau_account_id=data.get("accountNumber"),
            account_number_masked=self._mask_account(data.get("accountNumber")),
            institution_name=data.get("memberName"),
            institution_type=data.get("memberType"),
            account_type=self._map_account_type(data.get("accountType", "")),
            account_status=self._map_account_status(data.get("accountStatus", "")),
            ownership=self._map_ownership(data.get("ownership", "")),
            sanctioned_amount=self._parse_decimal(data.get("sanctionedAmount")),
            current_balance=self._parse_decimal(data.get("currentBalance")),
            overdue_amount=self._parse_decimal(data.get("overdueAmount")),
            emi_amount=self._parse_decimal(data.get("emiAmount")),
            credit_limit=self._parse_decimal(data.get("creditLimit")),
            high_credit=self._parse_decimal(data.get("highCredit")),
            write_off_amount=self._parse_decimal(data.get("writtenOffAmount")),
            opened_date=self._parse_date(data.get("dateOpened")),
            closed_date=self._parse_date(data.get("dateClosed")),
            last_payment_date=self._parse_date(data.get("lastPaymentDate")),
            reported_date=self._parse_date(data.get("dateReported")),
            tenure_months=self._parse_int(data.get("tenure")),
            raw_data=data,
        )

        # Parse DPD history
        dpd_string = data.get("dpdHistory", "")
        if dpd_string:
            account.dpd_history = self._parse_dpd_history(dpd_string)
            if account.dpd_history:
                account.max_dpd = max(account.dpd_history.values())

        # Determine if secured
        secured_types = ["HOME_LOAN", "AUTO_LOAN", "PROPERTY_LOAN", "GOLD_LOAN"]
        account.is_secured = account.account_type in secured_types

        return account

    def _parse_enquiry(self, data: Dict[str, Any]) -> CreditEnquiry:
        """Parse credit enquiry from CIBIL response."""
        return CreditEnquiry(
            enquiry_date=self._parse_date(data.get("dateOfEnquiry")),
            institution_name=data.get("memberName"),
            enquiry_purpose=data.get("enquiryPurpose"),
            enquiry_amount=self._parse_decimal(data.get("enquiryAmount")),
            raw_data=data,
        )

    def _parse_dpd_history(self, dpd_string: str) -> Dict[str, int]:
        """Parse DPD history string to dictionary.

        CIBIL format: "000000030060000000000000" (24 months, right to left)
        Each 3 chars represent DPD for a month.
        """
        dpd_history = {}
        if not dpd_string:
            return dpd_history

        today = date.today()
        # Parse in chunks of 3 from right to left
        for i in range(0, min(len(dpd_string), 72), 3):
            month_index = i // 3
            dpd_value = dpd_string[-(i+3):-(i) if i > 0 else None]
            if dpd_value:
                try:
                    month_date = date(
                        today.year - (month_index // 12),
                        today.month - (month_index % 12) if today.month > (month_index % 12) else 12 - ((month_index % 12) - today.month),
                        1
                    )
                    key = month_date.strftime("%Y%m")
                    # Handle special codes
                    if dpd_value in ["XXX", "***", "STD"]:
                        dpd_history[key] = 0
                    else:
                        dpd_history[key] = int(dpd_value)
                except (ValueError, TypeError):
                    continue
        return dpd_history

    @staticmethod
    def _mask_account(account_number: Optional[str]) -> Optional[str]:
        """Mask account number for display."""
        if not account_number or len(account_number) < 4:
            return account_number
        return f"XXXX{account_number[-4:]}"

    @staticmethod
    def _map_ownership(ownership: str) -> str:
        """Map CIBIL ownership type to standard type."""
        mapping = {
            "Individual": "INDIVIDUAL",
            "Joint": "JOINT",
            "Authorised User": "AUTHORIZED_USER",
            "Guarantor": "GUARANTOR",
        }
        return mapping.get(ownership, "INDIVIDUAL")

    @staticmethod
    def _map_inquiry_purpose(purpose: str) -> str:
        """Map purpose to CIBIL inquiry purpose code."""
        mapping = {
            "ACCOUNT_REVIEW": "05",
            "NEW_LOAN": "01",
            "CREDIT_CARD": "02",
            "RESTRUCTURE": "07",
            "COLLECTION": "08",
        }
        return mapping.get(purpose, "05")

    @staticmethod
    def _parse_int(value: Any) -> Optional[int]:
        """Parse value to integer."""
        if value is None:
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None
