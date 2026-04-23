"""Loan Sanction service for the lending module."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lending.sanction import (
    LoanSanction,
    SanctionCondition,
    LoanSecurity,
)
from app.models.lending.enums import (
    SanctionStatus,
    ConditionType,
    ConditionComplianceStatus,
    SecurityCategory,
    SecurityStatus,
    ApplicationStage,
    ApplicationStatus,
)
from app.schemas.lending.sanction import (
    LoanSanctionCreate,
    LoanSanctionUpdate,
    SanctionConditionCreate,
    SanctionConditionUpdate,
    LoanSecurityCreate,
    LoanSecurityUpdate,
)
from app.repositories.lending.sanction_repo import (
    LoanSanctionRepository,
    SanctionConditionRepository,
    LoanSecurityRepository,
)
from app.repositories.lending.application_repo import LoanApplicationRepository
from app.repositories.lending.entity_repo import EntityRepository
from app.repositories.lending.product_repo import LoanProductRepository
from app.core.exceptions import NotFoundException, ConflictException, ValidationException


class SanctionService:
    """Service for Loan Sanction operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.sanction_repo = LoanSanctionRepository(session)
        self.condition_repo = SanctionConditionRepository(session)
        self.security_repo = LoanSecurityRepository(session)
        self.app_repo = LoanApplicationRepository(session)
        self.entity_repo = EntityRepository(session)
        self.product_repo = LoanProductRepository(session)

    # =========================================================================
    # Loan Sanction Operations
    # =========================================================================

    async def create_sanction(
        self, data: LoanSanctionCreate, created_by: UUID
    ) -> LoanSanction:
        """Create a new loan sanction."""
        # Verify application exists
        application = await self.app_repo.get(data.application_id)
        if not application:
            raise NotFoundException("Application not found")

        # Check if sanction already exists for this application
        existing = await self.sanction_repo.get_by_application(data.application_id)
        if existing:
            raise ConflictException("Sanction already exists for this application")

        # Get product for generating sanction number
        product = await self.product_repo.get(application.product_id)

        # Generate sanction number
        sanction_number = await self.sanction_repo.generate_sanction_number(
            data.organization_id, product.code if product else "GEN"
        )

        # Create sanction
        sanction_data = data.model_dump(exclude={"conditions", "securities"})
        sanction = LoanSanction(
            **sanction_data,
            product_id=application.product_id,
            requested_amount=application.requested_amount,
            sanction_number=sanction_number,
            status=SanctionStatus.DRAFT,
            created_by=created_by,
        )
        self.session.add(sanction)
        await self.session.flush()

        # Add conditions
        for condition_data in data.conditions:
            condition = SanctionCondition(
                sanction_id=sanction.id,
                **condition_data.model_dump(exclude={"sanction_id"}),
                created_by=created_by,
            )
            self.session.add(condition)

        # Add securities
        for security_data in data.securities:
            security = LoanSecurity(
                sanction_id=sanction.id,
                **security_data.model_dump(exclude={"sanction_id"}),
                created_by=created_by,
            )
            self.session.add(security)

        await self.session.commit()
        await self.session.refresh(sanction)
        return sanction

    async def update_sanction(
        self, id: UUID, data: LoanSanctionUpdate, updated_by: UUID
    ) -> LoanSanction:
        """Update a loan sanction."""
        sanction = await self.sanction_repo.get(id)
        if not sanction:
            raise NotFoundException("Sanction not found")

        if sanction.status not in [SanctionStatus.DRAFT, SanctionStatus.PENDING_APPROVAL]:
            raise ValidationException("Sanction cannot be updated in current status")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(sanction, field, value)
        sanction.updated_by = updated_by

        await self.session.commit()
        await self.session.refresh(sanction)
        return sanction

    async def submit_for_approval(
        self, id: UUID, submitted_by: UUID
    ) -> LoanSanction:
        """Submit sanction for approval."""
        sanction = await self.sanction_repo.get(id)
        if not sanction:
            raise NotFoundException("Sanction not found")

        if sanction.status != SanctionStatus.DRAFT:
            raise ValidationException("Only draft sanctions can be submitted")

        sanction.status = SanctionStatus.PENDING_APPROVAL
        sanction.updated_by = submitted_by

        # Route through the workflow engine. `build_workflow_request`
        # infers the required approval level from the sanctioned amount
        # (Officer → GM → ED → CMD → Board) per the delegation matrix in
        # app/core/maker_checker.py. The workflow engine is a separate
        # service; we construct the request here and enqueue it, but the
        # actual processing (escalation, SLA, maker-checker check at the
        # approval site) lives in app.services.workflow. See CLAUDE.md §8.4.
        from app.core.maker_checker import build_workflow_request

        self._pending_workflow_request = build_workflow_request(
            workflow_code="LOAN_SANCTION_APPROVAL",
            entity_type="loan_sanction",
            entity_id=sanction.id,
            maker_user_id=submitted_by,
            organization_id=sanction.organization_id,
            amount=sanction.sanctioned_amount,
        )

        await self.session.commit()
        await self.session.refresh(sanction)
        return sanction

    async def approve_sanction_with_maker_checker_check(
        self,
        id: UUID,
        approver_user_id: UUID,
        remarks: Optional[str] = None,
    ) -> LoanSanction:
        """Approve a sanction, enforcing the maker ≠ checker invariant.

        See CLAUDE.md §8.4. The workflow engine ultimately calls this at the
        terminal approval step; services that bypass it (e.g. unit tests)
        should use `approve_sanction` directly.
        """
        from app.core.maker_checker import ensure_maker_is_not_checker

        sanction = await self.sanction_repo.get(id)
        if not sanction:
            raise NotFoundException("Sanction not found")

        ensure_maker_is_not_checker(
            maker_user_id=sanction.created_by,
            checker_user_id=approver_user_id,
        )
        return await self.approve_sanction(id, approver_user_id, remarks)

    async def approve_sanction(
        self, id: UUID, approved_by: UUID, remarks: Optional[str] = None
    ) -> LoanSanction:
        """Approve a sanction."""
        sanction = await self.sanction_repo.get(id)
        if not sanction:
            raise NotFoundException("Sanction not found")

        if sanction.status != SanctionStatus.PENDING_APPROVAL:
            raise ValidationException("Sanction is not pending approval")

        sanction.status = SanctionStatus.APPROVED
        sanction.sanctioned_by_id = approved_by
        sanction.updated_by = approved_by

        # Update application status
        application = await self.app_repo.get(sanction.application_id)
        if application:
            application.stage = ApplicationStage.SANCTION
            application.status = ApplicationStatus.SANCTIONED

        await self.session.commit()
        await self.session.refresh(sanction)
        return sanction

    async def record_borrower_acceptance(
        self,
        id: UUID,
        acceptance_date: date,
        document_path: Optional[str],
        updated_by: UUID,
    ) -> LoanSanction:
        """Record borrower acceptance of sanction."""
        sanction = await self.sanction_repo.get(id)
        if not sanction:
            raise NotFoundException("Sanction not found")

        if sanction.status != SanctionStatus.APPROVED:
            raise ValidationException("Sanction must be approved before acceptance")

        sanction.borrower_acceptance_date = acceptance_date
        sanction.borrower_acceptance_document_path = document_path
        sanction.status = SanctionStatus.ACCEPTED
        sanction.updated_by = updated_by

        # Move application to post-sanction
        application = await self.app_repo.get(sanction.application_id)
        if application:
            application.stage = ApplicationStage.POST_SANCTION

        await self.session.commit()
        await self.session.refresh(sanction)
        return sanction

    async def get_sanction(self, id: UUID) -> LoanSanction:
        """Get sanction by ID."""
        sanction = await self.sanction_repo.get(id)
        if not sanction:
            raise NotFoundException("Sanction not found")
        return sanction

    async def get_sanction_with_details(
        self, id: UUID
    ) -> LoanSanction:
        """Get sanction with conditions and securities."""
        sanction = await self.sanction_repo.get_with_details(id)
        if not sanction:
            raise NotFoundException("Sanction not found")
        return sanction

    async def get_sanction_by_application(
        self, application_id: UUID
    ) -> Optional[LoanSanction]:
        """Get sanction for an application."""
        return await self.sanction_repo.get_by_application(application_id)

    async def get_all_sanctions(
        self,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False,
        search: Optional[str] = None,
        entity_id: Optional[UUID] = None,
        status: Optional[SanctionStatus] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> Tuple[List[LoanSanction], int]:
        """Get all sanctions with filters."""
        return await self.sanction_repo.get_all_by_organization(
            organization_id=organization_id,
            skip=skip,
            limit=limit,
            include_inactive=include_inactive,
            search=search,
            entity_id=entity_id,
            status=status,
            from_date=from_date,
            to_date=to_date,
        )

    async def get_entity_sanctions(
        self, entity_id: UUID, include_inactive: bool = False
    ) -> List[LoanSanction]:
        """Get all sanctions for an entity."""
        return await self.sanction_repo.get_by_entity(entity_id, include_inactive)

    async def get_total_sanctioned_amount(
        self,
        organization_id: UUID,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> float:
        """Get total sanctioned amount."""
        return await self.sanction_repo.get_total_sanctioned_amount(
            organization_id, from_date, to_date
        )

    # =========================================================================
    # Sanction Condition Operations
    # =========================================================================

    async def add_condition(
        self, data: SanctionConditionCreate, created_by: UUID
    ) -> SanctionCondition:
        """Add a condition to a sanction."""
        sanction = await self.sanction_repo.get(data.sanction_id)
        if not sanction:
            raise NotFoundException("Sanction not found")

        condition = SanctionCondition(
            **data.model_dump(),
            created_by=created_by,
        )
        self.session.add(condition)
        await self.session.commit()
        await self.session.refresh(condition)
        return condition

    async def update_condition(
        self, id: UUID, data: SanctionConditionUpdate, updated_by: UUID
    ) -> SanctionCondition:
        """Update a sanction condition."""
        condition = await self.condition_repo.get(id)
        if not condition:
            raise NotFoundException("Condition not found")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(condition, field, value)
        condition.updated_by = updated_by

        await self.session.commit()
        await self.session.refresh(condition)
        return condition

    async def comply_condition(
        self,
        id: UUID,
        complied_on: date,
        verified_by: UUID,
        remarks: Optional[str] = None,
        document_path: Optional[str] = None,
    ) -> SanctionCondition:
        """Mark a condition as complied."""
        condition = await self.condition_repo.get(id)
        if not condition:
            raise NotFoundException("Condition not found")

        condition.compliance_status = ConditionComplianceStatus.COMPLIED
        condition.complied_on = complied_on
        condition.verified_by_id = verified_by
        condition.compliance_remarks = remarks
        condition.compliance_document_path = document_path
        condition.updated_by = verified_by

        await self.session.commit()
        await self.session.refresh(condition)
        return condition

    async def waive_condition(
        self,
        id: UUID,
        waived_by: UUID,
        waiver_remarks: str,
    ) -> SanctionCondition:
        """Waive a condition."""
        condition = await self.condition_repo.get(id)
        if not condition:
            raise NotFoundException("Condition not found")

        condition.compliance_status = ConditionComplianceStatus.WAIVED
        condition.waived_by_id = waived_by
        condition.waiver_remarks = waiver_remarks
        condition.updated_by = waived_by

        await self.session.commit()
        await self.session.refresh(condition)
        return condition

    async def get_sanction_conditions(
        self, sanction_id: UUID, include_inactive: bool = False
    ) -> List[SanctionCondition]:
        """Get all conditions for a sanction."""
        return await self.condition_repo.get_by_sanction(sanction_id, include_inactive)

    async def get_pending_conditions(
        self, sanction_id: UUID, condition_type: Optional[ConditionType] = None
    ) -> List[SanctionCondition]:
        """Get pending conditions for a sanction."""
        return await self.condition_repo.get_pending_conditions(
            sanction_id, condition_type
        )

    async def check_disbursement_eligible(
        self, sanction_id: UUID
    ) -> Dict[str, Any]:
        """Check if sanction is eligible for disbursement."""
        sanction = await self.sanction_repo.get(sanction_id)
        if not sanction:
            raise NotFoundException("Sanction not found")

        # Check pre-disbursement conditions
        pre_conditions_complied = await self.condition_repo.check_pre_disbursement_complied(
            sanction_id
        )
        pending_conditions = await self.condition_repo.get_mandatory_pending(
            sanction_id, ConditionType.PRE_DISBURSEMENT
        )

        # Check security status
        securities = await self.security_repo.get_by_sanction(sanction_id)
        securities_created = all(
            s.status in [SecurityStatus.CREATED, SecurityStatus.REGISTERED]
            for s in securities
        )

        is_eligible = (
            sanction.status == SanctionStatus.ACCEPTED
            and pre_conditions_complied
            and securities_created
        )

        return {
            "is_eligible": is_eligible,
            "sanction_status": sanction.status.value,
            "pre_conditions_complied": pre_conditions_complied,
            "pending_conditions": pending_conditions,
            "securities_created": securities_created,
        }

    # =========================================================================
    # Loan Security Operations
    # =========================================================================

    async def add_security(
        self, data: LoanSecurityCreate, created_by: UUID
    ) -> LoanSecurity:
        """Add a security to a sanction."""
        sanction = await self.sanction_repo.get(data.sanction_id)
        if not sanction:
            raise NotFoundException("Sanction not found")

        security = LoanSecurity(
            **data.model_dump(),
            created_by=created_by,
        )
        self.session.add(security)
        await self.session.commit()
        await self.session.refresh(security)

        # Update sanction security totals
        await self._update_security_totals(data.sanction_id)

        return security

    async def update_security(
        self, id: UUID, data: LoanSecurityUpdate, updated_by: UUID
    ) -> LoanSecurity:
        """Update a loan security."""
        security = await self.security_repo.get(id)
        if not security:
            raise NotFoundException("Security not found")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(security, field, value)
        security.updated_by = updated_by

        await self.session.commit()
        await self.session.refresh(security)

        # Update sanction security totals
        await self._update_security_totals(security.sanction_id)

        return security

    async def register_security(
        self,
        id: UUID,
        cersai_registration_id: str,
        registration_date: date,
        updated_by: UUID,
    ) -> LoanSecurity:
        """Register security with CERSAI."""
        security = await self.security_repo.get(id)
        if not security:
            raise NotFoundException("Security not found")

        security.status = SecurityStatus.REGISTERED
        security.cersai_registration_id = cersai_registration_id
        security.cersai_registration_date = registration_date
        security.updated_by = updated_by

        await self.session.commit()
        await self.session.refresh(security)
        return security

    async def get_sanction_securities(
        self, sanction_id: UUID, include_inactive: bool = False
    ) -> List[LoanSecurity]:
        """Get all securities for a sanction."""
        return await self.security_repo.get_by_sanction(sanction_id, include_inactive)

    async def get_security_summary(
        self, sanction_id: UUID
    ) -> Dict[str, Any]:
        """Get security summary for a sanction."""
        securities = await self.security_repo.get_by_sanction(sanction_id)
        total_market = await self.security_repo.get_total_security_value(sanction_id)
        total_fsv = await self.security_repo.get_total_forced_sale_value(sanction_id)

        sanction = await self.sanction_repo.get(sanction_id)
        coverage = (
            (total_market / float(sanction.sanctioned_amount) * 100)
            if sanction and sanction.sanctioned_amount
            else 0
        )

        return {
            "total_securities": len(securities),
            "total_market_value": total_market,
            "total_forced_sale_value": total_fsv,
            "security_coverage_percentage": round(coverage, 2),
            "by_category": {
                category.value: [s for s in securities if s.security_category == category]
                for category in SecurityCategory
            },
        }

    async def _update_security_totals(self, sanction_id: UUID) -> None:
        """Update sanction security totals."""
        sanction = await self.sanction_repo.get(sanction_id)
        if not sanction:
            return

        total_value = await self.security_repo.get_total_security_value(sanction_id)
        sanction.total_security_value = Decimal(str(total_value))

        if sanction.sanctioned_amount and sanction.sanctioned_amount > 0:
            sanction.security_coverage_percentage = Decimal(
                str(total_value / float(sanction.sanctioned_amount) * 100)
            )

        await self.session.flush()
