"""Integrated SFC borrower-portal workbench service."""

from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.lending.application import LoanApplication
from app.models.portal.enums import PortalActorRole, PortalRegistrationStatus
from app.models.portal.portal_user import PortalUser
from app.schemas.portal.workbench import (
    PortalWorkbenchResponse,
    WorkbenchAction,
    WorkbenchApplication,
    WorkbenchStat,
)
from app.services.portal.actor_roles import portal_actor_role
from app.services.portal.claim_service import PortalClaimService
from app.services.portal.entity_access import get_accessible_entity_ids
from app.services.portal.scheme_rules import derive_scheme_application_status


class PortalWorkbenchService:
    """Aggregate integrated SFC portal workbench data by actor role."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_workbench(self, portal_user: PortalUser) -> PortalWorkbenchResponse:
        role = portal_actor_role(portal_user)
        if role == PortalActorRole.SCHEME_BORROWER.value:
            return await self._borrower_workbench(portal_user)
        if role == PortalActorRole.SCHEME_LENDER.value:
            return await self._lender_workbench(portal_user)
        if role == PortalActorRole.SCHEME_SMFCL_REVIEWER.value:
            return await self._smfcl_reviewer_workbench(portal_user)
        if role == PortalActorRole.SCHEME_SMFCL_APPROVER.value:
            return await self._smfcl_approver_workbench(portal_user)
        if role == PortalActorRole.SCHEME_MINISTRY_VIEWER.value:
            return await self._ministry_workbench(portal_user)
        return await self._admin_workbench(portal_user)

    async def _borrower_workbench(
        self,
        portal_user: PortalUser,
    ) -> PortalWorkbenchResponse:
        accessible = await get_accessible_entity_ids(portal_user, self.db)
        display_name = self._display_name(portal_user)
        if not accessible:
            return PortalWorkbenchResponse(
                actor_role=PortalActorRole.SCHEME_BORROWER.value,
                display_name=display_name,
                active_entity_count=0,
                stats=[
                    WorkbenchStat(
                        key="pendingApproval",
                        label="Registration",
                        value=1,
                        hint="Awaiting organisation approval and entity linkage",
                    )
                ],
                priority_actions=[
                    WorkbenchAction(
                        title="Await approval",
                        description=(
                            "Your registration is complete. SFC will link your "
                            "organisation before applications can be submitted."
                        ),
                        href="/portal/register",
                        status="attention",
                    )
                ],
            )

        apps = await self._load_applications_for_entities(accessible)
        scheme_statuses = [
            derive_scheme_application_status(app.status, app.stage, app.extra_data or {})
            for app in apps
        ]
        counts = {
            "drafts": sum(status == "DRAFT" for status in scheme_statuses),
            "lender_review": sum(status == "LENDER_REVIEW" for status in scheme_statuses),
            "smfcl_review": sum(
                status
                in {
                    "LENDER_VALIDATED",
                    "SMFCL_PRELIM_REVIEW",
                    "SMFCL_APPRAISAL",
                }
                for status in scheme_statuses
            ),
            "queries": sum(status == "QUERY_PENDING" for status in scheme_statuses),
            "approved": sum(
                status in {"APPROVED", "SANCTION_ISSUED", "CLAIM_OPEN", "RELEASED"}
                for status in scheme_statuses
            ),
        }

        actions: list[WorkbenchAction] = []
        if counts["drafts"] > 0:
            actions.append(
                WorkbenchAction(
                    title="Complete draft applications",
                    description=(
                        "Draft applications are not visible to SFC reviewers until submitted."
                    ),
                    href="/portal/applications",
                    status="attention",
                )
            )
        if counts["queries"] > 0:
            actions.append(
                WorkbenchAction(
                    title="Respond to review queries",
                    description=(
                        "One or more applications require clarification or "
                        "additional information."
                    ),
                    href="/portal/applications",
                    status="attention",
                )
            )

        claim_workbench = await PortalClaimService(self.db).get_workbench(
            portal_user,
            claims_limit=25,
        )
        if claim_workbench.stats.draft > 0:
            actions.append(
                WorkbenchAction(
                    title="Submit draft subsidy claims",
                    description="Draft claims are ready to be submitted for SFC verification.",
                    href="/portal/claims",
                    status="attention",
                )
            )
        elif claim_workbench.stats.eligible_periods > 0:
            actions.append(
                WorkbenchAction(
                    title="Create subsidy claims",
                    description=(
                        "One or more enrolled loans have claim periods ready "
                        "for borrower submission."
                    ),
                    href="/portal/claims",
                    status="info",
                )
            )
        if not actions:
            actions.append(
                WorkbenchAction(
                    title="Start a new loan application",
                    description=(
                        "Create a new institutional loan request for maritime "
                        "or shipyard funding."
                    ),
                    href="/portal/applications/new",
                    status="info",
                )
            )

        return PortalWorkbenchResponse(
            actor_role=PortalActorRole.SCHEME_BORROWER.value,
            display_name=display_name,
            active_entity_count=len(accessible),
            stats=[
                WorkbenchStat(key="drafts", label="Draft applications", value=counts["drafts"]),
                WorkbenchStat(
                    key="lenderReview", label="Pending SFC review", value=counts["lender_review"]
                ),
                WorkbenchStat(
                    key="smfclReview", label="Pending SFC review", value=counts["smfcl_review"]
                ),
                WorkbenchStat(key="queries", label="Queries to answer", value=counts["queries"]),
                WorkbenchStat(
                    key="approved", label="Approved / sanctioned", value=counts["approved"]
                ),
            ],
            priority_actions=actions,
            recent_applications=self._recent_applications(apps),
        )

    async def _lender_workbench(
        self,
        portal_user: PortalUser,
    ) -> PortalWorkbenchResponse:
        apps = await self._load_org_applications(portal_user)
        statuses = [
            derive_scheme_application_status(app.status, app.stage, app.extra_data or {})
            for app in apps
        ]
        pending = sum(status == "LENDER_REVIEW" for status in statuses)
        queries = sum(status == "QUERY_PENDING" for status in statuses)
        validated = sum(status == "LENDER_VALIDATED" for status in statuses)
        approved = sum(
            status in {"APPROVED", "SANCTION_ISSUED", "CLAIM_OPEN", "RELEASED"}
            for status in statuses
        )
        actions: list[WorkbenchAction] = []
        if pending > 0:
            actions.append(
                WorkbenchAction(
                    title="Validate SFC review applications",
                    description="Submitted borrower applications are awaiting SFC validation.",
                    href="/portal/applications",
                    status="attention",
                )
            )
        if queries > 0:
            actions.append(
                WorkbenchAction(
                    title="Review borrower query responses",
                    description="Queried applications have been updated and should be rechecked.",
                    href="/portal/applications",
                    status="info",
                )
            )
        return PortalWorkbenchResponse(
            actor_role=PortalActorRole.SCHEME_LENDER.value,
            display_name=self._display_name(portal_user),
            active_entity_count=0,
            stats=[
                WorkbenchStat(key="pendingLenderReview", label="Pending SFC review", value=pending),
                WorkbenchStat(key="queries", label="Applications queried", value=queries),
                WorkbenchStat(key="validated", label="SFC validated", value=validated),
                WorkbenchStat(key="approved", label="Approved / sanctioned", value=approved),
            ],
            priority_actions=actions,
            recent_applications=self._recent_applications(
                [
                    app
                    for app in apps
                    if derive_scheme_application_status(
                        app.status,
                        app.stage,
                        app.extra_data or {},
                    )
                    in {"LENDER_REVIEW", "QUERY_PENDING", "LENDER_VALIDATED"}
                ]
            ),
        )

    async def _smfcl_reviewer_workbench(
        self,
        portal_user: PortalUser,
    ) -> PortalWorkbenchResponse:
        apps = await self._load_org_applications(portal_user)
        claim_workbench = await PortalClaimService(self.db).get_workbench(
            portal_user,
            claims_limit=25,
        )
        statuses = [
            derive_scheme_application_status(app.status, app.stage, app.extra_data or {})
            for app in apps
        ]
        pending_regs = await self._pending_registrations_count()
        prelim = sum(status in {"LENDER_VALIDATED", "SMFCL_PRELIM_REVIEW"} for status in statuses)
        appraisal = sum(status == "SMFCL_APPRAISAL" for status in statuses)
        queries = sum(status == "QUERY_PENDING" for status in statuses)
        actions: list[WorkbenchAction] = []
        if pending_regs > 0:
            actions.append(
                WorkbenchAction(
                    title="Review borrower registrations",
                    description=(
                        "New organisation registrations are awaiting SFC linkage and approval."
                    ),
                    href="/portal/registrations",
                    status="attention",
                )
            )
        if prelim > 0 or appraisal > 0:
            actions.append(
                WorkbenchAction(
                    title="Process application review queue",
                    description="Validated applications are ready for prelim review or appraisal.",
                    href="/portal/applications",
                    status="attention",
                )
            )
        if claim_workbench.stats.submitted > 0:
            actions.append(
                WorkbenchAction(
                    title="Verify submitted subsidy claims",
                    description="Borrower claims are waiting for SFC verification.",
                    href="/portal/claims",
                    status="attention",
                )
            )
        return PortalWorkbenchResponse(
            actor_role=PortalActorRole.SCHEME_SMFCL_REVIEWER.value,
            display_name=self._display_name(portal_user),
            active_entity_count=0,
            stats=[
                WorkbenchStat(
                    key="registrations", label="Pending registrations", value=pending_regs
                ),
                WorkbenchStat(key="prelimReview", label="Prelim review queue", value=prelim),
                WorkbenchStat(key="appraisal", label="Appraisal in progress", value=appraisal),
                WorkbenchStat(key="queries", label="Borrower queries open", value=queries),
                WorkbenchStat(
                    key="claimVerification",
                    label="Claims to verify",
                    value=claim_workbench.stats.submitted,
                ),
            ],
            priority_actions=actions,
            recent_applications=self._recent_applications(
                [
                    app
                    for app in apps
                    if derive_scheme_application_status(
                        app.status,
                        app.stage,
                        app.extra_data or {},
                    )
                    in {
                        "LENDER_VALIDATED",
                        "SMFCL_PRELIM_REVIEW",
                        "SMFCL_APPRAISAL",
                        "QUERY_PENDING",
                    }
                ]
            ),
        )

    async def _smfcl_approver_workbench(
        self,
        portal_user: PortalUser,
    ) -> PortalWorkbenchResponse:
        apps = await self._load_org_applications(portal_user)
        claim_workbench = await PortalClaimService(self.db).get_workbench(
            portal_user,
            claims_limit=25,
        )
        statuses = [
            derive_scheme_application_status(app.status, app.stage, app.extra_data or {})
            for app in apps
        ]
        appraisal = sum(status == "SMFCL_APPRAISAL" for status in statuses)
        approved = sum(
            status in {"APPROVED", "SANCTION_ISSUED", "CLAIM_OPEN", "RELEASED"}
            for status in statuses
        )
        actions: list[WorkbenchAction] = []
        if appraisal > 0:
            actions.append(
                WorkbenchAction(
                    title="Approve applications for sanction",
                    description="Appraised cases are waiting for final SFC approval.",
                    href="/portal/applications",
                    status="attention",
                )
            )
        if claim_workbench.stats.verified > 0:
            actions.append(
                WorkbenchAction(
                    title="Release verified subsidy claims",
                    description="Verified claims are ready to be marked as released.",
                    href="/portal/claims",
                    status="attention",
                )
            )
        return PortalWorkbenchResponse(
            actor_role=PortalActorRole.SCHEME_SMFCL_APPROVER.value,
            display_name=self._display_name(portal_user),
            active_entity_count=0,
            stats=[
                WorkbenchStat(key="appraisal", label="Awaiting approval", value=appraisal),
                WorkbenchStat(key="approved", label="Approved / sanctioned", value=approved),
                WorkbenchStat(
                    key="claimsVerified",
                    label="Claims ready for release",
                    value=claim_workbench.stats.verified,
                ),
                WorkbenchStat(
                    key="claimsReleaseInProgress",
                    label="Release in progress",
                    value=claim_workbench.stats.release_in_progress,
                ),
                WorkbenchStat(
                    key="claimsReleased",
                    label="Claims released",
                    value=claim_workbench.stats.released,
                ),
            ],
            priority_actions=actions,
            recent_applications=self._recent_applications(
                [
                    app
                    for app in apps
                    if derive_scheme_application_status(
                        app.status,
                        app.stage,
                        app.extra_data or {},
                    )
                    in {"SMFCL_APPRAISAL", "APPROVED", "SANCTION_ISSUED"}
                ]
            ),
        )

    async def _ministry_workbench(
        self,
        portal_user: PortalUser,
    ) -> PortalWorkbenchResponse:
        apps = await self._load_org_applications(portal_user)
        claim_workbench = await PortalClaimService(self.db).get_workbench(
            portal_user,
            claims_limit=25,
        )
        statuses = [
            derive_scheme_application_status(app.status, app.stage, app.extra_data or {})
            for app in apps
        ]
        submitted = sum(status != "DRAFT" for status in statuses)
        approved = sum(
            status in {"APPROVED", "SANCTION_ISSUED", "CLAIM_OPEN", "RELEASED"}
            for status in statuses
        )
        released = claim_workbench.stats.released
        return PortalWorkbenchResponse(
            actor_role=PortalActorRole.SCHEME_MINISTRY_VIEWER.value,
            display_name=self._display_name(portal_user),
            active_entity_count=0,
            stats=[
                WorkbenchStat(key="submitted", label="Submitted applications", value=submitted),
                WorkbenchStat(key="approved", label="Approved / sanctioned", value=approved),
                WorkbenchStat(
                    key="claimsSubmitted",
                    label="Submitted claims",
                    value=claim_workbench.stats.submitted,
                ),
                WorkbenchStat(key="claimsReleased", label="Claims released", value=released),
            ],
            priority_actions=[],
            recent_applications=self._recent_applications(apps),
        )

    async def _admin_workbench(
        self,
        portal_user: PortalUser,
    ) -> PortalWorkbenchResponse:
        reviewer = await self._smfcl_reviewer_workbench(portal_user)
        approver = await self._smfcl_approver_workbench(portal_user)
        return PortalWorkbenchResponse(
            actor_role=PortalActorRole.SCHEME_ADMIN.value,
            display_name=self._display_name(portal_user),
            active_entity_count=0,
            stats=[
                *reviewer.stats[:2],
                *approver.stats[:2],
                WorkbenchStat(
                    key="claimsReadyForRelease",
                    label="Claims ready for release",
                    value=next(
                        (stat.value for stat in approver.stats if stat.key == "claimsVerified"),
                        0,
                    ),
                ),
            ],
            priority_actions=reviewer.priority_actions
            + [
                action
                for action in approver.priority_actions
                if action.href != "/portal/applications"
            ],
            recent_applications=reviewer.recent_applications or approver.recent_applications,
        )

    async def _load_applications_for_entities(
        self,
        entity_ids: Iterable,
    ) -> list[LoanApplication]:
        stmt = (
            select(LoanApplication)
            .options(
                selectinload(LoanApplication.entity),
                selectinload(LoanApplication.product),
            )
            .where(
                LoanApplication.entity_id.in_(entity_ids),
                LoanApplication.deleted_at.is_(None),
            )
            .order_by(
                LoanApplication.updated_at.desc().nullslast(), LoanApplication.created_at.desc()
            )
        )
        return list((await self.db.execute(stmt)).scalars().all())

    async def _load_org_applications(
        self,
        portal_user: PortalUser,
    ) -> list[LoanApplication]:
        stmt = (
            select(LoanApplication)
            .options(
                selectinload(LoanApplication.entity),
                selectinload(LoanApplication.product),
            )
            .where(
                LoanApplication.organization_id == portal_user.organization_id,
                LoanApplication.deleted_at.is_(None),
            )
            .order_by(
                LoanApplication.updated_at.desc().nullslast(), LoanApplication.created_at.desc()
            )
        )
        return list((await self.db.execute(stmt)).scalars().all())

    async def _pending_registrations_count(self) -> int:
        stmt = (
            select(func.count())
            .select_from(PortalUser)
            .where(
                PortalUser.registration_status == PortalRegistrationStatus.PENDING_APPROVAL,
                PortalUser.deleted_at.is_(None),
            )
        )
        return int((await self.db.execute(stmt)).scalar_one() or 0)

    def _display_name(self, portal_user: PortalUser) -> str:
        return (
            portal_user.registration_authorized_signatory_name
            or portal_user.email
            or portal_user.mobile
        )

    def _recent_applications(
        self,
        apps: list[LoanApplication],
        *,
        limit: int = 5,
    ) -> list[WorkbenchApplication]:
        return [
            WorkbenchApplication(
                id=app.id,
                application_number=app.application_number,
                entity_legal_name=app.entity.legal_name if app.entity else None,
                product_name=app.product.name if app.product else None,
                scheme_status=derive_scheme_application_status(
                    app.status,
                    app.stage,
                    app.extra_data or {},
                ),
                submitted_at=app.created_at if app.submission_date else None,
                updated_at=app.updated_at or app.created_at,
            )
            for app in apps[:limit]
        ]
