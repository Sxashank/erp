"""Document Studio and DMS filing rules.

Revision ID: zzc66_document_studio_and_dms_filing
Revises: zzc65_add_hris_training_tables
Create Date: 2026-05-26 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "zzc66_document_studio_and_dms_filing"
down_revision = "zzc65_add_hris_training_tables"
branch_labels = None
depends_on = None


def _base_columns() -> list[sa.Column]:
    return [
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("version", sa.Integer(), nullable=False, server_default=sa.text("1")),
    ]


def _base_constraints(table_name: str) -> list[sa.ForeignKeyConstraint | sa.PrimaryKeyConstraint]:
    return [
        sa.ForeignKeyConstraint(["created_by"], ["mst_user.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by"], ["mst_user.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["deleted_by"], ["mst_user.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=f"{table_name}_pkey"),
    ]


def upgrade() -> None:
    op.create_table(
        "dms_filing_rule",
        *_base_columns(),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("module", sa.String(length=50), nullable=False),
        sa.Column("document_type", sa.String(length=100), nullable=False),
        sa.Column("entity_type", sa.String(length=100), nullable=False),
        sa.Column("path_template", sa.String(length=2000), nullable=False),
        sa.Column(
            "access_level", sa.String(length=50), nullable=False, server_default="organization"
        ),
        sa.Column("retention_policy", sa.String(length=100), nullable=True),
        sa.Column("portal_visible", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "default_tags",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=False, server_default=sa.text("100")),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.ForeignKeyConstraint(["organization_id"], ["mst_organization.id"], ondelete="CASCADE"),
        sa.UniqueConstraint(
            "organization_id",
            "module",
            "document_type",
            "entity_type",
            name="uq_dms_filing_rule_scope",
        ),
        *_base_constraints("dms_filing_rule"),
    )
    op.create_index(
        "ix_dms_filing_rule_lookup",
        "dms_filing_rule",
        ["organization_id", "module", "document_type"],
    )
    op.create_index(
        op.f("ix_dms_filing_rule_organization_id"), "dms_filing_rule", ["organization_id"]
    )

    op.create_table(
        "dst_template",
        *_base_columns(),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("module", sa.String(length=50), nullable=False),
        sa.Column("document_type", sa.String(length=100), nullable=False),
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("product_code", sa.String(length=100), nullable=True),
        sa.Column("entity_type", sa.String(length=100), nullable=True),
        sa.Column("locale", sa.String(length=10), nullable=False, server_default="en"),
        sa.Column("channel", sa.String(length=40), nullable=False, server_default="PDF"),
        sa.Column("priority", sa.Integer(), nullable=False, server_default=sa.text("100")),
        sa.Column(
            "selection_rules",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.ForeignKeyConstraint(["organization_id"], ["mst_organization.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("organization_id", "code", name="uq_dst_template_org_code"),
        *_base_constraints("dst_template"),
    )
    op.create_index(
        "ix_dst_template_org_module_type",
        "dst_template",
        ["organization_id", "module", "document_type"],
    )
    op.create_index(op.f("ix_dst_template_organization_id"), "dst_template", ["organization_id"])

    op.create_table(
        "dst_template_version",
        *_base_columns(),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("template_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="DRAFT"),
        sa.Column("format", sa.String(length=30), nullable=False, server_default="HTML"),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("header", sa.Text(), nullable=True),
        sa.Column("footer", sa.Text(), nullable=True),
        sa.Column(
            "style_config",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "variable_schema",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "required_variables",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "locked_blocks",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("source_document_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("approved_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("retired_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("change_notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["organization_id"], ["mst_organization.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["template_id"], ["dst_template.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_document_id"], ["dms_document.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["approved_by_id"], ["mst_user.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("template_id", "version_number", name="uq_dst_template_version_number"),
        *_base_constraints("dst_template_version"),
    )
    op.create_index(
        "ix_dst_template_version_status", "dst_template_version", ["organization_id", "status"]
    )
    op.create_index(
        op.f("ix_dst_template_version_organization_id"), "dst_template_version", ["organization_id"]
    )
    op.create_index(
        op.f("ix_dst_template_version_template_id"), "dst_template_version", ["template_id"]
    )

    op.create_table(
        "dst_generated_document",
        *_base_columns(),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("module", sa.String(length=50), nullable=False),
        sa.Column("document_type", sa.String(length=100), nullable=False),
        sa.Column("document_subtype", sa.String(length=100), nullable=True),
        sa.Column("template_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("template_version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("template_code", sa.String(length=100), nullable=False),
        sa.Column("template_version", sa.Integer(), nullable=False),
        sa.Column("dms_document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("folder_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("entity_type", sa.String(length=100), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("generated_from", sa.String(length=100), nullable=True),
        sa.Column("business_number", sa.String(length=100), nullable=True),
        sa.Column(
            "render_snapshot",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("checksum", sa.String(length=128), nullable=True),
        sa.Column("portal_visible", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("finalized_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finalized_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["organization_id"], ["mst_organization.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["template_id"], ["dst_template.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["template_version_id"], ["dst_template_version.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["dms_document_id"], ["dms_document.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["folder_id"], ["dms_folder.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["finalized_by_id"], ["mst_user.id"], ondelete="SET NULL"),
        *_base_constraints("dst_generated_document"),
    )
    op.create_index(
        "ix_dst_generated_document_entity",
        "dst_generated_document",
        ["organization_id", "entity_type", "entity_id"],
    )
    op.create_index(
        "ix_dst_generated_document_template",
        "dst_generated_document",
        ["template_id", "template_version_id"],
    )

    op.create_table(
        "dst_document_package",
        *_base_columns(),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("package_number", sa.String(length=100), nullable=False),
        sa.Column("package_type", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="DRAFT"),
        sa.Column("entity_type", sa.String(length=100), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "manifest",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("finalized_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finalized_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["organization_id"], ["mst_organization.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["finalized_by_id"], ["mst_user.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("organization_id", "package_number", name="uq_dst_package_number"),
        *_base_constraints("dst_document_package"),
    )
    op.create_index(
        "ix_dst_document_package_entity",
        "dst_document_package",
        ["organization_id", "entity_type", "entity_id"],
    )

    op.create_table(
        "dst_document_package_item",
        *_base_columns(),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("package_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("dms_document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("generated_document_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("role", sa.String(length=100), nullable=False, server_default="SUPPORTING"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.ForeignKeyConstraint(["organization_id"], ["mst_organization.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["package_id"], ["dst_document_package.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["dms_document_id"], ["dms_document.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["generated_document_id"], ["dst_generated_document.id"], ondelete="SET NULL"
        ),
        sa.UniqueConstraint("package_id", "dms_document_id", name="uq_dst_package_item_doc"),
        *_base_constraints("dst_document_package_item"),
    )


def downgrade() -> None:
    op.drop_table("dst_document_package_item")
    op.drop_index("ix_dst_document_package_entity", table_name="dst_document_package")
    op.drop_table("dst_document_package")
    op.drop_index("ix_dst_generated_document_template", table_name="dst_generated_document")
    op.drop_index("ix_dst_generated_document_entity", table_name="dst_generated_document")
    op.drop_table("dst_generated_document")
    op.drop_index(op.f("ix_dst_template_version_template_id"), table_name="dst_template_version")
    op.drop_index(
        op.f("ix_dst_template_version_organization_id"), table_name="dst_template_version"
    )
    op.drop_index("ix_dst_template_version_status", table_name="dst_template_version")
    op.drop_table("dst_template_version")
    op.drop_index(op.f("ix_dst_template_organization_id"), table_name="dst_template")
    op.drop_index("ix_dst_template_org_module_type", table_name="dst_template")
    op.drop_table("dst_template")
    op.drop_index(op.f("ix_dms_filing_rule_organization_id"), table_name="dms_filing_rule")
    op.drop_index("ix_dms_filing_rule_lookup", table_name="dms_filing_rule")
    op.drop_table("dms_filing_rule")
