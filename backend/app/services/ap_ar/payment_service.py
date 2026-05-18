"""Payment Service for business logic."""

from collections.abc import Sequence
from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import GLEntrySourceType
from app.core.constants import PartyType as GLPartyType
from app.core.exceptions import (
    BadRequestException,
    NotFoundException,
)
from app.models.ap_ar.payment import (
    ChequeStatus,
    DocumentType,
    PartyType,
    Payment,
    PaymentAllocation,
    PaymentMode,
    PaymentStatus,
    PaymentType,
)
from app.models.ap_ar.purchase_bill import BillStatus, PurchaseBill
from app.models.ap_ar.purchase_bill import PaymentStatus as BillPaymentStatus
from app.models.ap_ar.sales_invoice import InvoiceStatus, ReceiptStatus, SalesInvoice
from app.models.common.audit_log import AuditAction, EntityType
from app.models.workflow import WorkflowEntityType, WorkflowInstanceStatus
from app.repositories.ap_ar.customer_repo import CustomerRepository
from app.repositories.ap_ar.payment_repo import (
    OutstandingDocumentsRepository,
    PaymentAllocationRepository,
    PaymentRepository,
)
from app.repositories.ap_ar.vendor_repo import VendorRepository
from app.repositories.finance.account_repo import AccountRepository
from app.repositories.finance.financial_year_repo import (
    FinancialPeriodRepository,
    FinancialYearRepository,
)
from app.schemas.ap_ar.payment import (
    ChequeStatusUpdate,
    PaymentAllocationCreate,
    PaymentCreate,
    PaymentUpdate,
)
from app.services.common.audit_service import AuditService, model_to_dict
from app.services.finance.gl_posting_service import GLPostingService
from app.services.tds.tds_entry_service import TDSEntryService
from app.services.workflow import WorkflowEngine


class PaymentService:
    """Service for Payment operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = PaymentRepository(session)
        self.allocation_repo = PaymentAllocationRepository(session)
        self.outstanding_repo = OutstandingDocumentsRepository(session)
        self.audit_service = AuditService(session)
        self.workflow_engine = WorkflowEngine(session)
        self.gl_posting_service = GLPostingService(session)
        self.vendor_repo = VendorRepository(session)
        self.customer_repo = CustomerRepository(session)
        self.fy_repo = FinancialYearRepository(session)
        self.period_repo = FinancialPeriodRepository(session)
        self.account_repo = AccountRepository(session)
        self.tds_entry_service = TDSEntryService(session)

    async def get_by_id(self, payment_id: UUID) -> Payment:
        """Get payment by ID."""
        payment = await self.repo.get_with_allocations(payment_id)
        if not payment:
            raise NotFoundException("Payment not found")
        return payment

    async def list_payments(
        self,
        organization_id: UUID,
        *,
        search: str | None = None,
        payment_type: PaymentType | None = None,
        party_type: PartyType | None = None,
        vendor_id: UUID | None = None,
        customer_id: UUID | None = None,
        payment_mode: PaymentMode | None = None,
        status: PaymentStatus | None = None,
        cheque_status: ChequeStatus | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
        is_posted: bool | None = None,
        unit_id: UUID | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[Sequence[Payment], int]:
        """List payments with filters."""
        return await self.repo.list_payments(
            organization_id,
            search=search,
            payment_type=payment_type,
            party_type=party_type,
            vendor_id=vendor_id,
            customer_id=customer_id,
            payment_mode=payment_mode,
            status=status,
            cheque_status=cheque_status,
            from_date=from_date,
            to_date=to_date,
            is_posted=is_posted,
            unit_id=unit_id,
            skip=skip,
            limit=limit,
        )

    async def generate_payment_number(
        self,
        organization_id: UUID,
        payment_type: PaymentType,
    ) -> str:
        """Generate next payment number."""
        # Prefix based on payment type
        prefix_map = {
            PaymentType.VENDOR_PAYMENT: "PAY-",
            PaymentType.CUSTOMER_RECEIPT: "REC-",
            PaymentType.ADVANCE_PAYMENT: "ADVP-",
            PaymentType.ADVANCE_RECEIPT: "ADVR-",
            PaymentType.REFUND_PAYMENT: "REFP-",
            PaymentType.REFUND_RECEIPT: "REFR-",
        }
        prefix = prefix_map.get(payment_type, "PMT-")
        return await self.repo.get_next_number(organization_id, payment_type, prefix)

    async def create_payment(
        self,
        data: PaymentCreate,
        created_by_id: UUID,
    ) -> Payment:
        """Create a new payment entry."""
        # Validate party exists
        await self._validate_party(data.party_type, data.vendor_id, data.customer_id)

        # Generate payment number
        payment_number = await self.generate_payment_number(data.organization_id, data.payment_type)

        # Calculate net amount
        net_amount = data.amount - data.tds_amount - data.discount_amount - data.write_off_amount

        # Validate allocations
        if data.allocations:
            await self._validate_allocations(data)

        # Create payment
        payment = Payment(
            payment_number=payment_number,
            payment_date=data.payment_date,
            payment_type=data.payment_type,
            party_type=data.party_type,
            vendor_id=data.vendor_id,
            customer_id=data.customer_id,
            organization_id=data.organization_id,
            unit_id=data.unit_id,
            payment_mode=data.payment_mode,
            bank_account_id=data.bank_account_id,
            cash_account_id=data.cash_account_id,
            amount=data.amount,
            tds_amount=data.tds_amount,
            tds_section_id=data.tds_section_id,
            tds_rate=data.tds_rate,
            discount_amount=data.discount_amount,
            write_off_amount=data.write_off_amount,
            net_amount=net_amount,
            currency_code=data.currency_code,
            exchange_rate=data.exchange_rate,
            cheque_number=data.cheque_number,
            cheque_date=data.cheque_date,
            cheque_bank_name=data.cheque_bank_name,
            cheque_branch=data.cheque_branch,
            cheque_status=(
                ChequeStatus.ISSUED if data.payment_mode == PaymentMode.CHEQUE else None
            ),
            reference_number=data.reference_number,
            narration=data.narration,
            status=PaymentStatus.DRAFT,
            created_by_id=created_by_id,
        )
        self.session.add(payment)
        await self.session.flush()

        # Create allocations
        if data.allocations:
            await self._create_allocations(payment, data.allocations)

        await self.session.flush()
        await self.session.refresh(payment)

        # Audit log: CREATE
        await self.audit_service.log_create(
            organization_id=payment.organization_id,
            entity_type=EntityType.PAYMENT.value,
            entity_id=payment.id,
            entity_reference=payment.payment_number,
            new_values=model_to_dict(payment),
            user_id=created_by_id,
        )

        return payment

    async def update_payment(
        self,
        payment_id: UUID,
        data: PaymentUpdate,
        updated_by_id: UUID,
    ) -> Payment:
        """Update a draft payment."""
        payment = await self.get_by_id(payment_id)

        if payment.status != PaymentStatus.DRAFT:
            raise BadRequestException("Only draft payments can be updated")

        # Capture old state for audit trail
        old_values = model_to_dict(payment)
        old_allocations = (
            [model_to_dict(alloc) for alloc in payment.allocations] if payment.allocations else []
        )

        # Update fields
        update_data = data.model_dump(exclude_unset=True, exclude={"allocations"})
        for field, value in update_data.items():
            setattr(payment, field, value)

        # Recalculate net amount if amounts changed
        payment.net_amount = (
            payment.amount - payment.tds_amount - payment.discount_amount - payment.write_off_amount
        )

        # Update cheque status if payment mode changed
        if data.payment_mode:
            if data.payment_mode == PaymentMode.CHEQUE:
                payment.cheque_status = ChequeStatus.ISSUED
            else:
                payment.cheque_status = None

        payment.updated_by_id = updated_by_id
        payment.updated_at = datetime.utcnow()

        # Update allocations if provided
        if data.allocations is not None:
            await self.allocation_repo.delete_allocations_for_payment(payment_id)
            await self._create_allocations(payment, data.allocations)

        await self.session.flush()
        await self.session.refresh(payment)

        # Audit log: UPDATE
        audit_entry = await self.audit_service.log_update(
            organization_id=payment.organization_id,
            entity_type=EntityType.PAYMENT.value,
            entity_id=payment.id,
            entity_reference=payment.payment_number,
            old_values=old_values,
            new_values=model_to_dict(payment),
            user_id=updated_by_id,
        )

        # Log allocation changes if allocations were updated
        if data.allocations is not None:
            new_allocations = (
                [model_to_dict(alloc) for alloc in payment.allocations]
                if payment.allocations
                else []
            )
            await self.audit_service.log_line_changes(
                parent_audit_id=audit_entry.id,
                entity_type="PAYMENT_ALLOCATION",
                old_lines=old_allocations,
                new_lines=new_allocations,
            )

        return payment

    async def submit_payment(
        self,
        payment_id: UUID,
        submitted_by_id: UUID,
    ) -> Payment:
        """Submit payment for approval using workflow engine."""
        payment = await self.get_by_id(payment_id)

        if payment.status != PaymentStatus.DRAFT:
            raise BadRequestException("Only draft payments can be submitted")

        if payment.amount <= 0:
            raise BadRequestException("Payment amount must be greater than zero")

        # Capture old state
        old_values = model_to_dict(payment)

        # Build workflow context
        context = {
            "amount": float(payment.amount),
            "payment_type": payment.payment_type.value,
            "party_type": payment.party_type.value,
            "payment_mode": payment.payment_mode.value,
            "vendor_id": str(payment.vendor_id) if payment.vendor_id else None,
            "customer_id": str(payment.customer_id) if payment.customer_id else None,
        }

        # Try to start workflow
        try:
            workflow_instance = await self.workflow_engine.start_workflow(
                entity_type=WorkflowEntityType.PAYMENT,
                entity_id=payment.id,
                entity_reference=payment.payment_number,
                organization_id=payment.organization_id,
                context=context,
                started_by=submitted_by_id,
            )

            payment.status = PaymentStatus.SUBMITTED
            payment.submitted_at = datetime.utcnow()
            payment.submitted_by_id = submitted_by_id
            payment.workflow_instance_id = workflow_instance.id
        except Exception:
            # If no workflow definition exists, just mark as submitted
            payment.status = PaymentStatus.SUBMITTED
            payment.submitted_at = datetime.utcnow()
            payment.submitted_by_id = submitted_by_id

        await self.session.flush()
        await self.session.refresh(payment)

        # Audit log: SUBMIT
        await self.audit_service.log_action(
            organization_id=payment.organization_id,
            entity_type=EntityType.PAYMENT.value,
            entity_id=payment.id,
            entity_reference=payment.payment_number,
            action="SUBMIT",
            user_id=submitted_by_id,
            old_values=old_values,
            new_values=model_to_dict(payment),
        )

        return payment

    async def approve_payment(
        self,
        payment_id: UUID,
        approved_by_id: UUID,
    ) -> Payment:
        """Approve payment and post to GL (legacy method for non-workflow approvals).

        Enforces §8.4 maker-checker: the submitter cannot approve their own
        payment. Workflow-routed payments are handled by the workflow engine.
        """
        from app.core.maker_checker import ensure_maker_is_not_checker

        payment = await self.get_by_id(payment_id)

        if payment.status != PaymentStatus.SUBMITTED:
            raise BadRequestException("Only submitted payments can be approved")

        # If using workflow, redirect to workflow-based approval
        if payment.workflow_instance_id:
            raise BadRequestException(
                "This payment uses workflow-based approval. Please use the workflow task endpoints."
            )

        # Maker is whoever submitted; fall back to created_by if submission
        # wasn't captured (legacy rows).
        ensure_maker_is_not_checker(
            maker_user_id=payment.submitted_by_id or payment.created_by,
            checker_user_id=approved_by_id,
        )

        # Capture old state
        old_values = model_to_dict(payment)

        payment.status = PaymentStatus.APPROVED
        payment.approved_at = datetime.utcnow()
        payment.approved_by_id = approved_by_id

        # Update document balances
        await self._update_document_balances(payment)

        # Create GL voucher and post
        await self._post_to_gl(payment, approved_by_id)

        # Create TDS entry if TDS was deducted
        if payment.tds_amount and payment.tds_amount > 0:
            await self._create_tds_entry(payment, approved_by_id)

        payment.is_posted = True
        payment.posted_at = datetime.utcnow()
        payment.posted_by_id = approved_by_id
        payment.status = PaymentStatus.POSTED

        await self.session.flush()
        await self.session.refresh(payment)

        # Audit log: APPROVE + POST
        await self.audit_service.log_action(
            organization_id=payment.organization_id,
            entity_type=EntityType.PAYMENT.value,
            entity_id=payment.id,
            entity_reference=payment.payment_number,
            action=AuditAction.APPROVE.value,
            user_id=approved_by_id,
            old_values=old_values,
            new_values=model_to_dict(payment),
        )

        return payment

    async def handle_workflow_complete(
        self,
        payment_id: UUID,
        workflow_status: WorkflowInstanceStatus,
        completed_by: UUID | None = None,
    ) -> Payment:
        """Handle workflow completion callback to update payment status."""
        payment = await self.get_by_id(payment_id)
        old_values = model_to_dict(payment)

        if workflow_status == WorkflowInstanceStatus.APPROVED:
            payment.status = PaymentStatus.APPROVED
            payment.approved_at = datetime.utcnow()
            payment.approved_by_id = completed_by

            # Update document balances
            await self._update_document_balances(payment)

            # Create GL voucher and post
            await self._post_to_gl(payment, completed_by)

            # Create TDS entry if TDS was deducted
            if payment.tds_amount and payment.tds_amount > 0:
                await self._create_tds_entry(payment, completed_by)

            # Mark as posted
            payment.is_posted = True
            payment.posted_at = datetime.utcnow()
            payment.posted_by_id = completed_by
            payment.status = PaymentStatus.POSTED

        elif workflow_status == WorkflowInstanceStatus.REJECTED:
            payment.status = PaymentStatus.DRAFT
            payment.workflow_instance_id = None
        elif workflow_status == WorkflowInstanceStatus.CANCELLED:
            payment.status = PaymentStatus.DRAFT
            payment.workflow_instance_id = None

        await self.session.flush()
        await self.session.refresh(payment)

        # Audit log
        await self.audit_service.log_action(
            organization_id=payment.organization_id,
            entity_type=EntityType.PAYMENT.value,
            entity_id=payment.id,
            entity_reference=payment.payment_number,
            action=workflow_status.value,
            user_id=completed_by,
            old_values=old_values,
            new_values=model_to_dict(payment),
        )

        return payment

    async def cancel_payment(
        self,
        payment_id: UUID,
        cancelled_by_id: UUID,
        reason: str,
    ) -> Payment:
        """Cancel a payment."""
        payment = await self.get_by_id(payment_id)

        if payment.status == PaymentStatus.CANCELLED:
            raise BadRequestException("Payment is already cancelled")

        # Capture old state
        old_values = model_to_dict(payment)

        if payment.status == PaymentStatus.POSTED:
            # Reverse document balance updates
            await self._reverse_document_balances(payment)

        old_status = payment.status
        payment.status = PaymentStatus.CANCELLED
        payment.cancelled_at = datetime.utcnow()
        payment.cancelled_by_id = cancelled_by_id
        payment.cancellation_reason = reason

        # If was posted, create reversal voucher
        if old_status == PaymentStatus.POSTED:
            payment.is_posted = False
            # TODO: Create reversal GL voucher

        await self.session.flush()
        await self.session.refresh(payment)

        # Audit log: CANCEL
        await self.audit_service.log_action(
            organization_id=payment.organization_id,
            entity_type=EntityType.PAYMENT.value,
            entity_id=payment.id,
            entity_reference=payment.payment_number,
            action=AuditAction.CANCEL.value,
            user_id=cancelled_by_id,
            old_values=old_values,
            new_values=model_to_dict(payment),
            change_reason=reason,
        )

        return payment

    async def update_cheque_status(
        self,
        payment_id: UUID,
        data: ChequeStatusUpdate,
        updated_by_id: UUID,
    ) -> Payment:
        """Update cheque status (cleared/bounced/etc)."""
        payment = await self.get_by_id(payment_id)

        if payment.payment_mode != PaymentMode.CHEQUE:
            raise BadRequestException("Payment is not a cheque payment")

        if payment.status != PaymentStatus.POSTED:
            raise BadRequestException("Only posted payments can have cheque status updated")

        # Validate status transition
        valid_transitions = {
            ChequeStatus.ISSUED: [ChequeStatus.DEPOSITED, ChequeStatus.CANCELLED],
            ChequeStatus.DEPOSITED: [
                ChequeStatus.CLEARED,
                ChequeStatus.BOUNCED,
                ChequeStatus.RETURNED,
            ],
            ChequeStatus.CLEARED: [],  # Final state
            ChequeStatus.BOUNCED: [ChequeStatus.RETURNED],
            ChequeStatus.CANCELLED: [],  # Final state
            ChequeStatus.RETURNED: [],  # Final state
        }

        current_status = payment.cheque_status
        new_status = data.cheque_status

        if new_status not in valid_transitions.get(current_status, []):
            raise BadRequestException(f"Cannot transition from {current_status} to {new_status}")

        payment.cheque_status = new_status
        payment.updated_by_id = updated_by_id
        payment.updated_at = datetime.utcnow()

        if new_status == ChequeStatus.CLEARED:
            payment.cheque_cleared_date = data.cleared_date
        elif new_status == ChequeStatus.BOUNCED:
            payment.cheque_bounced_date = data.bounced_date
            payment.cheque_bounced_reason = data.bounced_reason
            # Reverse document balance updates for bounced cheque
            await self._reverse_document_balances(payment)

        await self.session.flush()
        await self.session.refresh(payment)
        return payment

    async def get_pending_cheques(
        self,
        organization_id: UUID,
        *,
        party_type: PartyType | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[Sequence[Payment], int]:
        """Get pending cheques."""
        return await self.repo.get_pending_cheques(
            organization_id,
            party_type=party_type,
            from_date=from_date,
            to_date=to_date,
            skip=skip,
            limit=limit,
        )

    async def get_outstanding_documents(
        self,
        party_type: PartyType,
        party_id: UUID,
        organization_id: UUID,
    ) -> list[dict]:
        """Get outstanding documents for a party."""
        if party_type == PartyType.VENDOR:
            return await self.outstanding_repo.get_outstanding_bills(party_id, organization_id)
        else:
            return await self.outstanding_repo.get_outstanding_invoices(party_id, organization_id)

    async def delete_payment(
        self,
        payment_id: UUID,
        deleted_by_id: UUID,
    ) -> None:
        """Soft delete a draft payment."""
        payment = await self.get_by_id(payment_id)

        if payment.status != PaymentStatus.DRAFT:
            raise BadRequestException("Only draft payments can be deleted")

        # Capture old state for audit trail
        old_values = model_to_dict(payment)
        org_id = payment.organization_id
        payment_number = payment.payment_number

        await self.repo.soft_delete(payment_id, deleted_by_id)
        await self.session.flush()

        # Audit log: DELETE
        await self.audit_service.log_delete(
            organization_id=org_id,
            entity_type=EntityType.PAYMENT.value,
            entity_id=payment_id,
            entity_reference=payment_number,
            old_values=old_values,
            user_id=deleted_by_id,
        )

    # Private helper methods

    async def _validate_party(
        self,
        party_type: PartyType,
        vendor_id: UUID | None,
        customer_id: UUID | None,
    ) -> None:
        """Validate party exists."""
        from sqlalchemy import select

        from app.models.ap_ar.customer import Customer
        from app.models.ap_ar.vendor import Vendor

        if party_type == PartyType.VENDOR:
            if not vendor_id:
                raise BadRequestException("Vendor ID is required for vendor payment")
            query = select(Vendor).where(Vendor.id == vendor_id)
            result = await self.session.execute(query)
            if not result.scalar_one_or_none():
                raise NotFoundException("Vendor not found")
        else:
            if not customer_id:
                raise BadRequestException("Customer ID is required for customer receipt")
            query = select(Customer).where(Customer.id == customer_id)
            result = await self.session.execute(query)
            if not result.scalar_one_or_none():
                raise NotFoundException("Customer not found")

    async def _validate_allocations(self, data: PaymentCreate) -> None:
        """Validate allocation amounts against document balances."""
        from sqlalchemy import select

        for allocation in data.allocations:
            if allocation.document_type == DocumentType.PURCHASE_BILL:
                query = select(PurchaseBill).where(PurchaseBill.id == allocation.document_id)
                result = await self.session.execute(query)
                doc = result.scalar_one_or_none()
                if not doc:
                    raise NotFoundException(f"Purchase bill not found: {allocation.document_id}")
                if allocation.allocated_amount > doc.balance_amount:
                    raise BadRequestException(
                        f"Allocation amount ({allocation.allocated_amount}) exceeds "
                        f"outstanding balance ({doc.balance_amount}) for bill {doc.bill_number}"
                    )
            elif allocation.document_type == DocumentType.SALES_INVOICE:
                query = select(SalesInvoice).where(SalesInvoice.id == allocation.document_id)
                result = await self.session.execute(query)
                doc = result.scalar_one_or_none()
                if not doc:
                    raise NotFoundException(f"Sales invoice not found: {allocation.document_id}")
                if allocation.allocated_amount > doc.balance_amount:
                    raise BadRequestException(
                        f"Allocation amount ({allocation.allocated_amount}) exceeds "
                        f"outstanding balance ({doc.balance_amount}) for invoice {doc.invoice_number}"
                    )

    async def _create_allocations(
        self,
        payment: Payment,
        allocations: list[PaymentAllocationCreate],
    ) -> None:
        """Create payment allocations."""
        from sqlalchemy import select

        for alloc_data in allocations:
            # Get document details
            if alloc_data.document_type == DocumentType.PURCHASE_BILL:
                query = select(PurchaseBill).where(PurchaseBill.id == alloc_data.document_id)
                result = await self.session.execute(query)
                doc = result.scalar_one()
                doc_number = doc.bill_number
                doc_date = doc.bill_date
                doc_amount = doc.total_amount
                outstanding = doc.balance_amount
            elif alloc_data.document_type == DocumentType.SALES_INVOICE:
                query = select(SalesInvoice).where(SalesInvoice.id == alloc_data.document_id)
                result = await self.session.execute(query)
                doc = result.scalar_one()
                doc_number = doc.invoice_number
                doc_date = doc.invoice_date
                doc_amount = doc.total_amount
                outstanding = doc.balance_amount
            else:
                continue  # Skip other document types for now

            allocation = PaymentAllocation(
                payment_id=payment.id,
                document_type=alloc_data.document_type,
                document_id=alloc_data.document_id,
                document_number=doc_number,
                document_date=doc_date,
                document_amount=doc_amount,
                outstanding_before=outstanding,
                allocated_amount=alloc_data.allocated_amount,
                allocation_date=payment.payment_date,
            )
            self.session.add(allocation)

    async def _update_document_balances(self, payment: Payment) -> None:
        """Update document balances when payment is posted."""
        from sqlalchemy import select

        for allocation in payment.allocations:
            if allocation.document_type == DocumentType.PURCHASE_BILL:
                query = select(PurchaseBill).where(PurchaseBill.id == allocation.document_id)
                result = await self.session.execute(query)
                doc = result.scalar_one()
                doc.balance_amount -= allocation.allocated_amount

                # Update payment status
                if doc.balance_amount <= 0:
                    doc.balance_amount = Decimal("0.00")
                    doc.payment_status = BillPaymentStatus.PAID
                    doc.status = BillStatus.PAID
                else:
                    doc.payment_status = BillPaymentStatus.PARTIALLY_PAID
                    doc.status = BillStatus.PARTIALLY_PAID

            elif allocation.document_type == DocumentType.SALES_INVOICE:
                query = select(SalesInvoice).where(SalesInvoice.id == allocation.document_id)
                result = await self.session.execute(query)
                doc = result.scalar_one()
                doc.balance_amount -= allocation.allocated_amount

                # Update receipt status
                if doc.balance_amount <= 0:
                    doc.balance_amount = Decimal("0.00")
                    doc.receipt_status = ReceiptStatus.RECEIVED
                    doc.status = InvoiceStatus.RECEIVED
                else:
                    doc.receipt_status = ReceiptStatus.PARTIALLY_RECEIVED
                    doc.status = InvoiceStatus.PARTIALLY_RECEIVED

    async def _reverse_document_balances(self, payment: Payment) -> None:
        """Reverse document balance updates when payment is cancelled/bounced."""
        from sqlalchemy import select

        for allocation in payment.allocations:
            if allocation.document_type == DocumentType.PURCHASE_BILL:
                query = select(PurchaseBill).where(PurchaseBill.id == allocation.document_id)
                result = await self.session.execute(query)
                doc = result.scalar_one()
                doc.balance_amount += allocation.allocated_amount

                # Update payment status
                if doc.balance_amount >= doc.total_amount:
                    doc.payment_status = BillPaymentStatus.UNPAID
                    doc.status = BillStatus.APPROVED
                else:
                    doc.payment_status = BillPaymentStatus.PARTIALLY_PAID
                    doc.status = BillStatus.PARTIALLY_PAID

            elif allocation.document_type == DocumentType.SALES_INVOICE:
                query = select(SalesInvoice).where(SalesInvoice.id == allocation.document_id)
                result = await self.session.execute(query)
                doc = result.scalar_one()
                doc.balance_amount += allocation.allocated_amount

                # Update receipt status
                if doc.balance_amount >= doc.total_amount:
                    doc.receipt_status = ReceiptStatus.UNRECEIVED
                    doc.status = InvoiceStatus.APPROVED
                else:
                    doc.receipt_status = ReceiptStatus.PARTIALLY_RECEIVED
                    doc.status = InvoiceStatus.PARTIALLY_RECEIVED

    async def _post_to_gl(self, payment: Payment, posted_by: UUID | None) -> None:
        """
        Post payment to GL.

        For Vendor Payment (VENDOR_PAYMENT):
        - Dr. AP Control Account (vendor's control_account_id)
        - Cr. Bank/Cash Account (bank_account_id or cash_account_id)
        - Dr. TDS Payable Account (if TDS deducted - reduces liability)

        For Customer Receipt (CUSTOMER_RECEIPT):
        - Dr. Bank/Cash Account (bank_account_id or cash_account_id)
        - Cr. AR Control Account (customer's control_account_id)
        """
        # Skip if already posted
        if payment.is_posted:
            return

        # Get financial year and period
        fy = await self.fy_repo.get_by_date(payment.organization_id, payment.payment_date)
        if not fy:
            raise BadRequestException(
                f"No financial year found for payment date {payment.payment_date}"
            )

        period = await self.period_repo.get_by_date(fy.id, payment.payment_date)
        if not period:
            raise BadRequestException(f"No period found for payment date {payment.payment_date}")

        # Build GL entry lines
        gl_lines: list[dict[str, Any]] = []

        # Get bank/cash account
        payment_account_id = payment.bank_account_id or payment.cash_account_id
        if not payment_account_id:
            raise BadRequestException("Payment must have either bank or cash account")

        if payment.payment_type == PaymentType.VENDOR_PAYMENT:
            # Vendor Payment: Dr AP, Cr Bank/Cash
            vendor = await self.vendor_repo.get(payment.vendor_id)
            if not vendor or not vendor.control_account_id:
                raise BadRequestException("Vendor does not have a control account configured")

            # Dr. AP Control (pay off vendor liability)
            gl_lines.append(
                {
                    "account_id": vendor.control_account_id,
                    "debit_amount": payment.amount,
                    "credit_amount": Decimal("0"),
                    "party_type": GLPartyType.VENDOR,
                    "party_id": payment.vendor_id,
                    "narration": f"Payment to {vendor.name}",
                }
            )

            # Cr. Bank/Cash Account (net payment after TDS)
            gl_lines.append(
                {
                    "account_id": payment_account_id,
                    "debit_amount": Decimal("0"),
                    "credit_amount": payment.net_amount,
                    "narration": f"Payment: {payment.payment_number}",
                }
            )

            # If TDS was deducted, Dr. TDS Payable (reduce TDS liability as we're settling it)
            if payment.tds_amount and payment.tds_amount > 0:
                tds_account = await self._get_tds_payable_account(payment.organization_id)
                if tds_account:
                    gl_lines.append(
                        {
                            "account_id": tds_account,
                            "debit_amount": Decimal("0"),
                            "credit_amount": payment.tds_amount,
                            "narration": f"TDS on payment {payment.payment_number}",
                        }
                    )

        elif payment.payment_type == PaymentType.CUSTOMER_RECEIPT:
            # Customer Receipt: Dr Bank/Cash, Cr AR
            customer = await self.customer_repo.get(payment.customer_id)
            if not customer or not customer.control_account_id:
                raise BadRequestException("Customer does not have a control account configured")

            # Dr. Bank/Cash Account
            gl_lines.append(
                {
                    "account_id": payment_account_id,
                    "debit_amount": payment.net_amount,
                    "credit_amount": Decimal("0"),
                    "narration": f"Receipt: {payment.payment_number}",
                }
            )

            # Cr. AR Control (reduce customer receivable)
            gl_lines.append(
                {
                    "account_id": customer.control_account_id,
                    "debit_amount": Decimal("0"),
                    "credit_amount": payment.amount,
                    "party_type": GLPartyType.CUSTOMER,
                    "party_id": payment.customer_id,
                    "narration": f"Receipt from {customer.name}",
                }
            )

        # Post GL entries
        if gl_lines:
            await self.gl_posting_service.post_entries(
                organization_id=payment.organization_id,
                financial_year_id=fy.id,
                period_id=period.id,
                voucher_date=payment.payment_date,
                source_type=GLEntrySourceType.PAYMENT,
                source_id=payment.id,
                source_reference=payment.payment_number,
                lines=gl_lines,
                narration=f"Payment: {payment.payment_number}",
                posted_by=posted_by,
            )

    async def _create_tds_entry(self, payment: Payment, created_by: UUID | None) -> None:
        """Create TDS entry for TDS deducted on payment."""
        from app.schemas.tds.tds_entry import TDSEntryCreate

        if not payment.tds_amount or payment.tds_amount <= 0:
            return

        # Get vendor/deductee details
        deductee_pan = None
        deductee_name = None

        if payment.vendor_id:
            vendor = await self.vendor_repo.get(payment.vendor_id)
            if vendor:
                deductee_pan = vendor.pan
                deductee_name = vendor.name

        # Create TDS entry
        tds_data = TDSEntryCreate(
            organization_id=payment.organization_id,
            section_id=payment.tds_section_id,
            deductee_type="VENDOR",
            deductee_id=payment.vendor_id,
            deductee_pan=deductee_pan,
            deductee_name=deductee_name or "Unknown",
            transaction_date=payment.payment_date,
            base_amount=payment.amount,
            tds_rate=payment.tds_rate or Decimal("0"),
            tds_amount=payment.tds_amount,
            source_type="PAYMENT",
            source_id=payment.id,
            source_reference=payment.payment_number,
        )

        await self.tds_entry_service.create(tds_data, created_by)

    async def _get_tds_payable_account(self, organization_id: UUID) -> UUID | None:
        """Get TDS payable account for the organization."""
        # Search for TDS Payable account by code pattern
        accounts = await self.account_repo.search(
            organization_id=organization_id,
            query="TDS Payable",
            limit=1,
        )
        if accounts:
            return accounts[0].id

        # Fallback: search by common TDS account codes
        for code in ["TDS-PAY", "TDSPAY", "TDS_PAYABLE"]:
            account = await self.account_repo.get_by_code(organization_id, code)
            if account:
                return account.id

        return None
