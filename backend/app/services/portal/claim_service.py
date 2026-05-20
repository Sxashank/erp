"""Scheme-portal borrower claim service."""

from __future__ import annotations

from datetime import date
from io import BytesIO
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import (
    BadRequestException,
    ForbiddenException,
    NotFoundException,
)
from app.models.dms import DocumentAccessLevel
from app.models.lending.enums import (
    SubventionClaimStatus,
    SubventionEnrollmentStatus,
)
from app.models.lending.iif.loan_subvention_enrollment import (
    LoanSubventionEnrollment,
)
from app.models.lending.iif.subvention_claim import SubventionClaim
from app.models.lending.loan_account import LoanAccount
from app.models.portal.portal_user import PortalUser
from app.schemas.lending.iif import SubventionClaimDocumentInput
from app.schemas.portal.claim import (
    BorrowerClaimCreateRequest,
    BorrowerClaimEnrollmentItem,
    BorrowerClaimEnrollmentListResponse,
    BorrowerClaimItem,
    BorrowerClaimListResponse,
    BorrowerClaimStats,
    BorrowerClaimSubmitRequest,
    BorrowerClaimsWorkbenchResponse,
    BorrowerEligibleClaimPeriod,
    BorrowerEligibleClaimPeriodsResponse,
)
from app.services.dms.document_service import DocumentService
from app.services.lending.iif.subvention_claim_service import (
    SubventionClaimService,
)
from app.services.portal.actor_roles import (
    CLAIM_SUBMITTER_ROLES,
    CLAIM_RELEASE_ROLES,
    CLAIM_VERIFY_ROLES,
    is_borrower_role,
    portal_actor_role,
)
from app.services.portal.entity_access import get_accessible_entity_ids
from app.services.portal.notification_service import PortalNotificationService


class PortalClaimService:
    """Borrower-side access wrapper over subvention claims."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.claim_service = SubventionClaimService(db)

    async def get_workbench(
        self,
        portal_user: PortalUser,
        *,
        claims_limit: int = 10,
    ) -> BorrowerClaimsWorkbenchResponse:
        claim_list = await self.list_claims(
            portal_user,
            page=1,
            page_size=200,
        )
        enrollments = (
            await self.list_enrollments(portal_user)
            if portal_actor_role(portal_user) in CLAIM_SUBMITTER_ROLES
            else BorrowerClaimEnrollmentListResponse(items=[], total=0)
        )
        stats = BorrowerClaimStats(
            draft=sum(
                claim.status == SubventionClaimStatus.DRAFT.value for claim in claim_list.items
            ),
            submitted=sum(
                claim.status == SubventionClaimStatus.SUBMITTED.value for claim in claim_list.items
            ),
            verified=sum(
                claim.status == SubventionClaimStatus.VERIFIED.value for claim in claim_list.items
            ),
            release_in_progress=sum(
                claim.status == SubventionClaimStatus.RELEASE_IN_PROGRESS.value
                for claim in claim_list.items
            ),
            released=sum(
                claim.status == SubventionClaimStatus.RELEASED.value for claim in claim_list.items
            ),
            eligible_periods=sum(
                len(
                    [period for period in enrollment.eligible_periods if not period.already_claimed]
                )
                for enrollment in enrollments.items
            ),
        )
        return BorrowerClaimsWorkbenchResponse(
            stats=stats,
            enrollments=enrollments.items,
            claims=claim_list.items[:claims_limit],
        )

    async def list_enrollments(
        self,
        portal_user: PortalUser,
    ) -> BorrowerClaimEnrollmentListResponse:
        self._require_role(portal_user, CLAIM_SUBMITTER_ROLES)
        accessible_loan_ids = await self._get_accessible_loan_ids(portal_user)
        if not accessible_loan_ids:
            return BorrowerClaimEnrollmentListResponse(items=[], total=0)

        stmt = (
            select(LoanSubventionEnrollment)
            .options(
                selectinload(LoanSubventionEnrollment.loan_account),
                selectinload(LoanSubventionEnrollment.scheme),
            )
            .where(
                LoanSubventionEnrollment.loan_account_id.in_(accessible_loan_ids),
                LoanSubventionEnrollment.deleted_at.is_(None),
            )
            .order_by(LoanSubventionEnrollment.enrolled_date.desc())
        )
        rows = list((await self.db.execute(stmt)).scalars().all())
        items = [await self._to_enrollment_item(portal_user, enrollment) for enrollment in rows]
        return BorrowerClaimEnrollmentListResponse(
            items=items,
            total=len(items),
        )

    async def eligible_periods(
        self,
        portal_user: PortalUser,
        enrollment_id: UUID,
    ) -> BorrowerEligibleClaimPeriodsResponse:
        self._require_role(portal_user, CLAIM_SUBMITTER_ROLES)
        enrollment = await self._assert_enrollment_access(portal_user, enrollment_id)
        periods = await self.claim_service.eligible_periods(
            enrollment.organization_id,
            enrollment.id,
        )
        return BorrowerEligibleClaimPeriodsResponse(
            enrollment_id=periods.enrollment_id,
            claim_frequency=periods.claim_frequency,
            periods=[
                BorrowerEligibleClaimPeriod.model_validate(period) for period in periods.periods
            ],
        )

    async def list_claims(
        self,
        portal_user: PortalUser,
        *,
        loan_account_id: UUID | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> BorrowerClaimListResponse:
        page = max(1, page)
        page_size = max(1, min(page_size, 200))
        stmt = (
            select(SubventionClaim)
            .options(
                selectinload(SubventionClaim.enrollment).selectinload(
                    LoanSubventionEnrollment.loan_account
                ),
                selectinload(SubventionClaim.enrollment).selectinload(
                    LoanSubventionEnrollment.scheme
                ),
            )
            .where(
                SubventionClaim.deleted_at.is_(None),
            )
            .order_by(SubventionClaim.created_at.desc())
        )
        role = portal_actor_role(portal_user)
        if is_borrower_role(portal_user) or role == "scheme_lender":
            accessible_loan_ids = await self._get_accessible_loan_ids(portal_user)
            if not accessible_loan_ids:
                return BorrowerClaimListResponse(
                    items=[],
                    total=0,
                    page=page,
                    page_size=page_size,
                )
            if loan_account_id is not None and loan_account_id not in accessible_loan_ids:
                raise NotFoundException(
                    "Loan account not found",
                    error_code="LOAN_ACCOUNT_NOT_FOUND",
                )
            stmt = stmt.where(
                SubventionClaim.enrollment_id.in_(
                    select(LoanSubventionEnrollment.id).where(
                        LoanSubventionEnrollment.loan_account_id.in_(accessible_loan_ids),
                        LoanSubventionEnrollment.deleted_at.is_(None),
                    )
                )
            )
        else:
            stmt = stmt.where(SubventionClaim.organization_id == portal_user.organization_id)
        if loan_account_id is not None:
            stmt = stmt.where(
                SubventionClaim.enrollment_id.in_(
                    select(LoanSubventionEnrollment.id).where(
                        LoanSubventionEnrollment.loan_account_id == loan_account_id,
                        LoanSubventionEnrollment.deleted_at.is_(None),
                    )
                )
            )
        rows = list((await self.db.execute(stmt)).scalars().all())
        if status is not None:
            rows = [claim for claim in rows if claim.status == status]
        total = len(rows)
        rows = rows[(page - 1) * page_size : (page - 1) * page_size + page_size]
        return BorrowerClaimListResponse(
            items=[BorrowerClaimItem.model_validate(claim) for claim in rows],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def get_claim(
        self,
        portal_user: PortalUser,
        claim_id: UUID,
    ) -> BorrowerClaimItem:
        claim = await self.get_claim_record(portal_user, claim_id)
        return BorrowerClaimItem.model_validate(claim)

    async def get_claim_record(
        self,
        portal_user: PortalUser,
        claim_id: UUID,
    ) -> SubventionClaim:
        role = portal_actor_role(portal_user)
        if not is_borrower_role(portal_user) and role != "scheme_lender":
            return await self.claim_service.get(
                portal_user.organization_id,
                claim_id,
            )
        return await self._assert_claim_access(portal_user, claim_id)

    async def create_claim(
        self,
        portal_user: PortalUser,
        payload: BorrowerClaimCreateRequest,
    ) -> BorrowerClaimItem:
        self._require_role(portal_user, CLAIM_SUBMITTER_ROLES)
        enrollment = await self._assert_enrollment_access(portal_user, payload.enrollment_id)
        claim = await self.claim_service.create_claim(
            enrollment.organization_id,
            enrollment.id,
            payload.period_start,
            payload.period_end,
            payload.documents,
            _PortalActorUser(portal_user.id),
        )
        claim = await self.claim_service.get(enrollment.organization_id, claim.id)
        return BorrowerClaimItem.model_validate(claim)

    async def submit_claim(
        self,
        portal_user: PortalUser,
        claim_id: UUID,
        payload: BorrowerClaimSubmitRequest | None = None,
    ) -> BorrowerClaimItem:
        self._require_role(portal_user, CLAIM_SUBMITTER_ROLES)
        claim = await self._assert_claim_access(portal_user, claim_id)
        if not claim.documents:
            raise BadRequestException(
                "At least one supporting document is required before submitting a scheme claim",
                error_code="CLAIM_DOCUMENTS_REQUIRED",
            )
        await self.claim_service.submit_claim(
            claim.organization_id,
            claim.id,
            payload.declaration_signed_at if payload else None,
            _PortalActorUser(portal_user.id),
        )
        claim = await self.claim_service.get(claim.organization_id, claim.id)
        await self._notify_claim_transition(
            claim=claim,
            title="Scheme claim submitted",
            body=(f"Claim {claim.claim_reference} has been submitted for SMFCL verification."),
            notification_type="SCHEME_CLAIM_SUBMITTED",
            target_roles=list(CLAIM_VERIFY_ROLES),
        )
        return BorrowerClaimItem.model_validate(claim)

    async def upload_claim_document(
        self,
        portal_user: PortalUser,
        claim_id: UUID,
        *,
        file_bytes: bytes,
        file_name: str,
        file_size_bytes: int,
        file_mime_type: str | None,
        document_name: str | None = None,
        document_category: str = "BORROWER_CLAIM_SUPPORTING_DOCUMENT",
    ) -> BorrowerClaimItem:
        self._require_role(portal_user, CLAIM_SUBMITTER_ROLES)
        claim = await self._assert_claim_access(portal_user, claim_id)
        if claim.status != SubventionClaimStatus.DRAFT.value:
            raise ForbiddenException(
                "Only draft claims can be updated",
                error_code="INVALID_CLAIM_STATUS",
            )

        dms_service = DocumentService(self.db)
        dms_document = await dms_service.upload_document(
            organization_id=claim.organization_id,
            file=BytesIO(file_bytes),
            file_name=file_name,
            file_size=file_size_bytes,
            mime_type=file_mime_type or "application/octet-stream",
            name=document_name or file_name,
            description=(f"Scheme claim supporting document for " f"{claim.claim_reference}"),
            document_type="SCHEME_CLAIM",
            document_subtype=document_category,
            entity_type="scheme_claim",
            entity_id=claim.id,
            access_level=DocumentAccessLevel.ORGANIZATION,
            created_by=portal_user.id,
            auto_commit=False,
        )
        existing_documents = [
            SubventionClaimDocumentInput.model_validate(doc) for doc in (claim.documents or [])
        ]
        existing_documents.append(
            SubventionClaimDocumentInput(
                document_id=dms_document.id,
                name=document_name or file_name,
                file_name=file_name,
                document_category=document_category,
            )
        )
        await self.claim_service.update_documents(
            claim.organization_id,
            claim.id,
            existing_documents,
            _PortalActorUser(portal_user.id),
        )
        refreshed = await self.claim_service.get(claim.organization_id, claim.id)
        return BorrowerClaimItem.model_validate(refreshed)

    async def verify_claim(
        self,
        portal_user: PortalUser,
        claim_id: UUID,
        *,
        decision: str,
        reason: str | None = None,
    ) -> BorrowerClaimItem:
        self._require_role(portal_user, CLAIM_VERIFY_ROLES)
        claim = await self.claim_service.get(
            portal_user.organization_id,
            claim_id,
        )
        await self.claim_service.verify_claim(
            claim.organization_id,
            claim.id,
            decision,
            reason,
            _PortalActorUser(portal_user.id),
        )
        claim = await self.claim_service.get(claim.organization_id, claim.id)
        status_value = claim.status.value if hasattr(claim.status, "value") else str(claim.status)
        status_label = status_value.replace("_", " ").title()
        await self._notify_claim_transition(
            claim=claim,
            title=f"Scheme claim {status_label.lower()}",
            body=(
                f"Claim {claim.claim_reference} is now {status_label.lower()}."
                + (f" Note: {reason}" if reason else "")
            ),
            notification_type="SCHEME_CLAIM_REVIEWED",
            target_roles=(
                list(CLAIM_RELEASE_ROLES)
                if status_value == SubventionClaimStatus.VERIFIED.value
                else []
            ),
        )
        return BorrowerClaimItem.model_validate(claim)

    async def initiate_release(
        self,
        portal_user: PortalUser,
        claim_id: UUID,
        *,
        release_instruction_reference: str,
        release_initiated_date: date | None = None,
        release_instruction_notes: str | None = None,
    ) -> BorrowerClaimItem:
        self._require_role(portal_user, CLAIM_RELEASE_ROLES)
        claim = await self.claim_service.get(
            portal_user.organization_id,
            claim_id,
        )
        await self.claim_service.initiate_release(
            claim.organization_id,
            claim.id,
            release_instruction_reference,
            release_initiated_date,
            release_instruction_notes,
            _PortalActorUser(portal_user.id),
        )
        claim = await self.claim_service.get(claim.organization_id, claim.id)
        await self._notify_claim_transition(
            claim=claim,
            title="Claim release initiated",
            body=(
                f"Release instruction {release_instruction_reference} has been captured "
                f"for claim {claim.claim_reference}."
            ),
            notification_type="SCHEME_CLAIM_RELEASE_INITIATED",
            target_roles=[],
        )
        return BorrowerClaimItem.model_validate(claim)

    async def mark_released(
        self,
        portal_user: PortalUser,
        claim_id: UUID,
        *,
        release_reference: str,
        released_date: date | None = None,
    ) -> BorrowerClaimItem:
        self._require_role(portal_user, CLAIM_RELEASE_ROLES)
        claim = await self.claim_service.get(
            portal_user.organization_id,
            claim_id,
        )
        await self.claim_service.mark_released(
            claim.organization_id,
            claim.id,
            release_reference,
            released_date,
            _PortalActorUser(portal_user.id),
        )
        claim = await self.claim_service.get(claim.organization_id, claim.id)
        await self._notify_claim_transition(
            claim=claim,
            title="Claim released",
            body=(
                f"Claim {claim.claim_reference} has been released. "
                f"Reference: {release_reference}."
            ),
            notification_type="SCHEME_CLAIM_RELEASED",
            target_roles=[],
        )
        return BorrowerClaimItem.model_validate(claim)

    async def _get_accessible_loan_ids(
        self,
        portal_user: PortalUser,
    ) -> set[UUID]:
        accessible_entities = await get_accessible_entity_ids(portal_user, self.db)
        if not accessible_entities:
            return set()
        stmt = select(LoanAccount.id).where(
            LoanAccount.entity_id.in_(accessible_entities),
            LoanAccount.deleted_at.is_(None),
        )
        result = await self.db.execute(stmt)
        return {row[0] for row in result.all()}

    async def _assert_enrollment_access(
        self,
        portal_user: PortalUser,
        enrollment_id: UUID,
    ) -> LoanSubventionEnrollment:
        accessible_loan_ids = await self._get_accessible_loan_ids(portal_user)
        if not accessible_loan_ids:
            raise NotFoundException(
                "Enrollment not found",
                error_code="ENROLLMENT_NOT_FOUND",
            )
        stmt = (
            select(LoanSubventionEnrollment)
            .options(
                selectinload(LoanSubventionEnrollment.loan_account),
                selectinload(LoanSubventionEnrollment.scheme),
            )
            .where(
                LoanSubventionEnrollment.id == enrollment_id,
                LoanSubventionEnrollment.loan_account_id.in_(accessible_loan_ids),
                LoanSubventionEnrollment.deleted_at.is_(None),
            )
        )
        enrollment = (await self.db.execute(stmt)).scalar_one_or_none()
        if enrollment is None:
            raise NotFoundException(
                "Enrollment not found",
                error_code="ENROLLMENT_NOT_FOUND",
            )
        return enrollment

    async def _assert_claim_access(
        self,
        portal_user: PortalUser,
        claim_id: UUID,
    ) -> SubventionClaim:
        claim = await self.claim_service.get(
            portal_user.organization_id,
            claim_id,
        )
        accessible_loan_ids = await self._get_accessible_loan_ids(portal_user)
        loan_id = (
            claim.enrollment.loan_account.id
            if claim.enrollment and claim.enrollment.loan_account
            else None
        )
        if loan_id is None or loan_id not in accessible_loan_ids:
            raise NotFoundException(
                "Claim not found",
                error_code="CLAIM_NOT_FOUND",
            )
        return claim

    async def _notify_claim_transition(
        self,
        *,
        claim: SubventionClaim,
        title: str,
        body: str,
        notification_type: str,
        target_roles: list[str],
        include_borrowers: bool = True,
    ) -> None:
        entity_id = (
            claim.enrollment.loan_account.entity_id
            if claim.enrollment is not None and claim.enrollment.loan_account is not None
            else None
        )
        service = PortalNotificationService(self.db)
        action_url = "/portal/claims"
        if include_borrowers and entity_id is not None:
            await service.notify_entity_borrowers(
                organization_id=claim.organization_id,
                entity_id=entity_id,
                title=title,
                body=body,
                notification_type=notification_type,
                action_url=action_url,
                reference_type="SCHEME_CLAIM",
                reference_id=claim.id,
            )
        if target_roles:
            await service.notify_roles(
                organization_id=claim.organization_id,
                actor_roles=target_roles,
                title=title,
                body=body,
                notification_type=notification_type,
                action_url=action_url,
                reference_type="SCHEME_CLAIM",
                reference_id=claim.id,
            )

    async def _to_enrollment_item(
        self,
        portal_user: PortalUser,
        enrollment: LoanSubventionEnrollment,
    ) -> BorrowerClaimEnrollmentItem:
        periods: list[BorrowerEligibleClaimPeriod] = []
        if enrollment.status == SubventionEnrollmentStatus.ENROLLED.value:
            eligible = await self.eligible_periods(portal_user, enrollment.id)
            periods = eligible.periods
        return BorrowerClaimEnrollmentItem(
            enrollment_id=enrollment.id,
            loan_account_id=enrollment.loan_account_id,
            loan_account_number=(
                enrollment.loan_account.loan_account_number if enrollment.loan_account else None
            ),
            scheme_id=enrollment.scheme_id,
            scheme_code=(enrollment.scheme.scheme_code if enrollment.scheme else None),
            scheme_name=(enrollment.scheme.scheme_name if enrollment.scheme else None),
            status=enrollment.status,
            enrolled_date=enrollment.enrolled_date,
            total_claimed_to_date=enrollment.total_claimed_to_date,
            total_paid_to_date=enrollment.total_paid_to_date,
            eligible_periods=periods,
        )

    def _require_borrower(self, portal_user: PortalUser) -> None:
        if not is_borrower_role(portal_user):
            raise ForbiddenException(
                "Only borrower actors can perform this action",
                error_code="PORTAL_ROLE_FORBIDDEN",
            )

    def _require_role(
        self,
        portal_user: PortalUser,
        allowed_roles: set[str] | frozenset[str],
    ) -> None:
        role = portal_actor_role(portal_user)
        if role not in allowed_roles:
            raise ForbiddenException(
                "Portal actor is not allowed to perform this action",
                error_code="PORTAL_ROLE_FORBIDDEN",
            )


class _PortalActorUser:
    """Minimal user adapter for downstream service created_by/update_by fields."""

    def __init__(self, user_id: UUID) -> None:
        self.id = user_id
