"""Per-loan checklist service.

Applies templates to applications, manages per-item lifecycle
(PENDING → IN_PROGRESS → MET / WAIVED / NOT_APPLICABLE), and computes
the "mandatory pending" count that feeds the sanction-approval gate.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    NotFoundException,
)
from app.models.auth.user import User
from app.models.lending.application import LoanApplication
from app.models.lending.checklist.loan_checklist import (
    LoanChecklist,
    LoanChecklistItem,
)
from app.models.lending.checklist.template import (
    ApprovalChecklistTemplate,
)
from app.models.lending.enums import ChecklistItemStatus
from app.schemas.lending.approval_checklist import (
    LoanChecklistItemUpdate,
    MarkMetRequest,
    MarkNotApplicableRequest,
    WaiveRequest,
)
from app.services.lending.checklist.checklist_template_service import (
    ChecklistTemplateService,
)

# Statuses that count as "mandatory still pending" for the sanction gate.
_PENDING_STATUSES = {
    ChecklistItemStatus.PENDING.value,
    ChecklistItemStatus.IN_PROGRESS.value,
}

# Statuses considered "complete enough" for the gate.
_COMPLETE_STATUSES = {
    ChecklistItemStatus.MET.value,
    ChecklistItemStatus.WAIVED.value,
    ChecklistItemStatus.NOT_APPLICABLE.value,
}

_VALID_STATUSES = {e.value for e in ChecklistItemStatus}


class LoanChecklistService:
    """Service for the live per-application checklist."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self._template_service = ChecklistTemplateService(session)

    # =========================================================================
    # Apply / Replace
    # =========================================================================

    async def apply_template_to_application(
        self,
        organization_id: UUID,
        template_id: UUID,
        application_id: UUID,
        due_date_anchor: date | None,
        current_user: User,
    ) -> LoanChecklist:
        """Clone a template onto an application.

        Raises ``ConflictException`` if a live checklist already exists
        for the application — call ``replace_template_for_application``
        in that case.
        """
        await self._get_application(organization_id, application_id)

        existing = await self._get_live_checklist(organization_id, application_id)
        if existing is not None:
            raise ConflictException(
                (
                    "A checklist already exists for this application. "
                    "Use the replace endpoint to swap templates."
                ),
                error_code="CHECKLIST_ALREADY_EXISTS",
            )

        template = await self._template_service.get_template_with_items(
            organization_id, template_id
        )
        return await self._clone_template(
            organization_id=organization_id,
            application_id=application_id,
            template=template,
            due_date_anchor=due_date_anchor,
            current_user=current_user,
            carry_forward={},
        )

    async def replace_template_for_application(
        self,
        organization_id: UUID,
        template_id: UUID,
        application_id: UUID,
        due_date_anchor: date | None,
        current_user: User,
    ) -> LoanChecklist:
        """Soft-delete the existing checklist and apply a new template.

        Best-effort carries forward MET / WAIVED / NOT_APPLICABLE status
        for items whose ``code`` matches a row in the new template.
        """
        await self._get_application(organization_id, application_id)
        template = await self._template_service.get_template_with_items(
            organization_id, template_id
        )

        # Capture status of MET / WAIVED / NOT_APPLICABLE items before
        # we soft-delete the existing checklist.
        carry_forward: dict[str, LoanChecklistItem] = {}
        existing = await self._get_live_checklist(organization_id, application_id)
        if existing is not None:
            for item in existing.items:
                if item.deleted_at is not None:
                    continue
                if item.status in _COMPLETE_STATUSES:
                    carry_forward[item.code] = item
            # Soft-delete the existing checklist + every live item.
            existing.soft_delete(deleted_by=current_user.id)
            for item in existing.items:
                if item.deleted_at is None:
                    item.soft_delete(deleted_by=current_user.id)
            await self.session.flush()

        return await self._clone_template(
            organization_id=organization_id,
            application_id=application_id,
            template=template,
            due_date_anchor=due_date_anchor,
            current_user=current_user,
            carry_forward=carry_forward,
        )

    # =========================================================================
    # Read
    # =========================================================================

    async def get_for_application(
        self,
        organization_id: UUID,
        application_id: UUID,
    ) -> LoanChecklist:
        await self._get_application(organization_id, application_id)
        checklist = await self._get_live_checklist(organization_id, application_id)
        if checklist is None:
            raise NotFoundException(
                "No checklist exists for this application",
                error_code="LOAN_CHECKLIST_NOT_FOUND",
            )
        return checklist

    async def count_mandatory_pending(
        self,
        organization_id: UUID,
        application_id: UUID,
    ) -> int:
        """Return the count of mandatory items not yet completed."""
        checklist = await self._get_live_checklist(organization_id, application_id)
        if checklist is None:
            return 0
        return sum(
            1
            for i in checklist.items
            if i.deleted_at is None and i.is_mandatory and i.status in _PENDING_STATUSES
        )

    async def list_pending_mandatory_items(
        self,
        organization_id: UUID,
        application_id: UUID,
    ) -> list[LoanChecklistItem]:
        """Return the mandatory items still pending."""
        checklist = await self._get_live_checklist(organization_id, application_id)
        if checklist is None:
            return []
        return [
            i
            for i in checklist.items
            if i.deleted_at is None and i.is_mandatory and i.status in _PENDING_STATUSES
        ]

    # =========================================================================
    # Item lifecycle
    # =========================================================================

    async def update_item(
        self,
        organization_id: UUID,
        application_id: UUID,
        item_id: UUID,
        data: LoanChecklistItemUpdate,
        current_user: User,
    ) -> LoanChecklistItem:
        item = await self._get_live_item(organization_id, application_id, item_id)

        # If status is being changed, validate transition and side-effects.
        new_status = data.status
        if new_status is not None and new_status != item.status:
            if new_status not in _VALID_STATUSES:
                raise BadRequestException(
                    f"status must be one of {sorted(_VALID_STATUSES)}",
                    error_code="INVALID_CHECKLIST_STATUS",
                )
            self._apply_status_transition(
                item=item,
                target_status=new_status,
                evidence_document_path=data.evidence_document_path,
                waiver_reason=data.waiver_reason,
                notes=data.notes,
                current_user=current_user,
            )
        else:
            # Free-form patch (no status change).
            if data.evidence_document_path is not None:
                item.evidence_document_path = data.evidence_document_path
                item.evidence_uploaded_at = self._now()

        if data.notes is not None:
            item.notes = data.notes
        if data.due_date is not None:
            item.due_date = data.due_date

        item.updated_by = current_user.id
        item.version = (item.version or 1) + 1
        await self.session.flush()
        await self.session.refresh(item)
        return item

    async def mark_met(
        self,
        organization_id: UUID,
        application_id: UUID,
        item_id: UUID,
        data: MarkMetRequest,
        current_user: User,
    ) -> LoanChecklistItem:
        item = await self._get_live_item(organization_id, application_id, item_id)
        self._apply_status_transition(
            item=item,
            target_status=ChecklistItemStatus.MET.value,
            evidence_document_path=data.evidence_document_path,
            waiver_reason=None,
            notes=data.notes,
            current_user=current_user,
        )
        if data.notes is not None:
            item.notes = data.notes
        item.updated_by = current_user.id
        item.version = (item.version or 1) + 1
        await self.session.flush()
        await self.session.refresh(item)
        return item

    async def waive(
        self,
        organization_id: UUID,
        application_id: UUID,
        item_id: UUID,
        data: WaiveRequest,
        current_user: User,
    ) -> LoanChecklistItem:
        item = await self._get_live_item(organization_id, application_id, item_id)
        self._apply_status_transition(
            item=item,
            target_status=ChecklistItemStatus.WAIVED.value,
            evidence_document_path=None,
            waiver_reason=data.waiver_reason,
            notes=None,
            current_user=current_user,
        )
        item.updated_by = current_user.id
        item.version = (item.version or 1) + 1
        await self.session.flush()
        await self.session.refresh(item)
        return item

    async def mark_not_applicable(
        self,
        organization_id: UUID,
        application_id: UUID,
        item_id: UUID,
        data: MarkNotApplicableRequest,
        current_user: User,
    ) -> LoanChecklistItem:
        item = await self._get_live_item(organization_id, application_id, item_id)
        self._apply_status_transition(
            item=item,
            target_status=ChecklistItemStatus.NOT_APPLICABLE.value,
            evidence_document_path=None,
            waiver_reason=None,
            notes=data.notes,
            current_user=current_user,
        )
        if data.notes is not None:
            item.notes = data.notes
        item.updated_by = current_user.id
        item.version = (item.version or 1) + 1
        await self.session.flush()
        await self.session.refresh(item)
        return item

    async def reset_item(
        self,
        organization_id: UUID,
        application_id: UUID,
        item_id: UUID,
        current_user: User,
    ) -> LoanChecklistItem:
        item = await self._get_live_item(organization_id, application_id, item_id)
        item.status = ChecklistItemStatus.PENDING.value
        item.met_at = None
        item.met_by = None
        item.waived_at = None
        item.waived_by = None
        item.waiver_reason = None
        # We intentionally KEEP evidence + due_date so the operator
        # doesn't have to re-upload to retry.
        item.updated_by = current_user.id
        item.version = (item.version or 1) + 1
        await self.session.flush()
        await self.session.refresh(item)
        return item

    # =========================================================================
    # Helpers
    # =========================================================================

    @staticmethod
    def _now() -> datetime:
        return datetime.now(UTC)

    def _apply_status_transition(
        self,
        item: LoanChecklistItem,
        target_status: str,
        evidence_document_path: str | None,
        waiver_reason: str | None,
        notes: str | None,
        current_user: User,
    ) -> None:
        """Centralised status mutation + validation.

        - MET requires evidence when ``requires_evidence`` is True.
        - WAIVED requires ``waiver_reason``.
        """
        if target_status == ChecklistItemStatus.MET.value:
            if evidence_document_path is not None:
                item.evidence_document_path = evidence_document_path
                item.evidence_uploaded_at = self._now()
            if item.requires_evidence and not item.evidence_document_path:
                raise BadRequestException(
                    (
                        f"Item '{item.code}' requires an evidence document "
                        f"before it can be marked MET"
                    ),
                    error_code="CHECKLIST_EVIDENCE_REQUIRED",
                )
            item.status = ChecklistItemStatus.MET.value
            item.met_at = self._now()
            item.met_by = current_user.id
            # Clear waiver fields if previously waived.
            item.waived_at = None
            item.waived_by = None
            item.waiver_reason = None
        elif target_status == ChecklistItemStatus.WAIVED.value:
            if not waiver_reason or len(waiver_reason.strip()) < 5:
                raise BadRequestException(
                    (
                        f"Item '{item.code}': waiver_reason is required "
                        f"(min 5 characters) to waive"
                    ),
                    error_code="CHECKLIST_WAIVER_REASON_REQUIRED",
                )
            item.status = ChecklistItemStatus.WAIVED.value
            item.waived_at = self._now()
            item.waived_by = current_user.id
            item.waiver_reason = waiver_reason
            # Clear MET fields if previously met.
            item.met_at = None
            item.met_by = None
        elif target_status == ChecklistItemStatus.NOT_APPLICABLE.value:
            item.status = ChecklistItemStatus.NOT_APPLICABLE.value
            item.met_at = None
            item.met_by = None
            item.waived_at = None
            item.waived_by = None
            item.waiver_reason = None
        elif target_status == ChecklistItemStatus.IN_PROGRESS.value:
            item.status = ChecklistItemStatus.IN_PROGRESS.value
        elif target_status == ChecklistItemStatus.PENDING.value:
            item.status = ChecklistItemStatus.PENDING.value
            item.met_at = None
            item.met_by = None
            item.waived_at = None
            item.waived_by = None
            item.waiver_reason = None
        else:
            # _VALID_STATUSES check upstream should have caught this.
            raise BadRequestException(
                f"Unknown checklist status '{target_status}'",
                error_code="INVALID_CHECKLIST_STATUS",
            )

    async def _get_application(
        self, organization_id: UUID, application_id: UUID
    ) -> LoanApplication:
        application = await self.session.get(LoanApplication, application_id)
        if (
            application is None
            or application.deleted_at is not None
            or application.organization_id != organization_id
        ):
            raise NotFoundException(
                "Application not found",
                error_code="APPLICATION_NOT_FOUND",
            )
        return application

    async def _get_live_checklist(
        self,
        organization_id: UUID,
        application_id: UUID,
    ) -> LoanChecklist | None:
        stmt = (
            select(LoanChecklist)
            .options(selectinload(LoanChecklist.items))
            .where(
                LoanChecklist.application_id == application_id,
                LoanChecklist.organization_id == organization_id,
                LoanChecklist.deleted_at.is_(None),
            )
            .order_by(LoanChecklist.created_at.desc())
            .limit(1)
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def _get_live_item(
        self,
        organization_id: UUID,
        application_id: UUID,
        item_id: UUID,
    ) -> LoanChecklistItem:
        checklist = await self._get_live_checklist(organization_id, application_id)
        if checklist is None:
            raise NotFoundException(
                "No checklist exists for this application",
                error_code="LOAN_CHECKLIST_NOT_FOUND",
            )
        item = await self.session.get(LoanChecklistItem, item_id)
        if item is None or item.deleted_at is not None or item.checklist_id != checklist.id:
            raise NotFoundException(
                "Checklist item not found",
                error_code="CHECKLIST_ITEM_NOT_FOUND",
            )
        return item

    async def _clone_template(
        self,
        organization_id: UUID,
        application_id: UUID,
        template: ApprovalChecklistTemplate,
        due_date_anchor: date | None,
        current_user: User,
        carry_forward: dict[str, LoanChecklistItem],
    ) -> LoanChecklist:
        """Create a new ``LoanChecklist`` + ``LoanChecklistItem``s
        from the supplied template.

        ``carry_forward`` (keyed by item code) carries status / met_at /
        evidence forward from the previous live checklist when matching
        codes exist in the new template.
        """
        checklist = LoanChecklist(
            organization_id=organization_id,
            application_id=application_id,
            template_id=template.id,
            name=template.name,
            created_by=current_user.id,
        )
        self.session.add(checklist)
        await self.session.flush()

        anchor = due_date_anchor or date.today()
        for t_item in template.items:
            if t_item.deleted_at is not None:
                continue
            due = (
                anchor + timedelta(days=t_item.default_due_offset_days)
                if t_item.default_due_offset_days is not None
                else None
            )
            cf = carry_forward.get(t_item.code)
            item = LoanChecklistItem(
                checklist_id=checklist.id,
                template_item_id=t_item.id,
                code=t_item.code,
                label=t_item.label,
                description=t_item.description,
                category=t_item.category,
                is_mandatory=t_item.is_mandatory,
                sort_order=t_item.sort_order,
                requires_evidence=t_item.requires_evidence,
                status=(cf.status if cf is not None else ChecklistItemStatus.PENDING.value),
                met_at=cf.met_at if cf is not None else None,
                met_by=cf.met_by if cf is not None else None,
                waived_at=cf.waived_at if cf is not None else None,
                waived_by=cf.waived_by if cf is not None else None,
                waiver_reason=cf.waiver_reason if cf is not None else None,
                evidence_document_path=(cf.evidence_document_path if cf is not None else None),
                evidence_uploaded_at=(cf.evidence_uploaded_at if cf is not None else None),
                due_date=due,
                notes=cf.notes if cf is not None else None,
                created_by=current_user.id,
            )
            self.session.add(item)

        await self.session.flush()
        await self.session.refresh(checklist, attribute_names=["items"])
        return checklist
