"""Vendor Invoice Service with Matching Engine."""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    NotFoundException,
    ConflictException,
    ValidationException,
)
from app.repositories.vendor_portal.invoice_repo import (
    VendorInvoiceRepository,
    VendorInvoiceLineRepository,
    VendorInvoiceDocumentRepository,
)
from app.models.vendor_portal.invoice import (
    VendorInvoice,
    VendorInvoiceLine,
    VendorInvoiceDocument,
)
from app.models.vendor_portal.enums import (
    VendorInvoiceStatus,
    InvoiceMatchingType,
    InvoiceMatchingStatus,
    InvoiceDocumentType,
)
from app.schemas.vendor_portal.invoice import (
    VendorInvoiceCreate,
    VendorInvoiceUpdate,
    VendorInvoiceLineCreate,
    VendorInvoiceDocumentCreate,
    InvoiceMatchingResult,
)


class VendorInvoiceService:
    """Service for vendor invoice operations with matching engine."""

    # Default tolerance percentages
    DEFAULT_PRICE_TOLERANCE = Decimal("1.0")  # 1%
    DEFAULT_QUANTITY_TOLERANCE = Decimal("5.0")  # 5%

    def __init__(self, session: AsyncSession):
        self.session = session
        self.invoice_repo = VendorInvoiceRepository(session)
        self.line_repo = VendorInvoiceLineRepository(session)
        self.doc_repo = VendorInvoiceDocumentRepository(session)

    async def create_invoice(
        self,
        vendor_id: UUID,
        organization_id: UUID,
        submitted_by_id: UUID,
        data: VendorInvoiceCreate,
    ) -> VendorInvoice:
        """Create a new invoice draft."""
        # Check for duplicate invoice number
        existing = await self.invoice_repo.get_by_invoice_number(
            vendor_id, data.invoice_number
        )
        if existing:
            raise ConflictException(
                f"Invoice {data.invoice_number} already exists"
            )

        # Calculate GST type (IGST vs CGST+SGST)
        is_igst = self._is_igst_applicable(
            data.vendor_gstin, data.place_of_supply, organization_id
        )

        # Create invoice
        invoice_data = data.model_dump(exclude={"lines"})
        invoice_data.update({
            "vendor_id": vendor_id,
            "organization_id": organization_id,
            "submitted_by_id": submitted_by_id,
            "status": VendorInvoiceStatus.DRAFT,
            "is_igst_applicable": is_igst,
            "price_tolerance": self.DEFAULT_PRICE_TOLERANCE,
            "quantity_tolerance": self.DEFAULT_QUANTITY_TOLERANCE,
        })

        invoice = await self.invoice_repo.create(invoice_data)

        # Add lines
        for line_data in data.lines:
            await self._add_invoice_line(invoice.id, line_data, is_igst)

        # Recalculate totals
        await self._recalculate_invoice_totals(invoice)

        await self.session.flush()
        return await self.invoice_repo.get_with_details(invoice.id)

    async def update_invoice(
        self,
        id: UUID,
        data: VendorInvoiceUpdate,
    ) -> VendorInvoice:
        """Update an invoice draft."""
        invoice = await self.invoice_repo.get(id)
        if not invoice:
            raise NotFoundException("Invoice not found")

        if invoice.status != VendorInvoiceStatus.DRAFT:
            raise ValidationException("Only draft invoices can be updated")

        update_data = data.model_dump(exclude_unset=True)
        invoice = await self.invoice_repo.update(invoice, update_data)

        await self.session.flush()
        return await self.invoice_repo.get_with_details(id)

    async def add_line(
        self,
        invoice_id: UUID,
        data: VendorInvoiceLineCreate,
    ) -> VendorInvoiceLine:
        """Add a line item to invoice."""
        invoice = await self.invoice_repo.get(invoice_id)
        if not invoice:
            raise NotFoundException("Invoice not found")

        if invoice.status != VendorInvoiceStatus.DRAFT:
            raise ValidationException("Only draft invoices can be modified")

        line = await self._add_invoice_line(
            invoice_id, data, invoice.is_igst_applicable
        )

        # Recalculate totals
        await self._recalculate_invoice_totals(invoice)

        await self.session.flush()
        return line

    async def validate_invoice(
        self,
        id: UUID,
    ) -> InvoiceMatchingResult:
        """Validate invoice using matching engine."""
        invoice = await self.invoice_repo.get_with_details(id)
        if not invoice:
            raise NotFoundException("Invoice not found")

        matching_result = await self._perform_matching(invoice)

        # Update invoice matching status
        invoice.matching_status = matching_result.matching_status
        invoice.po_matched = matching_result.po_matched
        invoice.grn_matched = matching_result.grn_matched
        invoice.matching_remarks = matching_result.message
        invoice.matching_exceptions = matching_result.exceptions

        await self.session.flush()

        return matching_result

    async def submit_invoice(
        self,
        id: UUID,
    ) -> VendorInvoice:
        """Submit invoice for approval."""
        invoice = await self.invoice_repo.get_with_details(id)
        if not invoice:
            raise NotFoundException("Invoice not found")

        if invoice.status != VendorInvoiceStatus.DRAFT:
            raise ValidationException("Only draft invoices can be submitted")

        # Validate required documents
        if not invoice.documents:
            raise ValidationException("At least one document is required")

        has_invoice_doc = any(
            d.document_type == InvoiceDocumentType.INVOICE_PDF
            for d in invoice.documents
        )
        if not has_invoice_doc:
            raise ValidationException("Invoice PDF is required")

        # Perform matching
        matching_result = await self._perform_matching(invoice)

        # Update invoice
        invoice.status = VendorInvoiceStatus.SUBMITTED
        invoice.submitted_at = datetime.utcnow()
        invoice.matching_status = matching_result.matching_status
        invoice.po_matched = matching_result.po_matched
        invoice.grn_matched = matching_result.grn_matched
        invoice.matching_remarks = matching_result.message
        invoice.matching_exceptions = matching_result.exceptions

        # Set status based on matching result
        if matching_result.matching_status == InvoiceMatchingStatus.MATCHED:
            invoice.status = VendorInvoiceStatus.MATCHED
        elif matching_result.matching_status == InvoiceMatchingStatus.MISMATCH:
            invoice.status = VendorInvoiceStatus.EXCEPTION

        await self.session.flush()

        return invoice

    async def approve_invoice(
        self,
        id: UUID,
        approved_by: UUID,
        remarks: Optional[str] = None,
    ) -> VendorInvoice:
        """Approve an invoice."""
        invoice = await self.invoice_repo.get(id)
        if not invoice:
            raise NotFoundException("Invoice not found")

        if invoice.status not in [
            VendorInvoiceStatus.SUBMITTED,
            VendorInvoiceStatus.MATCHED,
            VendorInvoiceStatus.EXCEPTION,
        ]:
            raise ValidationException("Invoice cannot be approved in current status")

        invoice.status = VendorInvoiceStatus.APPROVED
        invoice.approved_by_id = approved_by
        invoice.approved_at = datetime.utcnow()
        invoice.approval_remarks = remarks
        invoice.balance_amount = invoice.payable_amount

        # TODO: Create purchase bill from approved invoice

        await self.session.flush()

        return invoice

    async def reject_invoice(
        self,
        id: UUID,
        rejected_by: UUID,
        reason: str,
    ) -> VendorInvoice:
        """Reject an invoice."""
        invoice = await self.invoice_repo.get(id)
        if not invoice:
            raise NotFoundException("Invoice not found")

        if invoice.status not in [
            VendorInvoiceStatus.SUBMITTED,
            VendorInvoiceStatus.MATCHED,
            VendorInvoiceStatus.EXCEPTION,
        ]:
            raise ValidationException("Invoice cannot be rejected in current status")

        invoice.status = VendorInvoiceStatus.REJECTED
        invoice.rejected_by_id = rejected_by
        invoice.rejected_at = datetime.utcnow()
        invoice.rejection_reason = reason

        await self.session.flush()

        # TODO: Send rejection notification to vendor

        return invoice

    async def get_invoice(self, id: UUID) -> VendorInvoice:
        """Get invoice by ID."""
        invoice = await self.invoice_repo.get_with_details(id)
        if not invoice:
            raise NotFoundException("Invoice not found")
        return invoice

    async def get_vendor_invoices(
        self,
        vendor_id: UUID,
        skip: int = 0,
        limit: int = 100,
        status: Optional[VendorInvoiceStatus] = None,
    ) -> Tuple[List[VendorInvoice], int]:
        """Get all invoices for a vendor."""
        return await self.invoice_repo.get_all_by_vendor(
            vendor_id, skip, limit, status
        )

    async def add_document(
        self,
        invoice_id: UUID,
        data: VendorInvoiceDocumentCreate,
        file_path: str,
        file_size: int,
        mime_type: str,
        original_filename: str,
    ) -> VendorInvoiceDocument:
        """Add document to invoice."""
        invoice = await self.invoice_repo.get(invoice_id)
        if not invoice:
            raise NotFoundException("Invoice not found")

        if invoice.status != VendorInvoiceStatus.DRAFT:
            raise ValidationException("Cannot add documents to non-draft invoice")

        doc_data = {
            "invoice_id": invoice_id,
            "document_type": data.document_type,
            "document_name": data.document_name,
            "document_number": data.document_number,
            "document_date": data.document_date,
            "file_path": file_path,
            "file_size": file_size,
            "mime_type": mime_type,
            "original_filename": original_filename,
        }

        document = await self.doc_repo.create(doc_data)
        await self.session.flush()

        return document

    # Private helper methods
    async def _add_invoice_line(
        self,
        invoice_id: UUID,
        data: VendorInvoiceLineCreate,
        is_igst: bool,
    ) -> VendorInvoiceLine:
        """Add a line item to invoice."""
        line_number = await self.line_repo.get_next_line_number(invoice_id)

        # Calculate amounts
        line_total = data.quantity * data.unit_price
        discount_amount = (
            data.discount_amount
            if data.discount_amount
            else line_total * data.discount_percent / 100
        )
        taxable_amount = line_total - discount_amount

        # Calculate GST
        if is_igst:
            igst_amount = taxable_amount * data.igst_rate / 100
            cgst_amount = Decimal("0")
            sgst_amount = Decimal("0")
        else:
            igst_amount = Decimal("0")
            cgst_amount = taxable_amount * data.cgst_rate / 100
            sgst_amount = taxable_amount * data.sgst_rate / 100

        cess_amount = taxable_amount * data.cess_rate / 100
        net_amount = taxable_amount + cgst_amount + sgst_amount + igst_amount + cess_amount

        line_data = {
            "invoice_id": invoice_id,
            "line_number": line_number,
            "po_line_id": data.po_line_id,
            "po_line_number": data.po_line_number,
            "item_code": data.item_code,
            "item_description": data.item_description,
            "hsn_sac_code": data.hsn_sac_code,
            "uom": data.uom,
            "quantity": data.quantity,
            "unit_price": data.unit_price,
            "line_total": line_total,
            "discount_percent": data.discount_percent,
            "discount_amount": discount_amount,
            "taxable_amount": taxable_amount,
            "cgst_rate": data.cgst_rate if not is_igst else Decimal("0"),
            "cgst_amount": cgst_amount,
            "sgst_rate": data.sgst_rate if not is_igst else Decimal("0"),
            "sgst_amount": sgst_amount,
            "igst_rate": data.igst_rate if is_igst else Decimal("0"),
            "igst_amount": igst_amount,
            "cess_rate": data.cess_rate,
            "cess_amount": cess_amount,
            "net_amount": net_amount,
        }

        line = await self.line_repo.create(line_data)
        return line

    async def _recalculate_invoice_totals(
        self,
        invoice: VendorInvoice,
    ) -> None:
        """Recalculate invoice totals from lines."""
        lines = await self.line_repo.get_by_invoice(invoice.id)

        subtotal = sum(line.line_total for line in lines)
        discount_amount = sum(line.discount_amount for line in lines)
        taxable_amount = sum(line.taxable_amount for line in lines)
        cgst_amount = sum(line.cgst_amount for line in lines)
        sgst_amount = sum(line.sgst_amount for line in lines)
        igst_amount = sum(line.igst_amount for line in lines)
        cess_amount = sum(line.cess_amount for line in lines)

        total_amount = taxable_amount + cgst_amount + sgst_amount + igst_amount + cess_amount

        # Apply TDS if applicable
        tds_amount = Decimal("0")
        if invoice.tds_applicable and invoice.tds_rate:
            tds_amount = taxable_amount * invoice.tds_rate / 100

        payable_amount = total_amount - tds_amount

        # Round off
        round_off = round(payable_amount) - payable_amount
        payable_amount = round(payable_amount)

        invoice.subtotal = subtotal
        invoice.discount_amount = discount_amount
        invoice.taxable_amount = taxable_amount
        invoice.cgst_amount = cgst_amount
        invoice.sgst_amount = sgst_amount
        invoice.igst_amount = igst_amount
        invoice.cess_amount = cess_amount
        invoice.tds_amount = tds_amount
        invoice.total_amount = total_amount
        invoice.round_off = round_off
        invoice.payable_amount = payable_amount
        invoice.balance_amount = payable_amount

        await self.session.flush()

    async def _perform_matching(
        self,
        invoice: VendorInvoice,
    ) -> InvoiceMatchingResult:
        """Perform 2-way or 3-way matching."""
        exceptions = []
        warnings = []
        po_matched = False
        grn_matched = False

        if not invoice.purchase_order_id:
            return InvoiceMatchingResult(
                is_matched=False,
                matching_type=invoice.matching_type,
                matching_status=InvoiceMatchingStatus.PENDING,
                po_matched=False,
                grn_matched=False,
                can_submit=True,
                message="No PO reference - manual review required",
            )

        # TODO: Implement actual PO and GRN matching with database queries
        # For now, return a placeholder result

        # Simulate 2-way matching
        po_match_details = []
        for line in invoice.lines:
            if line.po_line_id:
                # Compare quantities and prices with PO line
                # This would fetch actual PO data from database
                po_match_details.append({
                    "line_number": line.line_number,
                    "matched": True,
                    "quantity_variance": 0,
                    "price_variance": 0,
                })

        po_matched = len(po_match_details) > 0

        # Simulate 3-way matching if required
        grn_match_details = []
        if invoice.matching_type == InvoiceMatchingType.THREE_WAY:
            for line in invoice.lines:
                if line.grn_line_id:
                    grn_match_details.append({
                        "line_number": line.line_number,
                        "matched": True,
                        "received_quantity": line.quantity,
                    })
            grn_matched = len(grn_match_details) > 0

        # Determine overall matching status
        if po_matched and (
            invoice.matching_type != InvoiceMatchingType.THREE_WAY or grn_matched
        ):
            matching_status = InvoiceMatchingStatus.MATCHED
            is_matched = True
            message = "Invoice matched successfully"
        elif len(exceptions) > 0:
            matching_status = InvoiceMatchingStatus.MISMATCH
            is_matched = False
            message = f"Found {len(exceptions)} matching exceptions"
        else:
            matching_status = InvoiceMatchingStatus.PARTIAL_MATCH
            is_matched = False
            message = "Partial match - review required"

        return InvoiceMatchingResult(
            is_matched=is_matched,
            matching_type=invoice.matching_type,
            matching_status=matching_status,
            po_matched=po_matched,
            po_match_details=po_match_details,
            grn_matched=grn_matched,
            grn_match_details=grn_match_details,
            exceptions=exceptions,
            warnings=warnings,
            can_submit=True,
            message=message,
        )

    def _is_igst_applicable(
        self,
        vendor_gstin: Optional[str],
        place_of_supply: Optional[str],
        organization_id: UUID,
    ) -> bool:
        """Determine if IGST is applicable based on place of supply."""
        # TODO: Get organization's state code from database
        # For now, assume same state = CGST+SGST, different = IGST
        if not vendor_gstin or not place_of_supply:
            return False

        vendor_state = vendor_gstin[:2] if vendor_gstin else None
        # This should be fetched from organization settings
        org_state = "27"  # Maharashtra placeholder

        return vendor_state != org_state
