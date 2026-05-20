"""Align portal document tables with ORM contracts.

Revision ID: zzc51_align_portal_document_tables
Revises: zzc50_iif_portal_loan_tagging_tables
Create Date: 2026-05-20
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "zzc51_align_portal_document_tables"
down_revision: str | None = "zzc50_iif_portal_loan_tagging_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _has_column(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    return bool(
        bind.execute(
            sa.text(
                """
                SELECT 1
                FROM information_schema.columns
                WHERE table_name = :table_name
                  AND column_name = :column_name
                """
            ),
            {"table_name": table_name, "column_name": column_name},
        ).scalar()
    )


def _add_column_if_missing(table_name: str, column: sa.Column) -> None:
    if not _has_column(table_name, column.name):
        op.add_column(table_name, column)


def upgrade() -> None:
    _add_column_if_missing(
        "portal_document",
        sa.Column("document_name", sa.String(length=255), nullable=True),
    )
    _add_column_if_missing(
        "portal_document",
        sa.Column("file_name", sa.String(length=255), nullable=True),
    )
    _add_column_if_missing(
        "portal_document",
        sa.Column("file_type", sa.String(length=50), nullable=True),
    )
    _add_column_if_missing(
        "portal_document",
        sa.Column("file_hash", sa.String(length=64), nullable=True),
    )
    _add_column_if_missing("portal_document", sa.Column("period_from", sa.Date(), nullable=True))
    _add_column_if_missing("portal_document", sa.Column("period_to", sa.Date(), nullable=True))
    _add_column_if_missing(
        "portal_document",
        sa.Column("requires_otp", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    _add_column_if_missing(
        "portal_document",
        sa.Column("is_watermarked", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    _add_column_if_missing(
        "portal_document",
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    _add_column_if_missing(
        "portal_document",
        sa.Column("view_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
    )
    _add_column_if_missing(
        "portal_document",
        sa.Column("last_viewed_at", sa.DateTime(timezone=True), nullable=True),
    )
    _add_column_if_missing(
        "portal_document",
        sa.Column(
            "is_auto_generated",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    _add_column_if_missing(
        "portal_document",
        sa.Column("generation_params", sa.Text(), nullable=True),
    )
    _add_column_if_missing(
        "portal_document",
        sa.Column("source_document_id", postgresql.UUID(as_uuid=True), nullable=True),
    )

    op.execute(
        """
        UPDATE portal_document
        SET
            document_name = COALESCE(document_name, title, 'Document'),
            file_name = COALESCE(file_name, title, 'document.pdf'),
            file_type = COALESCE(file_type, mime_type, 'application/pdf'),
            file_size = COALESCE(file_size, 0),
            file_path = COALESCE(file_path, '/portal/documents/' || id::text),
            is_downloadable = COALESCE(is_downloadable, true),
            download_count = COALESCE(download_count, 0),
            is_active = COALESCE(is_active, true),
            version = COALESCE(version, 1)
        """
    )
    op.alter_column("portal_document", "document_name", nullable=False)
    op.alter_column("portal_document", "file_name", nullable=False)
    op.alter_column("portal_document", "file_type", nullable=False)
    op.alter_column("portal_document", "file_size", nullable=False)
    op.alter_column("portal_document", "file_path", nullable=False)

    _add_column_if_missing(
        "portal_document_request",
        sa.Column("request_number", sa.String(length=50), nullable=True),
    )
    _add_column_if_missing(
        "portal_document_request",
        sa.Column("period_from", sa.Date(), nullable=True),
    )
    _add_column_if_missing(
        "portal_document_request",
        sa.Column("period_to", sa.Date(), nullable=True),
    )
    _add_column_if_missing(
        "portal_document_request",
        sa.Column("financial_year", sa.String(length=10), nullable=True),
    )
    _add_column_if_missing(
        "portal_document_request",
        sa.Column("additional_params", sa.Text(), nullable=True),
    )
    _add_column_if_missing(
        "portal_document_request",
        sa.Column("delivery_mode", sa.String(length=20), nullable=False, server_default="DOWNLOAD"),
    )
    _add_column_if_missing(
        "portal_document_request",
        sa.Column("delivery_address", sa.Text(), nullable=True),
    )
    _add_column_if_missing(
        "portal_document_request",
        sa.Column("delivery_email", sa.String(length=255), nullable=True),
    )
    _add_column_if_missing(
        "portal_document_request",
        sa.Column("status_message", sa.String(length=500), nullable=True),
    )
    _add_column_if_missing(
        "portal_document_request",
        sa.Column("generated_document_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    _add_column_if_missing(
        "portal_document_request",
        sa.Column("fulfilled_at", sa.DateTime(timezone=True), nullable=True),
    )
    _add_column_if_missing(
        "portal_document_request",
        sa.Column("courier_tracking", sa.String(length=100), nullable=True),
    )
    _add_column_if_missing(
        "portal_document_request",
        sa.Column(
            "charges_applicable",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    _add_column_if_missing(
        "portal_document_request",
        sa.Column("charges_amount", sa.Float(), nullable=True),
    )
    _add_column_if_missing(
        "portal_document_request",
        sa.Column("payment_status", sa.String(length=50), nullable=True),
    )
    _add_column_if_missing(
        "portal_document_request",
        sa.Column("payment_reference", sa.String(length=100), nullable=True),
    )

    op.execute(
        """
        UPDATE portal_document_request
        SET
            request_number = COALESCE(request_number, 'PDR-' || id::text),
            generated_document_id = COALESCE(generated_document_id, document_id),
            fulfilled_at = COALESCE(fulfilled_at, processed_at),
            delivery_mode = COALESCE(delivery_mode, 'DOWNLOAD'),
            charges_applicable = COALESCE(charges_applicable, false),
            is_active = COALESCE(is_active, true),
            version = COALESCE(version, 1)
        """
    )
    op.alter_column("portal_document_request", "request_number", nullable=False)


def downgrade() -> None:
    for column_name in (
        "payment_reference",
        "payment_status",
        "charges_amount",
        "charges_applicable",
        "courier_tracking",
        "fulfilled_at",
        "generated_document_id",
        "status_message",
        "delivery_email",
        "delivery_address",
        "delivery_mode",
        "additional_params",
        "financial_year",
        "period_to",
        "period_from",
        "request_number",
    ):
        if _has_column("portal_document_request", column_name):
            op.drop_column("portal_document_request", column_name)

    for column_name in (
        "source_document_id",
        "generation_params",
        "is_auto_generated",
        "last_viewed_at",
        "view_count",
        "expires_at",
        "is_watermarked",
        "requires_otp",
        "period_to",
        "period_from",
        "file_hash",
        "file_type",
        "file_name",
        "document_name",
    ):
        if _has_column("portal_document", column_name):
            op.drop_column("portal_document", column_name)
