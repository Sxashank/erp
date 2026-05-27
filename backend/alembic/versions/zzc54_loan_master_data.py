"""Loan master data layer — 21 tables for operator-controlled customisation.

Revision ID: zzc54_loan_master_data
Revises: zzc53_loan_lifecycle_spine
Create Date: 2026-05-21

Adds the "no-code-edit per client" master tables. Every table carries
``organization_id`` for tenant isolation, ``is_system`` to mark seeded
rows, and the standard BaseModel audit columns.

See ``app/models/lending/masters.py`` for the per-table documentation and
``app/db/seeds/lending_masters.py`` for the best-default seed.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "zzc54_loan_master_data"
down_revision: str | None = "zzc53_loan_lifecycle_spine"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# ---------------------------------------------------------------------------
# Shared column helpers — every table gets these BaseModel audit columns.
# ---------------------------------------------------------------------------


def _audit_columns() -> list[sa.Column]:
    return [
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
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
        sa.Column(
            "is_active",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
    ]


def _org_id_column() -> sa.Column:
    return sa.Column(
        "organization_id",
        postgresql.UUID(as_uuid=True),
        sa.ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
    )


def _id_column() -> sa.Column:
    return sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True)


def upgrade() -> None:
    # 1. mst_asset_class
    op.create_table(
        "mst_asset_class",
        _id_column(),
        _org_id_column(),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column(
            "details_schema",
            postgresql.JSONB,
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("valuation_required", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("valuation_frequency_months", sa.Integer, nullable=False, server_default="12"),
        sa.Column("insurance_required", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column(
            "mandatory_insurance_types",
            postgresql.ARRAY(sa.String(50)),
            nullable=False,
            server_default=sa.text("ARRAY[]::varchar[]"),
        ),
        sa.Column("registration_authority_code", sa.String(50)),
        sa.Column("default_provisioning_band", sa.String(40)),
        sa.Column("is_system", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("sort_order", sa.Integer, nullable=False, server_default="0"),
        *_audit_columns(),
        sa.UniqueConstraint("organization_id", "code", name="uq_asset_class_org_code"),
    )
    op.create_index("ix_mst_asset_class_org", "mst_asset_class", ["organization_id"])

    # 2. mst_lifecycle_event_catalog
    op.create_table(
        "mst_lifecycle_event_catalog",
        _id_column(),
        _org_id_column(),
        sa.Column("code", sa.String(80), nullable=False),
        sa.Column("label", sa.String(200), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("phase", sa.String(30)),
        sa.Column("icon", sa.String(40)),
        sa.Column(
            "is_borrower_visible_default",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "regulatory_tags",
            postgresql.ARRAY(sa.String(60)),
            nullable=False,
            server_default=sa.text("ARRAY[]::varchar[]"),
        ),
        sa.Column("is_system", sa.Boolean, nullable=False, server_default=sa.text("false")),
        *_audit_columns(),
        sa.UniqueConstraint("organization_id", "code", name="uq_lifecycle_catalog_org_code"),
    )
    op.create_index(
        "ix_mst_lifecycle_catalog_org", "mst_lifecycle_event_catalog", ["organization_id"]
    )

    # 3. mst_insurance_type
    op.create_table(
        "mst_insurance_type",
        _id_column(),
        _org_id_column(),
        sa.Column("code", sa.String(40), nullable=False),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("is_system", sa.Boolean, nullable=False, server_default=sa.text("false")),
        *_audit_columns(),
        sa.UniqueConstraint("organization_id", "code", name="uq_insurance_type_org_code"),
    )

    # 4. mst_registration_authority
    op.create_table(
        "mst_registration_authority",
        _id_column(),
        _org_id_column(),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("portal_url", sa.String(500)),
        sa.Column("integration_provider", sa.String(50)),
        sa.Column("is_system", sa.Boolean, nullable=False, server_default=sa.text("false")),
        *_audit_columns(),
        sa.UniqueConstraint("organization_id", "code", name="uq_reg_authority_org_code"),
    )

    # 5. mst_fee_type
    op.create_table(
        "mst_fee_type",
        _id_column(),
        _org_id_column(),
        sa.Column("code", sa.String(60), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("is_gst_applicable", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("gst_rate_percent", sa.Numeric(5, 2), nullable=False, server_default="18"),
        sa.Column("is_refundable", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column(
            "is_charged_to_borrower", sa.Boolean, nullable=False, server_default=sa.text("true")
        ),
        sa.Column("collection_stage", sa.String(40)),
        sa.Column("is_system", sa.Boolean, nullable=False, server_default=sa.text("false")),
        *_audit_columns(),
        sa.UniqueConstraint("organization_id", "code", name="uq_fee_type_org_code"),
    )

    # 6. mst_penal_charge_policy
    op.create_table(
        "mst_penal_charge_policy",
        _id_column(),
        _org_id_column(),
        sa.Column("code", sa.String(60), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("flat_amount", sa.Numeric(18, 2)),
        sa.Column("percent_of_overdue", sa.Numeric(5, 2)),
        sa.Column("cap_per_instalment", sa.Numeric(18, 2)),
        sa.Column("grace_days", sa.Integer, nullable=False, server_default="0"),
        sa.Column("is_capitalisable", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("effective_from", sa.Date, nullable=False),
        sa.Column("effective_to", sa.Date),
        sa.Column("is_system", sa.Boolean, nullable=False, server_default=sa.text("false")),
        *_audit_columns(),
        sa.UniqueConstraint("organization_id", "code", name="uq_penal_charge_policy_org_code"),
    )

    # 7. mst_checklist_item_catalog
    op.create_table(
        "mst_checklist_item_catalog",
        _id_column(),
        _org_id_column(),
        sa.Column("code", sa.String(80), nullable=False),
        sa.Column("label", sa.String(300), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("category", sa.String(40), nullable=False),
        sa.Column("stage", sa.String(40), nullable=False, server_default="APPLICATION"),
        sa.Column(
            "is_mandatory_default", sa.Boolean, nullable=False, server_default=sa.text("true")
        ),
        sa.Column("expiry_days", sa.Integer),
        sa.Column("is_system", sa.Boolean, nullable=False, server_default=sa.text("false")),
        *_audit_columns(),
        sa.UniqueConstraint("organization_id", "code", name="uq_checklist_catalog_org_code"),
    )
    op.create_index("ix_mst_checklist_catalog_category", "mst_checklist_item_catalog", ["category"])

    # 8. mst_npa_bucket
    op.create_table(
        "mst_npa_bucket",
        _id_column(),
        _org_id_column(),
        sa.Column("code", sa.String(40), nullable=False),
        sa.Column("label", sa.String(80), nullable=False),
        sa.Column("asset_classification", sa.String(40), nullable=False),
        sa.Column("min_dpd", sa.Integer, nullable=False),
        sa.Column("max_dpd", sa.Integer),
        sa.Column("sort_order", sa.Integer, nullable=False, server_default="0"),
        sa.Column("effective_from", sa.Date, nullable=False),
        sa.Column("effective_to", sa.Date),
        sa.Column("loan_segment", sa.String(40)),
        sa.Column("is_system", sa.Boolean, nullable=False, server_default=sa.text("false")),
        *_audit_columns(),
        sa.UniqueConstraint(
            "organization_id", "code", "effective_from", name="uq_npa_bucket_org_code_from"
        ),
    )
    op.create_index(
        "ix_mst_npa_bucket_org_effective", "mst_npa_bucket", ["organization_id", "effective_from"]
    )

    # 9. mst_provisioning_rate
    op.create_table(
        "mst_provisioning_rate",
        _id_column(),
        _org_id_column(),
        sa.Column("asset_classification", sa.String(40), nullable=False),
        sa.Column("secured_unsecured", sa.String(20), nullable=False),
        sa.Column("loan_segment", sa.String(40), nullable=False, server_default="DEFAULT"),
        sa.Column("rate_percent", sa.Numeric(7, 4), nullable=False),
        sa.Column("nbfc_layer", sa.String(10)),
        sa.Column("effective_from", sa.Date, nullable=False),
        sa.Column("effective_to", sa.Date),
        sa.Column("is_system", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("notes", sa.Text),
        *_audit_columns(),
        sa.UniqueConstraint(
            "organization_id",
            "asset_classification",
            "secured_unsecured",
            "loan_segment",
            "effective_from",
            name="uq_provisioning_rate_unique",
        ),
    )
    op.create_index(
        "ix_mst_provisioning_rate_lookup",
        "mst_provisioning_rate",
        ["organization_id", "asset_classification", "secured_unsecured", "effective_from"],
    )

    # 10. mst_day_count_convention
    op.create_table(
        "mst_day_count_convention",
        _id_column(),
        _org_id_column(),
        sa.Column("code", sa.String(20), nullable=False),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("days_in_year", sa.Integer, nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("is_system", sa.Boolean, nullable=False, server_default=sa.text("false")),
        *_audit_columns(),
        sa.UniqueConstraint("organization_id", "code", name="uq_day_count_org_code"),
    )

    # 11. mst_approval_matrix
    op.create_table(
        "mst_approval_matrix",
        _id_column(),
        _org_id_column(),
        sa.Column("action_code", sa.String(60), nullable=False),
        sa.Column("band_min", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("band_max", sa.Numeric(18, 2)),
        sa.Column("authority_role", sa.String(80), nullable=False),
        sa.Column(
            "requires_maker_checker", sa.Boolean, nullable=False, server_default=sa.text("true")
        ),
        sa.Column("escalation_role", sa.String(80)),
        sa.Column("sla_hours", sa.Integer),
        sa.Column("effective_from", sa.Date, nullable=False),
        sa.Column("effective_to", sa.Date),
        sa.Column("is_system", sa.Boolean, nullable=False, server_default=sa.text("false")),
        *_audit_columns(),
        sa.UniqueConstraint(
            "organization_id",
            "action_code",
            "band_min",
            "effective_from",
            name="uq_approval_matrix_unique",
        ),
    )
    op.create_index(
        "ix_mst_approval_matrix_lookup",
        "mst_approval_matrix",
        ["organization_id", "action_code", "band_min"],
    )

    # 12. mst_sla_matrix
    op.create_table(
        "mst_sla_matrix",
        _id_column(),
        _org_id_column(),
        sa.Column("stage", sa.String(40), nullable=False),
        sa.Column("action_code", sa.String(60), nullable=False),
        sa.Column("product_code", sa.String(40), nullable=False, server_default="DEFAULT"),
        sa.Column("tat_hours", sa.Integer, nullable=False),
        sa.Column("escalation_role", sa.String(80)),
        sa.Column("escalation_after_hours", sa.Integer),
        sa.Column("is_system", sa.Boolean, nullable=False, server_default=sa.text("false")),
        *_audit_columns(),
        sa.UniqueConstraint(
            "organization_id",
            "stage",
            "action_code",
            "product_code",
            name="uq_sla_matrix_unique",
        ),
    )

    # 13. mst_document_template
    op.create_table(
        "mst_document_template",
        _id_column(),
        _org_id_column(),
        sa.Column("code", sa.String(60), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("body_format", sa.String(20), nullable=False, server_default="MARKDOWN"),
        sa.Column(
            "merge_fields_schema",
            postgresql.JSONB,
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("locale", sa.String(10), nullable=False, server_default="en"),
        sa.Column("template_version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("is_current", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("is_system", sa.Boolean, nullable=False, server_default=sa.text("false")),
        *_audit_columns(),
        sa.UniqueConstraint(
            "organization_id", "code", "template_version", "locale", name="uq_doc_template_unique"
        ),
    )
    op.create_index(
        "ix_mst_doc_template_org_code", "mst_document_template", ["organization_id", "code"]
    )

    # 14. mst_communication_template
    op.create_table(
        "mst_communication_template",
        _id_column(),
        _org_id_column(),
        sa.Column("event_code", sa.String(80), nullable=False),
        sa.Column("channel", sa.String(20), nullable=False),
        sa.Column("locale", sa.String(10), nullable=False, server_default="en"),
        sa.Column("template_version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("is_current", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("subject", sa.String(300)),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("requires_opt_in", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("is_system", sa.Boolean, nullable=False, server_default=sa.text("false")),
        *_audit_columns(),
        sa.UniqueConstraint(
            "organization_id",
            "event_code",
            "channel",
            "locale",
            "template_version",
            name="uq_comm_template_unique",
        ),
    )
    op.create_index(
        "ix_mst_comm_template_event",
        "mst_communication_template",
        ["organization_id", "event_code"],
    )

    # 15. mst_rate_reset_benchmark
    op.create_table(
        "mst_rate_reset_benchmark",
        _id_column(),
        _org_id_column(),
        sa.Column("code", sa.String(30), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("current_value_percent", sa.Numeric(8, 4), nullable=False),
        sa.Column("effective_from", sa.Date, nullable=False),
        sa.Column("is_system", sa.Boolean, nullable=False, server_default=sa.text("false")),
        *_audit_columns(),
        sa.UniqueConstraint(
            "organization_id",
            "code",
            "effective_from",
            name="uq_rate_benchmark_unique",
        ),
    )

    # 16. mst_charge_trigger_rule
    op.create_table(
        "mst_charge_trigger_rule",
        _id_column(),
        _org_id_column(),
        sa.Column("trigger_event_code", sa.String(80), nullable=False),
        sa.Column("fee_type_code", sa.String(60), nullable=False),
        sa.Column("flat_amount", sa.Numeric(18, 2)),
        sa.Column("percent_of_amount", sa.Numeric(7, 4)),
        sa.Column("apply_gst", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("notes", sa.Text),
        sa.Column("is_system", sa.Boolean, nullable=False, server_default=sa.text("false")),
        *_audit_columns(),
        sa.UniqueConstraint(
            "organization_id",
            "trigger_event_code",
            "fee_type_code",
            name="uq_charge_trigger_unique",
        ),
    )

    # 17. mst_classification_override_policy
    op.create_table(
        "mst_classification_override_policy",
        _id_column(),
        _org_id_column(),
        sa.Column("code", sa.String(80), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("applies_to_segment", sa.String(40)),
        sa.Column("grace_days_addition", sa.Integer, nullable=False, server_default="0"),
        sa.Column("revivable_interest_cap_percent", sa.Numeric(5, 2)),
        sa.Column("effective_from", sa.Date, nullable=False),
        sa.Column("effective_to", sa.Date),
        sa.Column("is_system", sa.Boolean, nullable=False, server_default=sa.text("false")),
        *_audit_columns(),
    )

    # 18. mst_wilful_defaulter_committee
    op.create_table(
        "mst_wilful_defaulter_committee",
        _id_column(),
        _org_id_column(),
        sa.Column("committee_type", sa.String(20), nullable=False),
        sa.Column("role", sa.String(30), nullable=False),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("mst_user.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("effective_from", sa.Date, nullable=False),
        sa.Column("effective_to", sa.Date),
        sa.Column("is_system", sa.Boolean, nullable=False, server_default=sa.text("false")),
        *_audit_columns(),
    )

    # 19. mst_recovery_agent
    op.create_table(
        "mst_recovery_agent",
        _id_column(),
        _org_id_column(),
        sa.Column("agent_code", sa.String(40), nullable=False),
        sa.Column("agent_name", sa.String(200), nullable=False),
        sa.Column("agency_name", sa.String(200)),
        sa.Column("id_card_number", sa.String(80)),
        sa.Column("id_card_validity", sa.Date),
        sa.Column("training_cert_validity", sa.Date),
        sa.Column("allowed_contact_from_hour", sa.Integer, nullable=False, server_default="8"),
        sa.Column("allowed_contact_to_hour", sa.Integer, nullable=False, server_default="19"),
        sa.Column("contact_phone", sa.String(20)),
        sa.Column("contact_email", sa.String(200)),
        *_audit_columns(),
    )

    # 20. mst_fee_gl_mapping
    op.create_table(
        "mst_fee_gl_mapping",
        _id_column(),
        _org_id_column(),
        sa.Column("fee_type_code", sa.String(60), nullable=False),
        sa.Column(
            "income_account_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("mst_account.id", ondelete="SET NULL"),
        ),
        sa.Column(
            "receivable_account_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("mst_account.id", ondelete="SET NULL"),
        ),
        sa.Column(
            "gst_payable_account_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("mst_account.id", ondelete="SET NULL"),
        ),
        sa.Column("notes", sa.Text),
        *_audit_columns(),
        sa.UniqueConstraint("organization_id", "fee_type_code", name="uq_fee_gl_mapping_unique"),
    )

    # 21. mst_nach_return_reason
    op.create_table(
        "mst_nach_return_reason",
        _id_column(),
        _org_id_column(),
        sa.Column("code", sa.String(10), nullable=False),
        sa.Column("description", sa.String(300), nullable=False),
        sa.Column("category", sa.String(40), nullable=False, server_default="OTHER"),
        sa.Column(
            "auto_retry_eligible", sa.Boolean, nullable=False, server_default=sa.text("false")
        ),
        sa.Column("triggers_charge", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("is_system", sa.Boolean, nullable=False, server_default=sa.text("true")),
        *_audit_columns(),
        sa.UniqueConstraint("organization_id", "code", name="uq_nach_return_reason_unique"),
    )


def downgrade() -> None:
    # Drop in reverse order to satisfy any cross-FK dependencies.
    for table in (
        "mst_nach_return_reason",
        "mst_fee_gl_mapping",
        "mst_recovery_agent",
        "mst_wilful_defaulter_committee",
        "mst_classification_override_policy",
        "mst_charge_trigger_rule",
        "mst_rate_reset_benchmark",
        "mst_communication_template",
        "mst_document_template",
        "mst_sla_matrix",
        "mst_approval_matrix",
        "mst_day_count_convention",
        "mst_provisioning_rate",
        "mst_npa_bucket",
        "mst_checklist_item_catalog",
        "mst_penal_charge_policy",
        "mst_fee_type",
        "mst_registration_authority",
        "mst_insurance_type",
        "mst_lifecycle_event_catalog",
        "mst_asset_class",
    ):
        op.drop_table(table)
