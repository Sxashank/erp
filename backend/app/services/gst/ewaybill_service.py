"""E-Way Bill Service.

Business logic for E-Way Bill generation and management:
- E-Way Bill generation
- Vehicle updates
- Validity extension
- Cancellation
"""

import logging
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.gst.einvoice import (
    EWayBill,
    EWayBillItem,
    EWayBillVehicleUpdate,
    EWayBillStatus,
    EWayBillProvider,
    TransportMode,
    TransactionType,
    SubSupplyType,
)
from app.models.ap_ar.sales_invoice import SalesInvoice
from app.models.gst.gst_registration import GSTRegistration
from app.models.core.integration_config import IntegrationConfig, IntegrationType
from app.integrations.ewaybill import EWayBillClient, EWayBillAuthManager
from app.core.encryption import decrypt_value

logger = logging.getLogger(__name__)


class EWayBillService:
    """Service for E-Way Bill operations."""

    # E-Way Bill threshold (in INR)
    EWAY_BILL_THRESHOLD = Decimal("50000")

    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_integration_config(
        self,
        organization_id: UUID,
    ) -> Optional[IntegrationConfig]:
        """Get E-Way Bill integration configuration."""
        query = select(IntegrationConfig).where(
            and_(
                IntegrationConfig.organization_id == organization_id,
                IntegrationConfig.integration_type == IntegrationType.EWAYBILL,
                IntegrationConfig.is_active == True,
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def _get_ewaybill_client(
        self,
        config: IntegrationConfig,
        gst_registration: GSTRegistration,
    ) -> EWayBillClient:
        """Create E-Way Bill client from config."""
        config_data = config.config_data

        auth_manager = EWayBillAuthManager(
            client_id=config_data.get("client_id"),
            client_secret=decrypt_value(config_data.get("client_secret_encrypted")),
            username=config_data.get("username"),
            password=decrypt_value(config_data.get("password_encrypted")),
            gstin=gst_registration.gstin,
            public_key_pem=config_data.get("public_key"),
            sandbox_mode=config.sandbox_mode,
        )

        return EWayBillClient(auth_manager=auth_manager)

    def check_eway_bill_required(
        self,
        invoice_value: Decimal,
        supply_type: Optional[str] = None,
    ) -> bool:
        """Check if E-Way Bill is required based on value threshold.

        Args:
            invoice_value: Total invoice value
            supply_type: Type of supply

        Returns:
            True if E-Way Bill is required
        """
        # E-Way Bill required for goods movement > Rs. 50,000
        # Some states have different thresholds
        return invoice_value > self.EWAY_BILL_THRESHOLD

    async def generate_eway_bill(
        self,
        organization_id: UUID,
        gst_registration_id: UUID,
        eway_bill_data: Dict[str, Any],
        sales_invoice_id: Optional[UUID] = None,
        created_by: Optional[UUID] = None,
    ) -> EWayBill:
        """Generate E-Way Bill.

        Args:
            organization_id: Organization ID
            gst_registration_id: GST registration ID
            eway_bill_data: E-Way Bill data
            sales_invoice_id: Linked sales invoice (optional)
            created_by: User creating the E-Way Bill

        Returns:
            Created E-Way Bill record
        """
        # Get GST registration
        gst_registration = await self.db.get(GSTRegistration, gst_registration_id)
        if not gst_registration:
            raise ValueError("GST registration not found")

        # Get integration config
        config = await self._get_integration_config(organization_id)
        if not config:
            raise ValueError("E-Way Bill integration not configured")

        # Create E-Way Bill record
        eway_bill = EWayBill(
            organization_id=organization_id,
            gst_registration_id=gst_registration_id,
            sales_invoice_id=sales_invoice_id,
            provider=EWayBillProvider.NIC,
            status=EWayBillStatus.DRAFT,
            document_type=eway_bill_data.get("document_type", "INV"),
            document_number=eway_bill_data.get("document_number"),
            document_date=datetime.strptime(
                eway_bill_data.get("document_date"), "%d/%m/%Y"
            ).date() if isinstance(eway_bill_data.get("document_date"), str) else eway_bill_data.get("document_date"),
            transaction_type=TransactionType(eway_bill_data.get("transaction_type", "1")),
            sub_supply_type=SubSupplyType(eway_bill_data.get("sub_supply_type", "1")),
            supplier_gstin=eway_bill_data.get("from_gstin"),
            supplier_name=eway_bill_data.get("from_trade_name"),
            supplier_address=eway_bill_data.get("from_address1", ""),
            supplier_place=eway_bill_data.get("from_place", ""),
            supplier_pincode=str(eway_bill_data.get("from_pincode", "")),
            supplier_state_code=str(eway_bill_data.get("from_state_code", "")),
            recipient_gstin=eway_bill_data.get("to_gstin"),
            recipient_name=eway_bill_data.get("to_trade_name"),
            recipient_address=eway_bill_data.get("to_address1", ""),
            recipient_place=eway_bill_data.get("to_place", ""),
            recipient_pincode=str(eway_bill_data.get("to_pincode", "")),
            recipient_state_code=str(eway_bill_data.get("to_state_code", "")),
            total_quantity=Decimal(str(sum(
                item.get("quantity", 0) for item in eway_bill_data.get("items", [])
            ))),
            hsn_code=str(eway_bill_data.get("items", [{}])[0].get("hsn_code", "")),
            product_description=eway_bill_data.get("items", [{}])[0].get("product_name", ""),
            taxable_value=Decimal(str(eway_bill_data.get("total_value", 0))),
            cgst_amount=Decimal(str(eway_bill_data.get("cgst_value", 0))),
            sgst_amount=Decimal(str(eway_bill_data.get("sgst_value", 0))),
            igst_amount=Decimal(str(eway_bill_data.get("igst_value", 0))),
            cess_amount=Decimal(str(eway_bill_data.get("cess_value", 0))),
            total_value=Decimal(str(eway_bill_data.get("invoice_value", 0))),
            transport_mode=TransportMode(eway_bill_data.get("transport_mode", "1")),
            transporter_id=eway_bill_data.get("transporter_id"),
            transporter_name=eway_bill_data.get("transporter_name"),
            transport_doc_number=eway_bill_data.get("transport_doc_no"),
            transport_doc_date=datetime.strptime(
                eway_bill_data.get("transport_doc_date"), "%d/%m/%Y"
            ).date() if eway_bill_data.get("transport_doc_date") else None,
            vehicle_number=eway_bill_data.get("vehicle_number"),
            approximate_distance=int(eway_bill_data.get("distance", 0)),
            created_by_user=created_by,
        )
        self.db.add(eway_bill)
        await self.db.flush()

        # Add items
        for idx, item_data in enumerate(eway_bill_data.get("items", []), 1):
            item = EWayBillItem(
                eway_bill_id=eway_bill.id,
                line_number=idx,
                product_name=item_data.get("product_name", ""),
                product_description=item_data.get("product_desc"),
                hsn_code=str(item_data.get("hsn_code", "")),
                quantity=Decimal(str(item_data.get("quantity", 0))),
                unit=item_data.get("unit", "NOS"),
                taxable_value=Decimal(str(item_data.get("taxable_amount", 0))),
                cgst_rate=Decimal(str(item_data.get("cgst_rate", 0))),
                sgst_rate=Decimal(str(item_data.get("sgst_rate", 0))),
                igst_rate=Decimal(str(item_data.get("igst_rate", 0))),
                cess_rate=Decimal(str(item_data.get("cess_rate", 0))),
            )
            self.db.add(item)

        # Store request payload
        eway_bill.request_payload = eway_bill_data

        # Get client and generate
        client = await self._get_ewaybill_client(config, gst_registration)

        try:
            result = await client.generate_eway_bill(eway_bill_data)

            if result["success"]:
                eway_bill.status = EWayBillStatus.GENERATED
                eway_bill.eway_bill_number = str(result["eway_bill_number"])
                eway_bill.eway_bill_date = datetime.fromisoformat(
                    result["eway_bill_date"]
                ) if result.get("eway_bill_date") else datetime.utcnow()
                eway_bill.valid_from = eway_bill.eway_bill_date
                eway_bill.valid_until = datetime.fromisoformat(
                    result["valid_until"]
                ) if result.get("valid_until") else datetime.utcnow() + timedelta(days=1)
                eway_bill.response_payload = result.get("raw_response")

                # Update linked sales invoice
                if sales_invoice_id:
                    invoice = await self.db.get(SalesInvoice, sales_invoice_id)
                    if invoice:
                        invoice.eway_bill_number = eway_bill.eway_bill_number
                        invoice.eway_bill_date = eway_bill.eway_bill_date.date() if isinstance(eway_bill.eway_bill_date, datetime) else eway_bill.eway_bill_date

                logger.info(f"Generated E-Way Bill {eway_bill.eway_bill_number}")

            else:
                eway_bill.status = EWayBillStatus.DRAFT
                eway_bill.error_code = result.get("error_code")
                eway_bill.error_message = result.get("error_message")
                eway_bill.response_payload = result.get("raw_response")

                logger.warning(f"Failed to generate E-Way Bill: {result.get('error_message')}")

        finally:
            await client.close()

        await self.db.commit()
        await self.db.refresh(eway_bill)
        return eway_bill

    async def generate_from_invoice(
        self,
        sales_invoice_id: UUID,
        distance: int,
        transporter_id: Optional[str] = None,
        transporter_name: Optional[str] = None,
        vehicle_number: Optional[str] = None,
        transport_doc_no: Optional[str] = None,
        transport_doc_date: Optional[date] = None,
        created_by: Optional[UUID] = None,
    ) -> EWayBill:
        """Generate E-Way Bill from sales invoice.

        Args:
            sales_invoice_id: Sales invoice ID
            distance: Approximate distance in KM
            transporter_id: Transporter GSTIN
            transporter_name: Transporter name
            vehicle_number: Vehicle registration number
            transport_doc_no: Transport document number
            transport_doc_date: Transport document date
            created_by: User creating

        Returns:
            Created E-Way Bill
        """
        # Get invoice with relations
        invoice_query = select(SalesInvoice).options(
            selectinload(SalesInvoice.lines),
            selectinload(SalesInvoice.customer),
        ).where(SalesInvoice.id == sales_invoice_id)
        invoice_result = await self.db.execute(invoice_query)
        invoice = invoice_result.scalar_one_or_none()

        if not invoice:
            raise ValueError("Sales invoice not found")

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

        customer = invoice.customer

        # Build E-Way Bill data
        eway_bill_data = {
            "supply_type": "O",  # Outward
            "sub_supply_type": "1",  # Supply
            "document_type": "INV",
            "document_number": invoice.invoice_number,
            "document_date": invoice.invoice_date.strftime("%d/%m/%Y"),
            "from_gstin": gst_registration.gstin,
            "from_trade_name": gst_registration.trade_name or gst_registration.legal_name,
            "from_address1": gst_registration.address_line1 or "",
            "from_place": gst_registration.city or "",
            "from_pincode": gst_registration.pincode or "000000",
            "from_state_code": gst_registration.state_code or "",
            "to_gstin": invoice.customer_gstin or "URP",
            "to_trade_name": customer.trade_name if customer else "",
            "to_address1": customer.billing_address_line1 if customer else "",
            "to_place": customer.billing_city if customer else "",
            "to_pincode": customer.billing_pincode if customer else "000000",
            "to_state_code": customer.billing_state_code if customer else "",
            "total_value": float(invoice.taxable_amount),
            "cgst_value": float(invoice.cgst_amount),
            "sgst_value": float(invoice.sgst_amount),
            "igst_value": float(invoice.igst_amount),
            "cess_value": float(invoice.cess_amount),
            "invoice_value": float(invoice.total_amount),
            "transport_mode": "1",  # Road
            "distance": distance,
            "transporter_id": transporter_id or "",
            "transporter_name": transporter_name or invoice.transporter_name or "",
            "transport_doc_no": transport_doc_no or "",
            "transport_doc_date": transport_doc_date.strftime("%d/%m/%Y") if transport_doc_date else "",
            "vehicle_number": vehicle_number or invoice.vehicle_number or "",
            "items": [],
        }

        # Add items
        for line in invoice.lines:
            eway_bill_data["items"].append({
                "product_name": line.description[:100],
                "product_desc": line.description,
                "hsn_code": line.hsn_sac_code or "",
                "quantity": float(line.quantity),
                "unit": "NOS",
                "taxable_amount": float(line.taxable_amount),
                "cgst_rate": float(line.cgst_rate),
                "sgst_rate": float(line.sgst_rate),
                "igst_rate": float(line.igst_rate),
                "cess_rate": float(line.cess_rate),
            })

        return await self.generate_eway_bill(
            organization_id=invoice.organization_id,
            gst_registration_id=gst_registration.id,
            eway_bill_data=eway_bill_data,
            sales_invoice_id=sales_invoice_id,
            created_by=created_by,
        )

    async def cancel_eway_bill(
        self,
        eway_bill_id: UUID,
        cancel_reason: str,
        cancel_remarks: str,
        cancelled_by: UUID,
    ) -> EWayBill:
        """Cancel E-Way Bill.

        Args:
            eway_bill_id: E-Way Bill ID
            cancel_reason: Reason code (1-5)
            cancel_remarks: Cancellation remarks
            cancelled_by: User cancelling

        Returns:
            Updated E-Way Bill
        """
        eway_bill = await self.db.get(EWayBill, eway_bill_id)
        if not eway_bill:
            raise ValueError("E-Way Bill not found")

        if eway_bill.status not in [EWayBillStatus.GENERATED, EWayBillStatus.ACTIVE]:
            raise ValueError("E-Way Bill cannot be cancelled")

        if eway_bill.is_cancelled:
            raise ValueError("E-Way Bill already cancelled")

        # Get config
        config = await self._get_integration_config(eway_bill.organization_id)
        if not config:
            raise ValueError("E-Way Bill integration not configured")

        # Get GST registration
        gst_registration = await self.db.get(GSTRegistration, eway_bill.gst_registration_id)

        # Get client
        client = await self._get_ewaybill_client(config, gst_registration)

        try:
            result = await client.cancel_eway_bill(
                eway_bill_number=eway_bill.eway_bill_number,
                cancel_reason=cancel_reason,
                cancel_remarks=cancel_remarks,
            )

            if result["success"]:
                eway_bill.is_cancelled = True
                eway_bill.cancel_reason_code = cancel_reason
                eway_bill.cancel_remarks = cancel_remarks
                eway_bill.cancelled_at = datetime.utcnow()
                eway_bill.cancelled_by = cancelled_by
                eway_bill.status = EWayBillStatus.CANCELLED

                logger.info(f"Cancelled E-Way Bill {eway_bill.eway_bill_number}")

            else:
                raise ValueError(f"Failed to cancel: {result.get('error_message')}")

        finally:
            await client.close()

        await self.db.commit()
        await self.db.refresh(eway_bill)
        return eway_bill

    async def update_vehicle(
        self,
        eway_bill_id: UUID,
        vehicle_number: str,
        from_place: str,
        from_state_code: str,
        reason_code: str = "1",
        reason_remarks: str = "",
        updated_by: Optional[UUID] = None,
    ) -> EWayBill:
        """Update vehicle details (Part B).

        Args:
            eway_bill_id: E-Way Bill ID
            vehicle_number: New vehicle number
            from_place: Current location
            from_state_code: Current state code
            reason_code: Reason for update
            reason_remarks: Remarks
            updated_by: User updating

        Returns:
            Updated E-Way Bill
        """
        eway_bill = await self.db.get(EWayBill, eway_bill_id)
        if not eway_bill:
            raise ValueError("E-Way Bill not found")

        if eway_bill.status not in [EWayBillStatus.GENERATED, EWayBillStatus.ACTIVE]:
            raise ValueError("E-Way Bill not in valid state for vehicle update")

        # Get config and client
        config = await self._get_integration_config(eway_bill.organization_id)
        if not config:
            raise ValueError("E-Way Bill integration not configured")

        gst_registration = await self.db.get(GSTRegistration, eway_bill.gst_registration_id)
        client = await self._get_ewaybill_client(config, gst_registration)

        try:
            result = await client.update_vehicle(
                eway_bill_number=eway_bill.eway_bill_number,
                vehicle_number=vehicle_number,
                from_place=from_place,
                from_state_code=from_state_code,
                reason_code=reason_code,
                reason_remarks=reason_remarks,
            )

            if result["success"]:
                # Record vehicle update
                vehicle_update = EWayBillVehicleUpdate(
                    eway_bill_id=eway_bill.id,
                    update_type="VEHICLE_CHANGE",
                    previous_vehicle_number=eway_bill.vehicle_number,
                    new_vehicle_number=vehicle_number,
                    from_place=from_place,
                    from_state_code=from_state_code,
                    reason=reason_remarks,
                    new_valid_until=datetime.fromisoformat(result["valid_until"]) if result.get("valid_until") else None,
                    response_payload=result.get("raw_response"),
                    updated_by_user=updated_by,
                )
                self.db.add(vehicle_update)

                # Update E-Way Bill
                eway_bill.vehicle_number = vehicle_number
                eway_bill.status = EWayBillStatus.ACTIVE
                if result.get("valid_until"):
                    eway_bill.valid_until = datetime.fromisoformat(result["valid_until"])

                logger.info(f"Updated vehicle for E-Way Bill {eway_bill.eway_bill_number}")

            else:
                raise ValueError(f"Failed to update: {result.get('error_message')}")

        finally:
            await client.close()

        await self.db.commit()
        await self.db.refresh(eway_bill)
        return eway_bill

    async def extend_validity(
        self,
        eway_bill_id: UUID,
        remaining_distance: int,
        extend_reason: str,
        from_place: str,
        from_state_code: str,
        extended_by: Optional[UUID] = None,
    ) -> EWayBill:
        """Extend E-Way Bill validity.

        Args:
            eway_bill_id: E-Way Bill ID
            remaining_distance: Remaining distance in KM
            extend_reason: Reason for extension
            from_place: Current location
            from_state_code: Current state code
            extended_by: User extending

        Returns:
            Updated E-Way Bill
        """
        eway_bill = await self.db.get(EWayBill, eway_bill_id)
        if not eway_bill:
            raise ValueError("E-Way Bill not found")

        if eway_bill.status not in [EWayBillStatus.GENERATED, EWayBillStatus.ACTIVE]:
            raise ValueError("E-Way Bill not in valid state for extension")

        # Get config and client
        config = await self._get_integration_config(eway_bill.organization_id)
        if not config:
            raise ValueError("E-Way Bill integration not configured")

        gst_registration = await self.db.get(GSTRegistration, eway_bill.gst_registration_id)
        client = await self._get_ewaybill_client(config, gst_registration)

        try:
            result = await client.extend_validity(
                eway_bill_number=eway_bill.eway_bill_number,
                vehicle_number=eway_bill.vehicle_number or "",
                from_place=from_place,
                from_state_code=from_state_code,
                remaining_distance=remaining_distance,
                extend_reason=extend_reason,
            )

            if result["success"]:
                # Record extension
                vehicle_update = EWayBillVehicleUpdate(
                    eway_bill_id=eway_bill.id,
                    update_type="EXTENSION",
                    previous_valid_until=eway_bill.valid_until,
                    new_valid_until=datetime.fromisoformat(result["valid_until"]) if result.get("valid_until") else None,
                    from_place=from_place,
                    from_state_code=from_state_code,
                    reason=extend_reason,
                    response_payload=result.get("raw_response"),
                    updated_by_user=extended_by,
                )
                self.db.add(vehicle_update)

                # Update E-Way Bill
                eway_bill.status = EWayBillStatus.EXTENDED
                eway_bill.extension_count += 1
                eway_bill.last_extended_at = datetime.utcnow()
                if result.get("valid_until"):
                    eway_bill.valid_until = datetime.fromisoformat(result["valid_until"])

                logger.info(f"Extended E-Way Bill {eway_bill.eway_bill_number}")

            else:
                raise ValueError(f"Failed to extend: {result.get('error_message')}")

        finally:
            await client.close()

        await self.db.commit()
        await self.db.refresh(eway_bill)
        return eway_bill

    async def get_eway_bill(
        self,
        eway_bill_id: UUID,
    ) -> Optional[EWayBill]:
        """Get E-Way Bill by ID."""
        query = select(EWayBill).options(
            selectinload(EWayBill.items),
            selectinload(EWayBill.vehicle_updates),
        ).where(EWayBill.id == eway_bill_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_eway_bills(
        self,
        organization_id: UUID,
        status: Optional[EWayBillStatus] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        expiring_soon: bool = False,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[EWayBill], int]:
        """List E-Way Bills with filtering."""
        query = select(EWayBill).where(
            EWayBill.organization_id == organization_id
        )

        if status:
            query = query.where(EWayBill.status == status)
        if from_date:
            query = query.where(EWayBill.eway_bill_date >= datetime.combine(from_date, datetime.min.time()))
        if to_date:
            query = query.where(EWayBill.eway_bill_date <= datetime.combine(to_date, datetime.max.time()))
        if expiring_soon:
            # Expiring within 8 hours
            soon = datetime.utcnow() + timedelta(hours=8)
            query = query.where(
                and_(
                    EWayBill.valid_until <= soon,
                    EWayBill.valid_until > datetime.utcnow(),
                    EWayBill.status.in_([EWayBillStatus.GENERATED, EWayBillStatus.ACTIVE]),
                )
            )

        # Count
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Paginate
        query = query.order_by(EWayBill.eway_bill_date.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def get_statistics(
        self,
        organization_id: UUID,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """Get E-Way Bill statistics."""
        query = select(EWayBill).where(
            EWayBill.organization_id == organization_id
        )

        if from_date:
            query = query.where(EWayBill.eway_bill_date >= datetime.combine(from_date, datetime.min.time()))
        if to_date:
            query = query.where(EWayBill.eway_bill_date <= datetime.combine(to_date, datetime.max.time()))

        result = await self.db.execute(query)
        eway_bills = list(result.scalars().all())

        now = datetime.utcnow()

        return {
            "total": len(eway_bills),
            "active": sum(1 for e in eway_bills if e.status in [EWayBillStatus.GENERATED, EWayBillStatus.ACTIVE] and e.valid_until and e.valid_until > now),
            "expired": sum(1 for e in eway_bills if e.valid_until and e.valid_until <= now),
            "cancelled": sum(1 for e in eway_bills if e.status == EWayBillStatus.CANCELLED),
            "extended": sum(1 for e in eway_bills if e.extension_count > 0),
            "expiring_soon": sum(1 for e in eway_bills if e.valid_until and now < e.valid_until <= now + timedelta(hours=8)),
            "total_value": sum(e.total_value for e in eway_bills),
        }
