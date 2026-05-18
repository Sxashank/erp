"""Borrower-portal applications service.

Thin orchestrator on top of:

* :class:`app.services.lending.application_service.ApplicationService`
  (LOS application CRUD)
* :class:`app.services.lending.iif.loan_utilization_service.LoanUtilizationService`
  (fund-utilization line submission)

The portal-side service exists so we keep the entity-access guard and
the camelCase wire model out of the admin LOS service.
"""

from __future__ import annotations

from datetime import UTC, datetime
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
from app.models.lending.application import (
    ApplicationDocument,
    LoanApplication,
)
from app.models.lending.entity import Entity
from app.models.lending.enums import ApplicationStage, ApplicationStatus, DocumentStage
from app.models.lending.iif.application_utilization import (
    ApplicationUtilization,
)
from app.models.lending.iif.fund_utilization_category import (
    FundUtilizationCategory,
)
from app.models.lending.product import DocumentChecklist, LoanProduct
from app.models.portal.portal_user import PortalUser
from app.schemas.lending.application import LoanApplicationCreate, LoanApplicationUpdate
from app.schemas.lending.iif import (
    ApplicationUtilizationBulkReplace,
    ApplicationUtilizationLine,
)
from app.schemas.portal.application import (
    ApplicationDetailResponse,
    ApplicationDocumentRequirementResponse,
    ApplicationDocumentResponse,
    ApplicationListItem,
    ApplicationListResponse,
    ApplicationStatusEvent,
    CreateApplicationRequest,
    FundUtilizationResponseLine,
    ProductListItem,
    UpdateApplicationRequest,
    UtilizationCategoryListItem,
)
from app.services.dms.document_service import DocumentService
from app.services.lending.application_service import ApplicationService
from app.services.lending.iif.loan_utilization_service import (
    LoanUtilizationService,
)
from app.services.portal.actor_roles import (
    APPLICATION_APPROVER_ROLES,
    APPLICATION_LENDER_ROLES,
    APPLICATION_SMFCL_REVIEW_ROLES,
    is_borrower_role,
    portal_actor_role,
)
from app.services.portal.entity_access import (
    assert_application_access,
    get_accessible_entity_ids,
)
from app.services.portal.notification_service import PortalNotificationService
from app.services.portal.scheme_rules import (
    derive_scheme_application_status,
    is_scheme_eligible_entity_type,
)


class PortalApplicationService:
    """Borrower-side wrapper over the LOS application service."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # =====================================================================
    # List
    # =====================================================================

    async def list_applications(
        self,
        portal_user: PortalUser,
        page: int,
        page_size: int,
        status: str | None = None,
        entity_id: UUID | None = None,
    ) -> ApplicationListResponse:
        page = max(1, page)
        page_size = max(1, min(page_size, 200))

        stmt = (
            select(LoanApplication)
            .options(
                selectinload(LoanApplication.entity),
                selectinload(LoanApplication.product),
            )
            .where(LoanApplication.deleted_at.is_(None))
        )
        if is_borrower_role(portal_user):
            accessible = await get_accessible_entity_ids(portal_user, self.db)
            if not accessible:
                return ApplicationListResponse(
                    items=[],
                    total=0,
                    page=page,
                    page_size=page_size,
                )
            stmt = stmt.where(LoanApplication.entity_id.in_(accessible))
            if entity_id is not None:
                if entity_id not in accessible:
                    raise NotFoundException(
                        "Entity not found",
                        error_code="ENTITY_NOT_FOUND",
                    )
                stmt = stmt.where(LoanApplication.entity_id == entity_id)
        else:
            stmt = stmt.where(LoanApplication.organization_id == portal_user.organization_id)
            if entity_id is not None:
                stmt = stmt.where(LoanApplication.entity_id == entity_id)
        stmt = stmt.order_by(LoanApplication.created_at.desc())

        rows = list((await self.db.execute(stmt)).scalars().all())
        if status:
            rows = [
                app
                for app in rows
                if (
                    (app.status.value if hasattr(app.status, "value") else str(app.status))
                    == status
                    or derive_scheme_application_status(
                        app.status,
                        app.stage,
                        app.extra_data or {},
                    )
                    == status
                )
            ]
        total = len(rows)
        rows = rows[(page - 1) * page_size : (page - 1) * page_size + page_size]

        items = [self._to_list_item(app) for app in rows]
        return ApplicationListResponse(items=items, total=total, page=page, page_size=page_size)

    # =====================================================================
    # Detail
    # =====================================================================

    async def get_application(
        self,
        portal_user: PortalUser,
        application_id: UUID,
    ) -> ApplicationDetailResponse:
        if is_borrower_role(portal_user):
            await assert_application_access(portal_user, application_id, self.db)
            stmt = (
                select(LoanApplication)
                .options(
                    selectinload(LoanApplication.entity),
                    selectinload(LoanApplication.product),
                )
                .where(LoanApplication.id == application_id)
            )
        else:
            stmt = (
                select(LoanApplication)
                .options(
                    selectinload(LoanApplication.entity),
                    selectinload(LoanApplication.product),
                )
                .where(
                    LoanApplication.id == application_id,
                    LoanApplication.organization_id == portal_user.organization_id,
                    LoanApplication.deleted_at.is_(None),
                )
            )
        application = (await self.db.execute(stmt)).scalar_one_or_none()
        if application is None:
            raise NotFoundException(
                "Application not found",
                error_code="APPLICATION_NOT_FOUND",
            )

        util_stmt = (
            select(ApplicationUtilization)
            .options(selectinload(ApplicationUtilization.category))
            .where(
                ApplicationUtilization.application_id == application_id,
                ApplicationUtilization.deleted_at.is_(None),
            )
            .order_by(ApplicationUtilization.created_at.asc())
        )
        utilization_rows = list((await self.db.execute(util_stmt)).scalars().all())

        doc_stmt = (
            select(ApplicationDocument)
            .where(
                ApplicationDocument.application_id == application_id,
                ApplicationDocument.deleted_at.is_(None),
            )
            .order_by(ApplicationDocument.upload_date.desc())
        )
        documents = list((await self.db.execute(doc_stmt)).scalars().all())
        requirement_rows = await self._get_document_requirements(
            product_id=application.product_id,
            entity_type=(
                application.entity.entity_type if application.entity is not None else None
            ),
        )

        scheme_status = derive_scheme_application_status(
            application.status,
            application.stage,
            application.extra_data or {},
        )

        return ApplicationDetailResponse(
            id=application.id,
            application_number=application.application_number,
            entity_id=application.entity_id,
            entity_legal_name=(application.entity.legal_name if application.entity else None),
            product_id=application.product_id,
            product_name=(application.product.name if application.product else None),
            requested_amount=application.requested_amount,
            tenure_months=application.requested_tenure_months,
            purpose_description=application.purpose,
            detailed_purpose=application.detailed_purpose,
            status=(
                application.status.value
                if hasattr(application.status, "value")
                else str(application.status)
            ),
            scheme_status=scheme_status,
            stage=(
                application.stage.value
                if hasattr(application.stage, "value")
                else str(application.stage)
            ),
            submitted_at=application.submitted_at,
            decision_at=(
                application.updated_at
                if scheme_status in {"APPROVED", "REJECTED", "CLOSED"}
                else None
            ),
            created_at=application.created_at,
            updated_at=application.updated_at,
            project_name=application.project_name,
            project_location=application.project_location,
            project_cost=application.project_cost,
            shipyard_name=(application.extra_data or {}).get("shipyard_name"),
            maritime_segment=(application.extra_data or {}).get("maritime_segment"),
            lender_name=(application.extra_data or {}).get("lender_name"),
            lender_branch=(application.extra_data or {}).get("lender_branch"),
            sanction_reference=(application.extra_data or {}).get("sanction_reference"),
            declaration_accepted=(application.extra_data or {}).get("declaration_accepted"),
            review_remarks=(application.extra_data or {}).get("review_remarks"),
            rejection_reason=application.rejection_reason,
            fund_utilization=[
                FundUtilizationResponseLine(
                    id=row.id,
                    category_id=row.category_id,
                    category_code=(row.category.code if row.category else None),
                    category_label=(row.category.label if row.category else None),
                    amount=row.amount,
                    approved_amount=row.approved_amount,
                    remarks=row.remarks,
                )
                for row in utilization_rows
            ],
            documents=[self._to_doc_response(d) for d in documents],
            document_requirements=self._build_document_requirement_responses(
                requirement_rows,
                documents,
            ),
            status_timeline=self._build_timeline(application),
        )

    # =====================================================================
    # Create
    # =====================================================================

    async def create_application(
        self,
        portal_user: PortalUser,
        payload: CreateApplicationRequest,
    ) -> ApplicationDetailResponse:
        self._require_borrower(portal_user)
        accessible = await get_accessible_entity_ids(portal_user, self.db)
        if payload.entity_id not in accessible:
            raise NotFoundException(
                "Entity not found",
                error_code="ENTITY_NOT_FOUND",
            )

        entity = (
            await self.db.execute(select(Entity).where(Entity.id == payload.entity_id))
        ).scalar_one_or_none()
        if entity is None:
            raise NotFoundException(
                "Entity not found",
                error_code="ENTITY_NOT_FOUND",
            )
        if not is_scheme_eligible_entity_type(entity.entity_type):
            raise BadRequestException(
                "Scheme portal supports institutional borrowers only",
                error_code="ENTITY_TYPE_NOT_ALLOWED",
            )

        product = (
            await self.db.execute(select(LoanProduct).where(LoanProduct.id == payload.product_id))
        ).scalar_one_or_none()
        if product is None:
            raise NotFoundException(
                "Product not found",
                error_code="PRODUCT_NOT_FOUND",
            )
        if product.organization_id != entity.organization_id:
            raise BadRequestException(
                "Product is not available for this entity",
                error_code="PRODUCT_NOT_AVAILABLE",
            )

        # Delegate to the established LOS service for the canonical
        # create flow (number generation, defaults, stage='LEAD',
        # status='DRAFT'). We thread the portal user's id as
        # created_by — it's a UUID column with ON DELETE SET NULL so
        # this is safe even though mst_user is a different population
        # from portal_user.
        los_service = ApplicationService(self.db)
        create_payload = LoanApplicationCreate(
            organization_id=entity.organization_id,
            entity_id=payload.entity_id,
            product_id=payload.product_id,
            requested_amount=payload.requested_amount,
            requested_tenure_months=payload.tenure_months,
            purpose=payload.purpose_description,
            detailed_purpose=payload.detailed_purpose,
            is_project_finance=bool(
                payload.project_name or payload.project_location or payload.project_cost is not None
            ),
            project_name=payload.project_name,
            project_cost=payload.project_cost,
            project_location=payload.project_location,
            extra_data={
                "shipyard_name": payload.shipyard_name,
                "maritime_segment": payload.maritime_segment,
                "lender_name": payload.lender_name,
                "lender_branch": payload.lender_branch,
                "sanction_reference": payload.sanction_reference,
                "declaration_accepted": payload.declaration_accepted,
            },
        )
        application = await los_service.create_application(
            data=create_payload,
            created_by=portal_user.id,
        )

        # Save the fund-utilization breakdown (draft — not submit=True,
        # because the borrower may want to edit lines before formally
        # submitting via a separate endpoint).
        if payload.fund_utilization:
            util_service = LoanUtilizationService(self.db)
            await util_service.bulk_replace(
                organization_id=entity.organization_id,
                application_id=application.id,
                data=ApplicationUtilizationBulkReplace(
                    lines=[
                        ApplicationUtilizationLine(
                            category_id=ln.category_id,
                            amount=ln.amount,
                            approved_amount=None,
                            remarks=ln.remarks,
                        )
                        for ln in payload.fund_utilization
                    ],
                    submit=False,
                ),
                current_user=_ServiceCurrentUser(portal_user.id),
            )

        return await self.get_application(portal_user, application.id)

    async def update_application(
        self,
        portal_user: PortalUser,
        application_id: UUID,
        payload: UpdateApplicationRequest,
    ) -> ApplicationDetailResponse:
        self._require_borrower(portal_user)
        application = await assert_application_access(portal_user, application_id, self.db)
        entity = (
            await self.db.execute(select(Entity).where(Entity.id == application.entity_id))
        ).scalar_one_or_none()
        if entity is None or not is_scheme_eligible_entity_type(entity.entity_type):
            raise BadRequestException(
                "Scheme portal supports institutional borrowers only",
                error_code="ENTITY_TYPE_NOT_ALLOWED",
            )

        los_service = ApplicationService(self.db)
        update_payload = LoanApplicationUpdate(
            requested_amount=payload.requested_amount,
            requested_tenure_months=payload.tenure_months,
            purpose=payload.purpose_description,
            detailed_purpose=payload.detailed_purpose,
            is_project_finance=(
                bool(
                    payload.project_name
                    or payload.project_location
                    or payload.project_cost is not None
                )
                if any(
                    value is not None
                    for value in (
                        payload.project_name,
                        payload.project_location,
                        payload.project_cost,
                    )
                )
                else None
            ),
            project_name=payload.project_name,
            project_cost=payload.project_cost,
            project_location=payload.project_location,
            extra_data=(
                {
                    **(application.extra_data or {}),
                    **{
                        "shipyard_name": payload.shipyard_name,
                        "maritime_segment": payload.maritime_segment,
                        "lender_name": payload.lender_name,
                        "lender_branch": payload.lender_branch,
                        "sanction_reference": payload.sanction_reference,
                        "declaration_accepted": payload.declaration_accepted,
                    },
                }
                if any(
                    value is not None
                    for value in (
                        payload.shipyard_name,
                        payload.maritime_segment,
                        payload.lender_name,
                        payload.lender_branch,
                        payload.sanction_reference,
                        payload.declaration_accepted,
                    )
                )
                else None
            ),
        )
        await los_service.update_application(application.id, update_payload, portal_user.id)

        if payload.fund_utilization is not None:
            util_service = LoanUtilizationService(self.db)
            await util_service.bulk_replace(
                organization_id=application.organization_id,
                application_id=application.id,
                data=ApplicationUtilizationBulkReplace(
                    lines=[
                        ApplicationUtilizationLine(
                            category_id=ln.category_id,
                            amount=ln.amount,
                            approved_amount=None,
                            remarks=ln.remarks,
                        )
                        for ln in payload.fund_utilization
                    ],
                    submit=False,
                ),
                current_user=_ServiceCurrentUser(portal_user.id),
            )

        return await self.get_application(portal_user, application.id)

    async def submit_application(
        self,
        portal_user: PortalUser,
        application_id: UUID,
    ) -> ApplicationDetailResponse:
        self._require_borrower(portal_user)
        application = await assert_application_access(portal_user, application_id, self.db)
        entity = (
            await self.db.execute(select(Entity).where(Entity.id == application.entity_id))
        ).scalar_one_or_none()
        if entity is None or not is_scheme_eligible_entity_type(entity.entity_type):
            raise BadRequestException(
                "Scheme portal supports institutional borrowers only",
                error_code="ENTITY_TYPE_NOT_ALLOWED",
            )
        await self._ensure_application_document_requirements(
            application,
            entity.entity_type,
        )

        los_service = ApplicationService(self.db)
        await los_service.submit_application(application.id, portal_user.id)
        refreshed = await self.db.get(LoanApplication, application.id)
        if refreshed is not None:
            refreshed.extra_data = {
                **(refreshed.extra_data or {}),
                "scheme_review_state": "LENDER_REVIEW",
                "review_remarks": None,
                "resume_review_state": None,
            }
            refreshed.updated_by = portal_user.id
            await self.db.flush()
            await self._notify_application_transition(
                application=refreshed,
                title="Scheme application submitted",
                body=(
                    f"Application {refreshed.application_number} has been submitted "
                    "for lender review."
                ),
                notification_type="SCHEME_APPLICATION_SUBMITTED",
                target_roles=list(APPLICATION_LENDER_ROLES),
            )
        return await self.get_application(portal_user, application.id)

    async def resubmit_application(
        self,
        portal_user: PortalUser,
        application_id: UUID,
    ) -> ApplicationDetailResponse:
        self._require_borrower(portal_user)
        application = await assert_application_access(portal_user, application_id, self.db)
        if application.status != ApplicationStatus.ADDITIONAL_INFO_REQUIRED:
            raise BadRequestException(
                "Only queried applications can be resubmitted",
                error_code="INVALID_TRANSITION",
            )
        entity = (
            await self.db.execute(select(Entity).where(Entity.id == application.entity_id))
        ).scalar_one_or_none()
        if entity is None or not is_scheme_eligible_entity_type(entity.entity_type):
            raise BadRequestException(
                "Scheme portal supports institutional borrowers only",
                error_code="ENTITY_TYPE_NOT_ALLOWED",
            )
        await self._ensure_application_document_requirements(
            application,
            entity.entity_type,
        )

        extra = dict(application.extra_data or {})
        resume_review_state = str(extra.get("resume_review_state") or "LENDER_REVIEW").upper()
        if resume_review_state == "SMFCL_APPRAISAL":
            application.stage = ApplicationStage.APPRAISAL
            application.status = ApplicationStatus.UNDER_REVIEW
        elif resume_review_state in {
            "LENDER_VALIDATED",
            "SMFCL_PRELIM_REVIEW",
        }:
            application.stage = ApplicationStage.APPLICATION
            application.status = ApplicationStatus.UNDER_REVIEW
            resume_review_state = "SMFCL_PRELIM_REVIEW"
        else:
            application.stage = ApplicationStage.APPLICATION
            application.status = ApplicationStatus.SUBMITTED
            resume_review_state = "LENDER_REVIEW"

        application.submitted_at = datetime.utcnow()
        extra["scheme_review_state"] = resume_review_state
        extra["review_remarks"] = None
        application.extra_data = extra
        application.updated_by = portal_user.id
        await self.db.flush()
        await self._notify_application_transition(
            application=application,
            title="Scheme application resubmitted",
            body=(
                f"Application {application.application_number} has been resubmitted "
                "after responding to the review query."
            ),
            notification_type="SCHEME_APPLICATION_RESUBMITTED",
            target_roles=(
                list(APPLICATION_LENDER_ROLES)
                if resume_review_state == "LENDER_REVIEW"
                else list(APPLICATION_SMFCL_REVIEW_ROLES)
            ),
        )
        return await self.get_application(portal_user, application.id)

    async def withdraw_application(
        self,
        portal_user: PortalUser,
        application_id: UUID,
        reason: str,
    ) -> ApplicationDetailResponse:
        self._require_borrower(portal_user)
        application = await assert_application_access(portal_user, application_id, self.db)
        if application.status in {
            ApplicationStatus.SANCTIONED,
            ApplicationStatus.REJECTED,
            ApplicationStatus.WITHDRAWN,
            ApplicationStatus.CANCELLED,
            ApplicationStatus.EXPIRED,
        }:
            raise BadRequestException(
                "Application cannot be withdrawn in its current status",
                error_code="INVALID_TRANSITION",
            )

        extra = dict(application.extra_data or {})
        extra["review_remarks"] = reason
        extra["scheme_review_state"] = "CLOSED"
        application.extra_data = extra
        application.status = ApplicationStatus.WITHDRAWN
        application.stage = ApplicationStage.CLOSED
        application.updated_by = portal_user.id
        await self.db.flush()
        await self._notify_application_transition(
            application=application,
            title="Scheme application withdrawn",
            body=(
                f"Application {application.application_number} has been withdrawn "
                f"by the borrower. Reason: {reason}"
            ),
            notification_type="SCHEME_APPLICATION_WITHDRAWN",
            target_roles=list(APPLICATION_LENDER_ROLES.union(APPLICATION_SMFCL_REVIEW_ROLES)),
            include_borrowers=False,
        )
        return await self.get_application(portal_user, application.id)

    async def lender_validate_application(
        self,
        portal_user: PortalUser,
        application_id: UUID,
        remarks: str | None = None,
    ) -> ApplicationDetailResponse:
        self._require_actor_role(portal_user, APPLICATION_LENDER_ROLES)
        application = await self._get_review_application(portal_user, application_id)
        if (
            derive_scheme_application_status(
                application.status,
                application.stage,
                application.extra_data or {},
            )
            != "LENDER_REVIEW"
        ):
            raise BadRequestException(
                "Only lender-review applications can be validated",
                error_code="INVALID_TRANSITION",
            )
        extra = dict(application.extra_data or {})
        extra["scheme_review_state"] = "LENDER_VALIDATED"
        extra["review_remarks"] = remarks
        application.extra_data = extra
        application.status = ApplicationStatus.UNDER_REVIEW
        application.stage = ApplicationStage.APPLICATION
        application.updated_by = portal_user.id
        await self.db.flush()
        await self._notify_application_transition(
            application=application,
            title="Lender review completed",
            body=(
                f"Application {application.application_number} has completed lender validation "
                "and moved to SMFCL review."
            ),
            notification_type="SCHEME_APPLICATION_LENDER_VALIDATED",
            target_roles=list(APPLICATION_SMFCL_REVIEW_ROLES),
        )
        return await self.get_application(portal_user, application.id)

    async def start_appraisal(
        self,
        portal_user: PortalUser,
        application_id: UUID,
        remarks: str | None = None,
    ) -> ApplicationDetailResponse:
        self._require_actor_role(portal_user, APPLICATION_SMFCL_REVIEW_ROLES)
        application = await self._get_review_application(portal_user, application_id)
        current_status = derive_scheme_application_status(
            application.status,
            application.stage,
            application.extra_data or {},
        )
        if current_status not in {
            "LENDER_VALIDATED",
            "SMFCL_PRELIM_REVIEW",
        }:
            raise BadRequestException(
                "Application is not ready for appraisal",
                error_code="INVALID_TRANSITION",
            )
        extra = dict(application.extra_data or {})
        extra["scheme_review_state"] = "SMFCL_APPRAISAL"
        extra["review_remarks"] = remarks
        application.extra_data = extra
        application.status = ApplicationStatus.UNDER_REVIEW
        application.stage = ApplicationStage.APPRAISAL
        application.updated_by = portal_user.id
        await self.db.flush()
        await self._notify_application_transition(
            application=application,
            title="SMFCL appraisal started",
            body=(f"Application {application.application_number} is now under SMFCL appraisal."),
            notification_type="SCHEME_APPLICATION_APPRAISAL_STARTED",
            target_roles=list(APPLICATION_APPROVER_ROLES),
        )
        return await self.get_application(portal_user, application.id)

    async def raise_query(
        self,
        portal_user: PortalUser,
        application_id: UUID,
        reason: str,
    ) -> ApplicationDetailResponse:
        self._require_actor_role(
            portal_user,
            APPLICATION_LENDER_ROLES.union(APPLICATION_SMFCL_REVIEW_ROLES),
        )
        application = await self._get_review_application(portal_user, application_id)
        current_status = derive_scheme_application_status(
            application.status,
            application.stage,
            application.extra_data or {},
        )
        if current_status in {"APPROVED", "REJECTED", "CLOSED"}:
            raise BadRequestException(
                "Application cannot be queried in its current status",
                error_code="INVALID_TRANSITION",
            )
        extra = dict(application.extra_data or {})
        extra["resume_review_state"] = current_status
        extra["scheme_review_state"] = "QUERY_PENDING"
        extra["review_remarks"] = reason
        application.extra_data = extra
        application.status = ApplicationStatus.ADDITIONAL_INFO_REQUIRED
        if application.stage == ApplicationStage.LEAD:
            application.stage = ApplicationStage.APPLICATION
        application.updated_by = portal_user.id
        await self.db.flush()
        await self._notify_application_transition(
            application=application,
            title="Additional information requested",
            body=(
                f"Application {application.application_number} requires additional information. "
                f"Review note: {reason}"
            ),
            notification_type="SCHEME_APPLICATION_QUERY",
            target_roles=[],
        )
        return await self.get_application(portal_user, application.id)

    async def approve_application(
        self,
        portal_user: PortalUser,
        application_id: UUID,
        remarks: str | None = None,
    ) -> ApplicationDetailResponse:
        self._require_actor_role(portal_user, APPLICATION_APPROVER_ROLES)
        application = await self._get_review_application(portal_user, application_id)
        current_status = derive_scheme_application_status(
            application.status,
            application.stage,
            application.extra_data or {},
        )
        if current_status not in {
            "LENDER_VALIDATED",
            "SMFCL_PRELIM_REVIEW",
            "SMFCL_APPRAISAL",
        }:
            raise BadRequestException(
                "Application cannot be approved in its current state",
                error_code="INVALID_TRANSITION",
            )
        extra = dict(application.extra_data or {})
        extra["scheme_review_state"] = "APPROVED"
        extra["review_remarks"] = remarks
        application.extra_data = extra
        application.status = ApplicationStatus.SANCTIONED
        application.stage = ApplicationStage.SANCTION
        application.updated_by = portal_user.id
        await self.db.flush()
        await self._notify_application_transition(
            application=application,
            title="Scheme application approved",
            body=(
                f"Application {application.application_number} has been approved."
                + (f" Remarks: {remarks}" if remarks else "")
            ),
            notification_type="SCHEME_APPLICATION_APPROVED",
            target_roles=[],
        )
        return await self.get_application(portal_user, application.id)

    async def reject_application(
        self,
        portal_user: PortalUser,
        application_id: UUID,
        reason: str,
    ) -> ApplicationDetailResponse:
        self._require_actor_role(
            portal_user,
            APPLICATION_LENDER_ROLES.union(APPLICATION_SMFCL_REVIEW_ROLES),
        )
        application = await self._get_review_application(portal_user, application_id)
        extra = dict(application.extra_data or {})
        extra["scheme_review_state"] = "REJECTED"
        extra["review_remarks"] = reason
        application.extra_data = extra
        application.status = ApplicationStatus.REJECTED
        application.rejection_reason = reason
        application.updated_by = portal_user.id
        await self.db.flush()
        await self._notify_application_transition(
            application=application,
            title="Scheme application rejected",
            body=(
                f"Application {application.application_number} has been rejected. "
                f"Reason: {reason}"
            ),
            notification_type="SCHEME_APPLICATION_REJECTED",
            target_roles=[],
        )
        return await self.get_application(portal_user, application.id)

    async def list_products(
        self,
        portal_user: PortalUser,
        entity_id: UUID | None = None,
    ) -> list[ProductListItem]:
        accessible = await get_accessible_entity_ids(portal_user, self.db)
        if not accessible:
            return []

        entities_stmt = select(Entity).where(
            Entity.id.in_(accessible),
            Entity.deleted_at.is_(None),
        )
        if entity_id is not None:
            if entity_id not in accessible:
                raise NotFoundException(
                    "Entity not found",
                    error_code="ENTITY_NOT_FOUND",
                )
            entities_stmt = entities_stmt.where(Entity.id == entity_id)
        entities = list((await self.db.execute(entities_stmt)).scalars().all())
        eligible_types = {
            entity.entity_type.value
            for entity in entities
            if is_scheme_eligible_entity_type(entity.entity_type)
        }
        if not eligible_types:
            return []

        org_ids = {entity.organization_id for entity in entities}
        products_stmt = (
            select(LoanProduct)
            .where(
                LoanProduct.organization_id.in_(org_ids),
                LoanProduct.deleted_at.is_(None),
                LoanProduct.is_active.is_(True),
            )
            .order_by(LoanProduct.name.asc())
        )
        products = list((await self.db.execute(products_stmt)).scalars().all())
        out: list[ProductListItem] = []
        for product in products:
            entity_types = set(product.eligible_entity_types or [])
            if entity_types and not entity_types.intersection(eligible_types):
                continue
            out.append(
                ProductListItem(
                    id=product.id,
                    code=product.code,
                    name=product.name,
                    category=(
                        product.category.value
                        if hasattr(product.category, "value")
                        else str(product.category)
                    ),
                    min_amount=product.min_amount,
                    max_amount=product.max_amount,
                    min_tenure_months=product.min_tenure_months,
                    max_tenure_months=product.max_tenure_months,
                )
            )
        return out

    async def list_utilization_categories(
        self,
        portal_user: PortalUser,
    ) -> list[UtilizationCategoryListItem]:
        stmt = (
            select(FundUtilizationCategory)
            .where(
                FundUtilizationCategory.deleted_at.is_(None),
                FundUtilizationCategory.is_active.is_(True),
            )
            .where(
                (FundUtilizationCategory.organization_id.is_(None))
                | (FundUtilizationCategory.organization_id == portal_user.organization_id)
            )
            .order_by(
                FundUtilizationCategory.sort_order.asc(),
                FundUtilizationCategory.label.asc(),
            )
        )
        rows = list((await self.db.execute(stmt)).scalars().all())
        return [
            UtilizationCategoryListItem(
                id=row.id,
                code=row.code,
                label=row.label,
                description=row.description,
                sort_order=row.sort_order,
            )
            for row in rows
        ]

    # =====================================================================
    # Documents
    # =====================================================================

    async def upload_document(
        self,
        portal_user: PortalUser,
        application_id: UUID,
        *,
        file_bytes: bytes,
        file_name: str,
        file_size_bytes: int,
        file_mime_type: str | None,
        document_name: str | None = None,
        document_code: str = "BORROWER_UPLOAD",
        file_hash: str | None = None,
    ) -> ApplicationDocumentResponse:
        from datetime import datetime

        application = await assert_application_access(portal_user, application_id, self.db)
        dms_service = DocumentService(self.db)
        checklist_item = await self._get_checklist_item_by_code(
            product_id=application.product_id,
            entity_type=(
                application.entity.entity_type if application.entity is not None else None
            ),
            document_code=document_code,
        )
        dms_document = await dms_service.upload_document(
            organization_id=application.organization_id,
            file=BytesIO(file_bytes),
            file_name=file_name,
            file_size=file_size_bytes,
            mime_type=file_mime_type or "application/octet-stream",
            name=document_name or file_name,
            description=(f"Scheme application document for " f"{application.application_number}"),
            document_type="SCHEME_APPLICATION",
            document_subtype=document_code,
            entity_type="scheme_application",
            entity_id=application.id,
            access_level=DocumentAccessLevel.ORGANIZATION,
            created_by=portal_user.id,
            auto_commit=False,
        )

        doc = ApplicationDocument(
            application_id=application.id,
            checklist_item_id=(checklist_item.id if checklist_item is not None else None),
            dms_document_id=dms_document.id,
            document_code=document_code,
            document_name=(
                document_name or (checklist_item.name if checklist_item is not None else file_name)
            ),
            file_name=file_name,
            file_path=dms_document.storage_path,
            file_size_bytes=file_size_bytes,
            file_mime_type=file_mime_type,
            file_hash=file_hash,
            upload_date=datetime.now(UTC),
            status="PENDING",
            is_mandatory=(checklist_item.is_mandatory if checklist_item is not None else False),
            created_by=portal_user.id,
        )
        self.db.add(doc)
        await self.db.flush()
        return self._to_doc_response(doc)

    async def list_documents(
        self,
        portal_user: PortalUser,
        application_id: UUID,
    ) -> list[ApplicationDocumentResponse]:
        await assert_application_access(portal_user, application_id, self.db)
        stmt = (
            select(ApplicationDocument)
            .where(
                ApplicationDocument.application_id == application_id,
                ApplicationDocument.deleted_at.is_(None),
            )
            .order_by(ApplicationDocument.upload_date.desc())
        )
        docs = list((await self.db.execute(stmt)).scalars().all())
        return [self._to_doc_response(d) for d in docs]

    async def get_document_record(
        self,
        portal_user: PortalUser,
        application_id: UUID,
        document_id: UUID,
    ) -> ApplicationDocument:
        await assert_application_access(portal_user, application_id, self.db)
        stmt = select(ApplicationDocument).where(
            ApplicationDocument.id == document_id,
            ApplicationDocument.application_id == application_id,
            ApplicationDocument.deleted_at.is_(None),
        )
        doc = (await self.db.execute(stmt)).scalar_one_or_none()
        if doc is None:
            raise NotFoundException(
                "Document not found",
                error_code="DOCUMENT_NOT_FOUND",
            )
        return doc

    # =====================================================================
    # Helpers
    # =====================================================================

    def _to_list_item(self, application: LoanApplication) -> ApplicationListItem:
        scheme_status = derive_scheme_application_status(
            application.status,
            application.stage,
            application.extra_data or {},
        )
        return ApplicationListItem(
            id=application.id,
            application_number=application.application_number,
            entity_id=application.entity_id,
            entity_legal_name=(application.entity.legal_name if application.entity else None),
            product_id=application.product_id,
            product_name=(application.product.name if application.product else None),
            requested_amount=application.requested_amount,
            tenure_months=application.requested_tenure_months,
            purpose_description=application.purpose,
            status=(
                application.status.value
                if hasattr(application.status, "value")
                else str(application.status)
            ),
            scheme_status=scheme_status,
            stage=(
                application.stage.value
                if hasattr(application.stage, "value")
                else str(application.stage)
            ),
            submitted_at=application.submitted_at,
            decision_at=(
                application.updated_at
                if scheme_status in {"APPROVED", "REJECTED", "CLOSED"}
                else None
            ),
            created_at=application.created_at,
            review_remarks=(application.extra_data or {}).get("review_remarks"),
            rejection_reason=application.rejection_reason,
        )

    def _to_doc_response(self, doc: ApplicationDocument) -> ApplicationDocumentResponse:
        return ApplicationDocumentResponse(
            id=doc.id,
            application_id=doc.application_id,
            dms_document_id=doc.dms_document_id,
            document_code=doc.document_code,
            document_name=doc.document_name,
            file_name=doc.file_name,
            file_size_bytes=doc.file_size_bytes,
            file_mime_type=doc.file_mime_type,
            status=doc.status,
            upload_date=doc.upload_date,
            document_date=doc.document_date,
            download_url=(
                f"/api/v1/portal/applications/{doc.application_id}/documents/" f"{doc.id}/download"
            ),
        )

    async def _get_document_requirements(
        self,
        *,
        product_id: UUID,
        entity_type,
    ) -> list[DocumentChecklist]:
        stmt = (
            select(DocumentChecklist)
            .where(
                DocumentChecklist.product_id == product_id,
                DocumentChecklist.required_at_stage == DocumentStage.APPLICATION,
                DocumentChecklist.is_active == True,
            )
            .order_by(DocumentChecklist.display_order.asc(), DocumentChecklist.name.asc())
        )
        rows = list((await self.db.execute(stmt)).scalars().all())
        if entity_type is None:
            return rows
        return [
            row
            for row in rows
            if not row.applicable_entity_types or entity_type.value in row.applicable_entity_types
        ]

    async def _get_checklist_item_by_code(
        self,
        *,
        product_id: UUID,
        entity_type,
        document_code: str,
    ) -> DocumentChecklist | None:
        rows = await self._get_document_requirements(
            product_id=product_id,
            entity_type=entity_type,
        )
        normalized_code = document_code.strip().upper()
        for row in rows:
            if row.code.strip().upper() == normalized_code:
                return row
        return None

    def _build_document_requirement_responses(
        self,
        requirements: list[DocumentChecklist],
        documents: list[ApplicationDocument],
    ) -> list[ApplicationDocumentRequirementResponse]:
        uploaded_counts: dict[str, int] = {}
        for document in documents:
            key = document.document_code.strip().upper()
            uploaded_counts[key] = uploaded_counts.get(key, 0) + 1

        items: list[ApplicationDocumentRequirementResponse] = []
        for requirement in requirements:
            uploaded_count = uploaded_counts.get(
                requirement.code.strip().upper(),
                0,
            )
            is_uploaded = uploaded_count >= max(requirement.min_file_count or 1, 1)
            items.append(
                ApplicationDocumentRequirementResponse(
                    code=requirement.code,
                    name=requirement.name,
                    category=(
                        requirement.category.value
                        if hasattr(requirement.category, "value")
                        else str(requirement.category)
                    ),
                    required_at_stage=(
                        requirement.required_at_stage.value
                        if hasattr(requirement.required_at_stage, "value")
                        else str(requirement.required_at_stage)
                    ),
                    is_mandatory=requirement.is_mandatory,
                    min_file_count=requirement.min_file_count,
                    max_file_count=requirement.max_file_count,
                    uploaded_count=uploaded_count,
                    is_uploaded=is_uploaded,
                    missing=requirement.is_mandatory and not is_uploaded,
                    help_text=requirement.help_text,
                )
            )
        return items

    async def _ensure_application_document_requirements(
        self,
        application: LoanApplication,
        entity_type,
    ) -> list[ApplicationDocumentRequirementResponse]:
        requirements = await self._get_document_requirements(
            product_id=application.product_id,
            entity_type=entity_type,
        )
        doc_stmt = (
            select(ApplicationDocument)
            .where(
                ApplicationDocument.application_id == application.id,
                ApplicationDocument.deleted_at.is_(None),
            )
            .order_by(ApplicationDocument.upload_date.desc())
        )
        documents = list((await self.db.execute(doc_stmt)).scalars().all())
        resolved = self._build_document_requirement_responses(
            requirements,
            documents,
        )
        missing = [requirement.name for requirement in resolved if requirement.missing]
        if missing:
            missing_text = ", ".join(missing)
            raise BadRequestException(
                "Mandatory application documents are missing: " f"{missing_text}",
                error_code="APPLICATION_DOCUMENTS_REQUIRED",
            )
        return resolved

    def _build_timeline(self, application: LoanApplication) -> list[ApplicationStatusEvent]:
        current_status = derive_scheme_application_status(
            application.status,
            application.stage,
            application.extra_data or {},
        )
        events: list[ApplicationStatusEvent] = [
            ApplicationStatusEvent(
                at=application.created_at,
                label="Application created",
                stage=(
                    application.stage.value
                    if hasattr(application.stage, "value")
                    else str(application.stage)
                ),
                status=(
                    application.status.value
                    if hasattr(application.status, "value")
                    else str(application.status)
                ),
            )
        ]
        if application.submitted_at:
            events.append(
                ApplicationStatusEvent(
                    at=application.submitted_at,
                    label="Submitted for review",
                    stage="APPLICATION",
                    status="SUBMITTED",
                )
            )
        if (
            application.updated_at
            and application.updated_at != application.created_at
            and current_status not in {"DRAFT", "LENDER_REVIEW"}
        ):
            events.append(
                ApplicationStatusEvent(
                    at=application.updated_at,
                    label=current_status.replace("_", " ").title(),
                    stage=(
                        application.stage.value
                        if hasattr(application.stage, "value")
                        else str(application.stage)
                    ),
                    status=(
                        application.status.value
                        if hasattr(application.status, "value")
                        else str(application.status)
                    ),
                )
            )
        return events

    async def _get_review_application(
        self,
        portal_user: PortalUser,
        application_id: UUID,
    ) -> LoanApplication:
        stmt = select(LoanApplication).where(
            LoanApplication.id == application_id,
            LoanApplication.organization_id == portal_user.organization_id,
            LoanApplication.deleted_at.is_(None),
        )
        application = (await self.db.execute(stmt)).scalar_one_or_none()
        if application is None:
            raise NotFoundException(
                "Application not found",
                error_code="APPLICATION_NOT_FOUND",
            )
        return application

    async def _notify_application_transition(
        self,
        *,
        application: LoanApplication,
        title: str,
        body: str,
        notification_type: str,
        target_roles: list[str],
        include_borrowers: bool = True,
    ) -> None:
        service = PortalNotificationService(self.db)
        action_url = f"/portal/applications/{application.id}"
        if include_borrowers:
            await service.notify_entity_borrowers(
                organization_id=application.organization_id,
                entity_id=application.entity_id,
                title=title,
                body=body,
                notification_type=notification_type,
                action_url=action_url,
                reference_type="SCHEME_APPLICATION",
                reference_id=application.id,
            )
        if target_roles:
            await service.notify_roles(
                organization_id=application.organization_id,
                actor_roles=target_roles,
                title=title,
                body=body,
                notification_type=notification_type,
                action_url=action_url,
                reference_type="SCHEME_APPLICATION",
                reference_id=application.id,
            )

    def _require_borrower(self, portal_user: PortalUser) -> None:
        if not is_borrower_role(portal_user):
            raise ForbiddenException(
                "Only borrower actors can perform this action",
                error_code="PORTAL_ROLE_FORBIDDEN",
            )

    def _require_actor_role(
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


class _ServiceCurrentUser:
    """Lightweight stand-in for the LOS service's ``current_user`` arg.

    The downstream :class:`LoanUtilizationService` only reads
    ``current_user.id`` to stamp ``created_by`` / ``deleted_by``. We
    pass the portal_user id since the column accepts any UUID with
    ``ON DELETE SET NULL``.
    """

    def __init__(self, user_id: UUID) -> None:
        self.id = user_id
