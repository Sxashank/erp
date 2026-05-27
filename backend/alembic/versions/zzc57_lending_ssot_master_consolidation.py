"""Lending master SSOT consolidation.

Revision ID: zzc57_lending_ssot_master_consolidation
Revises: zzc56_lifecycle_modules
Create Date: 2026-05-26
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "zzc57_lending_ssot_master_consolidation"
down_revision: str | None = "zzc56_lifecycle_modules"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _audit_columns() -> list[sa.Column]:
    return [
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("mst_user.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "updated_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("mst_user.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "deleted_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("mst_user.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
    ]


def upgrade() -> None:
    op.create_table(
        "mst_lending_option",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("mst_organization.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("option_group", sa.String(80), nullable=False),
        sa.Column("code", sa.String(80), nullable=False),
        sa.Column("label", sa.String(200), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("sort_order", sa.Integer, nullable=False, server_default="0"),
        sa.Column("is_system", sa.Boolean, nullable=False, server_default=sa.text("false")),
        *_audit_columns(),
        sa.UniqueConstraint(
            "organization_id",
            "option_group",
            "code",
            name="uq_lending_option_org_group_code",
        ),
    )
    op.create_index(
        "ix_mst_lending_option_group",
        "mst_lending_option",
        ["organization_id", "option_group"],
    )

    op.add_column(
        "los_document_checklist",
        sa.Column("catalog_item_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "mst_approval_checklist_item",
        sa.Column("catalog_item_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "los_loan_checklist_item",
        sa.Column("catalog_item_id", postgresql.UUID(as_uuid=True), nullable=True),
    )

    # Backfill existing free-text product document requirements into the
    # checklist catalog before enforcing the SSOT foreign key.
    op.execute("""
        WITH source AS (
            SELECT DISTINCT ON (product.organization_id, doc.code)
                product.organization_id,
                doc.code,
                doc.name,
                doc.description,
                doc.category::text AS category,
                doc.required_at_stage::text AS stage,
                doc.is_mandatory
            FROM los_document_checklist doc
            JOIN los_loan_product product ON product.id = doc.product_id
            ORDER BY product.organization_id, doc.code, doc.created_at NULLS LAST
        )
        INSERT INTO mst_checklist_item_catalog (
            id,
            organization_id,
            code,
            label,
            description,
            category,
            stage,
            is_mandatory_default,
            is_system,
            created_at,
            is_active,
            version
        )
        SELECT
            gen_random_uuid(),
            source.organization_id,
            source.code,
            source.name,
            source.description,
            source.category,
            source.stage,
            source.is_mandatory,
            true,
            now(),
            true,
            1
        FROM source
        WHERE NOT EXISTS (
            SELECT 1
            FROM mst_checklist_item_catalog catalog
            WHERE catalog.organization_id = source.organization_id
              AND catalog.code = source.code
        )
        """)
    op.execute("""
        UPDATE los_document_checklist doc
        SET catalog_item_id = catalog.id
        FROM los_loan_product product
        JOIN mst_checklist_item_catalog catalog
          ON catalog.organization_id = product.organization_id
        WHERE product.id = doc.product_id
          AND catalog.code = doc.code
          AND doc.catalog_item_id IS NULL
        """)

    # Existing org-owned approval templates are also free-text. Attach them to
    # catalog items with the same code, creating missing catalog rows first.
    op.execute("""
        WITH source AS (
            SELECT DISTINCT ON (template.organization_id, item.code)
                template.organization_id,
                item.code,
                item.label,
                item.description,
                item.category,
                template.applies_to AS stage,
                item.is_mandatory
            FROM mst_approval_checklist_item item
            JOIN mst_approval_checklist_template template ON template.id = item.template_id
            WHERE template.organization_id IS NOT NULL
            ORDER BY template.organization_id, item.code, item.created_at NULLS LAST
        )
        INSERT INTO mst_checklist_item_catalog (
            id,
            organization_id,
            code,
            label,
            description,
            category,
            stage,
            is_mandatory_default,
            is_system,
            created_at,
            is_active,
            version
        )
        SELECT
            gen_random_uuid(),
            source.organization_id,
            source.code,
            source.label,
            source.description,
            source.category,
            source.stage,
            source.is_mandatory,
            true,
            now(),
            true,
            1
        FROM source
        WHERE NOT EXISTS (
              SELECT 1
              FROM mst_checklist_item_catalog catalog
              WHERE catalog.organization_id = source.organization_id
                AND catalog.code = source.code
          )
        """)
    op.execute("""
        UPDATE mst_approval_checklist_item item
        SET catalog_item_id = catalog.id
        FROM mst_approval_checklist_template template
        JOIN mst_checklist_item_catalog catalog
          ON catalog.organization_id = template.organization_id
        WHERE template.id = item.template_id
          AND template.organization_id IS NOT NULL
          AND catalog.code = item.code
          AND item.catalog_item_id IS NULL
        """)

    # Previous seeds allowed platform-default approval templates while the
    # checklist catalog is tenant-owned. Convert those platform defaults into
    # tenant-owned templates, then remove the global rows so every template item
    # can point at a tenant-scoped catalog row.
    op.execute("""
        WITH source AS (
            SELECT DISTINCT ON (org.id, item.code)
                org.id AS organization_id,
                item.code,
                item.label,
                item.description,
                item.category,
                template.applies_to AS stage,
                item.is_mandatory
            FROM mst_approval_checklist_item item
            JOIN mst_approval_checklist_template template ON template.id = item.template_id
            CROSS JOIN mst_organization org
            WHERE template.organization_id IS NULL
            ORDER BY org.id, item.code, item.created_at NULLS LAST
        )
        INSERT INTO mst_checklist_item_catalog (
            id,
            organization_id,
            code,
            label,
            description,
            category,
            stage,
            is_mandatory_default,
            is_system,
            created_at,
            is_active,
            version
        )
        SELECT
            gen_random_uuid(),
            source.organization_id,
            source.code,
            source.label,
            source.description,
            source.category,
            source.stage,
            source.is_mandatory,
            true,
            now(),
            true,
            1
        FROM source
        WHERE NOT EXISTS (
              SELECT 1
              FROM mst_checklist_item_catalog catalog
              WHERE catalog.organization_id = source.organization_id
                AND catalog.code = source.code
          )
        """)
    op.execute("""
        INSERT INTO mst_approval_checklist_template (
            id,
            organization_id,
            code,
            name,
            description,
            applies_to,
            is_default,
            created_at,
            is_active,
            version
        )
        SELECT
            gen_random_uuid(),
            org.id,
            source.code,
            source.name,
            source.description,
            source.applies_to,
            source.is_default,
            now(),
            source.is_active,
            source.version
        FROM mst_approval_checklist_template source
        CROSS JOIN mst_organization org
        WHERE source.organization_id IS NULL
          AND NOT EXISTS (
              SELECT 1
              FROM mst_approval_checklist_template existing
              WHERE existing.organization_id = org.id
                AND existing.code = source.code
          )
        """)
    op.execute("""
        INSERT INTO mst_approval_checklist_item (
            id,
            template_id,
            catalog_item_id,
            code,
            label,
            description,
            category,
            is_mandatory,
            sort_order,
            default_due_offset_days,
            requires_evidence,
            created_at,
            is_active,
            version
        )
        SELECT
            gen_random_uuid(),
            target.id,
            catalog.id,
            item.code,
            item.label,
            item.description,
            item.category,
            item.is_mandatory,
            item.sort_order,
            item.default_due_offset_days,
            item.requires_evidence,
            now(),
            item.is_active,
            item.version
        FROM mst_approval_checklist_item item
        JOIN mst_approval_checklist_template source ON source.id = item.template_id
        JOIN mst_approval_checklist_template target
          ON target.code = source.code
         AND target.organization_id IS NOT NULL
        JOIN mst_checklist_item_catalog catalog
          ON catalog.organization_id = target.organization_id
         AND catalog.code = item.code
        WHERE source.organization_id IS NULL
          AND NOT EXISTS (
              SELECT 1
              FROM mst_approval_checklist_item existing
              WHERE existing.template_id = target.id
                AND existing.code = item.code
          )
        """)
    op.execute("""
        UPDATE los_loan_checklist
        SET template_id = NULL
        WHERE template_id IN (
            SELECT id
            FROM mst_approval_checklist_template
            WHERE organization_id IS NULL
        )
        """)
    op.execute("""
        DELETE FROM mst_approval_checklist_item
        WHERE template_id IN (
            SELECT id
            FROM mst_approval_checklist_template
            WHERE organization_id IS NULL
        )
        """)
    op.execute("DELETE FROM mst_approval_checklist_template WHERE organization_id IS NULL")

    op.execute("""
        UPDATE los_loan_checklist_item live_item
        SET catalog_item_id = template_item.catalog_item_id
        FROM mst_approval_checklist_item template_item
        WHERE live_item.template_item_id = template_item.id
          AND live_item.catalog_item_id IS NULL
        """)

    op.alter_column("los_document_checklist", "catalog_item_id", nullable=False)
    op.alter_column("mst_approval_checklist_item", "catalog_item_id", nullable=False)
    op.create_foreign_key(
        "fk_los_document_checklist_catalog_item",
        "los_document_checklist",
        "mst_checklist_item_catalog",
        ["catalog_item_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index(
        "ix_los_doc_checklist_catalog",
        "los_document_checklist",
        ["catalog_item_id"],
    )

    op.create_foreign_key(
        "fk_mst_approval_checklist_item_catalog",
        "mst_approval_checklist_item",
        "mst_checklist_item_catalog",
        ["catalog_item_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index(
        "ix_mst_approval_checklist_item_catalog",
        "mst_approval_checklist_item",
        ["catalog_item_id"],
    )

    op.create_foreign_key(
        "fk_los_loan_checklist_item_catalog",
        "los_loan_checklist_item",
        "mst_checklist_item_catalog",
        ["catalog_item_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_los_loan_checklist_item_catalog",
        "los_loan_checklist_item",
        ["catalog_item_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_los_loan_checklist_item_catalog", table_name="los_loan_checklist_item")
    op.drop_constraint(
        "fk_los_loan_checklist_item_catalog",
        "los_loan_checklist_item",
        type_="foreignkey",
    )
    op.drop_column("los_loan_checklist_item", "catalog_item_id")

    op.drop_index(
        "ix_mst_approval_checklist_item_catalog", table_name="mst_approval_checklist_item"
    )
    op.drop_constraint(
        "fk_mst_approval_checklist_item_catalog",
        "mst_approval_checklist_item",
        type_="foreignkey",
    )
    op.drop_column("mst_approval_checklist_item", "catalog_item_id")

    op.drop_index("ix_los_doc_checklist_catalog", table_name="los_document_checklist")
    op.drop_constraint(
        "fk_los_document_checklist_catalog_item",
        "los_document_checklist",
        type_="foreignkey",
    )
    op.drop_column("los_document_checklist", "catalog_item_id")

    op.drop_index("ix_mst_lending_option_group", table_name="mst_lending_option")
    op.drop_table("mst_lending_option")
