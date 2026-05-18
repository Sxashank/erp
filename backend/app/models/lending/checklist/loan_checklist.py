"""Per-loan checklist models.

When a template is applied to a loan application, its items are cloned
into ``los_loan_checklist_item`` rows so the application's checklist
survives later template edits. The clone captures ``template_item_id``
for traceability but is otherwise self-contained.

Mandatory items must be MET / WAIVED / NOT_APPLICABLE before
``SanctionService.approve_sanction`` lets the loan through.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.lending.checklist.template import (
        ApprovalChecklistTemplate,
        ApprovalChecklistTemplateItem,
    )


class LoanChecklist(BaseModel):
    """Live checklist attached to one loan application.

    Captures the template it was applied from (nullable for ad-hoc
    checklists) and a snapshot of the template name so the audit trail
    survives template renames.
    """

    __tablename__ = "los_loan_checklist"
    __table_args__ = (
        Index("ix_los_loan_checklist_org", "organization_id"),
        Index("ix_los_loan_checklist_app", "application_id"),
        Index("ix_los_loan_checklist_template", "template_id"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
    )
    application_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("los_loan_application.id", ondelete="CASCADE"),
        nullable=False,
    )
    template_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "mst_approval_checklist_template.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    name: Mapped[str] = mapped_column(String(200), nullable=False)

    # ----- Relationships -----------------------------------------------------

    template: Mapped[ApprovalChecklistTemplate | None] = relationship(
        "ApprovalChecklistTemplate",
        foreign_keys=[template_id],
        lazy="raise",
    )

    items: Mapped[list[LoanChecklistItem]] = relationship(
        "LoanChecklistItem",
        back_populates="checklist",
        cascade="all",  # No delete-orphan — we soft-delete.
        lazy="selectin",
        order_by="LoanChecklistItem.sort_order",
    )


class LoanChecklistItem(BaseModel):
    """Per-application checklist row.

    Carries its own status and evidence fields. Best-effort matched
    back to the original ``ApprovalChecklistTemplateItem`` by
    ``template_item_id`` for traceability — the template item may be
    soft-deleted while still being referenced here.
    """

    __tablename__ = "los_loan_checklist_item"
    __table_args__ = (
        UniqueConstraint(
            "checklist_id",
            "code",
            name="uq_los_loan_checklist_item_checklist_code",
        ),
        Index(
            "ix_los_loan_checklist_item_checklist",
            "checklist_id",
        ),
        Index(
            "ix_los_loan_checklist_item_status",
            "checklist_id",
            "status",
        ),
        Index(
            "ix_los_loan_checklist_item_sort",
            "checklist_id",
            "sort_order",
        ),
    )

    checklist_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "los_loan_checklist.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    template_item_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "mst_approval_checklist_item.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    # ----- Cloned definition (snapshot of the template item) ----------------

    code: Mapped[str] = mapped_column(String(50), nullable=False)
    label: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    is_mandatory: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    requires_evidence: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # ----- Status + completion ----------------------------------------------

    # ChecklistItemStatus value.
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING")

    met_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    met_by: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
    )

    waived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    waived_by: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
    )
    waiver_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)

    evidence_document_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    evidence_uploaded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    # ----- Relationships -----------------------------------------------------

    checklist: Mapped[LoanChecklist] = relationship(
        "LoanChecklist",
        back_populates="items",
        foreign_keys=[checklist_id],
        lazy="raise",
    )
    template_item: Mapped[ApprovalChecklistTemplateItem | None] = relationship(
        "ApprovalChecklistTemplateItem",
        foreign_keys=[template_item_id],
        lazy="raise",
    )
