"""Backfill missing portal_session / portal_device / portal_otp /
portal_consent columns to align live DB with the ORM.

Sibling of zz8 (which covered portal_user). The portal models accumulated
extensive ORM-only columns over time — audit mixins, soft-delete, version,
plus several domain columns added without a corresponding migration.
Without these the OTP send + verify flow 500s, blocking borrower onboarding.

Nothing is destructive. Down-migration drops the same columns.
"""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

revision = "zz9_portal_align"
down_revision = "zz8_portal_user_orm_db_alignment"
branch_labels = None
depends_on = None


# (table, column_name, column_type, server_default, nullable)
_CHANGES: list[tuple[str, str, sa.types.TypeEngine, str | None, bool]] = [
    # portal_session
    ("portal_session", "login_at", sa.DateTime(timezone=True), "now()", False),
    ("portal_session", "logout_at", sa.DateTime(timezone=True), None, True),
    ("portal_session", "logout_reason", sa.String(length=100), None, True),
    ("portal_session", "created_by", UUID(as_uuid=True), None, True),
    ("portal_session", "updated_at", sa.DateTime(timezone=True), None, True),
    ("portal_session", "updated_by", UUID(as_uuid=True), None, True),
    ("portal_session", "deleted_at", sa.DateTime(timezone=True), None, True),
    ("portal_session", "deleted_by", UUID(as_uuid=True), None, True),
    ("portal_session", "version", sa.Integer(), "1", False),
    # portal_device
    ("portal_device", "device_model", sa.String(length=100), None, True),
    ("portal_device", "fcm_token", sa.Text(), None, True),
    ("portal_device", "apns_token", sa.Text(), None, True),
    ("portal_device", "first_seen_at", sa.DateTime(timezone=True), "now()", False),
    ("portal_device", "last_seen_at", sa.DateTime(timezone=True), "now()", False),
    ("portal_device", "login_count", sa.Integer(), "0", False),
    ("portal_device", "blocked_at", sa.DateTime(timezone=True), None, True),
    ("portal_device", "block_reason", sa.String(length=255), None, True),
    ("portal_device", "created_by", UUID(as_uuid=True), None, True),
    ("portal_device", "updated_at", sa.DateTime(timezone=True), None, True),
    ("portal_device", "updated_by", UUID(as_uuid=True), None, True),
    ("portal_device", "deleted_at", sa.DateTime(timezone=True), None, True),
    ("portal_device", "deleted_by", UUID(as_uuid=True), None, True),
    ("portal_device", "version", sa.Integer(), "1", False),
    # portal_otp
    (
        "portal_otp",
        "organization_id",
        UUID(as_uuid=True),
        None,
        True,
    ),  # nullable for legacy + pre-registration OTPs
    ("portal_otp", "email", sa.String(length=255), None, True),
    ("portal_otp", "otp_code", sa.String(length=10), "''", False),
    ("portal_otp", "reference_type", sa.String(length=50), None, True),
    ("portal_otp", "reference_id", UUID(as_uuid=True), None, True),
    ("portal_otp", "generated_at", sa.DateTime(timezone=True), "now()", False),
    ("portal_otp", "is_used", sa.Boolean(), "false", False),
    ("portal_otp", "sent_via", sa.String(length=20), "'SMS'", False),
    ("portal_otp", "delivery_status", sa.String(length=50), None, True),
    ("portal_otp", "delivery_vendor_ref", sa.String(length=100), None, True),
    ("portal_otp", "created_by", UUID(as_uuid=True), None, True),
    ("portal_otp", "updated_at", sa.DateTime(timezone=True), None, True),
    ("portal_otp", "updated_by", UUID(as_uuid=True), None, True),
    ("portal_otp", "deleted_at", sa.DateTime(timezone=True), None, True),
    ("portal_otp", "deleted_by", UUID(as_uuid=True), None, True),
    ("portal_otp", "is_active", sa.Boolean(), "true", False),
    ("portal_otp", "version", sa.Integer(), "1", False),
    # portal_consent
    ("portal_consent", "is_granted", sa.Boolean(), "false", False),
    ("portal_consent", "granted_at", sa.DateTime(timezone=True), None, True),
    ("portal_consent", "revoked_at", sa.DateTime(timezone=True), None, True),
    ("portal_consent", "revocation_reason", sa.String(length=500), None, True),
    ("portal_consent", "user_agent", sa.Text(), None, True),
    ("portal_consent", "capture_method", sa.String(length=50), "'WEB'", False),
    ("portal_consent", "created_by", UUID(as_uuid=True), None, True),
    ("portal_consent", "updated_at", sa.DateTime(timezone=True), None, True),
    ("portal_consent", "updated_by", UUID(as_uuid=True), None, True),
    ("portal_consent", "deleted_at", sa.DateTime(timezone=True), None, True),
    ("portal_consent", "deleted_by", UUID(as_uuid=True), None, True),
    ("portal_consent", "is_active", sa.Boolean(), "true", False),
    ("portal_consent", "version", sa.Integer(), "1", False),
]


def upgrade() -> None:
    for table, name, type_, server_default, nullable in _CHANGES:
        kwargs: dict = {"nullable": nullable}
        if server_default is not None:
            kwargs["server_default"] = sa.text(server_default)
        op.add_column(table, sa.Column(name, type_, **kwargs))


def downgrade() -> None:
    for table, name, *_ in reversed(_CHANGES):
        op.drop_column(table, name)
