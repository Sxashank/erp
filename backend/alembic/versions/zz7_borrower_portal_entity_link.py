"""Borrower-portal: PortalUser ↔ Entity bridge + registration columns.

Two-tier delta:

1. ``mst_portal_user_entity`` (new) — N:N link between ``portal_user``
   and ``los_entity``. Carries ``organization_id`` for RLS. A partial
   unique index keeps "at most one live link per (user, entity)" while
   soft-deletes remain for audit.

2. ``portal_user`` (extend) — registration approval lifecycle columns
   so an unauthenticated borrower can register, OTP-verify, await admin
   approval, and self-poll their status by reference.

   * ``portal_registration_status`` enum (PENDING_APPROVAL | ACTIVE | REJECTED)
   * ``registration_requested_*`` self-asserted identifiers
   * ``registration_authorized_signatory_name``
   * ``registered_at`` / ``approved_at`` / ``approved_by`` / ``rejection_reason``
   * ``registration_reference`` (unique, REG/{YYYY}/{NNNNNN})

Back-compat: existing rows are stamped ``ACTIVE`` via the column
default; legacy customer-portal users continue to log in unchanged.

Revision ID: zz7_borrower_portal_entity_link
Revises: zz6_checklist_approved
Create Date: 2026-05-12
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "zz7_borrower_portal_entity_link"
down_revision: str | None = "zz6_checklist_approved"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _base_audit_columns() -> list[sa.Column]:
    """AuditMixin + SoftDeleteMixin + VersionedMixin columns (matches BaseModel)."""
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


def upgrade() -> None:
    # =====================================================================
    # Enum type for the registration lifecycle
    # =====================================================================
    op.execute(
        "CREATE TYPE portal_registration_status AS ENUM "
        "('PENDING_APPROVAL', 'ACTIVE', 'REJECTED')"
    )

    # =====================================================================
    # mst_portal_user_entity — bridge table
    # =====================================================================
    op.create_table(
        "mst_portal_user_entity",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("portal_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "granted_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("granted_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "is_link_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        *_base_audit_columns(),
        sa.ForeignKeyConstraint(
            ["portal_user_id"],
            ["portal_user.id"],
            ondelete="CASCADE",
            name="fk_mst_portal_user_entity_portal_user",
        ),
        sa.ForeignKeyConstraint(
            ["entity_id"],
            ["los_entity.id"],
            ondelete="CASCADE",
            name="fk_mst_portal_user_entity_entity",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["mst_organization.id"],
            ondelete="CASCADE",
            name="fk_mst_portal_user_entity_organization",
        ),
        sa.ForeignKeyConstraint(
            ["granted_by"],
            ["mst_user.id"],
            ondelete="SET NULL",
            name="fk_mst_portal_user_entity_granted_by",
        ),
        *_base_audit_fks("mst_portal_user_entity"),
    )
    op.create_index(
        "ix_mst_portal_user_entity_portal_user",
        "mst_portal_user_entity",
        ["portal_user_id"],
    )
    op.create_index(
        "ix_mst_portal_user_entity_entity",
        "mst_portal_user_entity",
        ["entity_id"],
    )
    op.create_index(
        "ix_mst_portal_user_entity_org",
        "mst_portal_user_entity",
        ["organization_id"],
    )
    # Partial unique index: at most one live link per (user, entity).
    op.create_index(
        "uq_portal_user_entity_live",
        "mst_portal_user_entity",
        ["portal_user_id", "entity_id"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    # =====================================================================
    # portal_user — registration columns
    # =====================================================================
    op.add_column(
        "portal_user",
        sa.Column(
            "registration_status",
            postgresql.ENUM(
                "PENDING_APPROVAL",
                "ACTIVE",
                "REJECTED",
                name="portal_registration_status",
                create_type=False,
            ),
            nullable=False,
            server_default=sa.text("'ACTIVE'::portal_registration_status"),
        ),
    )
    op.add_column(
        "portal_user",
        sa.Column("registration_requested_pan", sa.String(length=20), nullable=True),
    )
    op.add_column(
        "portal_user",
        sa.Column("registration_requested_cin", sa.String(length=30), nullable=True),
    )
    op.add_column(
        "portal_user",
        sa.Column(
            "registration_requested_gstin",
            sa.String(length=20),
            nullable=True,
        ),
    )
    op.add_column(
        "portal_user",
        sa.Column(
            "registration_requested_llpin",
            sa.String(length=20),
            nullable=True,
        ),
    )
    op.add_column(
        "portal_user",
        sa.Column(
            "registration_authorized_signatory_name",
            sa.String(length=200),
            nullable=True,
        ),
    )
    op.add_column(
        "portal_user",
        sa.Column("registered_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "portal_user",
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "portal_user",
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_portal_user_approved_by",
        "portal_user",
        "mst_user",
        ["approved_by"],
        ["id"],
        ondelete="SET NULL",
    )
    op.add_column(
        "portal_user",
        sa.Column("rejection_reason", sa.String(length=500), nullable=True),
    )
    op.add_column(
        "portal_user",
        sa.Column("registration_reference", sa.String(length=50), nullable=True),
    )
    op.create_unique_constraint(
        "uq_portal_user_registration_reference",
        "portal_user",
        ["registration_reference"],
    )


def downgrade() -> None:
    # ----- portal_user reverts -----
    op.drop_constraint(
        "uq_portal_user_registration_reference",
        "portal_user",
        type_="unique",
    )
    op.drop_column("portal_user", "registration_reference")
    op.drop_column("portal_user", "rejection_reason")
    op.drop_constraint("fk_portal_user_approved_by", "portal_user", type_="foreignkey")
    op.drop_column("portal_user", "approved_by")
    op.drop_column("portal_user", "approved_at")
    op.drop_column("portal_user", "registered_at")
    op.drop_column("portal_user", "registration_authorized_signatory_name")
    op.drop_column("portal_user", "registration_requested_llpin")
    op.drop_column("portal_user", "registration_requested_gstin")
    op.drop_column("portal_user", "registration_requested_cin")
    op.drop_column("portal_user", "registration_requested_pan")
    op.drop_column("portal_user", "registration_status")

    # ----- mst_portal_user_entity drop -----
    op.drop_index("uq_portal_user_entity_live", table_name="mst_portal_user_entity")
    op.drop_index("ix_mst_portal_user_entity_org", table_name="mst_portal_user_entity")
    op.drop_index(
        "ix_mst_portal_user_entity_entity",
        table_name="mst_portal_user_entity",
    )
    op.drop_index(
        "ix_mst_portal_user_entity_portal_user",
        table_name="mst_portal_user_entity",
    )
    op.drop_table("mst_portal_user_entity")

    # Finally the enum type.
    op.execute("DROP TYPE IF EXISTS portal_registration_status")
