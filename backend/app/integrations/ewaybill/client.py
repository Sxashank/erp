"""E-Way Bill API Client.

Main client for E-Way Bill operations including:
- E-Way Bill generation
- E-Way Bill cancellation
- Vehicle update (Part B)
- E-Way Bill extension
- Consolidated E-Way Bill
"""

import base64
import json
import logging
from datetime import datetime, date
from decimal import Decimal
from typing import Dict, Any, List, Optional

import httpx

from app.integrations.ewaybill.auth import EWayBillAuthManager

logger = logging.getLogger(__name__)


class EWayBillClient:
    """E-Way Bill API Client.

    Provides methods for E-Way Bill generation and management.
    """

    def __init__(
        self,
        auth_manager: EWayBillAuthManager,
        auth_token: Optional[str] = None,
        sek_b64: Optional[str] = None,
    ):
        """Initialize E-Way Bill Client.

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
        """Make authenticated API request."""
        if not self.auth.is_authenticated:
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
                    request_body = {"data": encrypted_payload}
                else:
                    request_body = payload or {}

                response = await self._client.request(
                    method,
                    url,
                    headers=headers,
                    json=request_body,
                )

            result = response.json()

            if result.get("status") == 1 or result.get("success"):
                encrypted_data = result.get("data")
                if encrypted_data and isinstance(encrypted_data, str):
                    try:
                        decrypted_data = self.auth.decrypt_payload(encrypted_data)
                        return {
                            "success": True,
                            "data": decrypted_data,
                            "raw_response": result,
                        }
                    except Exception:
                        return {
                            "success": True,
                            "data": result.get("data"),
                            "raw_response": result,
                        }
                else:
                    return {
                        "success": True,
                        "data": result.get("data"),
                        "raw_response": result,
                    }
            else:
                error = result.get("error", {})
                return {
                    "success": False,
                    "error_code": error.get("errorCodes") if isinstance(error, dict) else None,
                    "error_message": error.get("message") if isinstance(error, dict) else str(error),
                    "raw_response": result,
                }

        except httpx.HTTPStatusError as e:
            logger.error(f"E-Way Bill API HTTP error: {e}")
            return {
                "success": False,
                "error_message": str(e),
                "http_status": e.response.status_code,
            }
        except Exception as e:
            logger.error(f"E-Way Bill API error: {e}")
            return {
                "success": False,
                "error_message": str(e),
            }

    # =========================================================================
    # E-Way Bill Generation
    # =========================================================================

    def build_eway_bill_payload(
        self,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Build E-Way Bill payload.

        Args:
            data: E-Way Bill data dictionary

        Returns:
            Formatted payload for NIC API
        """
        payload = {
            "supplyType": data.get("supply_type", "O"),  # O=Outward, I=Inward
            "subSupplyType": data.get("sub_supply_type", "1"),  # 1=Supply
            "docType": data.get("document_type", "INV"),
            "docNo": data.get("document_number"),
            "docDate": data.get("document_date"),
            "fromGstin": data.get("from_gstin"),
            "fromTrdName": data.get("from_trade_name"),
            "fromAddr1": data.get("from_address1"),
            "fromAddr2": data.get("from_address2", ""),
            "fromPlace": data.get("from_place"),
            "fromPincode": int(data.get("from_pincode", 0)),
            "fromStateCode": int(data.get("from_state_code", 0)),
            "toGstin": data.get("to_gstin", "URP"),
            "toTrdName": data.get("to_trade_name"),
            "toAddr1": data.get("to_address1"),
            "toAddr2": data.get("to_address2", ""),
            "toPlace": data.get("to_place"),
            "toPincode": int(data.get("to_pincode", 0)),
            "toStateCode": int(data.get("to_state_code", 0)),
            "totalValue": float(data.get("total_value", 0)),
            "cgstValue": float(data.get("cgst_value", 0)),
            "sgstValue": float(data.get("sgst_value", 0)),
            "igstValue": float(data.get("igst_value", 0)),
            "cessValue": float(data.get("cess_value", 0)),
            "totInvValue": float(data.get("invoice_value", 0)),
            "transMode": data.get("transport_mode", "1"),
            "transDistance": int(data.get("distance", 0)),
            "transporterId": data.get("transporter_id", ""),
            "transporterName": data.get("transporter_name", ""),
            "transDocNo": data.get("transport_doc_no", ""),
            "transDocDate": data.get("transport_doc_date", ""),
            "vehicleNo": data.get("vehicle_number", ""),
            "vehicleType": data.get("vehicle_type", "R"),
            "itemList": [],
        }

        # Add items
        for idx, item in enumerate(data.get("items", []), 1):
            item_entry = {
                "productName": item.get("product_name"),
                "productDesc": item.get("product_desc", ""),
                "hsnCode": int(item.get("hsn_code", 0)),
                "quantity": float(item.get("quantity", 0)),
                "qtyUnit": item.get("unit", "NOS"),
                "cgstRate": float(item.get("cgst_rate", 0)),
                "sgstRate": float(item.get("sgst_rate", 0)),
                "igstRate": float(item.get("igst_rate", 0)),
                "cessRate": float(item.get("cess_rate", 0)),
                "taxableAmount": float(item.get("taxable_amount", 0)),
            }
            payload["itemList"].append(item_entry)

        # Add dispatch from if different
        if data.get("dispatch_from_different"):
            payload["dispatchFromGSTIN"] = data.get("dispatch_from_gstin", "")
            payload["dispatchFromTradeName"] = data.get("dispatch_from_name", "")
            payload["dispatchFromAddress1"] = data.get("dispatch_from_address1", "")
            payload["dispatchFromAddress2"] = data.get("dispatch_from_address2", "")
            payload["dispatchFromPlace"] = data.get("dispatch_from_place", "")
            payload["dispatchFromPincode"] = int(data.get("dispatch_from_pincode", 0))
            payload["dispatchFromStateCode"] = int(data.get("dispatch_from_state_code", 0))

        # Add ship to if different
        if data.get("ship_to_different"):
            payload["shipToGSTIN"] = data.get("ship_to_gstin", "")
            payload["shipToTradeName"] = data.get("ship_to_name", "")
            payload["shipToAddress1"] = data.get("ship_to_address1", "")
            payload["shipToAddress2"] = data.get("ship_to_address2", "")
            payload["shipToPlace"] = data.get("ship_to_place", "")
            payload["shipToPincode"] = int(data.get("ship_to_pincode", 0))
            payload["shipToStateCode"] = int(data.get("ship_to_state_code", 0))

        return payload

    async def generate_eway_bill(
        self,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate E-Way Bill.

        Args:
            data: E-Way Bill data

        Returns:
            Generation result with E-Way Bill number
        """
        payload = self.build_eway_bill_payload(data)

        logger.info(f"Generating E-Way Bill for document {data.get('document_number')}")
        result = await self._make_request("POST", "/ewayapi/v1.03/ewbv1.03/ewayBill", payload)

        if result["success"]:
            response_data = result.get("data", {})
            return {
                "success": True,
                "eway_bill_number": response_data.get("ewayBillNo"),
                "eway_bill_date": response_data.get("ewayBillDate"),
                "valid_until": response_data.get("validUpto"),
                "alert": response_data.get("alert"),
                "raw_response": result.get("raw_response"),
            }
        else:
            return result

    async def cancel_eway_bill(
        self,
        eway_bill_number: str,
        cancel_reason: str,
        cancel_remarks: str,
    ) -> Dict[str, Any]:
        """Cancel E-Way Bill.

        Args:
            eway_bill_number: E-Way Bill number to cancel
            cancel_reason: Reason code (1-5)
            cancel_remarks: Cancellation remarks

        Returns:
            Cancellation result
        """
        payload = {
            "ewbNo": int(eway_bill_number),
            "cancelRsnCode": int(cancel_reason),
            "cancelRmrk": cancel_remarks,
        }

        logger.info(f"Cancelling E-Way Bill: {eway_bill_number}")
        result = await self._make_request("POST", "/ewayapi/v1.03/ewbv1.03/ewayBill/Cancel", payload)

        if result["success"]:
            return {
                "success": True,
                "eway_bill_number": eway_bill_number,
                "cancel_date": result.get("data", {}).get("cancelDate"),
                "raw_response": result.get("raw_response"),
            }
        else:
            return result

    async def update_vehicle(
        self,
        eway_bill_number: str,
        vehicle_number: str,
        from_place: str,
        from_state_code: str,
        reason_code: str = "1",
        reason_remarks: str = "",
        transport_doc_no: Optional[str] = None,
        transport_doc_date: Optional[str] = None,
        transporter_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update vehicle details (Part B).

        Args:
            eway_bill_number: E-Way Bill number
            vehicle_number: New vehicle number
            from_place: Current location
            from_state_code: Current state code
            reason_code: Reason for update (1=First time, 2=Break down, etc.)
            reason_remarks: Remarks
            transport_doc_no: New transport document number
            transport_doc_date: New transport document date
            transporter_id: New transporter GSTIN

        Returns:
            Update result
        """
        payload = {
            "ewbNo": int(eway_bill_number),
            "vehicleNo": vehicle_number,
            "fromPlace": from_place,
            "fromState": int(from_state_code),
            "reasonCode": reason_code,
            "reasonRem": reason_remarks,
            "transMode": "1",  # Road
        }

        if transport_doc_no:
            payload["transDocNo"] = transport_doc_no
        if transport_doc_date:
            payload["transDocDate"] = transport_doc_date
        if transporter_id:
            payload["TransporterId"] = transporter_id

        logger.info(f"Updating vehicle for E-Way Bill: {eway_bill_number}")
        result = await self._make_request("POST", "/ewayapi/v1.03/ewbv1.03/ewayBill/vehicleUpdate", payload)

        if result["success"]:
            return {
                "success": True,
                "eway_bill_number": eway_bill_number,
                "vehicle_number": vehicle_number,
                "valid_until": result.get("data", {}).get("validUpto"),
                "raw_response": result.get("raw_response"),
            }
        else:
            return result

    async def extend_validity(
        self,
        eway_bill_number: str,
        vehicle_number: str,
        from_place: str,
        from_state_code: str,
        remaining_distance: int,
        extend_reason: str,
        consignment_status: str = "M",  # M=In movement, T=In transit
        transit_type: Optional[str] = None,
        address_line1: Optional[str] = None,
        address_line2: Optional[str] = None,
        address_line3: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Extend E-Way Bill validity.

        Args:
            eway_bill_number: E-Way Bill number
            vehicle_number: Current vehicle number
            from_place: Current location
            from_state_code: Current state code
            remaining_distance: Remaining distance in KM
            extend_reason: Reason for extension
            consignment_status: M=Movement, T=Transit
            transit_type: Type of transit (if applicable)
            address_line1-3: Address lines

        Returns:
            Extension result with new validity
        """
        payload = {
            "ewbNo": int(eway_bill_number),
            "vehicleNo": vehicle_number,
            "fromPlace": from_place,
            "fromState": int(from_state_code),
            "remainingDistance": remaining_distance,
            "extendedRemarks": extend_reason,
            "consignmentStatus": consignment_status,
        }

        if transit_type:
            payload["transitType"] = transit_type
        if address_line1:
            payload["addressLine1"] = address_line1
        if address_line2:
            payload["addressLine2"] = address_line2
        if address_line3:
            payload["addressLine3"] = address_line3

        logger.info(f"Extending E-Way Bill validity: {eway_bill_number}")
        result = await self._make_request("POST", "/ewayapi/v1.03/ewbv1.03/ewayBill/extendValidity", payload)

        if result["success"]:
            return {
                "success": True,
                "eway_bill_number": eway_bill_number,
                "valid_until": result.get("data", {}).get("validUpto"),
                "raw_response": result.get("raw_response"),
            }
        else:
            return result

    async def get_eway_bill(
        self,
        eway_bill_number: str,
    ) -> Dict[str, Any]:
        """Get E-Way Bill details.

        Args:
            eway_bill_number: E-Way Bill number

        Returns:
            E-Way Bill details
        """
        logger.info(f"Fetching E-Way Bill: {eway_bill_number}")

        headers = self._get_headers()

        try:
            response = await self._client.get(
                f"{self.base_url}/ewayapi/v1.03/ewbv1.03/ewayBill/getEwayBill",
                headers=headers,
                params={"ewbNo": eway_bill_number},
            )

            result = response.json()

            if result.get("status") == 1 or result.get("success"):
                data = result.get("data", {})
                if isinstance(data, str):
                    data = self.auth.decrypt_payload(data)
                return {
                    "success": True,
                    "data": data,
                    "raw_response": result,
                }
            else:
                error = result.get("error", {})
                return {
                    "success": False,
                    "error_code": error.get("errorCodes") if isinstance(error, dict) else None,
                    "error_message": error.get("message") if isinstance(error, dict) else str(error),
                    "raw_response": result,
                }

        except Exception as e:
            logger.error(f"Error fetching E-Way Bill: {e}")
            return {
                "success": False,
                "error_message": str(e),
            }

    async def get_eway_bills_by_date(
        self,
        from_date: str,
        to_date: str,
    ) -> Dict[str, Any]:
        """Get E-Way Bills generated in a date range.

        Args:
            from_date: From date (DD/MM/YYYY)
            to_date: To date (DD/MM/YYYY)

        Returns:
            List of E-Way Bills
        """
        logger.info(f"Fetching E-Way Bills from {from_date} to {to_date}")

        headers = self._get_headers()

        try:
            response = await self._client.get(
                f"{self.base_url}/ewayapi/v1.03/ewbv1.03/ewayBill/getEwayBillsByDate",
                headers=headers,
                params={"date": from_date},
            )

            result = response.json()

            if result.get("status") == 1 or result.get("success"):
                data = result.get("data", [])
                if isinstance(data, str):
                    data = self.auth.decrypt_payload(data)
                return {
                    "success": True,
                    "data": data,
                    "raw_response": result,
                }
            else:
                return {
                    "success": False,
                    "error_message": result.get("error", {}).get("message"),
                    "raw_response": result,
                }

        except Exception as e:
            logger.error(f"Error fetching E-Way Bills by date: {e}")
            return {
                "success": False,
                "error_message": str(e),
            }

    # =========================================================================
    # Consolidated E-Way Bill
    # =========================================================================

    async def generate_consolidated_ewb(
        self,
        vehicle_number: str,
        from_place: str,
        from_state_code: str,
        transporter_id: str,
        eway_bill_numbers: List[str],
    ) -> Dict[str, Any]:
        """Generate Consolidated E-Way Bill.

        Args:
            vehicle_number: Vehicle number
            from_place: Starting place
            from_state_code: Starting state code
            transporter_id: Transporter GSTIN
            eway_bill_numbers: List of E-Way Bill numbers to consolidate

        Returns:
            Consolidated E-Way Bill result
        """
        payload = {
            "fromPlace": from_place,
            "fromState": int(from_state_code),
            "vehicleNo": vehicle_number,
            "transMode": "1",
            "TransporterId": transporter_id,
            "tripSheetEwbBills": [{"ewbNo": int(ewb)} for ewb in eway_bill_numbers],
        }

        logger.info(f"Generating Consolidated E-Way Bill for {len(eway_bill_numbers)} bills")
        result = await self._make_request("POST", "/ewayapi/v1.03/ewbv1.03/consolidatedEwayBill", payload)

        if result["success"]:
            response_data = result.get("data", {})
            return {
                "success": True,
                "consolidated_ewb_number": response_data.get("cEwbNo"),
                "consolidated_ewb_date": response_data.get("cEwbDate"),
                "raw_response": result.get("raw_response"),
            }
        else:
            return result

    async def cancel_consolidated_ewb(
        self,
        consolidated_ewb_number: str,
    ) -> Dict[str, Any]:
        """Cancel Consolidated E-Way Bill.

        Args:
            consolidated_ewb_number: Consolidated E-Way Bill number

        Returns:
            Cancellation result
        """
        payload = {
            "cEwbNo": int(consolidated_ewb_number),
        }

        logger.info(f"Cancelling Consolidated E-Way Bill: {consolidated_ewb_number}")
        result = await self._make_request("POST", "/ewayapi/v1.03/ewbv1.03/consolidatedEwayBill/Cancel", payload)

        if result["success"]:
            return {
                "success": True,
                "consolidated_ewb_number": consolidated_ewb_number,
                "raw_response": result.get("raw_response"),
            }
        else:
            return result
