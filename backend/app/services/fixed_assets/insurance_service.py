"""Insurance Service.

This service handles:
- Insurance policy management
- Claims processing
- Premium tracking
- Coverage analytics
"""

from datetime import date, timedelta
from decimal import Decimal
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.fixed_assets.insurance import (
    InsurancePolicy,
    InsuranceClaim,
    InsurancePolicyStatus,
    InsuranceType,
    ClaimStatus,
)
from app.schemas.fixed_assets.insurance import (
    InsurancePolicyCreate,
    InsurancePolicyUpdate,
    InsurancePolicyRenew,
    InsurancePremiumPayment,
    InsuranceClaimCreate,
    InsuranceClaimUpdate,
    InsuranceClaimSettle,
    InsuranceSummaryResponse,
)
from app.core.exceptions import ConcurrentModificationError
from app.core.optimistic_lock import increment_version


class InsuranceService:
    """Service for insurance operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # =========================================
    # Policy Operations
    # =========================================

    async def create_policy(
        self,
        data: InsurancePolicyCreate,
        created_by: UUID,
    ) -> InsurancePolicy:
        """Create a new insurance policy."""
        # Calculate totals
        gst_amount = data.base_premium * data.gst_rate / 100
        total_premium = data.base_premium + gst_amount + data.stamp_duty

        policy = InsurancePolicy(
            organization_id=data.organization_id,
            policy_number=data.policy_number,
            policy_name=data.policy_name,
            insurance_type=data.insurance_type,
            status=InsurancePolicyStatus.DRAFT,
            insurer_name=data.insurer_name,
            insurer_id=data.insurer_id,
            broker_name=data.broker_name,
            broker_id=data.broker_id,
            contact_person=data.contact_person,
            contact_phone=data.contact_phone,
            contact_email=data.contact_email,
            claim_helpline=data.claim_helpline,
            start_date=data.start_date,
            end_date=data.end_date,
            sum_insured=data.sum_insured,
            coverage_description=data.coverage_description,
            exclusions=data.exclusions,
            deductible_amount=data.deductible_amount,
            deductible_percentage=data.deductible_percentage,
            base_premium=data.base_premium,
            gst_rate=data.gst_rate,
            gst_amount=gst_amount,
            stamp_duty=data.stamp_duty,
            total_premium=total_premium,
            payment_mode=data.payment_mode,
            asset_ids=data.asset_ids,
            covers_all_assets=data.covers_all_assets,
            is_renewable=data.is_renewable,
            renewal_reminder_days=data.renewal_reminder_days,
            policy_document_url=data.policy_document_url,
            terms_conditions=data.terms_conditions,
            notes=data.notes,
            created_by=created_by,
            updated_by=created_by,
        )

        self.session.add(policy)
        await self.session.flush()
        await self.session.refresh(policy)

        return policy

    async def get_policy(self, policy_id: UUID) -> Optional[InsurancePolicy]:
        """Get insurance policy by ID."""
        result = await self.session.execute(
            select(InsurancePolicy)
            .options(
                selectinload(InsurancePolicy.insurer),
                selectinload(InsurancePolicy.broker),
            )
            .where(InsurancePolicy.id == policy_id)
        )
        return result.scalar_one_or_none()

    async def list_policies(
        self,
        organization_id: UUID,
        status: Optional[InsurancePolicyStatus] = None,
        insurance_type: Optional[InsuranceType] = None,
        expiring_within_days: Optional[int] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[InsurancePolicy], int]:
        """List insurance policies with filters."""
        query = (
            select(InsurancePolicy)
            .options(selectinload(InsurancePolicy.insurer))
            .where(InsurancePolicy.organization_id == organization_id)
        )

        if status:
            query = query.where(InsurancePolicy.status == status)

        if insurance_type:
            query = query.where(InsurancePolicy.insurance_type == insurance_type)

        if expiring_within_days:
            cutoff = date.today() + timedelta(days=expiring_within_days)
            query = query.where(
                InsurancePolicy.end_date <= cutoff,
                InsurancePolicy.status == InsurancePolicyStatus.ACTIVE,
            )

        # Count
        count_query = select(func.count(InsurancePolicy.id)).where(
            InsurancePolicy.organization_id == organization_id
        )
        if status:
            count_query = count_query.where(InsurancePolicy.status == status)

        total = await self.session.scalar(count_query)

        result = await self.session.execute(
            query.order_by(InsurancePolicy.end_date).offset(skip).limit(limit)
        )
        policies = list(result.scalars().all())

        return policies, total or 0

    async def update_policy(
        self,
        policy_id: UUID,
        data: InsurancePolicyUpdate,
        updated_by: UUID,
        expected_version: Optional[int] = None,
    ) -> Optional[InsurancePolicy]:
        """Update insurance policy.

        Args:
            policy_id: Policy UUID
            data: Update data
            updated_by: User performing the update
            expected_version: If provided, enables optimistic locking.
        """
        policy = await self.get_policy(policy_id)
        if not policy:
            return None

        # Optimistic locking check
        if expected_version is not None and policy.version != expected_version:
            raise ConcurrentModificationError(
                f"Insurance policy {policy.policy_number} was modified by another user. "
                "Please refresh and try again."
            )

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(policy, field, value)

        policy.updated_by = updated_by
        increment_version(policy)

        await self.session.flush()
        await self.session.refresh(policy)

        return policy

    async def activate_policy(
        self,
        policy_id: UUID,
        activated_by: UUID,
    ) -> InsurancePolicy:
        """Activate an insurance policy."""
        policy = await self.get_policy(policy_id)
        if not policy:
            raise ValueError("Policy not found")

        if policy.status != InsurancePolicyStatus.DRAFT:
            raise ValueError("Only draft policies can be activated")

        policy.status = InsurancePolicyStatus.ACTIVE
        policy.updated_by = activated_by

        await self.session.flush()
        await self.session.refresh(policy)

        return policy

    async def record_premium_payment(
        self,
        policy_id: UUID,
        data: InsurancePremiumPayment,
        recorded_by: UUID,
    ) -> InsurancePolicy:
        """Record premium payment for a policy."""
        policy = await self.get_policy(policy_id)
        if not policy:
            raise ValueError("Policy not found")

        policy.premium_paid = True
        policy.premium_paid_date = data.payment_date
        policy.payment_reference = data.payment_reference

        # Calculate next premium due based on payment mode
        if policy.payment_mode == "ANNUAL":
            policy.next_premium_due = None  # Fully paid
        elif policy.payment_mode == "HALF_YEARLY":
            policy.next_premium_due = data.payment_date + timedelta(days=182)
        elif policy.payment_mode == "QUARTERLY":
            policy.next_premium_due = data.payment_date + timedelta(days=91)
        elif policy.payment_mode == "MONTHLY":
            policy.next_premium_due = data.payment_date + timedelta(days=30)

        policy.updated_by = recorded_by

        await self.session.flush()
        await self.session.refresh(policy)

        return policy

    async def renew_policy(
        self,
        policy_id: UUID,
        data: InsurancePolicyRenew,
        renewed_by: UUID,
    ) -> InsurancePolicy:
        """Renew an insurance policy."""
        old_policy = await self.get_policy(policy_id)
        if not old_policy:
            raise ValueError("Policy not found")

        # Mark old policy as renewed
        old_policy.status = InsurancePolicyStatus.RENEWED
        old_policy.updated_by = renewed_by

        # Calculate new premium amounts
        gst_amount = data.new_base_premium * old_policy.gst_rate / 100
        total_premium = data.new_base_premium + gst_amount + old_policy.stamp_duty

        # Create new policy
        new_number = f"{old_policy.policy_number}-R{date.today().year}"
        new_policy = InsurancePolicy(
            organization_id=old_policy.organization_id,
            policy_number=new_number,
            policy_name=old_policy.policy_name,
            insurance_type=old_policy.insurance_type,
            status=InsurancePolicyStatus.ACTIVE,
            insurer_name=old_policy.insurer_name,
            insurer_id=old_policy.insurer_id,
            broker_name=old_policy.broker_name,
            broker_id=old_policy.broker_id,
            contact_person=old_policy.contact_person,
            contact_phone=old_policy.contact_phone,
            contact_email=old_policy.contact_email,
            claim_helpline=old_policy.claim_helpline,
            start_date=data.new_start_date,
            end_date=data.new_end_date,
            sum_insured=data.new_sum_insured,
            coverage_description=old_policy.coverage_description,
            exclusions=old_policy.exclusions,
            deductible_amount=old_policy.deductible_amount,
            deductible_percentage=old_policy.deductible_percentage,
            base_premium=data.new_base_premium,
            gst_rate=old_policy.gst_rate,
            gst_amount=gst_amount,
            stamp_duty=old_policy.stamp_duty,
            total_premium=total_premium,
            payment_mode=old_policy.payment_mode,
            asset_ids=old_policy.asset_ids,
            covers_all_assets=old_policy.covers_all_assets,
            is_renewable=old_policy.is_renewable,
            renewal_reminder_days=old_policy.renewal_reminder_days,
            previous_policy_id=old_policy.id,
            created_by=renewed_by,
            updated_by=renewed_by,
        )

        self.session.add(new_policy)
        await self.session.flush()
        await self.session.refresh(new_policy)

        return new_policy

    # =========================================
    # Claim Operations
    # =========================================

    async def create_claim(
        self,
        data: InsuranceClaimCreate,
        created_by: UUID,
    ) -> InsuranceClaim:
        """Create a new insurance claim."""
        # Generate claim number
        claim_number = await self._generate_claim_number(data.organization_id)

        claim = InsuranceClaim(
            organization_id=data.organization_id,
            policy_id=data.policy_id,
            claim_number=claim_number,
            asset_id=data.asset_id,
            status=ClaimStatus.DRAFT,
            incident_date=data.incident_date,
            incident_description=data.incident_description,
            incident_location=data.incident_location,
            cause_of_loss=data.cause_of_loss,
            reported_date=data.reported_date,
            reported_by=created_by,
            fir_number=data.fir_number,
            fir_date=data.fir_date,
            estimated_loss=data.estimated_loss,
            claim_amount=data.claim_amount,
            notes=data.notes,
            created_by=created_by,
            updated_by=created_by,
        )

        self.session.add(claim)

        # Update policy claim count
        policy = await self.get_policy(data.policy_id)
        if policy:
            policy.total_claims_count += 1
            policy.total_claims_amount += data.claim_amount

        await self.session.flush()
        await self.session.refresh(claim)

        return claim

    async def get_claim(self, claim_id: UUID) -> Optional[InsuranceClaim]:
        """Get insurance claim by ID."""
        result = await self.session.execute(
            select(InsuranceClaim)
            .options(
                selectinload(InsuranceClaim.policy),
                selectinload(InsuranceClaim.asset),
            )
            .where(InsuranceClaim.id == claim_id)
        )
        return result.scalar_one_or_none()

    async def list_claims(
        self,
        organization_id: UUID,
        policy_id: Optional[UUID] = None,
        asset_id: Optional[UUID] = None,
        status: Optional[ClaimStatus] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[InsuranceClaim], int]:
        """List insurance claims with filters."""
        query = (
            select(InsuranceClaim)
            .options(
                selectinload(InsuranceClaim.policy),
                selectinload(InsuranceClaim.asset),
            )
            .where(InsuranceClaim.organization_id == organization_id)
        )

        if policy_id:
            query = query.where(InsuranceClaim.policy_id == policy_id)
        if asset_id:
            query = query.where(InsuranceClaim.asset_id == asset_id)
        if status:
            query = query.where(InsuranceClaim.status == status)
        if from_date:
            query = query.where(InsuranceClaim.incident_date >= from_date)
        if to_date:
            query = query.where(InsuranceClaim.incident_date <= to_date)

        # Count
        count_query = select(func.count(InsuranceClaim.id)).where(
            InsuranceClaim.organization_id == organization_id
        )
        total = await self.session.scalar(count_query)

        result = await self.session.execute(
            query.order_by(InsuranceClaim.incident_date.desc())
            .offset(skip).limit(limit)
        )
        claims = list(result.scalars().all())

        return claims, total or 0

    async def update_claim(
        self,
        claim_id: UUID,
        data: InsuranceClaimUpdate,
        updated_by: UUID,
    ) -> Optional[InsuranceClaim]:
        """Update insurance claim."""
        claim = await self.get_claim(claim_id)
        if not claim:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(claim, field, value)

        # Update approval date if status changes to approved
        if data.status == ClaimStatus.APPROVED:
            claim.approval_date = date.today()

        claim.updated_by = updated_by
        await self.session.flush()
        await self.session.refresh(claim)

        return claim

    async def submit_claim(
        self,
        claim_id: UUID,
        submitted_by: UUID,
    ) -> InsuranceClaim:
        """Submit a claim to insurer."""
        claim = await self.get_claim(claim_id)
        if not claim:
            raise ValueError("Claim not found")

        if claim.status != ClaimStatus.DRAFT:
            raise ValueError("Only draft claims can be submitted")

        claim.status = ClaimStatus.SUBMITTED
        claim.submitted_date = date.today()
        claim.updated_by = submitted_by

        await self.session.flush()
        await self.session.refresh(claim)

        return claim

    async def settle_claim(
        self,
        claim_id: UUID,
        data: InsuranceClaimSettle,
        settled_by: UUID,
    ) -> InsuranceClaim:
        """Settle an insurance claim."""
        claim = await self.get_claim(claim_id)
        if not claim:
            raise ValueError("Claim not found")

        if claim.status not in [ClaimStatus.APPROVED, ClaimStatus.PARTIALLY_APPROVED]:
            raise ValueError("Only approved claims can be settled")

        claim.status = ClaimStatus.SETTLED
        claim.settlement_date = data.settlement_date
        claim.settled_amount = data.settled_amount
        claim.payment_received_date = data.payment_received_date
        claim.payment_reference = data.payment_reference
        claim.asset_written_off = data.asset_written_off
        claim.asset_repaired = data.asset_repaired
        claim.repair_cost = data.repair_cost
        claim.updated_by = settled_by

        # Update policy totals
        policy = await self.get_policy(claim.policy_id)
        if policy:
            policy.total_settled_amount += data.settled_amount

        await self.session.flush()
        await self.session.refresh(claim)

        return claim

    # =========================================
    # Analytics
    # =========================================

    async def get_insurance_summary(
        self,
        organization_id: UUID,
        as_on_date: Optional[date] = None,
    ) -> InsuranceSummaryResponse:
        """Get insurance portfolio summary."""
        if not as_on_date:
            as_on_date = date.today()

        # Determine FY start
        if as_on_date.month >= 4:
            fy_start = date(as_on_date.year, 4, 1)
        else:
            fy_start = date(as_on_date.year - 1, 4, 1)

        # Policy stats
        policy_result = await self.session.execute(
            select(
                func.count(InsurancePolicy.id).label("total"),
                func.count(InsurancePolicy.id).filter(
                    InsurancePolicy.status == InsurancePolicyStatus.ACTIVE
                ).label("active"),
                func.count(InsurancePolicy.id).filter(
                    and_(
                        InsurancePolicy.status == InsurancePolicyStatus.ACTIVE,
                        InsurancePolicy.end_date <= as_on_date + timedelta(days=30),
                        InsurancePolicy.end_date >= as_on_date,
                    )
                ).label("expiring_30"),
                func.count(InsurancePolicy.id).filter(
                    InsurancePolicy.status == InsurancePolicyStatus.EXPIRED
                ).label("expired"),
                func.sum(InsurancePolicy.sum_insured).filter(
                    InsurancePolicy.status == InsurancePolicyStatus.ACTIVE
                ).label("total_sum_insured"),
                func.sum(InsurancePolicy.total_premium).filter(
                    InsurancePolicy.premium_paid == True
                ).label("premium_paid"),
                func.sum(InsurancePolicy.total_premium).filter(
                    InsurancePolicy.premium_paid == False
                ).label("premium_due"),
            )
            .where(InsurancePolicy.organization_id == organization_id)
        )
        policy_stats = policy_result.one()

        # Claim stats
        claim_result = await self.session.execute(
            select(
                func.count(InsuranceClaim.id).filter(
                    InsuranceClaim.incident_date >= fy_start
                ).label("claims_ytd"),
                func.count(InsuranceClaim.id).filter(
                    InsuranceClaim.status.in_([
                        ClaimStatus.SUBMITTED,
                        ClaimStatus.UNDER_REVIEW,
                        ClaimStatus.DOCUMENTS_REQUIRED,
                    ])
                ).label("pending"),
                func.count(InsuranceClaim.id).filter(
                    and_(
                        InsuranceClaim.status == ClaimStatus.SETTLED,
                        InsuranceClaim.settlement_date >= fy_start,
                    )
                ).label("settled_ytd"),
                func.sum(InsuranceClaim.claim_amount).filter(
                    InsuranceClaim.incident_date >= fy_start
                ).label("claim_amount_ytd"),
                func.sum(InsuranceClaim.settled_amount).filter(
                    and_(
                        InsuranceClaim.status == ClaimStatus.SETTLED,
                        InsuranceClaim.settlement_date >= fy_start,
                    )
                ).label("settled_amount_ytd"),
            )
            .where(InsuranceClaim.organization_id == organization_id)
        )
        claim_stats = claim_result.one()

        # By type
        type_result = await self.session.execute(
            select(
                InsurancePolicy.insurance_type,
                func.count(InsurancePolicy.id).label("count"),
                func.sum(InsurancePolicy.sum_insured).label("sum_insured"),
                func.sum(InsurancePolicy.total_premium).label("premium"),
            )
            .where(
                InsurancePolicy.organization_id == organization_id,
                InsurancePolicy.status == InsurancePolicyStatus.ACTIVE,
            )
            .group_by(InsurancePolicy.insurance_type)
        )
        by_type = [
            {
                "type": row.insurance_type.value,
                "count": row.count,
                "sum_insured": float(row.sum_insured or 0),
                "premium": float(row.premium or 0),
            }
            for row in type_result
        ]

        # Claim ratio
        premium_paid = policy_stats.premium_paid or Decimal("0.00")
        settled_ytd = claim_stats.settled_amount_ytd or Decimal("0.00")
        claim_ratio = (settled_ytd / premium_paid * 100) if premium_paid > 0 else Decimal("0.00")

        return InsuranceSummaryResponse(
            organization_id=organization_id,
            as_on_date=as_on_date,
            total_policies=policy_stats.total or 0,
            active_policies=policy_stats.active or 0,
            expiring_within_30_days=policy_stats.expiring_30 or 0,
            expired_policies=policy_stats.expired or 0,
            total_sum_insured=policy_stats.total_sum_insured or Decimal("0.00"),
            total_premium_paid=premium_paid,
            premium_due=policy_stats.premium_due or Decimal("0.00"),
            total_claims_ytd=claim_stats.claims_ytd or 0,
            claims_pending=claim_stats.pending or 0,
            claims_settled_ytd=claim_stats.settled_ytd or 0,
            total_claim_amount_ytd=claim_stats.claim_amount_ytd or Decimal("0.00"),
            total_settled_amount_ytd=settled_ytd,
            by_insurance_type=by_type,
            claim_ratio_percentage=claim_ratio.quantize(Decimal("0.01")),
        )

    async def get_expiring_policies(
        self,
        organization_id: UUID,
        days: int = 30,
    ) -> List[InsurancePolicy]:
        """Get policies expiring within specified days."""
        policies, _ = await self.list_policies(
            organization_id,
            expiring_within_days=days,
        )
        return policies

    async def get_pending_claims(
        self,
        organization_id: UUID,
    ) -> List[InsuranceClaim]:
        """Get all pending claims."""
        claims, _ = await self.list_claims(
            organization_id,
            status=ClaimStatus.UNDER_REVIEW,
        )
        # Also get submitted and documents required
        submitted, _ = await self.list_claims(
            organization_id,
            status=ClaimStatus.SUBMITTED,
        )
        docs_required, _ = await self.list_claims(
            organization_id,
            status=ClaimStatus.DOCUMENTS_REQUIRED,
        )
        return claims + submitted + docs_required

    # =========================================
    # Helper Methods
    # =========================================

    async def _generate_claim_number(self, organization_id: UUID) -> str:
        """Generate next claim number."""
        result = await self.session.execute(
            select(func.count(InsuranceClaim.id))
            .where(InsuranceClaim.organization_id == organization_id)
        )
        count = result.scalar_one() or 0
        return f"CLM-{date.today().year}-{count + 1:05d}"
