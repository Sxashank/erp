"""Purchase Bill service."""

from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import GLEntrySourceType, PartyType
from app.models.ap_ar.purchase_bill import BillStatus, PaymentStatus, PurchaseBill
from app.models.common.audit_log import AuditAction, EntityType
from app.models.workflow import WorkflowEntityType, WorkflowInstanceStatus
from app.repositories.ap_ar.purchase_bill_repo import PurchaseBillRepository
from app.repositories.ap_ar.vendor_repo import VendorRepository
from app.repositories.finance.account_repo import AccountRepository
from app.repositories.finance.financial_year_repo import (
    FinancialPeriodRepository,
    FinancialYearRepository,
)
from app.schemas.ap_ar.purchase_bill import PurchaseBillCreate, PurchaseBillUpdate
from app.services.common.audit_service import AuditService, model_to_dict
from app.services.finance.gl_posting_service import GLPostingService
from app.services.workflow import WorkflowEngine


class PurchaseBillService:
    """Service for purchase bill operations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = PurchaseBillRepository(db)
        self.vendor_repo = VendorRepository(db)
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
        status: str | None = None,
        payment_status: str | None = None,
        vendor_id: UUID | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
        search: str | None = None,
    ) -> tuple[list[PurchaseBill], int]:
        """Get all purchase bills with filters."""
        return await self.repo.get_all(
            organization_id,
            skip,
            limit,
            include_inactive,
            status,
            payment_status,
            vendor_id,
            from_date,
            to_date,
            search,
        )

    async def get(self, bill_id: UUID) -> PurchaseBill:
        """Get purchase bill by ID with lines."""
        bill = await self.repo.get_with_lines(bill_id)
        if not bill:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Purchase bill not found",
            )
        return bill

    async def get_unpaid_for_vendor(
        self, organization_id: UUID, vendor_id: UUID
    ) -> list[PurchaseBill]:
        """Get unpaid bills for a vendor."""
        return await self.repo.get_unpaid_for_vendor(organization_id, vendor_id)

    async def generate_number(self, organization_id: UUID) -> str:
        """Generate next bill number."""
        return await self.repo.get_next_number(organization_id)

    async def create(self, data: PurchaseBillCreate, user_id: UUID) -> PurchaseBill:
        """Create a new purchase bill."""
        # Get vendor for GSTIN
        vendor = await self.vendor_repo.get(data.vendor_id)
        if not vendor:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Vendor not found",
            )

        # Generate bill number
        bill_number = await self.repo.get_next_number(data.organization_id)

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
            taxable_amount
            + cgst_amount
            + sgst_amount
            + igst_amount
            + cess_amount
            - data.tds_amount
            + data.round_off
        )

        # Create bill
        bill_data = {
            "bill_number": bill_number,
            "vendor_invoice_number": data.vendor_invoice_number,
            "vendor_invoice_date": data.vendor_invoice_date,
            "bill_date": data.bill_date,
            "due_date": data.due_date,
            "vendor_id": data.vendor_id,
            "organization_id": data.organization_id,
            "unit_id": data.unit_id,
            "subtotal": subtotal,
            "discount_amount": discount_amount,
            "taxable_amount": taxable_amount,
            "cgst_amount": cgst_amount,
            "sgst_amount": sgst_amount,
            "igst_amount": igst_amount,
            "cess_amount": cess_amount,
            "tds_amount": data.tds_amount,
            "round_off": data.round_off,
            "total_amount": total_amount,
            "balance_amount": total_amount,
            "is_reverse_charge": data.is_reverse_charge,
            "supply_type": data.supply_type,
            "vendor_gstin": vendor.gstin,
            "place_of_supply": data.place_of_supply,
            "narration": data.narration,
            "reference_number": data.reference_number,
            "status": BillStatus.DRAFT,
            "payment_status": PaymentStatus.UNPAID,
            "created_by": user_id,
        }

        bill = await self.repo.create(bill_data)

        # Create lines
        for line_data in data.lines:
            line_dict = line_data.model_dump()
            line_dict["bill_id"] = bill.id
            await self.repo.create_line(line_dict)

        await self.db.flush()
        loaded_bill = await self.get(bill.id)

        # Audit log: CREATE
        await self.audit_service.log_create(
            organization_id=loaded_bill.organization_id,
            entity_type=EntityType.PURCHASE_BILL.value,
            entity_id=loaded_bill.id,
            entity_reference=loaded_bill.bill_number,
            new_values=model_to_dict(loaded_bill),
            user_id=user_id,
        )

        return loaded_bill

    async def update(self, bill_id: UUID, data: PurchaseBillUpdate, user_id: UUID) -> PurchaseBill:
        """Update a purchase bill."""
        bill = await self.get(bill_id)

        if bill.status not in [BillStatus.DRAFT]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only draft bills can be edited",
            )

        # Capture old state for audit trail
        old_values = model_to_dict(bill)
        old_lines = [model_to_dict(line) for line in bill.lines] if bill.lines else []

        # Update bill fields
        update_data = data.model_dump(exclude_unset=True, exclude={"lines"})
        update_data["updated_by"] = user_id
        update_data["updated_at"] = datetime.now(UTC)

        # If lines are provided, recalculate totals
        if data.lines:
            # Delete existing lines
            await self.repo.delete_lines(bill_id)

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

            tds_amount = data.tds_amount if data.tds_amount is not None else bill.tds_amount
            round_off = data.round_off if data.round_off is not None else bill.round_off
            total_amount = (
                taxable_amount
                + cgst_amount
                + sgst_amount
                + igst_amount
                + cess_amount
                - tds_amount
                + round_off
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
                line_dict["bill_id"] = bill_id
                await self.repo.create_line(line_dict)

        bill = await self.repo.update(bill, update_data)
        await self.db.flush()
        updated_bill = await self.get(bill_id)

        # Audit log: UPDATE
        audit_entry = await self.audit_service.log_update(
            organization_id=updated_bill.organization_id,
            entity_type=EntityType.PURCHASE_BILL.value,
            entity_id=updated_bill.id,
            entity_reference=updated_bill.bill_number,
            old_values=old_values,
            new_values=model_to_dict(updated_bill),
            user_id=user_id,
        )

        # Log line item changes if lines were updated
        if data.lines:
            new_lines = (
                [model_to_dict(line) for line in updated_bill.lines] if updated_bill.lines else []
            )
            await self.audit_service.log_line_changes(
                parent_audit_id=audit_entry.id,
                entity_type="BILL_LINE",
                old_lines=old_lines,
                new_lines=new_lines,
            )

        return updated_bill

    async def submit(self, bill_id: UUID, user_id: UUID) -> PurchaseBill:
        """Submit bill for approval using workflow engine."""
        bill = await self.get(bill_id)

        if bill.status != BillStatus.DRAFT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only draft bills can be submitted",
            )

        if not bill.lines or len(bill.lines) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bill must have at least one line item",
            )

        # Capture old state
        old_values = model_to_dict(bill)

        # Build workflow context
        context = {
            "amount": float(bill.total_amount),
            "vendor_id": str(bill.vendor_id),
            "vendor_name": bill.vendor.name if bill.vendor else None,
            "is_reverse_charge": bill.is_reverse_charge,
            "supply_type": bill.supply_type.value if bill.supply_type else None,
        }

        # Try to start workflow
        try:
            workflow_instance = await self.workflow_engine.start_workflow(
                entity_type=WorkflowEntityType.PURCHASE_BILL,
                entity_id=bill.id,
                entity_reference=bill.bill_number,
                organization_id=bill.organization_id,
                context=context,
                started_by=user_id,
            )

            update_data = {
                "status": BillStatus.SUBMITTED,
                "workflow_instance_id": workflow_instance.id,
                "updated_by": user_id,
                "updated_at": datetime.now(UTC),
            }
        except Exception:
            # If no workflow definition exists, just mark as submitted
            update_data = {
                "status": BillStatus.SUBMITTED,
                "updated_by": user_id,
                "updated_at": datetime.now(UTC),
            }

        bill = await self.repo.update(bill, update_data)
        await self.db.flush()

        # Audit log: SUBMIT
        await self.audit_service.log_action(
            organization_id=bill.organization_id,
            entity_type=EntityType.PURCHASE_BILL.value,
            entity_id=bill.id,
            entity_reference=bill.bill_number,
            action="SUBMIT",
            user_id=user_id,
            old_values=old_values,
            new_values=model_to_dict(bill),
        )

        return bill

    async def approve(self, bill_id: UUID, user_id: UUID) -> PurchaseBill:
        """Approve a bill (legacy method for non-workflow approvals).

        Enforces §8.4 maker-checker: the submitting user cannot approve their
        own bill. For workflow-routed bills the same guard runs at the task
        completion site inside `WorkflowEngine`.
        """
        from app.core.maker_checker import ensure_maker_is_not_checker

        bill = await self.get(bill_id)

        if bill.status != BillStatus.SUBMITTED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only submitted bills can be approved",
            )

        # If using workflow, redirect to workflow-based approval
        if bill.workflow_instance_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This bill uses workflow-based approval. Please use the workflow task endpoints.",
            )

        ensure_maker_is_not_checker(
            maker_user_id=bill.created_by,
            checker_user_id=user_id,
        )

        # Capture old state
        old_values = model_to_dict(bill)

        update_data = {
            "status": BillStatus.APPROVED,
            "updated_by": user_id,
            "updated_at": datetime.now(UTC),
        }
        bill = await self.repo.update(bill, update_data)

        # Auto-post to GL on approval
        await self._post_to_gl(bill, user_id)

        await self.db.flush()

        # Audit log: APPROVE
        await self.audit_service.log_action(
            organization_id=bill.organization_id,
            entity_type=EntityType.PURCHASE_BILL.value,
            entity_id=bill.id,
            entity_reference=bill.bill_number,
            action=AuditAction.APPROVE.value,
            user_id=user_id,
            old_values=old_values,
            new_values=model_to_dict(bill),
        )

        return bill

    async def handle_workflow_complete(
        self,
        bill_id: UUID,
        workflow_status: WorkflowInstanceStatus,
        completed_by: UUID | None = None,
    ) -> PurchaseBill:
        """Handle workflow completion callback to update bill status."""
        bill = await self.get(bill_id)
        old_values = model_to_dict(bill)

        if workflow_status == WorkflowInstanceStatus.APPROVED:
            bill.status = BillStatus.APPROVED
            # Auto-post to GL on approval
            await self._post_to_gl(bill, completed_by)
        elif workflow_status == WorkflowInstanceStatus.REJECTED:
            bill.status = BillStatus.DRAFT  # Return to draft for correction
            bill.workflow_instance_id = None
        elif workflow_status == WorkflowInstanceStatus.CANCELLED:
            bill.status = BillStatus.DRAFT
            bill.workflow_instance_id = None

        bill.updated_by = completed_by
        bill.updated_at = datetime.now(UTC)

        await self.db.flush()
        await self.db.refresh(bill)

        # Audit log
        await self.audit_service.log_action(
            organization_id=bill.organization_id,
            entity_type=EntityType.PURCHASE_BILL.value,
            entity_id=bill.id,
            entity_reference=bill.bill_number,
            action=workflow_status.value,
            user_id=completed_by,
            old_values=old_values,
            new_values=model_to_dict(bill),
        )

        return bill

    async def cancel(self, bill_id: UUID, user_id: UUID, reason: str) -> PurchaseBill:
        """Cancel a bill."""
        bill = await self.get(bill_id)

        if bill.status == BillStatus.CANCELLED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bill is already cancelled",
            )

        if bill.payment_status != PaymentStatus.UNPAID:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot cancel a bill with payments",
            )

        # Capture old state
        old_values = model_to_dict(bill)

        update_data = {
            "status": BillStatus.CANCELLED,
            "narration": f"{bill.narration or ''}\nCancelled: {reason}".strip(),
            "updated_by": user_id,
            "updated_at": datetime.now(UTC),
        }
        bill = await self.repo.update(bill, update_data)
        await self.db.flush()

        # Audit log: CANCEL
        await self.audit_service.log_action(
            organization_id=bill.organization_id,
            entity_type=EntityType.PURCHASE_BILL.value,
            entity_id=bill.id,
            entity_reference=bill.bill_number,
            action=AuditAction.CANCEL.value,
            user_id=user_id,
            old_values=old_values,
            new_values=model_to_dict(bill),
            change_reason=reason,
        )

        return bill

    async def delete(self, bill_id: UUID, user_id: UUID) -> None:
        """Soft delete a purchase bill."""
        bill = await self.get(bill_id)

        if bill.status != BillStatus.DRAFT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only draft bills can be deleted",
            )

        # Capture old state for audit trail
        old_values = model_to_dict(bill)
        org_id = bill.organization_id
        bill_number = bill.bill_number

        await self.repo.soft_delete(bill, user_id)
        await self.db.flush()

        # Audit log: DELETE
        await self.audit_service.log_delete(
            organization_id=org_id,
            entity_type=EntityType.PURCHASE_BILL.value,
            entity_id=bill_id,
            entity_reference=bill_number,
            old_values=old_values,
            user_id=user_id,
        )

    async def _post_to_gl(self, bill: PurchaseBill, posted_by: UUID | None) -> None:
        """
        Auto-post purchase bill to GL on approval.

        GL Entry Pattern:
        - Dr. Expense Account(s) - from each line's expense_account_id
        - Dr. CGST Input Account - if CGST amount > 0
        - Dr. SGST Input Account - if SGST amount > 0
        - Dr. IGST Input Account - if IGST amount > 0
        - Dr. Cess Input Account - if Cess amount > 0
        - Cr. AP Control Account - vendor's control_account_id
        - Cr. TDS Payable Account - if TDS amount > 0
        """
        # Skip if already posted
        if bill.is_posted:
            return

        # Get financial year and period
        fy = await self.fy_repo.get_by_date(bill.organization_id, bill.bill_date)
        if not fy:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No financial year found for bill date {bill.bill_date}",
            )

        period = await self.period_repo.get_by_date(fy.id, bill.bill_date)
        if not period:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No period found for bill date {bill.bill_date}",
            )

        # Get vendor for control account
        vendor = await self.vendor_repo.get(bill.vendor_id)
        if not vendor or not vendor.control_account_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Vendor does not have a control account configured",
            )

        # Build GL entry lines
        gl_lines: list[dict[str, Any]] = []

        # Expense entries from bill lines
        for line in bill.lines:
            if line.taxable_amount > 0:
                expense_account_id = line.expense_account_id or vendor.expense_account_id
                if not expense_account_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Line {line.line_number} does not have an expense account",
                    )

                gl_lines.append(
                    {
                        "account_id": expense_account_id,
                        "debit_amount": line.taxable_amount,
                        "credit_amount": Decimal("0"),
                        "narration": f"Purchase: {line.description}",
                    }
                )

        # GST Input entries (aggregated at bill level)
        gst_accounts = await self._get_gst_input_accounts(bill.organization_id)

        if bill.cgst_amount > 0 and gst_accounts.get("cgst_input"):
            gl_lines.append(
                {
                    "account_id": gst_accounts["cgst_input"],
                    "debit_amount": bill.cgst_amount,
                    "credit_amount": Decimal("0"),
                    "narration": "CGST Input",
                }
            )

        if bill.sgst_amount > 0 and gst_accounts.get("sgst_input"):
            gl_lines.append(
                {
                    "account_id": gst_accounts["sgst_input"],
                    "debit_amount": bill.sgst_amount,
                    "credit_amount": Decimal("0"),
                    "narration": "SGST Input",
                }
            )

        if bill.igst_amount > 0 and gst_accounts.get("igst_input"):
            gl_lines.append(
                {
                    "account_id": gst_accounts["igst_input"],
                    "debit_amount": bill.igst_amount,
                    "credit_amount": Decimal("0"),
                    "narration": "IGST Input",
                }
            )

        if bill.cess_amount > 0 and gst_accounts.get("cess_input"):
            gl_lines.append(
                {
                    "account_id": gst_accounts["cess_input"],
                    "debit_amount": bill.cess_amount,
                    "credit_amount": Decimal("0"),
                    "narration": "Cess Input",
                }
            )

        # TDS Payable (if applicable)
        if bill.tds_amount > 0:
            tds_account = await self._get_tds_payable_account(bill.organization_id)
            if tds_account:
                gl_lines.append(
                    {
                        "account_id": tds_account,
                        "debit_amount": Decimal("0"),
                        "credit_amount": bill.tds_amount,
                        "narration": "TDS Payable",
                    }
                )

        # AP Control (Credit - total payable to vendor)
        # Total payable = Total Amount (already net of TDS)
        gl_lines.append(
            {
                "account_id": vendor.control_account_id,
                "debit_amount": Decimal("0"),
                "credit_amount": bill.total_amount,
                "party_type": PartyType.VENDOR,
                "party_id": bill.vendor_id,
                "narration": f"Payable to {vendor.name}",
            }
        )

        # Post to GL
        narration = f"Purchase Bill: {bill.bill_number}"
        if bill.vendor_invoice_number:
            narration += f" (Vendor Inv: {bill.vendor_invoice_number})"

        await self.gl_posting_service.post_from_source(
            source_type=GLEntrySourceType.PURCHASE_BILL,
            source_id=bill.id,
            source_reference=bill.bill_number,
            organization_id=bill.organization_id,
            financial_year_id=fy.id,
            period_id=period.id,
            voucher_date=bill.bill_date,
            narration=narration,
            lines=gl_lines,
            posted_by=posted_by,
            unit_id=bill.unit_id,
        )

        # Mark as posted
        bill.is_posted = True

    async def _get_gst_input_accounts(self, organization_id: UUID) -> dict[str, UUID | None]:
        """
        Get GST input account IDs for an organization.
        These accounts should be configured in organization settings.
        For now, we'll look for accounts with specific codes.
        """
        result = {
            "cgst_input": None,
            "sgst_input": None,
            "igst_input": None,
            "cess_input": None,
        }

        # Look for accounts by common naming convention
        # TODO: Move these to organization settings
        account_codes = {
            "cgst_input": ["CGST-INPUT", "CGST_INPUT", "CGST INPUT"],
            "sgst_input": ["SGST-INPUT", "SGST_INPUT", "SGST INPUT"],
            "igst_input": ["IGST-INPUT", "IGST_INPUT", "IGST INPUT"],
            "cess_input": ["CESS-INPUT", "CESS_INPUT", "CESS INPUT"],
        }

        for key, codes in account_codes.items():
            for code in codes:
                account = await self.account_repo.get_by_code(organization_id, code)
                if account:
                    result[key] = account.id
                    break

        return result

    async def _get_tds_payable_account(self, organization_id: UUID) -> UUID | None:
        """
        Get TDS payable account ID for an organization.
        """
        # Look for TDS payable account by common naming convention
        codes = ["TDS-PAYABLE", "TDS_PAYABLE", "TDS PAYABLE"]
        for code in codes:
            account = await self.account_repo.get_by_code(organization_id, code)
            if account:
                return account.id
        return None
