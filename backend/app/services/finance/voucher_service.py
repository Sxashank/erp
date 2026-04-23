"""Voucher service."""

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException, ConflictException, BadRequestException
from app.models.finance.voucher import Voucher, VoucherLine
from app.models.common.audit_log import EntityType, AuditAction
from app.repositories.finance.voucher_repo import VoucherRepository, VoucherLineRepository
from app.repositories.finance.voucher_type_repo import VoucherTypeRepository
from app.repositories.finance.financial_year_repo import (
    FinancialYearRepository,
    FinancialPeriodRepository,
)
from app.repositories.finance.account_repo import AccountRepository
from app.repositories.masters.organization_repo import OrganizationRepository
from app.schemas.finance.voucher import (
    VoucherCreate,
    VoucherUpdate,
    VoucherLineCreate,
)
from app.core.constants import VoucherStatus, VoucherClass, GLEntrySourceType
from app.services.common.audit_service import AuditService, model_to_dict
from app.services.workflow import WorkflowEngine
from app.services.finance.gl_posting_service import GLPostingService
from app.models.workflow import WorkflowEntityType, WorkflowInstanceStatus


class VoucherService:
    """Service for voucher management."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = VoucherRepository(session)
        self.line_repo = VoucherLineRepository(session)
        self.vtype_repo = VoucherTypeRepository(session)
        self.fy_repo = FinancialYearRepository(session)
        self.period_repo = FinancialPeriodRepository(session)
        self.account_repo = AccountRepository(session)
        self.org_repo = OrganizationRepository(session)
        self.audit_service = AuditService(session)
        self.workflow_engine = WorkflowEngine(session)
        self.gl_posting_service = GLPostingService(session)

    async def create(
        self,
        data: VoucherCreate,
        created_by: Optional[UUID] = None,
    ) -> Voucher:
        """Create a new voucher."""
        # Verify organization exists
        org = await self.org_repo.get(data.organization_id)
        if not org:
            raise NotFoundException("Organization not found")

        # Verify voucher type
        vtype = await self.vtype_repo.get(data.voucher_type_id)
        if not vtype:
            raise NotFoundException("Voucher type not found")
        if vtype.organization_id != data.organization_id:
            raise BadRequestException("Voucher type must belong to the same organization")

        # Get financial year and period
        fy = await self.fy_repo.get_by_date(data.organization_id, data.voucher_date)
        if not fy:
            raise BadRequestException(
                f"No financial year found for date {data.voucher_date}"
            )
        if fy.is_closed:
            raise BadRequestException("Cannot post to a closed financial year")

        period = await self.period_repo.get_by_date(fy.id, data.voucher_date)
        if not period:
            raise BadRequestException(
                f"No period found for date {data.voucher_date}"
            )
        if period.is_closed:
            raise BadRequestException("Cannot post to a closed period")

        # Validate accounts exist and belong to organization
        for line in data.lines:
            account = await self.account_repo.get(line.account_id)
            if not account:
                raise NotFoundException(f"Account not found: {line.account_id}")
            if account.organization_id != data.organization_id:
                raise BadRequestException(
                    "All accounts must belong to the same organization"
                )

        # Generate voucher number
        voucher_number = vtype.get_next_number(fy.code)

        # Calculate totals
        total_debit = sum(line.debit_amount for line in data.lines)
        total_credit = sum(line.credit_amount for line in data.lines)

        # Create voucher
        voucher_data = {
            "voucher_type_id": data.voucher_type_id,
            "voucher_number": voucher_number,
            "voucher_date": data.voucher_date,
            "financial_year_id": fy.id,
            "period_id": period.id,
            "reference_number": data.reference_number,
            "reference_date": data.reference_date,
            "narration": data.narration,
            "total_debit": total_debit,
            "total_credit": total_credit,
            "status": VoucherStatus.DRAFT,
            "organization_id": data.organization_id,
            "unit_id": data.unit_id,
            "created_by": created_by,
        }
        voucher = await self.repo.create(voucher_data)

        # Create voucher lines
        for idx, line_data in enumerate(data.lines, start=1):
            line_dict = line_data.model_dump()
            line_dict["voucher_id"] = voucher.id
            line_dict["line_number"] = idx
            line_dict["created_by"] = created_by
            await self.line_repo.create(line_dict)

        await self.session.flush()
        await self.session.refresh(voucher)

        # Audit log: CREATE
        await self.audit_service.log_create(
            organization_id=voucher.organization_id,
            entity_type=EntityType.VOUCHER.value,
            entity_id=voucher.id,
            entity_reference=voucher.voucher_number,
            new_values=model_to_dict(voucher),
            user_id=created_by,
        )

        return voucher

    async def update(
        self,
        id: UUID,
        data: VoucherUpdate,
        updated_by: Optional[UUID] = None,
    ) -> Voucher:
        """Update a draft voucher."""
        voucher = await self.repo.get_with_lines(id)
        if not voucher:
            raise NotFoundException("Voucher not found")

        if voucher.status != VoucherStatus.DRAFT:
            raise BadRequestException("Only draft vouchers can be updated")

        # Capture old state for audit trail
        old_values = model_to_dict(voucher)
        old_lines = [model_to_dict(line) for line in voucher.lines]

        # Update voucher date if provided
        if data.voucher_date and data.voucher_date != voucher.voucher_date:
            # Re-validate period
            period = await self.period_repo.get_by_date(
                voucher.financial_year_id, data.voucher_date
            )
            if not period:
                raise BadRequestException(
                    f"No period found for date {data.voucher_date}"
                )
            if period.is_closed:
                raise BadRequestException("Cannot post to a closed period")

        # Update lines if provided
        if data.lines is not None:
            # Delete existing lines
            await self.line_repo.delete_by_voucher(voucher.id)

            # Create new lines
            total_debit = Decimal("0.00")
            total_credit = Decimal("0.00")
            for idx, line_data in enumerate(data.lines, start=1):
                # Validate account
                account = await self.account_repo.get(line_data.account_id)
                if not account:
                    raise NotFoundException(f"Account not found: {line_data.account_id}")
                if account.organization_id != voucher.organization_id:
                    raise BadRequestException(
                        "All accounts must belong to the same organization"
                    )

                line_dict = line_data.model_dump()
                line_dict["voucher_id"] = voucher.id
                line_dict["line_number"] = idx
                line_dict["created_by"] = updated_by
                await self.line_repo.create(line_dict)

                total_debit += line_data.debit_amount
                total_credit += line_data.credit_amount

            voucher.total_debit = total_debit
            voucher.total_credit = total_credit

        # Update other fields
        update_data = data.model_dump(exclude_unset=True, exclude={"lines"})
        update_data["updated_by"] = updated_by

        voucher = await self.repo.update(voucher, update_data)
        await self.session.flush()
        await self.session.refresh(voucher)

        # Audit log: UPDATE
        audit_entry = await self.audit_service.log_update(
            organization_id=voucher.organization_id,
            entity_type=EntityType.VOUCHER.value,
            entity_id=voucher.id,
            entity_reference=voucher.voucher_number,
            old_values=old_values,
            new_values=model_to_dict(voucher),
            user_id=updated_by,
        )

        # Log line item changes if lines were updated
        if data.lines is not None:
            new_lines = [model_to_dict(line) for line in voucher.lines]
            await self.audit_service.log_line_changes(
                parent_audit_id=audit_entry.id,
                entity_type="VOUCHER_LINE",
                old_lines=old_lines,
                new_lines=new_lines,
            )

        return voucher

    async def get(self, id: UUID) -> Voucher:
        """Get voucher by ID with lines."""
        voucher = await self.repo.get_with_lines(id)
        if not voucher:
            raise NotFoundException("Voucher not found")
        return voucher

    async def get_all(
        self,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False,
    ) -> Tuple[List[Voucher], int]:
        """Get all vouchers for an organization."""
        return await self.repo.get_by_organization(
            organization_id, skip, limit, include_inactive
        )

    async def get_by_status(
        self,
        organization_id: UUID,
        status: VoucherStatus,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[Voucher], int]:
        """Get vouchers by status."""
        return await self.repo.get_by_status(organization_id, status, skip, limit)

    async def get_by_date_range(
        self,
        organization_id: UUID,
        from_date: date,
        to_date: date,
        voucher_class: Optional[VoucherClass] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[Voucher], int]:
        """Get vouchers within a date range."""
        return await self.repo.get_by_date_range(
            organization_id, from_date, to_date, voucher_class, skip, limit
        )

    async def get_pending_approval(
        self,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Voucher]:
        """Get vouchers pending approval."""
        return await self.repo.get_pending_approval(organization_id, skip, limit)

    async def submit_for_approval(
        self,
        id: UUID,
        submitted_by: Optional[UUID] = None,
    ) -> Voucher:
        """Submit a voucher for approval using the workflow engine."""
        voucher = await self.repo.get_with_lines(id)
        if not voucher:
            raise NotFoundException("Voucher not found")

        if voucher.status != VoucherStatus.DRAFT:
            raise BadRequestException("Only draft vouchers can be submitted")

        if not voucher.is_balanced():
            raise BadRequestException("Voucher is not balanced")

        # Capture old state
        old_values = model_to_dict(voucher)

        # Check if approval is required
        if voucher.voucher_type.requires_approval:
            # Build workflow context
            context = {
                "amount": float(voucher.total_debit),
                "voucher_type": voucher.voucher_type.code if voucher.voucher_type else None,
                "voucher_class": voucher.voucher_type.voucher_class.value if voucher.voucher_type else None,
                "narration": voucher.narration,
            }

            # Try to start workflow
            try:
                workflow_instance = await self.workflow_engine.start_workflow(
                    entity_type=WorkflowEntityType.VOUCHER,
                    entity_id=voucher.id,
                    entity_reference=voucher.voucher_number,
                    organization_id=voucher.organization_id,
                    context=context,
                    started_by=submitted_by,
                )

                voucher.status = VoucherStatus.PENDING_APPROVAL
                voucher.submitted_at = datetime.now(timezone.utc)
                voucher.submitted_by = submitted_by
                voucher.workflow_instance_id = workflow_instance.id
            except Exception as e:
                # If no workflow definition exists, fall back to legacy approval
                voucher.status = VoucherStatus.PENDING_APPROVAL
                voucher.submitted_at = datetime.now(timezone.utc)
                voucher.submitted_by = submitted_by
                voucher.current_approval_level = 1
                voucher.approval_status = []
        else:
            # Direct approve and post
            voucher.status = VoucherStatus.APPROVED
            voucher.approved_at = datetime.now(timezone.utc)
            voucher.approved_by = submitted_by

        await self.session.flush()
        await self.session.refresh(voucher)

        # Audit log: status change action
        action = AuditAction.APPROVE.value if voucher.status == VoucherStatus.APPROVED else "SUBMIT"
        await self.audit_service.log_action(
            organization_id=voucher.organization_id,
            entity_type=EntityType.VOUCHER.value,
            entity_id=voucher.id,
            entity_reference=voucher.voucher_number,
            action=action,
            user_id=submitted_by,
            old_values=old_values,
            new_values=model_to_dict(voucher),
        )

        return voucher

    async def approve(
        self,
        id: UUID,
        approved_by: Optional[UUID] = None,
        remarks: Optional[str] = None,
    ) -> Voucher:
        """Approve a voucher (legacy method for non-workflow approvals)."""
        voucher = await self.repo.get_with_lines(id)
        if not voucher:
            raise NotFoundException("Voucher not found")

        if voucher.status != VoucherStatus.PENDING_APPROVAL:
            raise BadRequestException("Voucher is not pending approval")

        # If using workflow, redirect to workflow-based approval
        if voucher.workflow_instance_id:
            raise BadRequestException(
                "This voucher uses workflow-based approval. "
                "Please use the workflow task endpoints to approve."
            )

        # Capture old state
        old_values = model_to_dict(voucher)

        # Add approval record (legacy approval)
        approval_record = {
            "level": voucher.current_approval_level,
            "approved_by": str(approved_by) if approved_by else None,
            "approved_at": datetime.now(timezone.utc).isoformat(),
            "remarks": remarks,
        }
        if voucher.approval_status is None:
            voucher.approval_status = []
        voucher.approval_status.append(approval_record)

        # Check if all levels approved
        if voucher.current_approval_level >= voucher.voucher_type.approval_levels:
            voucher.status = VoucherStatus.APPROVED
            voucher.approved_at = datetime.now(timezone.utc)
            voucher.approved_by = approved_by
        else:
            voucher.current_approval_level += 1

        await self.session.flush()
        await self.session.refresh(voucher)

        # Audit log: APPROVE
        await self.audit_service.log_action(
            organization_id=voucher.organization_id,
            entity_type=EntityType.VOUCHER.value,
            entity_id=voucher.id,
            entity_reference=voucher.voucher_number,
            action=AuditAction.APPROVE.value,
            user_id=approved_by,
            old_values=old_values,
            new_values=model_to_dict(voucher),
            change_reason=remarks,
        )

        return voucher

    async def handle_workflow_complete(
        self,
        voucher_id: UUID,
        workflow_status: WorkflowInstanceStatus,
        completed_by: Optional[UUID] = None,
    ) -> Voucher:
        """Handle workflow completion callback to update voucher status."""
        voucher = await self.repo.get_with_lines(voucher_id)
        if not voucher:
            raise NotFoundException("Voucher not found")

        old_values = model_to_dict(voucher)

        if workflow_status == WorkflowInstanceStatus.APPROVED:
            voucher.status = VoucherStatus.APPROVED
            voucher.approved_at = datetime.now(timezone.utc)
            voucher.approved_by = completed_by
        elif workflow_status == WorkflowInstanceStatus.REJECTED:
            voucher.status = VoucherStatus.REJECTED
        elif workflow_status == WorkflowInstanceStatus.CANCELLED:
            voucher.status = VoucherStatus.DRAFT
            voucher.workflow_instance_id = None

        await self.session.flush()
        await self.session.refresh(voucher)

        # Audit log
        action = workflow_status.value
        await self.audit_service.log_action(
            organization_id=voucher.organization_id,
            entity_type=EntityType.VOUCHER.value,
            entity_id=voucher.id,
            entity_reference=voucher.voucher_number,
            action=action,
            user_id=completed_by,
            old_values=old_values,
            new_values=model_to_dict(voucher),
        )

        return voucher

    async def reject(
        self,
        id: UUID,
        rejected_by: Optional[UUID] = None,
        reason: Optional[str] = None,
    ) -> Voucher:
        """Reject a voucher."""
        voucher = await self.repo.get(id)
        if not voucher:
            raise NotFoundException("Voucher not found")

        if voucher.status != VoucherStatus.PENDING_APPROVAL:
            raise BadRequestException("Voucher is not pending approval")

        # Capture old state
        old_values = model_to_dict(voucher)

        voucher.status = VoucherStatus.REJECTED
        voucher.rejection_reason = reason

        await self.session.flush()
        await self.session.refresh(voucher)

        # Audit log: REJECT (custom action)
        await self.audit_service.log_action(
            organization_id=voucher.organization_id,
            entity_type=EntityType.VOUCHER.value,
            entity_id=voucher.id,
            entity_reference=voucher.voucher_number,
            action="REJECT",
            user_id=rejected_by,
            old_values=old_values,
            new_values=model_to_dict(voucher),
            change_reason=reason,
        )

        return voucher

    async def post(
        self,
        id: UUID,
        posted_by: Optional[UUID] = None,
    ) -> Voucher:
        """Post an approved voucher to the ledger."""
        voucher = await self.repo.get_with_lines(id)
        if not voucher:
            raise NotFoundException("Voucher not found")

        if voucher.status != VoucherStatus.APPROVED:
            raise BadRequestException("Only approved vouchers can be posted")

        # Capture old state
        old_values = model_to_dict(voucher)

        # Update account balances
        for line in voucher.lines:
            account = await self.account_repo.get(line.account_id)
            if account:
                if line.debit_amount > 0:
                    account.current_balance += line.debit_amount
                if line.credit_amount > 0:
                    account.current_balance -= line.credit_amount

        # Create GL Entry records for auditability
        await self._create_gl_entries(voucher, posted_by)

        voucher.status = VoucherStatus.POSTED
        voucher.posted_at = datetime.now(timezone.utc)
        voucher.posted_by = posted_by

        await self.session.flush()
        await self.session.refresh(voucher)

        # Audit log: POST
        await self.audit_service.log_action(
            organization_id=voucher.organization_id,
            entity_type=EntityType.VOUCHER.value,
            entity_id=voucher.id,
            entity_reference=voucher.voucher_number,
            action=AuditAction.POST.value,
            user_id=posted_by,
            old_values=old_values,
            new_values=model_to_dict(voucher),
        )

        return voucher

    async def _create_gl_entries(self, voucher: Voucher, posted_by: Optional[UUID]) -> None:
        """Create GL Entry records from voucher lines for audit trail."""
        # Build GL entry lines from voucher lines
        gl_lines: List[Dict[str, Any]] = []

        for line in voucher.lines:
            gl_lines.append({
                "account_id": line.account_id,
                "debit_amount": line.debit_amount or Decimal("0"),
                "credit_amount": line.credit_amount or Decimal("0"),
                "party_type": line.party_type,
                "party_id": line.party_id,
                "cost_center_id": line.cost_center_id,
                "narration": line.narration or voucher.narration,
            })

        if gl_lines:
            await self.gl_posting_service.post_entries(
                organization_id=voucher.organization_id,
                financial_year_id=voucher.financial_year_id,
                period_id=voucher.period_id,
                voucher_date=voucher.voucher_date,
                source_type=GLEntrySourceType.VOUCHER,
                source_id=voucher.id,
                source_reference=voucher.voucher_number,
                lines=gl_lines,
                narration=voucher.narration,
                posted_by=posted_by,
            )

    async def cancel(
        self,
        id: UUID,
        cancelled_by: Optional[UUID] = None,
        reason: Optional[str] = None,
    ) -> Voucher:
        """Cancel a voucher."""
        voucher = await self.repo.get_with_lines(id)
        if not voucher:
            raise NotFoundException("Voucher not found")

        if voucher.status == VoucherStatus.CANCELLED:
            raise BadRequestException("Voucher is already cancelled")

        # Capture old state
        old_values = model_to_dict(voucher)

        # If posted, reverse the account balances and create reversal GL entries
        if voucher.status == VoucherStatus.POSTED:
            for line in voucher.lines:
                account = await self.account_repo.get(line.account_id)
                if account:
                    if line.debit_amount > 0:
                        account.current_balance -= line.debit_amount
                    if line.credit_amount > 0:
                        account.current_balance += line.credit_amount

            # Create reversal GL entries
            await self._create_reversal_gl_entries(voucher, cancelled_by, reason)

        voucher.status = VoucherStatus.CANCELLED
        voucher.cancelled_at = datetime.now(timezone.utc)
        voucher.cancelled_by = cancelled_by
        voucher.cancellation_reason = reason

        await self.session.flush()
        await self.session.refresh(voucher)

        # Audit log: CANCEL
        await self.audit_service.log_action(
            organization_id=voucher.organization_id,
            entity_type=EntityType.VOUCHER.value,
            entity_id=voucher.id,
            entity_reference=voucher.voucher_number,
            action=AuditAction.CANCEL.value,
            user_id=cancelled_by,
            old_values=old_values,
            new_values=model_to_dict(voucher),
            change_reason=reason,
        )

        return voucher

    async def _create_reversal_gl_entries(
        self,
        voucher: Voucher,
        reversed_by: Optional[UUID],
        reason: Optional[str] = None,
    ) -> None:
        """Create reversal GL entries when voucher is cancelled."""
        # Reverse entries by swapping debit and credit
        gl_lines: List[Dict[str, Any]] = []

        for line in voucher.lines:
            gl_lines.append({
                "account_id": line.account_id,
                "debit_amount": line.credit_amount or Decimal("0"),  # Swap
                "credit_amount": line.debit_amount or Decimal("0"),  # Swap
                "party_type": line.party_type,
                "party_id": line.party_id,
                "cost_center_id": line.cost_center_id,
                "narration": f"Reversal: {line.narration or voucher.narration}",
            })

        if gl_lines:
            reversal_narration = f"Reversal of {voucher.voucher_number}"
            if reason:
                reversal_narration += f" - {reason}"

            await self.gl_posting_service.post_entries(
                organization_id=voucher.organization_id,
                financial_year_id=voucher.financial_year_id,
                period_id=voucher.period_id,
                voucher_date=datetime.now(timezone.utc).date(),
                source_type=GLEntrySourceType.VOUCHER,
                source_id=voucher.id,
                source_reference=f"REV-{voucher.voucher_number}",
                lines=gl_lines,
                narration=reversal_narration,
                posted_by=reversed_by,
                is_reversal=True,
                original_entry_id=voucher.id,
            )

    async def delete(
        self,
        id: UUID,
        deleted_by: Optional[UUID] = None,
    ) -> Voucher:
        """Soft delete a voucher (only draft)."""
        voucher = await self.repo.get(id)
        if not voucher:
            raise NotFoundException("Voucher not found")

        if voucher.status != VoucherStatus.DRAFT:
            raise BadRequestException("Only draft vouchers can be deleted")

        # Capture old state for audit trail
        old_values = model_to_dict(voucher)
        org_id = voucher.organization_id
        voucher_number = voucher.voucher_number

        result = await self.repo.soft_delete(id, deleted_by)

        # Audit log: DELETE
        await self.audit_service.log_delete(
            organization_id=org_id,
            entity_type=EntityType.VOUCHER.value,
            entity_id=id,
            entity_reference=voucher_number,
            old_values=old_values,
            user_id=deleted_by,
        )

        return result
