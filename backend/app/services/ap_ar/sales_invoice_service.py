"""Sales Invoice service."""

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ap_ar.sales_invoice import (
    SalesInvoice,
    SalesInvoiceLine,
    InvoiceStatus,
    ReceiptStatus,
    EInvoiceStatus,
)
from app.models.common.audit_log import EntityType, AuditAction
from app.models.workflow import WorkflowEntityType, WorkflowInstanceStatus
from app.repositories.ap_ar.sales_invoice_repo import SalesInvoiceRepository
from app.repositories.ap_ar.customer_repo import CustomerRepository
from app.repositories.finance.financial_year_repo import FinancialYearRepository, FinancialPeriodRepository
from app.repositories.finance.account_repo import AccountRepository
from app.schemas.ap_ar.sales_invoice import SalesInvoiceCreate, SalesInvoiceUpdate
from app.services.common.audit_service import AuditService, model_to_dict
from app.services.workflow import WorkflowEngine
from app.services.finance.gl_posting_service import GLPostingService
from app.core.constants import GLEntrySourceType, PartyType


class SalesInvoiceService:
    """Service for sales invoice operations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = SalesInvoiceRepository(db)
        self.customer_repo = CustomerRepository(db)
        self.audit_service = AuditService(db)
        self.workflow_engine = WorkflowEngine(db)
        self.gl_posting_service = GLPostingService(db)
        self.fy_repo = FinancialYearRepository(db)
        self.period_repo = FinancialPeriodRepository(db)
        self.account_repo = AccountRepository(db)

    async def get_all(
        self,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 50,
        include_inactive: bool = False,
        status: Optional[str] = None,
        receipt_status: Optional[str] = None,
        customer_id: Optional[UUID] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[SalesInvoice], int]:
        """Get all sales invoices with filters."""
        return await self.repo.get_all(
            organization_id, skip, limit, include_inactive,
            status, receipt_status, customer_id, from_date, to_date, search
        )

    async def get(self, invoice_id: UUID) -> SalesInvoice:
        """Get sales invoice by ID with lines."""
        invoice = await self.repo.get_with_lines(invoice_id)
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sales invoice not found",
            )
        return invoice

    async def get_unreceived_for_customer(
        self, organization_id: UUID, customer_id: UUID
    ) -> List[SalesInvoice]:
        """Get unreceived invoices for a customer."""
        return await self.repo.get_unreceived_for_customer(organization_id, customer_id)

    async def generate_number(self, organization_id: UUID) -> str:
        """Generate next invoice number."""
        return await self.repo.get_next_number(organization_id)

    async def create(self, data: SalesInvoiceCreate, user_id: UUID) -> SalesInvoice:
        """Create a new sales invoice."""
        # Get customer for GSTIN
        customer = await self.customer_repo.get(data.customer_id)
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Customer not found",
            )

        # Generate invoice number
        invoice_number = await self.repo.get_next_number(data.organization_id)

        # Calculate totals from lines
        subtotal = Decimal("0")
        discount_amount = Decimal("0")
        taxable_amount = Decimal("0")
        cgst_amount = Decimal("0")
        sgst_amount = Decimal("0")
        igst_amount = Decimal("0")
        cess_amount = Decimal("0")

        for line in data.lines:
            subtotal += line.quantity * line.unit_price
            discount_amount += line.discount_amount
            taxable_amount += line.taxable_amount
            cgst_amount += line.cgst_amount
            sgst_amount += line.sgst_amount
            igst_amount += line.igst_amount
            cess_amount += line.cess_amount

        total_amount = (
            taxable_amount + cgst_amount + sgst_amount + igst_amount +
            cess_amount + data.tcs_amount + data.round_off
        )

        # Create invoice
        invoice_data = {
            "invoice_number": invoice_number,
            "invoice_date": data.invoice_date,
            "due_date": data.due_date,
            "customer_id": data.customer_id,
            "organization_id": data.organization_id,
            "unit_id": data.unit_id,
            "subtotal": subtotal,
            "discount_amount": discount_amount,
            "taxable_amount": taxable_amount,
            "cgst_amount": cgst_amount,
            "sgst_amount": sgst_amount,
            "igst_amount": igst_amount,
            "cess_amount": cess_amount,
            "tcs_amount": data.tcs_amount,
            "round_off": data.round_off,
            "total_amount": total_amount,
            "balance_amount": total_amount,
            "is_reverse_charge": data.is_reverse_charge,
            "supply_type": data.supply_type,
            "customer_gstin": customer.gstin,
            "place_of_supply": data.place_of_supply,
            "narration": data.narration,
            "reference_number": data.reference_number,
            "po_number": data.po_number,
            "po_date": data.po_date,
            "shipping_address": data.shipping_address,
            "transporter_name": data.transporter_name,
            "vehicle_number": data.vehicle_number,
            "status": InvoiceStatus.DRAFT,
            "receipt_status": ReceiptStatus.UNRECEIVED,
            "e_invoice_status": EInvoiceStatus.NOT_APPLICABLE,
            "created_by": user_id,
        }

        invoice = await self.repo.create(invoice_data)

        # Create lines
        for line_data in data.lines:
            line_dict = line_data.model_dump()
            line_dict["invoice_id"] = invoice.id
            await self.repo.create_line(line_dict)

        await self.db.commit()
        loaded_invoice = await self.get(invoice.id)

        # Audit log: CREATE
        await self.audit_service.log_create(
            organization_id=loaded_invoice.organization_id,
            entity_type=EntityType.SALES_INVOICE.value,
            entity_id=loaded_invoice.id,
            entity_reference=loaded_invoice.invoice_number,
            new_values=model_to_dict(loaded_invoice),
            user_id=user_id,
        )

        return loaded_invoice

    async def update(
        self, invoice_id: UUID, data: SalesInvoiceUpdate, user_id: UUID
    ) -> SalesInvoice:
        """Update a sales invoice."""
        invoice = await self.get(invoice_id)

        if invoice.status not in [InvoiceStatus.DRAFT]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only draft invoices can be edited",
            )

        # Capture old state for audit trail
        old_values = model_to_dict(invoice)
        old_lines = [model_to_dict(line) for line in invoice.lines] if invoice.lines else []

        # Update invoice fields
        update_data = data.model_dump(exclude_unset=True, exclude={"lines"})
        update_data["updated_by"] = user_id
        update_data["updated_at"] = datetime.now(timezone.utc)

        # If lines are provided, recalculate totals
        if data.lines:
            # Delete existing lines
            await self.repo.delete_lines(invoice_id)

            # Recalculate totals
            subtotal = Decimal("0")
            discount_amount = Decimal("0")
            taxable_amount = Decimal("0")
            cgst_amount = Decimal("0")
            sgst_amount = Decimal("0")
            igst_amount = Decimal("0")
            cess_amount = Decimal("0")

            for line in data.lines:
                subtotal += line.quantity * line.unit_price
                discount_amount += line.discount_amount
                taxable_amount += line.taxable_amount
                cgst_amount += line.cgst_amount
                sgst_amount += line.sgst_amount
                igst_amount += line.igst_amount
                cess_amount += line.cess_amount

            tcs_amount = data.tcs_amount if data.tcs_amount is not None else invoice.tcs_amount
            round_off = data.round_off if data.round_off is not None else invoice.round_off
            total_amount = (
                taxable_amount + cgst_amount + sgst_amount + igst_amount +
                cess_amount + tcs_amount + round_off
            )

            update_data["subtotal"] = subtotal
            update_data["discount_amount"] = discount_amount
            update_data["taxable_amount"] = taxable_amount
            update_data["cgst_amount"] = cgst_amount
            update_data["sgst_amount"] = sgst_amount
            update_data["igst_amount"] = igst_amount
            update_data["cess_amount"] = cess_amount
            update_data["total_amount"] = total_amount
            update_data["balance_amount"] = total_amount

            # Create new lines
            for line_data in data.lines:
                line_dict = line_data.model_dump()
                line_dict["invoice_id"] = invoice_id
                await self.repo.create_line(line_dict)

        invoice = await self.repo.update(invoice, update_data)
        await self.db.commit()
        updated_invoice = await self.get(invoice_id)

        # Audit log: UPDATE
        audit_entry = await self.audit_service.log_update(
            organization_id=updated_invoice.organization_id,
            entity_type=EntityType.SALES_INVOICE.value,
            entity_id=updated_invoice.id,
            entity_reference=updated_invoice.invoice_number,
            old_values=old_values,
            new_values=model_to_dict(updated_invoice),
            user_id=user_id,
        )

        # Log line item changes if lines were updated
        if data.lines:
            new_lines = [model_to_dict(line) for line in updated_invoice.lines] if updated_invoice.lines else []
            await self.audit_service.log_line_changes(
                parent_audit_id=audit_entry.id,
                entity_type="INVOICE_LINE",
                old_lines=old_lines,
                new_lines=new_lines,
            )

        return updated_invoice

    async def submit(self, invoice_id: UUID, user_id: UUID) -> SalesInvoice:
        """Submit invoice for approval using workflow engine."""
        invoice = await self.get(invoice_id)

        if invoice.status != InvoiceStatus.DRAFT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only draft invoices can be submitted",
            )

        if not invoice.lines or len(invoice.lines) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invoice must have at least one line item",
            )

        # Capture old state
        old_values = model_to_dict(invoice)

        # Build workflow context
        context = {
            "amount": float(invoice.total_amount),
            "customer_id": str(invoice.customer_id),
            "customer_name": invoice.customer.name if invoice.customer else None,
            "supply_type": invoice.supply_type.value if invoice.supply_type else None,
            "e_invoice_required": invoice.e_invoice_required,
        }

        # Try to start workflow
        try:
            workflow_instance = await self.workflow_engine.start_workflow(
                entity_type=WorkflowEntityType.SALES_INVOICE,
                entity_id=invoice.id,
                entity_reference=invoice.invoice_number,
                organization_id=invoice.organization_id,
                context=context,
                started_by=user_id,
            )

            update_data = {
                "status": InvoiceStatus.SUBMITTED,
                "workflow_instance_id": workflow_instance.id,
                "updated_by": user_id,
                "updated_at": datetime.now(timezone.utc),
            }
        except Exception:
            # If no workflow definition exists, just mark as submitted
            update_data = {
                "status": InvoiceStatus.SUBMITTED,
                "updated_by": user_id,
                "updated_at": datetime.now(timezone.utc),
            }

        invoice = await self.repo.update(invoice, update_data)
        await self.db.commit()

        # Audit log: SUBMIT
        await self.audit_service.log_action(
            organization_id=invoice.organization_id,
            entity_type=EntityType.SALES_INVOICE.value,
            entity_id=invoice.id,
            entity_reference=invoice.invoice_number,
            action="SUBMIT",
            user_id=user_id,
            old_values=old_values,
            new_values=model_to_dict(invoice),
        )

        return invoice

    async def approve(self, invoice_id: UUID, user_id: UUID) -> SalesInvoice:
        """Approve an invoice (legacy method for non-workflow approvals)."""
        invoice = await self.get(invoice_id)

        if invoice.status != InvoiceStatus.SUBMITTED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only submitted invoices can be approved",
            )

        # If using workflow, redirect to workflow-based approval
        if invoice.workflow_instance_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This invoice uses workflow-based approval. Please use the workflow task endpoints.",
            )

        # Capture old state
        old_values = model_to_dict(invoice)

        update_data = {
            "status": InvoiceStatus.APPROVED,
            "updated_by": user_id,
            "updated_at": datetime.now(timezone.utc),
        }
        invoice = await self.repo.update(invoice, update_data)

        # Auto-post to GL on approval
        await self._post_to_gl(invoice, user_id)

        await self.db.commit()

        # Audit log: APPROVE
        await self.audit_service.log_action(
            organization_id=invoice.organization_id,
            entity_type=EntityType.SALES_INVOICE.value,
            entity_id=invoice.id,
            entity_reference=invoice.invoice_number,
            action=AuditAction.APPROVE.value,
            user_id=user_id,
            old_values=old_values,
            new_values=model_to_dict(invoice),
        )

        return invoice

    async def handle_workflow_complete(
        self,
        invoice_id: UUID,
        workflow_status: WorkflowInstanceStatus,
        completed_by: Optional[UUID] = None,
    ) -> SalesInvoice:
        """Handle workflow completion callback to update invoice status."""
        invoice = await self.get(invoice_id)
        old_values = model_to_dict(invoice)

        if workflow_status == WorkflowInstanceStatus.APPROVED:
            invoice.status = InvoiceStatus.APPROVED
            # Auto-post to GL on approval
            await self._post_to_gl(invoice, completed_by)
        elif workflow_status == WorkflowInstanceStatus.REJECTED:
            invoice.status = InvoiceStatus.DRAFT
            invoice.workflow_instance_id = None
        elif workflow_status == WorkflowInstanceStatus.CANCELLED:
            invoice.status = InvoiceStatus.DRAFT
            invoice.workflow_instance_id = None

        invoice.updated_by = completed_by
        invoice.updated_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(invoice)

        # Audit log
        await self.audit_service.log_action(
            organization_id=invoice.organization_id,
            entity_type=EntityType.SALES_INVOICE.value,
            entity_id=invoice.id,
            entity_reference=invoice.invoice_number,
            action=workflow_status.value,
            user_id=completed_by,
            old_values=old_values,
            new_values=model_to_dict(invoice),
        )

        return invoice

    async def cancel(
        self, invoice_id: UUID, user_id: UUID, reason: str
    ) -> SalesInvoice:
        """Cancel an invoice."""
        invoice = await self.get(invoice_id)

        if invoice.status == InvoiceStatus.CANCELLED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invoice is already cancelled",
            )

        if invoice.receipt_status != ReceiptStatus.UNRECEIVED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot cancel an invoice with receipts",
            )

        # Capture old state
        old_values = model_to_dict(invoice)

        update_data = {
            "status": InvoiceStatus.CANCELLED,
            "narration": f"{invoice.narration or ''}\nCancelled: {reason}".strip(),
            "updated_by": user_id,
            "updated_at": datetime.now(timezone.utc),
        }
        invoice = await self.repo.update(invoice, update_data)
        await self.db.commit()

        # Audit log: CANCEL
        await self.audit_service.log_action(
            organization_id=invoice.organization_id,
            entity_type=EntityType.SALES_INVOICE.value,
            entity_id=invoice.id,
            entity_reference=invoice.invoice_number,
            action=AuditAction.CANCEL.value,
            user_id=user_id,
            old_values=old_values,
            new_values=model_to_dict(invoice),
            change_reason=reason,
        )

        return invoice

    async def delete(self, invoice_id: UUID, user_id: UUID) -> None:
        """Soft delete a sales invoice."""
        invoice = await self.get(invoice_id)

        if invoice.status != InvoiceStatus.DRAFT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only draft invoices can be deleted",
            )

        # Capture old state for audit trail
        old_values = model_to_dict(invoice)
        org_id = invoice.organization_id
        invoice_number = invoice.invoice_number

        await self.repo.soft_delete(invoice, user_id)
        await self.db.commit()

        # Audit log: DELETE
        await self.audit_service.log_delete(
            organization_id=org_id,
            entity_type=EntityType.SALES_INVOICE.value,
            entity_id=invoice_id,
            entity_reference=invoice_number,
            old_values=old_values,
            user_id=user_id,
        )

    async def _post_to_gl(self, invoice: SalesInvoice, posted_by: Optional[UUID]) -> None:
        """
        Auto-post sales invoice to GL on approval.

        GL Entry Pattern:
        - Dr. AR Control Account - customer's control_account_id
        - Cr. Revenue Account(s) - from each line's revenue_account_id
        - Cr. CGST Output Account - if CGST amount > 0
        - Cr. SGST Output Account - if SGST amount > 0
        - Cr. IGST Output Account - if IGST amount > 0
        - Cr. Cess Output Account - if Cess amount > 0
        - Cr. TCS Payable Account - if TCS amount > 0
        """
        # Skip if already posted
        if invoice.is_posted:
            return

        # Get financial year and period
        fy = await self.fy_repo.get_by_date(invoice.organization_id, invoice.invoice_date)
        if not fy:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No financial year found for invoice date {invoice.invoice_date}",
            )

        period = await self.period_repo.get_by_date(fy.id, invoice.invoice_date)
        if not period:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No period found for invoice date {invoice.invoice_date}",
            )

        # Get customer for control account
        customer = await self.customer_repo.get(invoice.customer_id)
        if not customer or not customer.control_account_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Customer does not have a control account configured",
            )

        # Build GL entry lines
        gl_lines: List[Dict[str, Any]] = []

        # AR Control (Debit - customer receivable)
        gl_lines.append({
            "account_id": customer.control_account_id,
            "debit_amount": invoice.total_amount,
            "credit_amount": Decimal("0"),
            "party_type": PartyType.CUSTOMER,
            "party_id": invoice.customer_id,
            "narration": f"Receivable from {customer.name}",
        })

        # Revenue entries from invoice lines
        for line in invoice.lines:
            if line.taxable_amount > 0:
                revenue_account_id = line.revenue_account_id or customer.revenue_account_id
                if not revenue_account_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Line {line.line_number} does not have a revenue account",
                    )

                gl_lines.append({
                    "account_id": revenue_account_id,
                    "debit_amount": Decimal("0"),
                    "credit_amount": line.taxable_amount,
                    "narration": f"Sales: {line.description}",
                })

        # GST Output entries (aggregated at invoice level)
        gst_accounts = await self._get_gst_output_accounts(invoice.organization_id)

        if invoice.cgst_amount > 0 and gst_accounts.get("cgst_output"):
            gl_lines.append({
                "account_id": gst_accounts["cgst_output"],
                "debit_amount": Decimal("0"),
                "credit_amount": invoice.cgst_amount,
                "narration": "CGST Output",
            })

        if invoice.sgst_amount > 0 and gst_accounts.get("sgst_output"):
            gl_lines.append({
                "account_id": gst_accounts["sgst_output"],
                "debit_amount": Decimal("0"),
                "credit_amount": invoice.sgst_amount,
                "narration": "SGST Output",
            })

        if invoice.igst_amount > 0 and gst_accounts.get("igst_output"):
            gl_lines.append({
                "account_id": gst_accounts["igst_output"],
                "debit_amount": Decimal("0"),
                "credit_amount": invoice.igst_amount,
                "narration": "IGST Output",
            })

        if invoice.cess_amount > 0 and gst_accounts.get("cess_output"):
            gl_lines.append({
                "account_id": gst_accounts["cess_output"],
                "debit_amount": Decimal("0"),
                "credit_amount": invoice.cess_amount,
                "narration": "Cess Output",
            })

        # TCS Payable (if applicable)
        if invoice.tcs_amount and invoice.tcs_amount > 0:
            tcs_account = await self._get_tcs_payable_account(invoice.organization_id)
            if tcs_account:
                gl_lines.append({
                    "account_id": tcs_account,
                    "debit_amount": Decimal("0"),
                    "credit_amount": invoice.tcs_amount,
                    "narration": "TCS Payable",
                })

        # Post GL entries
        if gl_lines:
            await self.gl_posting_service.post_entries(
                organization_id=invoice.organization_id,
                financial_year_id=fy.id,
                period_id=period.id,
                voucher_date=invoice.invoice_date,
                source_type=GLEntrySourceType.SALES_INVOICE,
                source_id=invoice.id,
                source_reference=invoice.invoice_number,
                lines=gl_lines,
                narration=f"Sales Invoice: {invoice.invoice_number}",
                posted_by=posted_by,
            )

        # Update invoice as posted
        invoice.is_posted = True

    async def _get_gst_output_accounts(self, organization_id: UUID) -> Dict[str, Optional[UUID]]:
        """Get GST output accounts for the organization."""
        accounts = {}

        # Search for GST output accounts by code patterns
        search_patterns = {
            "cgst_output": ["CGST-OUT", "CGST_OUTPUT", "CGST Output"],
            "sgst_output": ["SGST-OUT", "SGST_OUTPUT", "SGST Output"],
            "igst_output": ["IGST-OUT", "IGST_OUTPUT", "IGST Output"],
            "cess_output": ["CESS-OUT", "CESS_OUTPUT", "Cess Output"],
        }

        for key, patterns in search_patterns.items():
            for pattern in patterns:
                account = await self.account_repo.get_by_code(organization_id, pattern)
                if account:
                    accounts[key] = account.id
                    break
            if key not in accounts:
                accounts[key] = None

        return accounts

    async def _get_tcs_payable_account(self, organization_id: UUID) -> Optional[UUID]:
        """Get TCS payable account for the organization."""
        for code in ["TCS-PAY", "TCS_PAYABLE", "TCS Payable"]:
            account = await self.account_repo.get_by_code(organization_id, code)
            if account:
                return account.id
        return None
