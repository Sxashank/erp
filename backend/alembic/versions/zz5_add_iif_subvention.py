"""Add IIF (Interest Incentivization Fund) tables + seed scheme.

Creates the five tables that power the IIF subvention module under the
Maritime Development Fund:

* ``mst_subvention_scheme``
* ``mst_fund_utilization_category``
* ``los_application_utilization``
* ``los_loan_subvention_enrollment``
* ``txn_subvention_claim``

Seeds one ``SubventionScheme`` row with ``scheme_code='IIF'`` and the
seven canonical ``FundUtilizationCategory`` rows (Land acquisition,
Civil works, Plant & machinery, Consultancy fees, IDC, Taxes &
duties, Contingencies). ``organization_id`` on the seeded rows is NULL
so every tenant inherits the same default; per-NBFC overrides are
created at runtime with the tenant's own org id.

Revision ID: zz5_add_iif_subvention
Revises: zz4_add_fin_capital_snapshot
Create Date: 2026-05-13
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import date
from decimal import Decimal

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "zz5_add_iif_subvention"
down_revision: str | None = "zz4_add_fin_capital_snapshot"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _base_audit_columns() -> list[sa.Column]:
    """The AuditMixin + SoftDeleteMixin + VersionedMixin column block."""
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
    """The user-FK constraints that ride with every audit-mixed table."""
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
    # mst_subvention_scheme
    # =====================================================================
    op.create_table(
        "mst_subvention_scheme",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        # nullable — NULL = platform-wide scheme.
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column("scheme_code", sa.String(length=50), nullable=False),
        sa.Column("scheme_name", sa.String(length=200), nullable=False),
        sa.Column("administering_ministry", sa.String(length=200), nullable=True),
        sa.Column("implementing_agency", sa.String(length=200), nullable=True),
        sa.Column("subvention_rate_percent", sa.Numeric(9, 4), nullable=False),
        sa.Column(
            "max_subvention_per_beneficiary",
            sa.Numeric(18, 2),
            nullable=True,
        ),
        sa.Column("scheme_corpus", sa.Numeric(18, 2), nullable=True),
        sa.Column(
            "eligible_loan_types",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("max_tenure_term_loan_months", sa.Integer(), nullable=True),
        sa.Column("max_tenure_working_capital_months", sa.Integer(), nullable=True),
        sa.Column("scheme_start_date", sa.Date(), nullable=False),
        sa.Column("scheme_end_date", sa.Date(), nullable=False),
        sa.Column("eligibility_window_months", sa.Integer(), nullable=True),
        sa.Column("claim_frequency", sa.String(length=20), nullable=False),
        sa.Column(
            "npa_disqualification_dpd_days",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("30"),
        ),
        sa.Column("description", sa.Text(), nullable=True),
        *_base_audit_columns(),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["mst_organization.id"],
            ondelete="CASCADE",
            name="fk_mst_subvention_scheme_organization",
        ),
        *_base_audit_fks("mst_subvention_scheme"),
        sa.UniqueConstraint(
            "organization_id",
            "scheme_code",
            name="uq_mst_subvention_scheme_org_code",
        ),
    )
    op.create_index(
        "ix_mst_subvention_scheme_org",
        "mst_subvention_scheme",
        ["organization_id"],
    )
    op.create_index(
        "ix_mst_subvention_scheme_code",
        "mst_subvention_scheme",
        ["scheme_code"],
    )

    # =====================================================================
    # mst_fund_utilization_category
    # =====================================================================
    op.create_table(
        "mst_fund_utilization_category",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column("scheme_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("label", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "sort_order",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        *_base_audit_columns(),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["mst_organization.id"],
            ondelete="CASCADE",
            name="fk_mst_fuc_organization",
        ),
        sa.ForeignKeyConstraint(
            ["scheme_id"],
            ["mst_subvention_scheme.id"],
            ondelete="CASCADE",
            name="fk_mst_fuc_scheme",
        ),
        *_base_audit_fks("mst_fund_utilization_category"),
        sa.UniqueConstraint(
            "organization_id",
            "scheme_id",
            "code",
            name="uq_mst_fuc_org_scheme_code",
        ),
    )
    op.create_index(
        "ix_mst_fuc_org",
        "mst_fund_utilization_category",
        ["organization_id"],
    )
    op.create_index(
        "ix_mst_fuc_scheme",
        "mst_fund_utilization_category",
        ["scheme_id"],
    )
    op.create_index(
        "ix_mst_fuc_code",
        "mst_fund_utilization_category",
        ["code"],
    )

    # =====================================================================
    # los_application_utilization
    # =====================================================================
    op.create_table(
        "los_application_utilization",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("remarks", sa.String(length=500), nullable=True),
        *_base_audit_columns(),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["mst_organization.id"],
            ondelete="CASCADE",
            name="fk_los_application_utilization_organization",
        ),
        sa.ForeignKeyConstraint(
            ["application_id"],
            ["los_loan_application.id"],
            ondelete="CASCADE",
            name="fk_los_application_utilization_application",
        ),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["mst_fund_utilization_category.id"],
            ondelete="RESTRICT",
            name="fk_los_application_utilization_category",
        ),
        *_base_audit_fks("los_application_utilization"),
        sa.UniqueConstraint(
            "application_id",
            "category_id",
            name="uq_los_application_utilization_app_cat",
        ),
    )
    op.create_index(
        "ix_los_application_utilization_org",
        "los_application_utilization",
        ["organization_id"],
    )
    op.create_index(
        "ix_los_application_utilization_app",
        "los_application_utilization",
        ["application_id"],
    )
    op.create_index(
        "ix_los_application_utilization_cat",
        "los_application_utilization",
        ["category_id"],
    )

    # =====================================================================
    # los_loan_subvention_enrollment
    # =====================================================================
    op.create_table(
        "los_loan_subvention_enrollment",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("loan_account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("scheme_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("enrolled_date", sa.Date(), nullable=False),
        sa.Column(
            "status",
            sa.String(length=30),
            nullable=False,
            server_default=sa.text("'PENDING_APPROVAL'"),
        ),
        sa.Column("rejection_reason", sa.String(length=500), nullable=True),
        sa.Column(
            "total_claimed_to_date",
            sa.Numeric(18, 2),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "total_paid_to_date",
            sa.Numeric(18, 2),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        *_base_audit_columns(),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["mst_organization.id"],
            ondelete="CASCADE",
            name="fk_los_lse_organization",
        ),
        sa.ForeignKeyConstraint(
            ["loan_account_id"],
            ["lms_loan_account.id"],
            ondelete="RESTRICT",
            name="fk_los_lse_loan_account",
        ),
        sa.ForeignKeyConstraint(
            ["scheme_id"],
            ["mst_subvention_scheme.id"],
            ondelete="RESTRICT",
            name="fk_los_lse_scheme",
        ),
        *_base_audit_fks("los_loan_subvention_enrollment"),
    )
    op.create_index(
        "ix_los_lse_org",
        "los_loan_subvention_enrollment",
        ["organization_id"],
    )
    op.create_index(
        "ix_los_lse_loan",
        "los_loan_subvention_enrollment",
        ["loan_account_id"],
    )
    op.create_index(
        "ix_los_lse_scheme",
        "los_loan_subvention_enrollment",
        ["scheme_id"],
    )
    op.create_index(
        "ix_los_lse_status",
        "los_loan_subvention_enrollment",
        ["status"],
    )
    # Partial unique index — at most one live (not-deleted) row per
    # (loan_account_id, scheme_id). Soft-deleted rows can coexist.
    op.create_index(
        "uq_los_lse_loan_scheme_live",
        "los_loan_subvention_enrollment",
        ["loan_account_id", "scheme_id"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    # =====================================================================
    # txn_subvention_claim
    # =====================================================================
    op.create_table(
        "txn_subvention_claim",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("enrollment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("claim_reference", sa.String(length=50), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("claim_frequency", sa.String(length=20), nullable=False),
        sa.Column("interest_paid_in_period", sa.Numeric(18, 2), nullable=False),
        sa.Column("applicable_subvention_amount", sa.Numeric(18, 2), nullable=False),
        sa.Column(
            "status",
            sa.String(length=30),
            nullable=False,
            server_default=sa.text("'DRAFT'"),
        ),
        sa.Column("submitted_date", sa.Date(), nullable=True),
        sa.Column("verified_date", sa.Date(), nullable=True),
        sa.Column("paid_date", sa.Date(), nullable=True),
        sa.Column("rejection_reason", sa.String(length=500), nullable=True),
        sa.Column("utr_reference", sa.String(length=100), nullable=True),
        sa.Column(
            "declaration_signed_by",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            "declaration_signed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "documents",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        *_base_audit_columns(),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["mst_organization.id"],
            ondelete="CASCADE",
            name="fk_txn_subvention_claim_organization",
        ),
        sa.ForeignKeyConstraint(
            ["enrollment_id"],
            ["los_loan_subvention_enrollment.id"],
            ondelete="RESTRICT",
            name="fk_txn_subvention_claim_enrollment",
        ),
        sa.ForeignKeyConstraint(
            ["declaration_signed_by"],
            ["mst_user.id"],
            ondelete="SET NULL",
            name="fk_txn_subvention_claim_signed_by",
        ),
        *_base_audit_fks("txn_subvention_claim"),
        sa.UniqueConstraint(
            "organization_id",
            "claim_reference",
            name="uq_txn_subvention_claim_org_ref",
        ),
    )
    op.create_index(
        "ix_txn_subvention_claim_org",
        "txn_subvention_claim",
        ["organization_id"],
    )
    op.create_index(
        "ix_txn_subvention_claim_enrollment",
        "txn_subvention_claim",
        ["enrollment_id"],
    )
    op.create_index(
        "ix_txn_subvention_claim_reference",
        "txn_subvention_claim",
        ["claim_reference"],
    )
    op.create_index(
        "ix_txn_subvention_claim_status",
        "txn_subvention_claim",
        ["status"],
    )
    op.create_index(
        "ix_txn_subvention_claim_period",
        "txn_subvention_claim",
        ["period_start", "period_end"],
    )

    # =====================================================================
    # Seed — platform-wide IIF scheme + 7 fund-utilization categories
    # =====================================================================

    iif_scheme_id = uuid.uuid4()
    # asyncpg infers parameter types from Python values — explicit
    # casts are still added on the SQL side as a belt-and-braces guard
    # against legacy DSNs that prepare statements aggressively.
    op.execute(
        sa.text("""
            INSERT INTO mst_subvention_scheme (
                id, organization_id, scheme_code, scheme_name,
                administering_ministry, implementing_agency,
                subvention_rate_percent, max_subvention_per_beneficiary,
                scheme_corpus, eligible_loan_types,
                max_tenure_term_loan_months, max_tenure_working_capital_months,
                scheme_start_date, scheme_end_date, eligibility_window_months,
                claim_frequency, npa_disqualification_dpd_days, description,
                is_active, version
            ) VALUES (
                :id, NULL, :scheme_code, :scheme_name,
                :ministry, :agency,
                CAST(:rate AS numeric(9,4)),
                CAST(:per_beneficiary AS numeric(18,2)),
                CAST(:corpus AS numeric(18,2)),
                CAST(:eligible_types AS jsonb),
                :tl_months, :wc_months,
                CAST(:start_date AS date),
                CAST(:end_date AS date),
                :window_months,
                :claim_freq, :npa_dpd, :description,
                TRUE, 1
            )
            """).bindparams(
            id=iif_scheme_id,
            scheme_code="IIF",
            scheme_name="Interest Incentivization Fund",
            ministry="Ministry of Ports, Shipping and Waterways",
            agency="Sagarmala Finance Corporation Limited",
            rate=Decimal("3.0000"),
            per_beneficiary=Decimal("10000000000.00"),  # ₹1,000 crore
            corpus=Decimal("50000000000.00"),  # ₹5,000 crore
            eligible_types='["TERM_LOAN_CAPEX", "WORKING_CAPITAL"]',
            tl_months=180,
            wc_months=60,
            start_date=date(2025, 9, 24),
            end_date=date(2036, 3, 31),
            window_months=36,
            claim_freq="QUARTERLY",
            npa_dpd=30,
            description=(
                "3% per-annum interest subvention administered by the "
                "Ministry of Ports, Shipping and Waterways and "
                "implemented by SMFCL for eligible Indian shipyards "
                "under the Maritime Development Fund."
            ),
        )
    )

    # Seven canonical utilization categories.
    categories = [
        ("LAND_ACQ", "Land acquisition", 1),
        ("CIVIL_WORKS", "Civil works & construction", 2),
        ("PLANT_MACHINERY", "Plant & machinery / equipment", 3),
        ("CONSULTANCY_FEES", "Consultancy & engineering fees", 4),
        ("IDC", "Interest during construction (IDC)", 5),
        ("TAXES_DUTIES", "Taxes & duties", 6),
        ("CONTINGENCIES", "Contingencies", 7),
    ]
    for code, label, sort_order in categories:
        op.execute(
            sa.text("""
                INSERT INTO mst_fund_utilization_category (
                    id, organization_id, scheme_id, code, label,
                    sort_order, is_active, version
                ) VALUES (
                    :id, NULL, :scheme_id, :code, :label,
                    :sort_order, TRUE, 1
                )
                """).bindparams(
                id=uuid.uuid4(),
                scheme_id=iif_scheme_id,
                code=code,
                label=label,
                sort_order=sort_order,
            )
        )


# ---------------------------------------------------------------------------
# Downgrade
# ---------------------------------------------------------------------------


def downgrade() -> None:
    # Drop indexes + tables in reverse dependency order. Seeded rows go
    # with the tables.
    op.drop_index("ix_txn_subvention_claim_period", table_name="txn_subvention_claim")
    op.drop_index("ix_txn_subvention_claim_status", table_name="txn_subvention_claim")
    op.drop_index(
        "ix_txn_subvention_claim_reference",
        table_name="txn_subvention_claim",
    )
    op.drop_index(
        "ix_txn_subvention_claim_enrollment",
        table_name="txn_subvention_claim",
    )
    op.drop_index("ix_txn_subvention_claim_org", table_name="txn_subvention_claim")
    op.drop_table("txn_subvention_claim")

    op.drop_index(
        "uq_los_lse_loan_scheme_live",
        table_name="los_loan_subvention_enrollment",
    )
    op.drop_index(
        "ix_los_lse_status",
        table_name="los_loan_subvention_enrollment",
    )
    op.drop_index(
        "ix_los_lse_scheme",
        table_name="los_loan_subvention_enrollment",
    )
    op.drop_index("ix_los_lse_loan", table_name="los_loan_subvention_enrollment")
    op.drop_index("ix_los_lse_org", table_name="los_loan_subvention_enrollment")
    op.drop_table("los_loan_subvention_enrollment")

    op.drop_index(
        "ix_los_application_utilization_cat",
        table_name="los_application_utilization",
    )
    op.drop_index(
        "ix_los_application_utilization_app",
        table_name="los_application_utilization",
    )
    op.drop_index(
        "ix_los_application_utilization_org",
        table_name="los_application_utilization",
    )
    op.drop_table("los_application_utilization")

    op.drop_index("ix_mst_fuc_code", table_name="mst_fund_utilization_category")
    op.drop_index("ix_mst_fuc_scheme", table_name="mst_fund_utilization_category")
    op.drop_index("ix_mst_fuc_org", table_name="mst_fund_utilization_category")
    op.drop_table("mst_fund_utilization_category")

    op.drop_index("ix_mst_subvention_scheme_code", table_name="mst_subvention_scheme")
    op.drop_index("ix_mst_subvention_scheme_org", table_name="mst_subvention_scheme")
    op.drop_table("mst_subvention_scheme")
