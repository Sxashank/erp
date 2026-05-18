"""Backfill missing portal_user columns to align DB with ORM.

Pre-existing schema drift surfaced when the borrower portal went live:
the ORM declares mobile_verified, email_verified, status_reason, etc.
on ``portal_user`` but the DB doesn't have them. This migration adds
the missing columns with safe defaults so every portal route (including
the existing send-otp / verify-otp flow) stops 500'ing.

No data is destroyed. Down-migration drops the same columns.
"""

import sqlalchemy as sa

from alembic import op

revision = "zz8_portal_user_orm_db_alignment"
down_revision = "zz7_borrower_portal_entity_link"
branch_labels = None
depends_on = None


# Columns the ORM declares but the live DB lacks. Each tuple is
# (column_name, column_type, server_default, nullable).
_MISSING_COLUMNS: list[tuple[str, sa.types.TypeEngine, str | None, bool]] = [
    ("mobile_verified", sa.Boolean(), "false", False),
    ("mobile_verified_at", sa.DateTime(timezone=True), None, True),
    ("email_verified", sa.Boolean(), "false", False),
    ("email_verified_at", sa.DateTime(timezone=True), None, True),
    ("status_reason", sa.String(length=500), None, True),
    ("notification_preferences", sa.Text(), None, True),
    ("last_login_ip", sa.String(length=45), None, True),
    ("last_login_device", sa.String(length=50), None, True),
    ("login_count", sa.Integer(), "0", False),
    ("is_2fa_enabled", sa.Boolean(), "false", False),
]


def upgrade() -> None:
    for name, type_, server_default, nullable in _MISSING_COLUMNS:
        kwargs: dict = {"nullable": nullable}
        if server_default is not None:
            kwargs["server_default"] = sa.text(server_default)
        op.add_column("portal_user", sa.Column(name, type_, **kwargs))


def downgrade() -> None:
    for name, *_ in reversed(_MISSING_COLUMNS):
        op.drop_column("portal_user", name)
