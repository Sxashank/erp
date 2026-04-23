"""Add idempotency_key table.

Revision ID: aa0_idempotency_key
Revises: z9_cost_center
Create Date: 2026-04-23

Supports CLAUDE.md §6.3: financial mutations require an `Idempotency-Key`
header; the server stores key + response for 24h and replays on collision.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "aa0_idempotency_key"
down_revision = "z32_bi_analytics"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "idempotency_key",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("key", sa.String(255), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("method", sa.String(10), nullable=False),
        sa.Column("path", sa.String(500), nullable=False),
        sa.Column(
            "request_hash",
            sa.String(64),
            nullable=False,
            comment="SHA-256 hex digest of normalized request body",
        ),
        sa.Column("response_status", sa.Integer, nullable=False),
        sa.Column("response_body", sa.Text, nullable=True),
        sa.Column("response_headers", postgresql.JSONB, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=False,
            comment="When this idempotency record becomes safe to delete",
        ),
    )
    op.create_index(
        "ix_idempotency_key_user_key",
        "idempotency_key",
        ["user_id", "key"],
        unique=True,
    )
    op.create_index(
        "ix_idempotency_key_expires_at",
        "idempotency_key",
        ["expires_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_idempotency_key_expires_at", table_name="idempotency_key")
    op.drop_index("ix_idempotency_key_user_key", table_name="idempotency_key")
    op.drop_table("idempotency_key")
