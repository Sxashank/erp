"""E-Invoice IRP API Client.

Main client for E-Invoice operations including:
- IRN generation
- E-Invoice cancellation
- QR code generation
- E-Way Bill generation with E-Invoice
"""

import base64
import json
import logging
from datetime import datetime, date
from decimal import Decimal
from typing import Dict, Any, List, Optional

import httpx

from app.integrations.einvoice.auth import EInvoiceAuthManager

logger = logging.getLogger(__name__)


class DecimalEncoder(json.JSONEncoder):
    """JSON encoder that handles Decimal types."""

    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)


class EInvoiceClient:
    """E-Invoice IRP API Client.

    Provides methods for E-Invoice generation and management.
    Supports NIC IRP and GSP (ClearTax, etc.) APIs.
    """

    # API versions
    NIC_API_VERSION = "1.04"

    def __init__(
        self,
        auth_manager: EInvoiceAuthManager,
        auth_token: Optional[str] = None,
        sek_b64: Optional[str] = None,
    ):
        """Initialize E-Invoice Client.

        Args:
            auth_manager: Authentication manager
            auth_token: Pre-existing auth token (optional)
            sek_b64: Pre-existing SEK (optional)
        """
        self.auth = auth_manager
        self.base_url = auth_manager.base_url
        self._client = httpx.AsyncClient(timeout=60.0)

        if auth_token:
            self.auth._auth_token = auth_token
        if sek_b64:
            self.auth._sek = base64.b64decode(sek_b64)

    async def close(self):
        """Close HTTP client."""
        await self._client.aclose()
        await self.auth.close()

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for authenticated API requests."""
        return {
            "Content-Type": "application/json",
            "client_id": self.auth.client_id,
            "client_secret": self.auth.client_secret,
            "gstin": self.auth.gstin,
            "authtoken": self.auth.auth_token or "",
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
            method: HTTP method
            endpoint: API endpoint
            payload: Request payload
            encrypt: Whether to encrypt payload

        Returns:
            API response
        """
        if not self.auth.is_authenticated:
            # Try to authenticate
            auth_result = await self.auth.authenticate()
            if not auth_result["success"]:
                return auth_result

        headers = self._get_headers()
        url = f"{self.base_url}{endpoint}"

        try:
            if method == "GET":
                response = await self._client.get(url, headers=headers)
            else:
                if payload and encrypt:
                    encrypted_payload = self.auth.encrypt_payload(payload)
                    request_body = {"Data": encrypted_payload}
                else:
                    request_body = payload or {}

                response = await self._client.request(
                    method,
                    url,
                    headers=headers,
                    json=request_body,
                )

            result = response.json()

            # Check for success
            if result.get("Status") == 1:
                # Decrypt response data if encrypted
                encrypted_data = result.get("Data")
                if encrypted_data and isinstance(encrypted_data, str):
                    try:
                        decrypted_data = self.auth.decrypt_payload(encrypted_data)
                        return {
                            "success": True,
                            "data": decrypted_data,
                            "raw_response": result,
                        }
                    except Exception as e:
                        logger.warning(f"Could not decrypt response: {e}")
                        return {
                            "success": True,
                            "data": result.get("Data"),
                            "raw_response": result,
                        }
                else:
                    return {
                        "success": True,
                        "data": result.get("Data"),
                        "raw_response": result,
                    }
            else:
                error_details = result.get("ErrorDetails", [{}])
                error = error_details[0] if error_details else {}
                return {
                    "success": False,
                    "error_code": error.get("ErrorCode"),
                    "error_message": error.get("ErrorMessage") or result.get("Info"),
                    "error_details": error_details,
                    "raw_response": result,
                }

        except httpx.HTTPStatusError as e:
            logger.error(f"E-Invoice API HTTP error: {e}")
            return {
                "success": False,
                "error_message": str(e),
                "http_status": e.response.status_code,
            }
        except Exception as e:
            logger.error(f"E-Invoice API error: {e}")
            return {
                "success": False,
                "error_message": str(e),
            }

    # =========================================================================
    # E-Invoice Generation
    # =========================================================================

    def build_invoice_payload(
        self,
        invoice_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Build E-Invoice payload from invoice data.

        Args:
            invoice_data: Invoice details dictionary

        Returns:
            E-Invoice payload in NIC format
        """
        # Build payload as per NIC schema
        payload = {
            "Version": "1.1",
            "TranDtls": {
                "TaxSch": "GST",
                "SupTyp": invoice_data.get("supply_type", "B2B"),
                "RegRev": "Y" if invoice_data.get("reverse_charge") else "N",
                "EcmGstin": invoice_data.get("ecom_gstin"),
                "IgstOnIntra": "N",
            },
            "DocDtls": {
                "Typ": invoice_data.get("document_type", "INV"),
                "No": invoice_data.get("invoice_number"),
                "Dt": invoice_data.get("invoice_date"),
            },
            "SellerDtls": {
                "Gstin": invoice_data.get("seller_gstin"),
                "LglNm": invoice_data.get("seller_name"),
                "TrdNm": invoice_data.get("seller_trade_name"),
                "Addr1": invoice_data.get("seller_address1"),
                "Addr2": invoice_data.get("seller_address2"),
                "Loc": invoice_data.get("seller_location"),
                "Pin": int(invoice_data.get("seller_pincode", 0)),
                "Stcd": invoice_data.get("seller_state_code"),
                "Ph": invoice_data.get("seller_phone"),
                "Em": invoice_data.get("seller_email"),
            },
            "BuyerDtls": {
                "Gstin": invoice_data.get("buyer_gstin", "URP"),
                "LglNm": invoice_data.get("buyer_name"),
                "TrdNm": invoice_data.get("buyer_trade_name"),
                "Addr1": invoice_data.get("buyer_address1"),
                "Addr2": invoice_data.get("buyer_address2"),
                "Loc": invoice_data.get("buyer_location"),
                "Pin": int(invoice_data.get("buyer_pincode", 0)),
                "Stcd": invoice_data.get("buyer_state_code"),
                "Pos": invoice_data.get("place_of_supply"),
                "Ph": invoice_data.get("buyer_phone"),
                "Em": invoice_data.get("buyer_email"),
            },
            "ItemList": [],
            "ValDtls": {
                "AssVal": float(invoice_data.get("taxable_value", 0)),
                "CgstVal": float(invoice_data.get("cgst_amount", 0)),
                "SgstVal": float(invoice_data.get("sgst_amount", 0)),
                "IgstVal": float(invoice_data.get("igst_amount", 0)),
                "CesVal": float(invoice_data.get("cess_amount", 0)),
                "StCesVal": 0,
                "Discount": float(invoice_data.get("discount_amount", 0)),
                "OthChrg": float(invoice_data.get("other_charges", 0)),
                "RndOffAmt": float(invoice_data.get("round_off", 0)),
                "TotInvVal": float(invoice_data.get("total_amount", 0)),
                "TotInvValFc": 0,
            },
        }

        # Add items
        for idx, item in enumerate(invoice_data.get("items", []), 1):
            item_entry = {
                "SlNo": str(idx),
                "PrdDesc": item.get("description"),
                "IsServc": "Y" if item.get("is_service") else "N",
                "HsnCd": item.get("hsn_code"),
                "Barcde": item.get("barcode"),
                "Qty": float(item.get("quantity", 0)),
                "FreeQty": 0,
                "Unit": item.get("unit", "NOS"),
                "UnitPrice": float(item.get("unit_price", 0)),
                "TotAmt": float(item.get("total_amount", 0)),
                "Discount": float(item.get("discount", 0)),
                "PreTaxVal": 0,
                "AssAmt": float(item.get("taxable_amount", 0)),
                "GstRt": float(item.get("gst_rate", 0)),
                "IgstAmt": float(item.get("igst_amount", 0)),
                "CgstAmt": float(item.get("cgst_amount", 0)),
                "SgstAmt": float(item.get("sgst_amount", 0)),
                "CesRt": float(item.get("cess_rate", 0)),
                "CesAmt": float(item.get("cess_amount", 0)),
                "CesNonAdvlAmt": 0,
                "StateCesRt": 0,
                "StateCesAmt": 0,
                "StateCesNonAdvlAmt": 0,
                "OthChrg": 0,
                "TotItemVal": float(item.get("line_total", 0)),
            }
            payload["ItemList"].append(item_entry)

        # Add dispatch details if different from seller
        if invoice_data.get("dispatch_from_different"):
            payload["DispDtls"] = {
                "Nm": invoice_data.get("dispatch_name"),
                "Addr1": invoice_data.get("dispatch_address1"),
                "Addr2": invoice_data.get("dispatch_address2"),
                "Loc": invoice_data.get("dispatch_location"),
                "Pin": int(invoice_data.get("dispatch_pincode", 0)),
                "Stcd": invoice_data.get("dispatch_state_code"),
            }

        # Add ship to details if different from buyer
        if invoice_data.get("ship_to_different"):
            payload["ShipDtls"] = {
                "Gstin": invoice_data.get("ship_to_gstin"),
                "LglNm": invoice_data.get("ship_to_name"),
                "TrdNm": invoice_data.get("ship_to_trade_name"),
                "Addr1": invoice_data.get("ship_to_address1"),
                "Addr2": invoice_data.get("ship_to_address2"),
                "Loc": invoice_data.get("ship_to_location"),
                "Pin": int(invoice_data.get("ship_to_pincode", 0)),
                "Stcd": invoice_data.get("ship_to_state_code"),
            }

        # Add E-Way Bill details if required
        if invoice_data.get("generate_eway_bill"):
            payload["EwbDtls"] = {
                "TransId": invoice_data.get("transporter_id"),
                "TransName": invoice_data.get("transporter_name"),
                "Distance": int(invoice_data.get("distance", 0)),
                "TransMode": invoice_data.get("transport_mode", "1"),
                "TransDocNo": invoice_data.get("transport_doc_no"),
                "TransDocDt": invoice_data.get("transport_doc_date"),
                "VehNo": invoice_data.get("vehicle_number"),
                "VehType": invoice_data.get("vehicle_type", "R"),
            }

        return payload

    async def generate_irn(
        self,
        invoice_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate IRN (Invoice Reference Number) for E-Invoice.

        Args:
            invoice_data: Invoice details

        Returns:
            IRN generation result with QR code
        """
        payload = self.build_invoice_payload(invoice_data)

        logger.info(f"Generating IRN for invoice {invoice_data.get('invoice_number')}")
        result = await self._make_request(
            "POST",
            f"/eivital/v{self.NIC_API_VERSION}/Invoice",
            payload,
        )

        if result["success"]:
            data = result.get("data", {})
            return {
                "success": True,
                "irn": data.get("Irn"),
                "ack_number": data.get("AckNo"),
                "ack_date": data.get("AckDt"),
                "signed_invoice": data.get("SignedInvoice"),
                "signed_qr_code": data.get("SignedQRCode"),
                "eway_bill_number": data.get("EwbNo"),
                "eway_bill_date": data.get("EwbDt"),
                "eway_bill_validity": data.get("EwbValidTill"),
                "raw_response": result.get("raw_response"),
            }
        else:
            return result

    async def cancel_irn(
        self,
        irn: str,
        cancel_reason: str,
        cancel_remarks: str,
    ) -> Dict[str, Any]:
        """Cancel an E-Invoice IRN.

        Args:
            irn: Invoice Reference Number to cancel
            cancel_reason: Reason code (1=Duplicate, 2=Data Entry Error, 3=Order Cancelled, 4=Others)
            cancel_remarks: Cancellation remarks

        Returns:
            Cancellation result
        """
        payload = {
            "Irn": irn,
            "CnlRsn": cancel_reason,
            "CnlRem": cancel_remarks,
        }

        logger.info(f"Cancelling IRN: {irn}")
        result = await self._make_request(
            "POST",
            f"/eivital/v{self.NIC_API_VERSION}/Invoice/Cancel",
            payload,
        )

        if result["success"]:
            data = result.get("data", {})
            return {
                "success": True,
                "irn": data.get("Irn"),
                "cancel_date": data.get("CancelDate"),
                "raw_response": result.get("raw_response"),
            }
        else:
            return result

    async def get_irn_details(
        self,
        irn: str,
    ) -> Dict[str, Any]:
        """Get E-Invoice details by IRN.

        Args:
            irn: Invoice Reference Number

        Returns:
            Invoice details
        """
        logger.info(f"Fetching IRN details: {irn}")

        headers = self._get_headers()
        headers["irn"] = irn

        try:
            response = await self._client.get(
                f"{self.base_url}/eivital/v{self.NIC_API_VERSION}/Invoice/irn/{irn}",
                headers=headers,
            )

            result = response.json()

            if result.get("Status") == 1:
                data = result.get("Data", {})
                if isinstance(data, str):
                    data = self.auth.decrypt_payload(data)
                return {
                    "success": True,
                    "data": data,
                    "raw_response": result,
                }
            else:
                error_details = result.get("ErrorDetails", [{}])
                error = error_details[0] if error_details else {}
                return {
                    "success": False,
                    "error_code": error.get("ErrorCode"),
                    "error_message": error.get("ErrorMessage"),
                    "raw_response": result,
                }

        except Exception as e:
            logger.error(f"Error fetching IRN details: {e}")
            return {
                "success": False,
                "error_message": str(e),
            }

    async def get_irn_by_doc(
        self,
        doc_type: str,
        doc_no: str,
        doc_date: str,
    ) -> Dict[str, Any]:
        """Get E-Invoice details by document number.

        Args:
            doc_type: Document type (INV/CRN/DBN)
            doc_no: Document number
            doc_date: Document date (DD/MM/YYYY)

        Returns:
            Invoice details
        """
        logger.info(f"Fetching IRN by document: {doc_type}/{doc_no}")

        headers = self._get_headers()

        try:
            response = await self._client.get(
                f"{self.base_url}/eivital/v{self.NIC_API_VERSION}/Invoice/gstinirn/{self.auth.gstin}/{doc_type}/{doc_no}/{doc_date}",
                headers=headers,
            )

            result = response.json()

            if result.get("Status") == 1:
                data = result.get("Data", {})
                if isinstance(data, str):
                    data = self.auth.decrypt_payload(data)
                return {
                    "success": True,
                    "data": data,
                    "raw_response": result,
                }
            else:
                error_details = result.get("ErrorDetails", [{}])
                error = error_details[0] if error_details else {}
                return {
                    "success": False,
                    "error_code": error.get("ErrorCode"),
                    "error_message": error.get("ErrorMessage"),
                    "raw_response": result,
                }

        except Exception as e:
            logger.error(f"Error fetching IRN by document: {e}")
            return {
                "success": False,
                "error_message": str(e),
            }

    # =========================================================================
    # E-Way Bill Operations (via E-Invoice)
    # =========================================================================

    async def generate_eway_bill_by_irn(
        self,
        irn: str,
        distance: int,
        transport_mode: str = "1",
        vehicle_number: Optional[str] = None,
        transporter_id: Optional[str] = None,
        transporter_name: Optional[str] = None,
        transport_doc_no: Optional[str] = None,
        transport_doc_date: Optional[str] = None,
        vehicle_type: str = "R",
    ) -> Dict[str, Any]:
        """Generate E-Way Bill for an existing IRN.

        Args:
            irn: Invoice Reference Number
            distance: Approximate distance in KM
            transport_mode: 1=Road, 2=Rail, 3=Air, 4=Ship
            vehicle_number: Vehicle registration number
            transporter_id: Transporter GSTIN
            transporter_name: Transporter name
            transport_doc_no: Transport document number
            transport_doc_date: Transport document date
            vehicle_type: R=Regular, O=ODC

        Returns:
            E-Way Bill generation result
        """
        payload = {
            "Irn": irn,
            "Distance": distance,
            "TransMode": transport_mode,
            "VehNo": vehicle_number,
            "TransId": transporter_id,
            "TransName": transporter_name,
            "TransDocNo": transport_doc_no,
            "TransDocDt": transport_doc_date,
            "VehType": vehicle_type,
        }

        # Remove None values
        payload = {k: v for k, v in payload.items() if v is not None}

        logger.info(f"Generating E-Way Bill for IRN: {irn}")
        result = await self._make_request(
            "POST",
            f"/eivital/v{self.NIC_API_VERSION}/ewaybill",
            payload,
        )

        if result["success"]:
            data = result.get("data", {})
            return {
                "success": True,
                "eway_bill_number": data.get("EwbNo"),
                "eway_bill_date": data.get("EwbDt"),
                "valid_until": data.get("EwbValidTill"),
                "raw_response": result.get("raw_response"),
            }
        else:
            return result

    async def cancel_eway_bill_by_irn(
        self,
        irn: str,
        eway_bill_number: str,
        cancel_reason: str,
        cancel_remarks: str,
    ) -> Dict[str, Any]:
        """Cancel E-Way Bill generated via E-Invoice.

        Args:
            irn: Invoice Reference Number
            eway_bill_number: E-Way Bill number
            cancel_reason: Reason code
            cancel_remarks: Cancellation remarks

        Returns:
            Cancellation result
        """
        payload = {
            "Irn": irn,
            "EwbNo": int(eway_bill_number),
            "CnlRsn": cancel_reason,
            "CnlRem": cancel_remarks,
        }

        logger.info(f"Cancelling E-Way Bill {eway_bill_number} for IRN: {irn}")
        result = await self._make_request(
            "POST",
            f"/eivital/v{self.NIC_API_VERSION}/ewaybill/cancel",
            payload,
        )

        if result["success"]:
            return {
                "success": True,
                "eway_bill_number": eway_bill_number,
                "cancel_date": result.get("data", {}).get("CancelDate"),
                "raw_response": result.get("raw_response"),
            }
        else:
            return result
