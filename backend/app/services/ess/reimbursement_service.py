"""ESS Reimbursement Claims Service."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List, Tuple
from uuid import UUID

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.ess.reimbursement import (
    ReimbursementCategory,
    ReimbursementClaim,
    ReimbursementLineItem,
    ReimbursementApproval,
)
from app.models.ess.enums import ClaimType, ClaimStatus


class ESSReimbursementService:
    """Service for ESS Reimbursement Claims management."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # ==================== Category Management ====================

    async def get_categories(
        self,
        organization_id: UUID,
        active_only: bool = True,
    ) -> List[ReimbursementCategory]:
        """Get reimbursement categories."""
        query = select(ReimbursementCategory).where(
            ReimbursementCategory.organization_id == organization_id
        )
        if active_only:
            query = query.where(ReimbursementCategory.is_active == True)
        query = query.order_by(ReimbursementCategory.name)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_category_by_id(
        self, category_id: UUID
    ) -> Optional[ReimbursementCategory]:
        """Get category by ID."""
        query = select(ReimbursementCategory).where(
            ReimbursementCategory.id == category_id
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    # ==================== Claim Management ====================

    async def generate_claim_number(self, organization_id: UUID) -> str:
        """Generate unique claim number."""
        today = date.today()
        prefix = f"CLM{today.strftime('%Y%m')}"

        # Get count of claims this month
        query = select(func.count()).select_from(ReimbursementClaim).where(
            and_(
                ReimbursementClaim.organization_id == organization_id,
                ReimbursementClaim.claim_number.like(f"{prefix}%")
            )
        )
        result = await self.session.execute(query)
        count = result.scalar() or 0

        return f"{prefix}{count + 1:04d}"

    async def create_claim(
        self,
        organization_id: UUID,
        ess_user_id: UUID,
        employee_id: UUID,
        claim_type: ClaimType,
        expense_from: date,
        expense_to: date,
        description: str,
        claimed_amount: Decimal,
        category_id: Optional[UUID] = None,
        purpose: Optional[str] = None,
        travel_from: Optional[str] = None,
        travel_to: Optional[str] = None,
        travel_mode: Optional[str] = None,
        kilometers: Optional[Decimal] = None,
        attachments: Optional[dict] = None,
        save_as_draft: bool = False,
    ) -> ReimbursementClaim:
        """Create a new reimbursement claim."""
        claim_number = await self.generate_claim_number(organization_id)

        claim = ReimbursementClaim(
            organization_id=organization_id,
            ess_user_id=ess_user_id,
            employee_id=employee_id,
            claim_number=claim_number,
            claim_date=date.today(),
            category_id=category_id,
            claim_type=claim_type,
            expense_from=expense_from,
            expense_to=expense_to,
            claimed_amount=claimed_amount,
            description=description,
            purpose=purpose,
            travel_from=travel_from,
            travel_to=travel_to,
            travel_mode=travel_mode,
            kilometers=kilometers,
            bills_attached=0,
            attachments=attachments,
            status=ClaimStatus.DRAFT if save_as_draft else ClaimStatus.SUBMITTED,
        )
        self.session.add(claim)
        await self.session.flush()
        return claim

    async def get_claim_by_id(
        self,
        claim_id: UUID,
        include_items: bool = True,
    ) -> Optional[ReimbursementClaim]:
        """Get claim by ID."""
        query = select(ReimbursementClaim).where(
            ReimbursementClaim.id == claim_id
        )
        if include_items:
            query = query.options(
                selectinload(ReimbursementClaim.line_items),
                selectinload(ReimbursementClaim.approval_history),
            )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_claims_by_employee(
        self,
        employee_id: UUID,
        status: Optional[ClaimStatus] = None,
        claim_type: Optional[ClaimType] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[ReimbursementClaim], int]:
        """Get claims for an employee with filters."""
        query = select(ReimbursementClaim).where(
            ReimbursementClaim.employee_id == employee_id
        )

        if status:
            query = query.where(ReimbursementClaim.status == status)
        if claim_type:
            query = query.where(ReimbursementClaim.claim_type == claim_type)
        if from_date:
            query = query.where(ReimbursementClaim.claim_date >= from_date)
        if to_date:
            query = query.where(ReimbursementClaim.claim_date <= to_date)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        # Apply pagination
        query = query.order_by(ReimbursementClaim.claim_date.desc())
        query = query.offset(offset).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all()), total

    async def get_pending_claims_for_approval(
        self,
        organization_id: UUID,
        approver_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[ReimbursementClaim], int]:
        """Get claims pending approval."""
        query = select(ReimbursementClaim).where(
            and_(
                ReimbursementClaim.organization_id == organization_id,
                ReimbursementClaim.status == ClaimStatus.SUBMITTED,
            )
        )

        # Workflow hierarchy filtering is applied by the admin approval layer.

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        # Apply pagination
        query = query.order_by(ReimbursementClaim.claim_date.asc())
        query = query.offset(offset).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all()), total

    async def update_claim(
        self,
        claim_id: UUID,
        **kwargs
    ) -> Optional[ReimbursementClaim]:
        """Update claim details."""
        claim = await self.get_claim_by_id(claim_id)
        if not claim:
            return None

        # Only allow updates for draft claims
        if claim.status not in [ClaimStatus.DRAFT, ClaimStatus.REJECTED]:
            raise ValueError("Cannot update submitted claim")

        for key, value in kwargs.items():
            if hasattr(claim, key) and key not in ['id', 'claim_number', 'organization_id']:
                setattr(claim, key, value)

        await self.session.flush()
        return claim

    async def submit_claim(self, claim_id: UUID) -> Optional[ReimbursementClaim]:
        """Submit a draft claim for approval."""
        claim = await self.get_claim_by_id(claim_id)
        if not claim:
            return None

        if claim.status != ClaimStatus.DRAFT:
            raise ValueError("Only draft claims can be submitted")

        claim.status = ClaimStatus.SUBMITTED
        await self.session.flush()
        return claim

    async def cancel_claim(
        self,
        claim_id: UUID,
        reason: Optional[str] = None,
    ) -> Optional[ReimbursementClaim]:
        """Cancel a claim."""
        claim = await self.get_claim_by_id(claim_id)
        if not claim:
            return None

        if claim.status not in [ClaimStatus.DRAFT, ClaimStatus.SUBMITTED]:
            raise ValueError("Cannot cancel processed claim")

        claim.status = ClaimStatus.CANCELLED
        if reason:
            claim.rejection_reason = reason

        await self.session.flush()
        return claim

    # ==================== Line Items ====================

    async def add_line_item(
        self,
        claim_id: UUID,
        expense_date: date,
        description: str,
        amount: Decimal,
        bill_number: Optional[str] = None,
        bill_date: Optional[date] = None,
        vendor_name: Optional[str] = None,
        vendor_gstin: Optional[str] = None,
        gst_amount: Optional[Decimal] = None,
        gst_rate: Optional[Decimal] = None,
        attachment_url: Optional[str] = None,
        attachment_name: Optional[str] = None,
    ) -> ReimbursementLineItem:
        """Add a line item to a claim."""
        claim = await self.get_claim_by_id(claim_id, include_items=True)
        if not claim:
            raise ValueError("Claim not found")

        if claim.status not in [ClaimStatus.DRAFT]:
            raise ValueError("Cannot add items to submitted claim")

        # Get next line number
        line_number = len(claim.line_items) + 1

        item = ReimbursementLineItem(
            claim_id=claim_id,
            line_number=line_number,
            expense_date=expense_date,
            description=description,
            amount=amount,
            bill_number=bill_number,
            bill_date=bill_date,
            vendor_name=vendor_name,
            vendor_gstin=vendor_gstin,
            gst_amount=gst_amount,
            gst_rate=gst_rate,
            attachment_url=attachment_url,
            attachment_name=attachment_name,
        )
        self.session.add(item)

        # Update claim totals
        claim.claimed_amount += amount
        claim.bills_attached += 1 if attachment_url else 0

        await self.session.flush()
        return item

    async def remove_line_item(
        self,
        claim_id: UUID,
        line_item_id: UUID,
    ) -> bool:
        """Remove a line item from a claim."""
        claim = await self.get_claim_by_id(claim_id, include_items=True)
        if not claim:
            return False

        if claim.status not in [ClaimStatus.DRAFT]:
            raise ValueError("Cannot modify submitted claim")

        item = next((i for i in claim.line_items if i.id == line_item_id), None)
        if not item:
            return False

        # Update claim totals
        claim.claimed_amount -= item.amount
        if item.attachment_url:
            claim.bills_attached -= 1

        await self.session.delete(item)
        await self.session.flush()
        return True

    # ==================== Approval ====================

    async def approve_claim(
        self,
        claim_id: UUID,
        approver_id: UUID,
        approved_amount: Optional[Decimal] = None,
        remarks: Optional[str] = None,
    ) -> Optional[ReimbursementClaim]:
        """Approve a claim."""
        claim = await self.get_claim_by_id(claim_id)
        if not claim:
            return None

        if claim.status != ClaimStatus.SUBMITTED:
            raise ValueError("Only submitted claims can be approved")

        # Set approved amount
        final_amount = approved_amount if approved_amount is not None else claim.claimed_amount
        claim.approved_amount = final_amount
        claim.approved_by = approver_id
        claim.approved_date = date.today()

        # Set status
        if approved_amount and approved_amount < claim.claimed_amount:
            claim.status = ClaimStatus.PARTIALLY_APPROVED
        else:
            claim.status = ClaimStatus.APPROVED

        # Record approval
        approval = ReimbursementApproval(
            claim_id=claim_id,
            approval_level=1,
            approver_id=approver_id,
            action="APPROVED",
            action_date=datetime.utcnow(),
            remarks=remarks,
            approved_amount=final_amount,
        )
        self.session.add(approval)

        await self.session.flush()
        return claim

    async def reject_claim(
        self,
        claim_id: UUID,
        approver_id: UUID,
        reason: str,
    ) -> Optional[ReimbursementClaim]:
        """Reject a claim."""
        claim = await self.get_claim_by_id(claim_id)
        if not claim:
            return None

        if claim.status != ClaimStatus.SUBMITTED:
            raise ValueError("Only submitted claims can be rejected")

        claim.status = ClaimStatus.REJECTED
        claim.rejection_reason = reason

        # Record rejection
        approval = ReimbursementApproval(
            claim_id=claim_id,
            approval_level=1,
            approver_id=approver_id,
            action="REJECTED",
            action_date=datetime.utcnow(),
            remarks=reason,
        )
        self.session.add(approval)

        await self.session.flush()
        return claim

    async def mark_as_paid(
        self,
        claim_id: UUID,
        payment_reference: str,
        payment_date: date,
        payment_mode: Optional[str] = None,
    ) -> Optional[ReimbursementClaim]:
        """Mark claim as paid."""
        claim = await self.get_claim_by_id(claim_id)
        if not claim:
            return None

        if claim.status not in [ClaimStatus.APPROVED, ClaimStatus.PARTIALLY_APPROVED]:
            raise ValueError("Only approved claims can be marked as paid")

        claim.status = ClaimStatus.PAID
        claim.payment_date = payment_date
        claim.payment_reference = payment_reference
        claim.payment_mode = payment_mode

        await self.session.flush()
        return claim

    # ==================== Analytics ====================

    async def get_claim_summary(
        self,
        employee_id: UUID,
        financial_year: Optional[str] = None,
    ) -> dict:
        """Get claim summary for an employee."""
        # Determine date range for financial year
        if financial_year:
            # Parse FY like "2024-25"
            start_year = int(financial_year.split("-")[0])
            start_date = date(start_year, 4, 1)
            end_date = date(start_year + 1, 3, 31)
        else:
            # Current FY
            today = date.today()
            if today.month >= 4:
                start_date = date(today.year, 4, 1)
                end_date = date(today.year + 1, 3, 31)
            else:
                start_date = date(today.year - 1, 4, 1)
                end_date = date(today.year, 3, 31)

        # Query summary
        query = select(
            ReimbursementClaim.status,
            func.count().label("count"),
            func.sum(ReimbursementClaim.claimed_amount).label("claimed"),
            func.sum(ReimbursementClaim.approved_amount).label("approved"),
        ).where(
            and_(
                ReimbursementClaim.employee_id == employee_id,
                ReimbursementClaim.claim_date >= start_date,
                ReimbursementClaim.claim_date <= end_date,
            )
        ).group_by(ReimbursementClaim.status)

        result = await self.session.execute(query)
        rows = result.all()

        summary = {
            "financial_year": financial_year or f"{start_date.year}-{str(end_date.year)[-2:]}",
            "total_claims": 0,
            "total_claimed": Decimal("0"),
            "total_approved": Decimal("0"),
            "total_paid": Decimal("0"),
            "pending_claims": 0,
            "by_status": {}
        }

        for row in rows:
            status = row.status if row.status else "UNKNOWN"
            summary["by_status"][status] = {
                "count": row.count,
                "claimed": float(row.claimed or 0),
                "approved": float(row.approved or 0),
            }
            summary["total_claims"] += row.count
            summary["total_claimed"] += row.claimed or Decimal("0")
            summary["total_approved"] += row.approved or Decimal("0")

            if status == ClaimStatus.PAID.value:
                summary["total_paid"] += row.approved or Decimal("0")
            elif status in [ClaimStatus.SUBMITTED.value, ClaimStatus.PENDING_APPROVAL.value]:
                summary["pending_claims"] += row.count

        # Convert decimals to float for JSON serialization
        summary["total_claimed"] = float(summary["total_claimed"])
        summary["total_approved"] = float(summary["total_approved"])
        summary["total_paid"] = float(summary["total_paid"])

        return summary
