"""Add approval-checklist tables + ``approved_amount`` column.

Schema delta:

* Adds the ``approved_amount`` column (nullable) to
  ``los_application_utilization`` so the lender's approved breakdown
  per category can sit alongside the borrower's requested split.
* Creates the four approval-checklist tables:
  ``mst_approval_checklist_template``,
  ``mst_approval_checklist_item``,
  ``los_loan_checklist``,
  ``los_loan_checklist_item``.

Seeds one platform-default template (``IIF_STANDARD``, 15 items) so
every tenant inherits a sensible starting set; tenants override by
creating their own template through the UI / API.

Revision ID: zz6_checklist_approved
Revises: zz5_add_iif_subvention
Create Date: 2026-05-12
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "zz6_checklist_approved"
down_revision: str | None = "zz5_add_iif_subvention"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# ---------------------------------------------------------------------------
# Helpers (mirrors zz5)
# ---------------------------------------------------------------------------


def _base_audit_columns() -> list[sa.Column]:
    """AuditMixin + SoftDeleteMixin + VersionedMixin column block."""
    return [
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "version",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("1"),
        ),
    ]


def _base_audit_fks(table: str) -> list[sa.ForeignKeyConstraint]:
    return [
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["mst_user.id"],
            ondelete="SET NULL",
            name=f"fk_{table}_created_by",
        ),
        sa.ForeignKeyConstraint(
            ["updated_by"],
            ["mst_user.id"],
            ondelete="SET NULL",
            name=f"fk_{table}_updated_by",
        ),
        sa.ForeignKeyConstraint(
            ["deleted_by"],
            ["mst_user.id"],
            ondelete="SET NULL",
            name=f"fk_{table}_deleted_by",
        ),
    ]


# ---------------------------------------------------------------------------
# Upgrade
# ---------------------------------------------------------------------------


def upgrade() -> None:
    # =====================================================================
    # los_application_utilization — add approved_amount (nullable)
    # =====================================================================
    op.add_column(
        "los_application_utilization",
        sa.Column(
            "approved_amount",
            sa.Numeric(18, 2),
            nullable=True,
        ),
    )

    # =====================================================================
    # mst_approval_checklist_template
    # =====================================================================
    op.create_table(
        "mst_approval_checklist_template",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        # nullable — NULL = platform-wide template every tenant inherits.
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column(
            "applies_to",
            sa.String(length=50),
            nullable=False,
            server_default=sa.text("'LOAN_APPLICATION'"),
        ),
        sa.Column(
            "is_default",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        *_base_audit_columns(),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["mst_organization.id"],
            ondelete="CASCADE",
            name="fk_mst_approval_checklist_template_organization",
        ),
        *_base_audit_fks("mst_approval_checklist_template"),
        sa.UniqueConstraint(
            "organization_id",
            "code",
            name="uq_mst_approval_checklist_template_org_code",
        ),
    )
    op.create_index(
        "ix_mst_approval_checklist_template_org",
        "mst_approval_checklist_template",
        ["organization_id"],
    )
    op.create_index(
        "ix_mst_approval_checklist_template_code",
        "mst_approval_checklist_template",
        ["code"],
    )
    op.create_index(
        "ix_mst_approval_checklist_template_applies_to",
        "mst_approval_checklist_template",
        ["applies_to"],
    )

    # =====================================================================
    # mst_approval_checklist_item
    # =====================================================================
    op.create_table(
        "mst_approval_checklist_item",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("template_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("label", sa.String(length=300), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column(
            "is_mandatory",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "sort_order",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("default_due_offset_days", sa.Integer(), nullable=True),
        sa.Column(
            "requires_evidence",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        *_base_audit_columns(),
        sa.ForeignKeyConstraint(
            ["template_id"],
            ["mst_approval_checklist_template.id"],
            ondelete="RESTRICT",
            name="fk_mst_approval_checklist_item_template",
        ),
        *_base_audit_fks("mst_approval_checklist_item"),
        sa.UniqueConstraint(
            "template_id",
            "code",
            name="uq_mst_approval_checklist_item_template_code",
        ),
    )
    op.create_index(
        "ix_mst_approval_checklist_item_template",
        "mst_approval_checklist_item",
        ["template_id"],
    )
    op.create_index(
        "ix_mst_approval_checklist_item_sort",
        "mst_approval_checklist_item",
        ["template_id", "sort_order"],
    )

    # =====================================================================
    # los_loan_checklist
    # =====================================================================
    op.create_table(
        "los_loan_checklist",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("template_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        *_base_audit_columns(),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["mst_organization.id"],
            ondelete="CASCADE",
            name="fk_los_loan_checklist_organization",
        ),
        sa.ForeignKeyConstraint(
            ["application_id"],
            ["los_loan_application.id"],
            ondelete="CASCADE",
            name="fk_los_loan_checklist_application",
        ),
        sa.ForeignKeyConstraint(
            ["template_id"],
            ["mst_approval_checklist_template.id"],
            ondelete="SET NULL",
            name="fk_los_loan_checklist_template",
        ),
        *_base_audit_fks("los_loan_checklist"),
    )
    op.create_index(
        "ix_los_loan_checklist_org",
        "los_loan_checklist",
        ["organization_id"],
    )
    op.create_index(
        "ix_los_loan_checklist_app",
        "los_loan_checklist",
        ["application_id"],
    )
    op.create_index(
        "ix_los_loan_checklist_template",
        "los_loan_checklist",
        ["template_id"],
    )
    # Partial unique index — at most one live (not-deleted) checklist
    # per application. Soft-deleted rows can coexist for audit history.
    op.create_index(
        "uq_los_loan_checklist_application_live",
        "los_loan_checklist",
        ["application_id"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    # =====================================================================
    # los_loan_checklist_item
    # =====================================================================
    op.create_table(
        "los_loan_checklist_item",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("checklist_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("template_item_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("label", sa.String(length=300), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column(
            "is_mandatory",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "sort_order",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "requires_evidence",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default=sa.text("'PENDING'"),
        ),
        sa.Column("met_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("met_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("waived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("waived_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("waiver_reason", sa.String(length=500), nullable=True),
        sa.Column("evidence_document_path", sa.String(length=1000), nullable=True),
        sa.Column(
            "evidence_uploaded_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("notes", sa.String(length=1000), nullable=True),
        *_base_audit_columns(),
        sa.ForeignKeyConstraint(
            ["checklist_id"],
            ["los_loan_checklist.id"],
            ondelete="RESTRICT",
            name="fk_los_loan_checklist_item_checklist",
        ),
        sa.ForeignKeyConstraint(
            ["template_item_id"],
            ["mst_approval_checklist_item.id"],
            ondelete="SET NULL",
            name="fk_los_loan_checklist_item_template_item",
        ),
        sa.ForeignKeyConstraint(
            ["met_by"],
            ["mst_user.id"],
            ondelete="SET NULL",
            name="fk_los_loan_checklist_item_met_by",
        ),
        sa.ForeignKeyConstraint(
            ["waived_by"],
            ["mst_user.id"],
            ondelete="SET NULL",
            name="fk_los_loan_checklist_item_waived_by",
        ),
        *_base_audit_fks("los_loan_checklist_item"),
        sa.UniqueConstraint(
            "checklist_id",
            "code",
            name="uq_los_loan_checklist_item_checklist_code",
        ),
    )
    op.create_index(
        "ix_los_loan_checklist_item_checklist",
        "los_loan_checklist_item",
        ["checklist_id"],
    )
    op.create_index(
        "ix_los_loan_checklist_item_status",
        "los_loan_checklist_item",
        ["checklist_id", "status"],
    )
    op.create_index(
        "ix_los_loan_checklist_item_sort",
        "los_loan_checklist_item",
        ["checklist_id", "sort_order"],
    )

    # =====================================================================
    # Seed — platform-default IIF_STANDARD template + 15 items
    # =====================================================================
    template_id = uuid.uuid4()
    op.execute(
        sa.text("""
            INSERT INTO mst_approval_checklist_template (
                id, organization_id, code, name, description,
                applies_to, is_default, is_active, version
            ) VALUES (
                :id, NULL, :code, :name, :description,
                :applies_to, TRUE, TRUE, 1
            )
            """).bindparams(
            id=template_id,
            code="IIF_STANDARD",
            name="IIF Standard Approval Checklist",
            description=(
                "Default approval checklist for IIF-eligible loan "
                "applications. Lenders may clone and override per-tenant."
            ),
            applies_to="LOAN_APPLICATION",
        )
    )

    # (code, label, category, is_mandatory, sort_order, requires_evidence,
    #  description)
    items = [
        (
            "KYC_COMPLETE",
            "KYC verification complete (PAN, GSTIN, CIN, AADHAAR of " "authorised signatories)",
            "KYC",
            True,
            1,
            True,
            None,
        ),
        (
            "BOARD_RESOLUTION",
            "Board resolution authorising borrowing received",
            "DOCUMENT",
            True,
            2,
            True,
            None,
        ),
        (
            "MOA_AOA",
            "Memorandum + Articles of Association on file",
            "DOCUMENT",
            True,
            3,
            True,
            None,
        ),
        (
            "AUDITED_FINANCIALS_3Y",
            "Last 3 years audited financial statements",
            "DOCUMENT",
            True,
            4,
            True,
            None,
        ),
        (
            "BANK_STATEMENTS_12M",
            "12-month bank statements",
            "DOCUMENT",
            True,
            5,
            True,
            None,
        ),
        (
            "CIBIL_REPORT",
            "CIBIL/Experian commercial report pulled (score on file)",
            "COMPLIANCE",
            True,
            6,
            True,
            None,
        ),
        (
            "LEGAL_OPINION_TITLE",
            "Legal opinion on title to property collateral",
            "LEGAL",
            True,
            7,
            True,
            None,
        ),
        (
            "INSURANCE_HYP",
            "Insurance policy assigned to bank (with HYP clause)",
            "INSURANCE",
            True,
            8,
            True,
            None,
        ),
        (
            "CERSAI_CHARGE_REG",
            "CERSAI charge registration completed",
            "COMPLIANCE",
            True,
            9,
            True,
            None,
        ),
        (
            "WILFUL_DEFAULTER_CHECK",
            "Wilful defaulter / RBI defaulters list check clean",
            "COMPLIANCE",
            True,
            10,
            False,
            None,
        ),
        (
            "NESL_CHARGE",
            "NeSL charge registration",
            "LEGAL",
            True,
            11,
            False,
            None,
        ),
        (
            "PERSONAL_GUARANTEE",
            "Personal guarantee deed signed by promoter(s)",
            "LEGAL",
            False,
            12,
            True,
            None,
        ),
        (
            "IIF_TAGGING_FORM",
            "IIF tagging form submitted to SMFCL",
            "COMPLIANCE",
            False,
            13,
            True,
            ("Only required for shipyards under the IIF scheme — " "optional for non-IIF loans."),
        ),
        (
            "SITE_VISIT_REPORT",
            "Site visit & technical evaluation report",
            "DOCUMENT",
            False,
            14,
            True,
            None,
        ),
        (
            "SANCTION_LETTER_DRAFT_REVIEWED",
            "Sanction letter draft reviewed by legal",
            "LEGAL",
            True,
            15,
            False,
            None,
        ),
    ]
    for (
        code,
        label,
        category,
        is_mandatory,
        sort_order,
        requires_evidence,
        description,
    ) in items:
        op.execute(
            sa.text("""
                INSERT INTO mst_approval_checklist_item (
                    id, template_id, code, label, description, category,
                    is_mandatory, sort_order, requires_evidence,
                    is_active, version
                ) VALUES (
                    :id, :template_id, :code, :label, :description,
                    :category, :is_mandatory, :sort_order,
                    :requires_evidence, TRUE, 1
                )
                """).bindparams(
                id=uuid.uuid4(),
                template_id=template_id,
                code=code,
                label=label,
                description=description,
                category=category,
                is_mandatory=is_mandatory,
                sort_order=sort_order,
                requires_evidence=requires_evidence,
            )
        )


# ---------------------------------------------------------------------------
# Downgrade
# ---------------------------------------------------------------------------


def downgrade() -> None:
    # Drop in reverse dependency order. Seed data goes with tables.
    op.drop_index(
        "ix_los_loan_checklist_item_sort",
        table_name="los_loan_checklist_item",
    )
    op.drop_index(
        "ix_los_loan_checklist_item_status",
        table_name="los_loan_checklist_item",
    )
    op.drop_index(
        "ix_los_loan_checklist_item_checklist",
        table_name="los_loan_checklist_item",
    )
    op.drop_table("los_loan_checklist_item")

    op.drop_index(
        "uq_los_loan_checklist_application_live",
        table_name="los_loan_checklist",
    )
    op.drop_index(
        "ix_los_loan_checklist_template",
        table_name="los_loan_checklist",
    )
    op.drop_index(
        "ix_los_loan_checklist_app",
        table_name="los_loan_checklist",
    )
    op.drop_index(
        "ix_los_loan_checklist_org",
        table_name="los_loan_checklist",
    )
    op.drop_table("los_loan_checklist")

    op.drop_index(
        "ix_mst_approval_checklist_item_sort",
        table_name="mst_approval_checklist_item",
    )
    op.drop_index(
        "ix_mst_approval_checklist_item_template",
        table_name="mst_approval_checklist_item",
    )
    op.drop_table("mst_approval_checklist_item")

    op.drop_index(
        "ix_mst_approval_checklist_template_applies_to",
        table_name="mst_approval_checklist_template",
    )
    op.drop_index(
        "ix_mst_approval_checklist_template_code",
        table_name="mst_approval_checklist_template",
    )
    op.drop_index(
        "ix_mst_approval_checklist_template_org",
        table_name="mst_approval_checklist_template",
    )
    op.drop_table("mst_approval_checklist_template")

    op.drop_column("los_application_utilization", "approved_amount")
