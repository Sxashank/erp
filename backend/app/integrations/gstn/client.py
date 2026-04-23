"""GSTN Portal API Client.

Main client for GSTN API operations including:
- GSTR-1 save, submit, and file
- GSTR-3B save, submit, and file
- GSTR-2A/2B data fetch
- Return filing status check
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

import httpx

from app.integrations.gstn.auth import GSTNAuthManager

logger = logging.getLogger(__name__)


class GSTNClient:
    """GSTN Portal API Client.

    Provides methods for interacting with GSTN APIs for GST return filing.
    All API calls require an authenticated session (auth_token + SEK).
    """

    # API versions
    RETURNS_API_VERSION = "v1.1"
    GSTR1_API_VERSION = "v4.0"
    GSTR3B_API_VERSION = "v3.0"
    GSTR2B_API_VERSION = "v1.0"

    def __init__(
        self,
        auth_manager: GSTNAuthManager,
        auth_token: str,
        sek_b64: str,
        gstin: str,
    ):
        """Initialize GSTN Client.

        Args:
            auth_manager: Authentication manager for encryption/decryption
            auth_token: Valid authentication token
            sek_b64: Base64-encoded Session Encryption Key
            gstin: GSTIN for which operations are performed
        """
        self.auth = auth_manager
        self.auth_token = auth_token
        self.sek = sek_b64
        self.gstin = gstin
        self.base_url = auth_manager.base_url

        self._client = httpx.AsyncClient(timeout=60.0)

    async def close(self):
        """Close HTTP client."""
        await self._client.aclose()

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for authenticated API requests."""
        return {
            "Content-Type": "application/json",
            "asp-id": self.auth.asp_id,
            "asp-secret": self.auth.asp_secret,
            "auth-token": self.auth_token,
            "Gstn-Txn-Id": f"TXN{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}",
            "gstin": self.gstin,
        }

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        payload: Optional[Dict[str, Any]] = None,
        encrypt: bool = True,
    ) -> Dict[str, Any]:
        """Make authenticated API request.

        Args:
            method: HTTP method (GET, POST, PUT)
            endpoint: API endpoint path
            payload: Request payload (will be encrypted if encrypt=True)
            encrypt: Whether to encrypt the payload

        Returns:
            Decrypted response data
        """
        headers = self._get_headers()
        url = f"{self.base_url}{endpoint}"

        try:
            if method == "GET":
                response = await self._client.get(url, headers=headers)
            else:
                if payload and encrypt:
                    encrypted_payload = self.auth.encrypt_request_payload(payload, self.sek)
                    request_body = {"data": encrypted_payload}
                else:
                    request_body = payload or {}

                response = await self._client.request(
                    method,
                    url,
                    headers=headers,
                    json=request_body,
                )

            response.raise_for_status()
            result = response.json()

            # Check for API-level errors
            if result.get("status_cd") != "1":
                error = result.get("error", {})
                logger.warning(f"GSTN API error: {error}")
                return {
                    "success": False,
                    "error_code": error.get("error_cd"),
                    "error_message": error.get("message") or result.get("status_desc"),
                    "raw_response": result,
                }

            # Decrypt response data if present
            encrypted_data = result.get("data")
            if encrypted_data and isinstance(encrypted_data, str):
                decrypted_data = self.auth.decrypt_response_payload(encrypted_data, self.sek)
                return {
                    "success": True,
                    "data": decrypted_data,
                    "raw_response": result,
                }
            else:
                return {
                    "success": True,
                    "data": result.get("data"),
                    "raw_response": result,
                }

        except httpx.HTTPStatusError as e:
            logger.error(f"GSTN API HTTP error: {e}")
            return {
                "success": False,
                "error_message": str(e),
                "http_status": e.response.status_code,
            }
        except Exception as e:
            logger.error(f"GSTN API error: {e}")
            return {
                "success": False,
                "error_message": str(e),
            }

    # =========================================================================
    # GSTR-1 Operations
    # =========================================================================

    async def save_gstr1(
        self,
        return_period: str,
        section: str,
        data: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Save GSTR-1 data for a section.

        Args:
            return_period: Return period in MMYYYY format
            section: GSTR-1 section (B2B, B2CL, B2CS, CDNR, EXP, etc.)
            data: Invoice data for the section

        Returns:
            API response with reference ID
        """
        payload = {
            "gstin": self.gstin,
            "ret_period": return_period,
            section.lower(): data,
        }

        endpoint = f"/taxpayerapi/v{self.GSTR1_API_VERSION}/returns/gstr1"

        logger.info(f"Saving GSTR-1 {section} for {self.gstin}, period {return_period}")
        return await self._make_request("PUT", endpoint, payload)

    async def get_gstr1(
        self,
        return_period: str,
        section: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get GSTR-1 data.

        Args:
            return_period: Return period in MMYYYY format
            section: Optional section to fetch (if None, fetches all)

        Returns:
            GSTR-1 data
        """
        endpoint = f"/taxpayerapi/v{self.GSTR1_API_VERSION}/returns/gstr1"
        params = f"?gstin={self.gstin}&ret_period={return_period}"
        if section:
            params += f"&action={section}"

        return await self._make_request("GET", f"{endpoint}{params}")

    async def submit_gstr1(self, return_period: str) -> Dict[str, Any]:
        """Submit GSTR-1 for filing.

        Args:
            return_period: Return period in MMYYYY format

        Returns:
            API response with submit reference
        """
        payload = {
            "gstin": self.gstin,
            "ret_period": return_period,
        }

        endpoint = f"/taxpayerapi/v{self.GSTR1_API_VERSION}/returns/gstr1/submit"

        logger.info(f"Submitting GSTR-1 for {self.gstin}, period {return_period}")
        return await self._make_request("POST", endpoint, payload)

    async def file_gstr1_with_evc(
        self,
        return_period: str,
        pan: str,
        otp: str,
    ) -> Dict[str, Any]:
        """File GSTR-1 using EVC (Electronic Verification Code).

        Args:
            return_period: Return period in MMYYYY format
            pan: PAN of the authorized signatory
            otp: OTP received for EVC

        Returns:
            API response with ARN
        """
        payload = {
            "gstin": self.gstin,
            "ret_period": return_period,
            "pan": pan,
            "otp": otp,
            "sign_mode": "EVC",
        }

        endpoint = f"/taxpayerapi/v{self.GSTR1_API_VERSION}/returns/gstr1/file"

        logger.info(f"Filing GSTR-1 with EVC for {self.gstin}, period {return_period}")
        return await self._make_request("POST", endpoint, payload)

    async def get_gstr1_status(self, return_period: str) -> Dict[str, Any]:
        """Get GSTR-1 filing status.

        Args:
            return_period: Return period in MMYYYY format

        Returns:
            Filing status including ARN if filed
        """
        endpoint = f"/taxpayerapi/v{self.RETURNS_API_VERSION}/returns"
        params = f"?gstin={self.gstin}&ret_period={return_period}&rtn_typ=GSTR1"

        return await self._make_request("GET", f"{endpoint}{params}")

    # =========================================================================
    # GSTR-3B Operations
    # =========================================================================

    async def save_gstr3b(
        self,
        return_period: str,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Save GSTR-3B data.

        Args:
            return_period: Return period in MMYYYY format
            data: GSTR-3B data structure

        Returns:
            API response with reference ID
        """
        payload = {
            "gstin": self.gstin,
            "ret_period": return_period,
            **data,
        }

        endpoint = f"/taxpayerapi/v{self.GSTR3B_API_VERSION}/returns/gstr3b"

        logger.info(f"Saving GSTR-3B for {self.gstin}, period {return_period}")
        return await self._make_request("PUT", endpoint, payload)

    async def get_gstr3b(self, return_period: str) -> Dict[str, Any]:
        """Get GSTR-3B data.

        Args:
            return_period: Return period in MMYYYY format

        Returns:
            GSTR-3B data
        """
        endpoint = f"/taxpayerapi/v{self.GSTR3B_API_VERSION}/returns/gstr3b"
        params = f"?gstin={self.gstin}&ret_period={return_period}"

        return await self._make_request("GET", f"{endpoint}{params}")

    async def submit_gstr3b(self, return_period: str) -> Dict[str, Any]:
        """Submit GSTR-3B for filing.

        Args:
            return_period: Return period in MMYYYY format

        Returns:
            API response with submit reference
        """
        payload = {
            "gstin": self.gstin,
            "ret_period": return_period,
        }

        endpoint = f"/taxpayerapi/v{self.GSTR3B_API_VERSION}/returns/gstr3b/submit"

        logger.info(f"Submitting GSTR-3B for {self.gstin}, period {return_period}")
        return await self._make_request("POST", endpoint, payload)

    async def file_gstr3b_with_evc(
        self,
        return_period: str,
        pan: str,
        otp: str,
    ) -> Dict[str, Any]:
        """File GSTR-3B using EVC.

        Args:
            return_period: Return period in MMYYYY format
            pan: PAN of the authorized signatory
            otp: OTP received for EVC

        Returns:
            API response with ARN
        """
        payload = {
            "gstin": self.gstin,
            "ret_period": return_period,
            "pan": pan,
            "otp": otp,
            "sign_mode": "EVC",
        }

        endpoint = f"/taxpayerapi/v{self.GSTR3B_API_VERSION}/returns/gstr3b/file"

        logger.info(f"Filing GSTR-3B with EVC for {self.gstin}, period {return_period}")
        return await self._make_request("POST", endpoint, payload)

    async def get_gstr3b_status(self, return_period: str) -> Dict[str, Any]:
        """Get GSTR-3B filing status.

        Args:
            return_period: Return period in MMYYYY format

        Returns:
            Filing status including ARN if filed
        """
        endpoint = f"/taxpayerapi/v{self.RETURNS_API_VERSION}/returns"
        params = f"?gstin={self.gstin}&ret_period={return_period}&rtn_typ=GSTR3B"

        return await self._make_request("GET", f"{endpoint}{params}")

    # =========================================================================
    # GSTR-2A/2B Operations
    # =========================================================================

    async def get_gstr2a(
        self,
        return_period: str,
        section: str = "B2B",
        from_gstin: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get GSTR-2A data (auto-populated inward supplies).

        Args:
            return_period: Return period in MMYYYY format
            section: Section to fetch (B2B, B2BA, CDN, CDNA, ISD, IMPG, IMPGSEZ)
            from_gstin: Optional supplier GSTIN filter

        Returns:
            GSTR-2A data for the section
        """
        endpoint = f"/taxpayerapi/v{self.RETURNS_API_VERSION}/returns/gstr2a"
        params = f"?gstin={self.gstin}&ret_period={return_period}&action={section}"
        if from_gstin:
            params += f"&ctin={from_gstin}"

        return await self._make_request("GET", f"{endpoint}{params}")

    async def get_gstr2b(
        self,
        return_period: str,
        file_num: int = 1,
    ) -> Dict[str, Any]:
        """Get GSTR-2B data (auto-generated ITC statement).

        Args:
            return_period: Return period in MMYYYY format
            file_num: File number for large data (1-based)

        Returns:
            GSTR-2B data including eligible ITC
        """
        endpoint = f"/taxpayerapi/v{self.GSTR2B_API_VERSION}/returns/gstr2b"
        params = f"?gstin={self.gstin}&ret_period={return_period}&file_num={file_num}"

        return await self._make_request("GET", f"{endpoint}{params}")

    async def get_gstr2b_summary(self, return_period: str) -> Dict[str, Any]:
        """Get GSTR-2B summary.

        Args:
            return_period: Return period in MMYYYY format

        Returns:
            Summary of GSTR-2B with ITC totals
        """
        endpoint = f"/taxpayerapi/v{self.GSTR2B_API_VERSION}/returns/gstr2b/summary"
        params = f"?gstin={self.gstin}&ret_period={return_period}"

        return await self._make_request("GET", f"{endpoint}{params}")

    # =========================================================================
    # Common Operations
    # =========================================================================

    async def get_return_status(
        self,
        return_period: str,
        return_type: str,
    ) -> Dict[str, Any]:
        """Get return filing status.

        Args:
            return_period: Return period in MMYYYY format
            return_type: Return type (GSTR1, GSTR3B, GSTR2A, GSTR2B)

        Returns:
            Filing status with ARN if filed
        """
        endpoint = f"/taxpayerapi/v{self.RETURNS_API_VERSION}/returns"
        params = f"?gstin={self.gstin}&ret_period={return_period}&rtn_typ={return_type}"

        return await self._make_request("GET", f"{endpoint}{params}")

    async def get_ledger_balance(self) -> Dict[str, Any]:
        """Get electronic ledger balances (Cash, ITC, Liability).

        Returns:
            Current ledger balances
        """
        endpoint = f"/taxpayerapi/v{self.RETURNS_API_VERSION}/ledgers"
        params = f"?gstin={self.gstin}"

        return await self._make_request("GET", f"{endpoint}{params}")

    async def request_otp_for_filing(self, pan: str) -> Dict[str, Any]:
        """Request OTP for filing return with EVC.

        Args:
            pan: PAN of the authorized signatory

        Returns:
            OTP reference for filing
        """
        payload = {
            "gstin": self.gstin,
            "pan": pan,
            "form_type": "R",  # Regular
        }

        endpoint = f"/taxpayerapi/v{self.RETURNS_API_VERSION}/otp"

        return await self._make_request("POST", endpoint, payload)

    async def verify_gstin(self, gstin_to_verify: str) -> Dict[str, Any]:
        """Verify a GSTIN.

        Args:
            gstin_to_verify: GSTIN to verify

        Returns:
            GSTIN details if valid
        """
        endpoint = f"/taxpayerapi/v{self.RETURNS_API_VERSION}/search"
        params = f"?gstin={gstin_to_verify}"

        return await self._make_request("GET", f"{endpoint}{params}")

    async def get_hsn_codes(
        self,
        search_text: str,
        hsn_type: str = "G",  # G=Goods, S=Services
    ) -> Dict[str, Any]:
        """Search HSN/SAC codes.

        Args:
            search_text: Text to search
            hsn_type: G for Goods (HSN), S for Services (SAC)

        Returns:
            List of matching HSN/SAC codes
        """
        endpoint = f"/taxpayerapi/v{self.RETURNS_API_VERSION}/hsn"
        params = f"?search={search_text}&type={hsn_type}"

        return await self._make_request("GET", f"{endpoint}{params}")
