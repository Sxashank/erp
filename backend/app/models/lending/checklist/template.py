"""Approval-checklist template models.

A template is a reusable list of conditions (per org or platform-wide)
that a sanction operator can apply to a loan application. Each template
item carries a category, a mandatory/optional flag, an optional
``default_due_offset_days`` (resolved against the sanction date when
the template is applied), and an ``requires_evidence`` flag that the
service-layer ``mark_met`` step enforces.

The ``organization_id`` is nullable — NULL = platform default
(every NBFC inherits it). Tenant-owned overrides set
``organization_id`` to the caller's org.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    Boolean,
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
    from app.models.lending.masters import ChecklistItemCatalog


class ApprovalChecklistTemplate(BaseModel):
    """Master template — a reusable list of approval conditions."""

    __tablename__ = "mst_approval_checklist_template"
    __table_args__ = (
        # Per-org uniqueness on code; platform-default rows
        # (organization_id IS NULL) form their own implicit set since
        # Postgres treats NULL as distinct in unique indexes.
        UniqueConstraint(
            "organization_id",
            "code",
            name="uq_mst_approval_checklist_template_org_code",
        ),
        Index(
            "ix_mst_approval_checklist_template_org",
            "organization_id",
        ),
        Index(
            "ix_mst_approval_checklist_template_code",
            "code",
        ),
        Index(
            "ix_mst_approval_checklist_template_applies_to",
            "applies_to",
        ),
    )

    # ----- Tenant (NULL = platform default) ----------------------------------

    organization_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=True,
    )

    # ----- Identity ----------------------------------------------------------

    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # ChecklistAppliesTo value — kept as a String column to leave room
    # for future variants (DISBURSEMENT / OTS) without a migration.
    applies_to: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="LOAN_APPLICATION",
    )

    # Service-layer enforces "at most one default per org" — see
    # ``ChecklistTemplateService.set_default_template``.
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # ----- Relationships -----------------------------------------------------

    items: Mapped[list[ApprovalChecklistTemplateItem]] = relationship(
        "ApprovalChecklistTemplateItem",
        back_populates="template",
        cascade="all",  # No delete-orphan — we soft-delete.
        lazy="selectin",
        order_by="ApprovalChecklistTemplateItem.sort_order",
    )


class ApprovalChecklistTemplateItem(BaseModel):
    """One item inside a checklist template."""

    __tablename__ = "mst_approval_checklist_item"
    __table_args__ = (
        UniqueConstraint(
            "template_id",
            "code",
            name="uq_mst_approval_checklist_item_template_code",
        ),
        Index(
            "ix_mst_approval_checklist_item_template",
            "template_id",
        ),
        Index(
            "ix_mst_approval_checklist_item_sort",
            "template_id",
            "sort_order",
        ),
    )

    template_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        # Soft-delete on the template — keep cascade OFF so we never
        # hard-drop a row that an existing application's checklist might
        # reference via template_item_id.
        ForeignKey(
            "mst_approval_checklist_template.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    catalog_item_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_checklist_item_catalog.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    code: Mapped[str] = mapped_column(String(50), nullable=False)
    label: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ChecklistItemCategory value.
    category: Mapped[str] = mapped_column(String(50), nullable=False)

    is_mandatory: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # If set, when applied to a loan, due_date = sanction_date + offset.
    default_due_offset_days: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Forces an evidence document upload before "Mark Met" succeeds.
    requires_evidence: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    template: Mapped[ApprovalChecklistTemplate] = relationship(
        "ApprovalChecklistTemplate",
        back_populates="items",
        foreign_keys=[template_id],
        lazy="raise",
    )
    catalog_item: Mapped["ChecklistItemCatalog"] = relationship(
        "ChecklistItemCatalog",
        foreign_keys=[catalog_item_id],
        lazy="selectin",
    )
