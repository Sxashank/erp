"""Loan lifecycle spine — lifecycle event log + application query bounce-back.

Revision ID: zzc53_loan_lifecycle_spine
Revises: zzc52_add_sys_webhook_event
Create Date: 2026-05-21

Adds two tables that form the spine of the strengthened loan lifecycle:

1. ``txn_loan_lifecycle_event`` — single append-only table that records
   every action on a loan (application → sanction → disbursement →
   servicing → closure) from any actor (lender, borrower, system,
   external vendor webhook). Powers the unified timeline UI + reports.

2. ``los_application_query`` — formal lender↔borrower bounce-back rows.
   Replaces the informal "remarks-field ping-pong" with explicit
   raised / responded / resolved state.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "zzc53_loan_lifecycle_spine"
down_revision: str | None = "zzc52_add_sys_webhook_event"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # txn_loan_lifecycle_event
    # ------------------------------------------------------------------
    op.create_table(
        "txn_loan_lifecycle_event",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("mst_organization.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("event_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "actor_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("mst_user.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("actor_role", sa.String(100), nullable=True),
        sa.Column(
            "actor_kind",
            sa.Enum(
                "LENDER",
                "BORROWER",
                "SYSTEM",
                "EXTERNAL",
                name="lifecycle_actor_kind",
            ),
            nullable=False,
        ),
        sa.Column(
            "subject_type",
            sa.Enum(
                "APPLICATION",
                "SANCTION",
                "LOAN_ACCOUNT",
                "DISBURSEMENT",
                "RECEIPT",
                "RESTRUCTURE",
                "OTS",
                "LEGAL_CASE",
                "NACH_MANDATE",
                "CERTIFICATE",
                "TAKEOVER",
                "TRANSFER_OUT",
                "WRITE_OFF",
                "INTEREST_REVIVAL",
                "RATE_RESET",
                name="lifecycle_subject_type",
            ),
            nullable=False,
        ),
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("business_number", sa.String(100), nullable=True),
        sa.Column("event_type", sa.String(80), nullable=False),
        sa.Column("state_from", sa.String(60), nullable=True),
        sa.Column("state_to", sa.String(60), nullable=True),
        sa.Column("reason_code", sa.String(80), nullable=True),
        sa.Column("reason_text", sa.Text, nullable=True),
        sa.Column(
            "payload",
            postgresql.JSONB,
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "attachments",
            postgresql.JSONB,
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "regulatory_tags",
            postgresql.ARRAY(sa.String(60)),
            nullable=False,
            server_default=sa.text("ARRAY[]::varchar[]"),
        ),
        sa.Column(
            "borrower_visible",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("correlation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("idempotency_key", sa.String(80), nullable=True),
        # BaseModel audit + soft-delete columns
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
    )
    op.create_index(
        "ix_txn_loan_lifecycle_event_subject_at",
        "txn_loan_lifecycle_event",
        ["subject_type", "subject_id", "event_at"],
    )
    op.create_index(
        "ix_txn_loan_lifecycle_event_org_at",
        "txn_loan_lifecycle_event",
        ["organization_id", "event_at"],
    )
    op.create_index(
        "ix_txn_loan_lifecycle_event_actor",
        "txn_loan_lifecycle_event",
        ["actor_user_id"],
    )
    op.create_index(
        "ix_txn_loan_lifecycle_event_type",
        "txn_loan_lifecycle_event",
        ["event_type"],
    )
    op.create_index(
        "ix_txn_loan_lifecycle_event_correlation",
        "txn_loan_lifecycle_event",
        ["correlation_id"],
    )

    # ------------------------------------------------------------------
    # los_application_query
    # ------------------------------------------------------------------
    op.create_table(
        "los_application_query",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("mst_organization.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "application_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("los_loan_application.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("query_number", sa.Integer, nullable=False),
        sa.Column(
            "raised_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("mst_user.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("raised_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "raised_reason_code",
            sa.Enum(
                "MISSING_DOCUMENT",
                "DOCUMENT_CLARIFICATION",
                "FINANCIAL_QUERY",
                "KYC_QUERY",
                "CREDIT_QUERY",
                "LEGAL_QUERY",
                "SECURITY_QUERY",
                "OTHER",
                name="application_query_reason",
            ),
            nullable=False,
            server_default="OTHER",
        ),
        sa.Column("query_text", sa.Text, nullable=False),
        sa.Column(
            "required_attachments",
            postgresql.ARRAY(sa.String(80)),
            nullable=False,
            server_default=sa.text("ARRAY[]::varchar[]"),
        ),
        sa.Column("sla_due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "RAISED",
                "RESPONDED",
                "RE_REVIEW",
                "RESOLVED",
                "LAPSED",
                name="application_query_status",
            ),
            nullable=False,
            server_default="RAISED",
        ),
        sa.Column(
            "responded_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("portal_user.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("response_text", sa.Text, nullable=True),
        sa.Column(
            "response_attachments",
            postgresql.JSONB,
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "resolved_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("mst_user.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolution_remark", sa.Text, nullable=True),
        # BaseModel columns
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
    )
    op.create_index(
        "ix_los_application_query_app_status",
        "los_application_query",
        ["application_id", "status"],
    )
    op.create_index(
        "ix_los_application_query_sla_due",
        "los_application_query",
        ["sla_due_at"],
    )
    op.create_index(
        "ix_los_application_query_org",
        "los_application_query",
        ["organization_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_los_application_query_org", "los_application_query")
    op.drop_index("ix_los_application_query_sla_due", "los_application_query")
    op.drop_index("ix_los_application_query_app_status", "los_application_query")
    op.drop_table("los_application_query")
    sa.Enum(name="application_query_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="application_query_reason").drop(op.get_bind(), checkfirst=True)

    op.drop_index("ix_txn_loan_lifecycle_event_correlation", "txn_loan_lifecycle_event")
    op.drop_index("ix_txn_loan_lifecycle_event_type", "txn_loan_lifecycle_event")
    op.drop_index("ix_txn_loan_lifecycle_event_actor", "txn_loan_lifecycle_event")
    op.drop_index("ix_txn_loan_lifecycle_event_org_at", "txn_loan_lifecycle_event")
    op.drop_index("ix_txn_loan_lifecycle_event_subject_at", "txn_loan_lifecycle_event")
    op.drop_table("txn_loan_lifecycle_event")
    sa.Enum(name="lifecycle_subject_type").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="lifecycle_actor_kind").drop(op.get_bind(), checkfirst=True)
