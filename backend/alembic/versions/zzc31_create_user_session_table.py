"""Create internal user session table.

Revision ID: zzc31_create_user_session_table
Revises: zzc30_wave6_permission_screaming_snake
Create Date: 2026-05-18
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "zzc31_create_user_session_table"
down_revision = "zzc30_wave6_permission_screaming_snake"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if not inspector.has_table("txn_user_session"):
        op.create_table(
            "txn_user_session",
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("refresh_token_hash", sa.String(length=255), nullable=False),
            sa.Column("token_family", sa.String(length=100), nullable=False),
            sa.Column("device_info", sa.Text(), nullable=True),
            sa.Column("user_agent", sa.String(length=500), nullable=True),
            sa.Column("ip_address", sa.String(length=50), nullable=True),
            sa.Column("location", sa.String(length=200), nullable=True),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("is_revoked", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("revoked_reason", sa.String(length=100), nullable=True),
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("deleted_by", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.ForeignKeyConstraint(["created_by"], ["mst_user.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["deleted_by"], ["mst_user.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["updated_by"], ["mst_user.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["user_id"], ["mst_user.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )

    op.execute("CREATE INDEX IF NOT EXISTS ix_txn_user_session_user_id ON txn_user_session (user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_txn_user_session_refresh_token_hash ON txn_user_session (refresh_token_hash)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_txn_user_session_token_family ON txn_user_session (token_family)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_txn_user_session_expires_at ON txn_user_session (expires_at)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_txn_user_session_expires_at")
    op.execute("DROP INDEX IF EXISTS ix_txn_user_session_token_family")
    op.execute("DROP INDEX IF EXISTS ix_txn_user_session_refresh_token_hash")
    op.execute("DROP INDEX IF EXISTS ix_txn_user_session_user_id")
    op.drop_table("txn_user_session")
