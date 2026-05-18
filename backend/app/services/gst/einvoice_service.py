"""E-Invoice Service.

Business logic for E-Invoice generation and management:
- IRN generation via IRP
- E-Invoice cancellation
- QR code handling
- Integration with Sales Invoice
"""

import logging
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.gst.einvoice import (
    EInvoiceRequest,
    EInvoiceRequestStatus,
    EInvoiceProvider,
)
from app.models.ap_ar.sales_invoice import SalesInvoice, EInvoiceStatus
from app.models.gst.gst_registration import GSTRegistration
from app.models.core.integration_config import IntegrationConfig, IntegrationType
from app.integrations.einvoice import EInvoiceClient, EInvoiceAuthManager
from app.core.encryption import decrypt_value

logger = logging.getLogger(__name__)


class EInvoiceService:
    """Service for E-Invoice operations."""

    # Turnover threshold for E-Invoice applicability (in INR)
    EINVOICE_THRESHOLD = Decimal("5_00_00_000")  # 5 Crores

    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_integration_config(
        self,
        organization_id: UUID,
    ) -> Optional[IntegrationConfig]:
        """Get E-Invoice integration configuration."""
        query = select(IntegrationConfig).where(
            and_(
                IntegrationConfig.organization_id == organization_id,
                IntegrationConfig.integration_type == IntegrationType.EINVOICE,
                IntegrationConfig.is_active == True,
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def _get_einvoice_client(
        self,
        config: IntegrationConfig,
        gst_registration: GSTRegistration,
    ) -> EInvoiceClient:
        """Create E-Invoice client from config."""
        config_data = config.config_data

        auth_manager = EInvoiceAuthManager(
            client_id=config_data.get("client_id"),
            client_secret=decrypt_value(config_data.get("client_secret_encrypted")),
            username=config_data.get("username"),
            password=decrypt_value(config_data.get("password_encrypted")),
            gstin=gst_registration.gstin,
            public_key_pem=config_data.get("public_key"),
            sandbox_mode=config.sandbox_mode,
            provider=config_data.get("provider", "NIC"),
        )

        return EInvoiceClient(auth_manager=auth_manager)

    @staticmethod
    def _split_address(address: Optional[str]) -> Tuple[str, str]:
        """Split the single GST registration address field for IRP payloads."""
        if not address:
            return "", ""
        first, _, rest = address.partition("\n")
        if rest:
            return first[:100], rest.replace("\n", ", ")[:100]
        if len(address) <= 100:
            return address, ""
        return address[:100], address[100:200]

    @staticmethod
    def _clean_pincode(value: Optional[str]) -> str:
        if value and value.isdigit() and len(value) == 6:
            return value
        return "999999"

    @staticmethod
    def _customer_name(customer: Any) -> str:
        if not customer:
            return ""
        return customer.display_name or customer.name

    def _build_invoice_data(
        self,
        invoice: SalesInvoice,
        gst_registration: GSTRegistration,
    ) -> Dict[str, Any]:
        """Build E-Invoice payload from sales invoice."""
        # Determine supply type
        if invoice.supply_type:
            supply_type_map = {
                "INTRA_STATE": "B2B",
                "INTER_STATE": "B2B",
                "EXPORT": "EXPWP",
                "SEZ": "SEZWP",
            }
            supply_type = supply_type_map.get(invoice.supply_type.value, "B2B")
        else:
            supply_type = "B2B"

        # Build seller details from GST registration
        seller_address1, seller_address2 = self._split_address(gst_registration.address)
        seller_data = {
            "seller_gstin": gst_registration.gstin,
            "seller_name": gst_registration.legal_name or gst_registration.trade_name,
            "seller_trade_name": gst_registration.trade_name,
            "seller_address1": seller_address1,
            "seller_address2": seller_address2,
            "seller_location": gst_registration.state_name,
            "seller_pincode": self._clean_pincode(gst_registration.pincode),
            "seller_state_code": gst_registration.state_code or "",
            "seller_phone": "",
            "seller_email": "",
        }

        # Build buyer details from customer
        customer = invoice.customer
        buyer_data = {
            "buyer_gstin": invoice.customer_gstin or "URP",
            "buyer_name": self._customer_name(customer),
            "buyer_trade_name": customer.display_name if customer else "",
            "buyer_address1": customer.billing_address_line1 if customer else "",
            "buyer_address2": customer.billing_address_line2 if customer else "",
            "buyer_location": customer.billing_city if customer else "",
            "buyer_pincode": self._clean_pincode(customer.billing_pincode if customer else None),
            "buyer_state_code": customer.billing_state_code if customer else "",
            "place_of_supply": invoice.place_of_supply or "",
            "buyer_phone": customer.phone if customer else "",
            "buyer_email": customer.email if customer else "",
        }

        # Build items
        items = []
        for line in invoice.lines:
            items.append({
                "description": line.description,
                "is_service": line.hsn_sac_code and line.hsn_sac_code.startswith("99"),
                "hsn_code": line.hsn_sac_code or "",
                "quantity": line.quantity,
                "unit": "NOS",  # Default unit
                "unit_price": line.unit_price,
                "total_amount": line.quantity * line.unit_price,
                "discount": line.discount_amount,
                "taxable_amount": line.taxable_amount,
                "gst_rate": line.cgst_rate + line.sgst_rate + line.igst_rate,
                "igst_amount": line.igst_amount,
                "cgst_amount": line.cgst_amount,
                "sgst_amount": line.sgst_amount,
                "cess_rate": line.cess_rate,
                "cess_amount": line.cess_amount,
                "line_total": line.total_amount,
            })

        return {
            "supply_type": supply_type,
            "reverse_charge": invoice.is_reverse_charge,
            "document_type": "INV",
            "invoice_number": invoice.invoice_number,
            "invoice_date": invoice.invoice_date.strftime("%d/%m/%Y"),
            **seller_data,
            **buyer_data,
            "items": items,
            "taxable_value": invoice.taxable_amount,
            "cgst_amount": invoice.cgst_amount,
            "sgst_amount": invoice.sgst_amount,
            "igst_amount": invoice.igst_amount,
            "cess_amount": invoice.cess_amount,
            "discount_amount": invoice.discount_amount,
            "round_off": invoice.round_off,
            "total_amount": invoice.total_amount,
            # E-Way Bill details
            "generate_eway_bill": bool(
                invoice.transporter_name or invoice.vehicle_number
            ),
            "transporter_name": invoice.transporter_name,
            "vehicle_number": invoice.vehicle_number,
            "distance": 0,  # Default, should be provided
            "transport_mode": "1",  # Road
        }

    async def check_einvoice_applicable(
        self,
        organization_id: UUID,
        invoice_date: date,
    ) -> bool:
        """Check if E-Invoice is applicable for organization.

        Based on aggregate turnover threshold.
        """
        # In production, this would check:
        # 1. Organization's aggregate turnover
        # 2. Invoice date vs E-Invoice mandate date
        # 3. Exclusions (SEZ, etc.)

        # For now, return based on config
        config = await self._get_integration_config(organization_id)
        return config is not None and config.is_active

    async def generate_einvoice(
        self,
        sales_invoice_id: UUID,
        initiated_by: UUID,
    ) -> EInvoiceRequest:
        """Generate E-Invoice for a sales invoice.

        Args:
            sales_invoice_id: Sales invoice ID
            initiated_by: User initiating the request

        Returns:
            E-Invoice request record
        """
        # Get sales invoice
        invoice_query = select(SalesInvoice).options(
            selectinload(SalesInvoice.lines),
            selectinload(SalesInvoice.customer),
        ).where(SalesInvoice.id == sales_invoice_id)
        invoice_result = await self.db.execute(invoice_query)
        invoice = invoice_result.scalar_one_or_none()

        if not invoice:
            raise ValueError("Sales invoice not found")

        if invoice.e_invoice_status == EInvoiceStatus.GENERATED:
            raise ValueError("E-Invoice already generated for this invoice")

        # Get GST registration
        gst_reg_query = select(GSTRegistration).where(
            and_(
                GSTRegistration.organization_id == invoice.organization_id,
                GSTRegistration.is_active == True,
            )
        )
        gst_reg_result = await self.db.execute(gst_reg_query)
        gst_registration = gst_reg_result.scalar_one_or_none()

        if not gst_registration:
            raise ValueError("GST registration not found")

        # Get integration config
        config = await self._get_integration_config(invoice.organization_id)
        if not config:
            raise ValueError("E-Invoice integration not configured")

        # Create request record
        einvoice_request = EInvoiceRequest(
            organization_id=invoice.organization_id,
            gst_registration_id=gst_registration.id,
            sales_invoice_id=sales_invoice_id,
            provider=EInvoiceProvider(config.config_data.get("provider", "NIC")),
            status=EInvoiceRequestStatus.PROCESSING,
            initiated_by=initiated_by,
        )
        self.db.add(einvoice_request)
        await self.db.flush()

        # Build invoice data
        invoice_data = self._build_invoice_data(invoice, gst_registration)

        # Store request payload
        einvoice_request.request_payload = invoice_data

        # Get client and generate IRN
        client = await self._get_einvoice_client(config, gst_registration)

        try:
            result = await client.generate_irn(invoice_data)

            if result["success"]:
                # Update request with success
                einvoice_request.status = EInvoiceRequestStatus.SUCCESS
                einvoice_request.irn = result["irn"]
                einvoice_request.ack_number = result["ack_number"]
                einvoice_request.ack_date = datetime.fromisoformat(
                    result["ack_date"]
                ) if result.get("ack_date") else None
                einvoice_request.signed_invoice = result.get("signed_invoice")
                einvoice_request.signed_qr_code = result.get("signed_qr_code")
                einvoice_request.response_payload = result.get("raw_response")

                # Update if E-Way Bill was auto-generated
                if result.get("eway_bill_number"):
                    einvoice_request.eway_bill_auto_generated = True
                    einvoice_request.eway_bill_number = result["eway_bill_number"]
                    einvoice_request.eway_bill_date = datetime.fromisoformat(
                        result["eway_bill_date"]
                    ) if result.get("eway_bill_date") else None
                    einvoice_request.eway_bill_validity = datetime.fromisoformat(
                        result["eway_bill_validity"]
                    ) if result.get("eway_bill_validity") else None

                # Update sales invoice
                invoice.e_invoice_status = EInvoiceStatus.GENERATED
                invoice.irn = result["irn"]
                invoice.irn_date = einvoice_request.ack_date
                invoice.qr_code = result.get("signed_qr_code")
                invoice.ack_number = result["ack_number"]
                invoice.ack_date = einvoice_request.ack_date

                if result.get("eway_bill_number"):
                    invoice.eway_bill_number = result["eway_bill_number"]
                    invoice.eway_bill_date = einvoice_request.eway_bill_date

                logger.info(f"Generated IRN {result['irn']} for invoice {invoice.invoice_number}")

            else:
                # Update request with failure
                einvoice_request.status = EInvoiceRequestStatus.FAILED
                einvoice_request.error_code = result.get("error_code")
                einvoice_request.error_message = result.get("error_message")
                einvoice_request.error_details = result.get("error_details")
                einvoice_request.response_payload = result.get("raw_response")
                einvoice_request.retry_count += 1

                invoice.e_invoice_status = EInvoiceStatus.PENDING

                logger.warning(f"Failed to generate IRN for invoice {invoice.invoice_number}: {result.get('error_message')}")

        finally:
            await client.close()

        await self.db.flush()
        await self.db.refresh(einvoice_request)
        return einvoice_request

    async def cancel_einvoice(
        self,
        einvoice_request_id: UUID,
        cancel_reason: str,
        cancel_remarks: str,
        cancelled_by: UUID,
    ) -> EInvoiceRequest:
        """Cancel an E-Invoice.

        Args:
            einvoice_request_id: E-Invoice request ID
            cancel_reason: Reason code (1-4)
            cancel_remarks: Cancellation remarks
            cancelled_by: User cancelling

        Returns:
            Updated E-Invoice request
        """
        # Get request
        request = await self.db.get(EInvoiceRequest, einvoice_request_id)
        if not request:
            raise ValueError("E-Invoice request not found")

        if request.status != EInvoiceRequestStatus.SUCCESS:
            raise ValueError("Only successful E-Invoices can be cancelled")

        if request.is_cancelled:
            raise ValueError("E-Invoice already cancelled")

        # Get config
        config = await self._get_integration_config(request.organization_id)
        if not config:
            raise ValueError("E-Invoice integration not configured")

        # Get GST registration
        gst_registration = await self.db.get(GSTRegistration, request.gst_registration_id)

        # Get client
        client = await self._get_einvoice_client(config, gst_registration)

        try:
            result = await client.cancel_irn(
                irn=request.irn,
                cancel_reason=cancel_reason,
                cancel_remarks=cancel_remarks,
            )

            if result["success"]:
                request.is_cancelled = True
                request.cancel_reason = cancel_reason
                request.cancel_remarks = cancel_remarks
                request.cancelled_at = datetime.utcnow()
                request.cancelled_by = cancelled_by
                request.status = EInvoiceRequestStatus.CANCELLED

                # Update sales invoice
                invoice = await self.db.get(SalesInvoice, request.sales_invoice_id)
                if invoice:
                    invoice.e_invoice_status = EInvoiceStatus.CANCELLED

                logger.info(f"Cancelled IRN {request.irn}")

            else:
                raise ValueError(f"Failed to cancel: {result.get('error_message')}")

        finally:
            await client.close()

        await self.db.flush()
        await self.db.refresh(request)
        return request

    async def get_einvoice_request(
        self,
        request_id: UUID,
    ) -> Optional[EInvoiceRequest]:
        """Get E-Invoice request by ID."""
        return await self.db.get(EInvoiceRequest, request_id)

    async def get_einvoice_by_invoice(
        self,
        sales_invoice_id: UUID,
    ) -> Optional[EInvoiceRequest]:
        """Get E-Invoice request by sales invoice ID."""
        query = select(EInvoiceRequest).where(
            and_(
                EInvoiceRequest.sales_invoice_id == sales_invoice_id,
                EInvoiceRequest.status == EInvoiceRequestStatus.SUCCESS,
            )
        ).order_by(EInvoiceRequest.created_at.desc())
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_einvoice_requests(
        self,
        organization_id: UUID,
        status: Optional[EInvoiceRequestStatus] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[EInvoiceRequest], int]:
        """List E-Invoice requests with filtering."""
        query = select(EInvoiceRequest).where(
            EInvoiceRequest.organization_id == organization_id
        )

        if status:
            query = query.where(EInvoiceRequest.status == status)
        if from_date:
            query = query.where(EInvoiceRequest.request_time >= datetime.combine(from_date, datetime.min.time()))
        if to_date:
            query = query.where(EInvoiceRequest.request_time <= datetime.combine(to_date, datetime.max.time()))

        # Count
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Paginate
        query = query.order_by(EInvoiceRequest.request_time.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def retry_failed_einvoice(
        self,
        request_id: UUID,
        initiated_by: UUID,
    ) -> EInvoiceRequest:
        """Retry a failed E-Invoice generation.

        Args:
            request_id: Failed E-Invoice request ID
            initiated_by: User retrying

        Returns:
            New E-Invoice request
        """
        # Get original request
        original = await self.db.get(EInvoiceRequest, request_id)
        if not original:
            raise ValueError("E-Invoice request not found")

        if original.status != EInvoiceRequestStatus.FAILED:
            raise ValueError("Only failed requests can be retried")

        # Generate new E-Invoice
        return await self.generate_einvoice(
            sales_invoice_id=original.sales_invoice_id,
            initiated_by=initiated_by,
        )

    async def get_statistics(
        self,
        organization_id: UUID,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """Get E-Invoice statistics."""
        query = select(EInvoiceRequest).where(
            EInvoiceRequest.organization_id == organization_id
        )

        if from_date:
            query = query.where(EInvoiceRequest.request_time >= datetime.combine(from_date, datetime.min.time()))
        if to_date:
            query = query.where(EInvoiceRequest.request_time <= datetime.combine(to_date, datetime.max.time()))

        result = await self.db.execute(query)
        requests = list(result.scalars().all())

        return {
            "total_requests": len(requests),
            "successful": sum(1 for r in requests if r.status == EInvoiceRequestStatus.SUCCESS),
            "failed": sum(1 for r in requests if r.status == EInvoiceRequestStatus.FAILED),
            "cancelled": sum(1 for r in requests if r.status == EInvoiceRequestStatus.CANCELLED),
            "pending": sum(1 for r in requests if r.status in [EInvoiceRequestStatus.PENDING, EInvoiceRequestStatus.PROCESSING]),
            "with_eway_bill": sum(1 for r in requests if r.eway_bill_auto_generated),
        }
