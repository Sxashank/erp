"""Add sys_webhook_event + sys_esign_request + sys_esign_status_event.

Revision ID: zzc52_add_sys_webhook_event
Revises: zzc51_align_portal_document_tables
Create Date: 2026-05-20

Three tables for the Phase-1 "no silent swallow" pass:

1. ``sys_webhook_event`` — every HMAC-verified inbound webhook (bureau /
   payment gateway / eSign provider) lands here before domain dispatch.
   Replaces the "log + return 200" pattern that was silently discarding
   production data.

2. ``sys_esign_request`` — one row per document-sign initiation. Replaces
   the ``pass``-only stubs in ``ESignService._store_signing_request`` /
   ``_update_signing_status``. Required for RBI / IT-Act §10A audit.

3. ``sys_esign_status_event`` — history table for each status transition
   on an ESignRequest (INITIATED → IN_PROGRESS → COMPLETED / FAILED /
   EXPIRED / CANCELLED).
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "zzc52_add_sys_webhook_event"
down_revision: str | None = "zzc51_align_portal_document_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    op.create_table(
        "sys_webhook_event",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("mst_organization.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("vendor", sa.String(50), nullable=False),
        sa.Column("integration_type", sa.String(50), nullable=False),
        sa.Column("event_type", sa.String(100), nullable=True),
        sa.Column("external_reference", sa.String(200), nullable=True),
        sa.Column("body", postgresql.JSONB, nullable=False),
        sa.Column("body_raw", sa.Text, nullable=False),
        sa.Column("signature", sa.String(500), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="RECEIVED",
        ),
        sa.Column("attempts", sa.Integer, nullable=False, server_default="0"),
        sa.Column("last_error", sa.Text, nullable=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        # AuditMixin / SoftDeleteMixin / VersionedMixin columns
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
        "ix_sys_webhook_event_org_vendor",
        "sys_webhook_event",
        ["organization_id", "vendor"],
    )
    op.create_index(
        "ix_sys_webhook_event_status_received",
        "sys_webhook_event",
        ["status", "received_at"],
    )
    op.create_index(
        "ix_sys_webhook_event_external_ref",
        "sys_webhook_event",
        ["external_reference"],
    )

    # --- eSign request + status event ---
    op.create_table(
        "sys_esign_request",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("mst_organization.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("provider_name", sa.String(50), nullable=False),
        sa.Column("provider_request_id", sa.String(200), nullable=True),
        sa.Column("document_id", sa.String(200), nullable=False),
        sa.Column("document_name", sa.String(500), nullable=False),
        sa.Column("document_path", sa.String(1000), nullable=False),
        sa.Column("entity_type", sa.String(100), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("signers", postgresql.JSONB, nullable=False),
        sa.Column("callback_url", sa.String(1000), nullable=True),
        sa.Column("expiry_hours", sa.Integer, nullable=False, server_default="72"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "status",
            sa.String(30),
            nullable=False,
            server_default="INITIATED",
        ),
        sa.Column("initiated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("signed_document_url", sa.String(1000), nullable=True),
        sa.Column("signed_document_path", sa.String(1000), nullable=True),
        sa.Column("last_error", sa.Text, nullable=True),
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

    op.create_index("ix_sys_esign_request_org", "sys_esign_request", ["organization_id"])
    op.create_index(
        "ix_sys_esign_request_entity",
        "sys_esign_request",
        ["entity_type", "entity_id"],
    )
    op.create_index(
        "ix_sys_esign_request_provider_ref",
        "sys_esign_request",
        ["provider_request_id"],
    )
    op.create_index("ix_sys_esign_request_status", "sys_esign_request", ["status"])

    op.create_table(
        "sys_esign_status_event",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "request_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sys_esign_request.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column(
            "event_source",
            sa.String(30),
            nullable=False,
            server_default="SYSTEM",
        ),
        sa.Column("signer_id", sa.String(200), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "payload",
            postgresql.JSONB,
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("error_message", sa.Text, nullable=True),
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
        "ix_sys_esign_status_event_request",
        "sys_esign_status_event",
        ["request_id"],
    )

    # --- Communication audit log ---
    op.create_table(
        "sys_communication_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("mst_organization.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("channel", sa.String(20), nullable=False),
        sa.Column("provider_name", sa.String(50), nullable=True),
        sa.Column("template_id", sa.String(100), nullable=True),
        sa.Column("subject", sa.String(500), nullable=True),
        sa.Column("body_preview", sa.Text, nullable=True),
        sa.Column("entity_type", sa.String(100), nullable=True),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "triggered_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("mst_user.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "recipients",
            postgresql.JSONB,
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("recipient_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("success_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("failure_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "extra_metadata",
            postgresql.JSONB,
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
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
    op.create_index("ix_sys_communication_log_org", "sys_communication_log", ["organization_id"])
    op.create_index("ix_sys_communication_log_channel", "sys_communication_log", ["channel"])
    op.create_index(
        "ix_sys_communication_log_entity",
        "sys_communication_log",
        ["entity_type", "entity_id"],
    )
    op.create_index("ix_sys_communication_log_sent_at", "sys_communication_log", ["sent_at"])

    # --- Goods Receipt Note (procurement) ---
    # z30_procurement is the SSOT owner for txn_grn. Older local databases that
    # missed z30 can still create it here, but fresh databases must not redefine
    # the table or its PostgreSQL enum types.
    if not _table_exists("txn_grn"):
        op.create_table(
            "txn_grn",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column(
                "organization_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("mst_organization.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("grn_number", sa.String(50), nullable=False, unique=True),
            sa.Column("received_date", sa.Date, nullable=False),
            sa.Column(
                "purchase_order_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("txn_purchase_order.id", ondelete="RESTRICT"),
                nullable=False,
            ),
            sa.Column("purchase_order_number", sa.String(50), nullable=False),
            sa.Column(
                "vendor_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("mst_vendor.id", ondelete="RESTRICT"),
                nullable=False,
            ),
            sa.Column("vendor_name", sa.String(300), nullable=False),
            sa.Column("vendor_code", sa.String(50), nullable=True),
            sa.Column("total_items", sa.Integer, nullable=False, server_default="0"),
            sa.Column("received_items", sa.Integer, nullable=False, server_default="0"),
            sa.Column("total_value", sa.Numeric(18, 2), nullable=False, server_default="0"),
            sa.Column(
                "status",
                sa.Enum(
                    "PENDING_QC",
                    "PARTIAL",
                    "COMPLETE",
                    "REJECTED",
                    name="grn_status",
                    create_type=False,
                ),
                nullable=False,
                server_default="PENDING_QC",
            ),
            sa.Column(
                "quality_status",
                sa.Enum(
                    "PENDING",
                    "APPROVED",
                    "REJECTED",
                    name="grn_quality_status",
                ),
                nullable=False,
                server_default="PENDING",
            ),
            sa.Column("received_by", sa.String(200), nullable=True),
            sa.Column("invoice_number", sa.String(100), nullable=True),
            sa.Column("qc_remarks", sa.Text, nullable=True),
            sa.Column("rejection_reason", sa.Text, nullable=True),
            sa.Column(
                "is_invoice_matched",
                sa.Boolean,
                nullable=False,
                server_default=sa.text("false"),
            ),
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
        op.create_index("ix_txn_grn_org_status", "txn_grn", ["organization_id", "status"])
        op.create_index("ix_txn_grn_po", "txn_grn", ["purchase_order_id"])
        op.create_index("ix_txn_grn_received_date", "txn_grn", ["received_date"])


def downgrade() -> None:
    op.drop_index("ix_txn_grn_received_date", "txn_grn")
    op.drop_index("ix_txn_grn_po", "txn_grn")
    op.drop_index("ix_txn_grn_org_status", "txn_grn")
    op.drop_table("txn_grn")
    sa.Enum(name="grn_quality_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="grn_status").drop(op.get_bind(), checkfirst=True)

    op.drop_index("ix_sys_communication_log_sent_at", "sys_communication_log")
    op.drop_index("ix_sys_communication_log_entity", "sys_communication_log")
    op.drop_index("ix_sys_communication_log_channel", "sys_communication_log")
    op.drop_index("ix_sys_communication_log_org", "sys_communication_log")
    op.drop_table("sys_communication_log")

    op.drop_index("ix_sys_esign_status_event_request", "sys_esign_status_event")
    op.drop_table("sys_esign_status_event")
    op.drop_index("ix_sys_esign_request_status", "sys_esign_request")
    op.drop_index("ix_sys_esign_request_provider_ref", "sys_esign_request")
    op.drop_index("ix_sys_esign_request_entity", "sys_esign_request")
    op.drop_index("ix_sys_esign_request_org", "sys_esign_request")
    op.drop_table("sys_esign_request")
    op.drop_index("ix_sys_webhook_event_external_ref", "sys_webhook_event")
    op.drop_index("ix_sys_webhook_event_status_received", "sys_webhook_event")
    op.drop_index("ix_sys_webhook_event_org_vendor", "sys_webhook_event")
    op.drop_table("sys_webhook_event")
