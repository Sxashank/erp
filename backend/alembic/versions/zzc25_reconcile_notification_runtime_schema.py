"""Reconcile notification runtime schema with the current ORM contract.

Revision ID: zzc25_reconcile_notification_runtime_schema
Revises: zzc24_add_payroll_gl_source_type
Create Date: 2026-05-18
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "zzc25_reconcile_notification_runtime_schema"
down_revision: Union[str, None] = "zzc24_add_payroll_gl_source_type"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(name: str) -> bool:
    return inspect(op.get_bind()).has_table(name)


def upgrade() -> None:
    if not _has_table("mst_notification_template"):
        op.create_table(
            "mst_notification_template",
            sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("code", sa.String(length=100), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("template_type", sa.String(length=50), nullable=False, server_default="transactional"),
            sa.Column("category", sa.String(length=50), nullable=False, server_default="system"),
            sa.Column(
                "channels",
                postgresql.ARRAY(sa.String(length=50)),
                nullable=False,
                server_default=sa.text("ARRAY['email','in_app']::varchar[]"),
            ),
            sa.Column("email_subject", sa.String(length=500), nullable=True),
            sa.Column("email_body_html", sa.Text(), nullable=True),
            sa.Column("email_body_text", sa.Text(), nullable=True),
            sa.Column("sms_body", sa.String(length=1000), nullable=True),
            sa.Column("push_title", sa.String(length=100), nullable=True),
            sa.Column("push_body", sa.String(length=500), nullable=True),
            sa.Column("push_image_url", sa.String(length=500), nullable=True),
            sa.Column("in_app_title", sa.String(length=255), nullable=True),
            sa.Column("in_app_message", sa.Text(), nullable=True),
            sa.Column("whatsapp_template_id", sa.String(length=255), nullable=True),
            sa.Column("whatsapp_template_params", postgresql.ARRAY(sa.String(length=100)), nullable=True),
            sa.Column("variables", postgresql.ARRAY(sa.String(length=100)), nullable=True),
            sa.Column("default_values", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column("trigger_event", sa.String(length=100), nullable=True),
            sa.Column("usage_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text("gen_random_uuid()")),
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
            sa.ForeignKeyConstraint(["organization_id"], ["mst_organization.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["updated_by"], ["mst_user.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            "ix_mst_notification_template_org_code",
            "mst_notification_template",
            ["organization_id", "code"],
            unique=True,
        )

    if not _has_table("mst_notification_template_variable"):
        op.create_table(
            "mst_notification_template_variable",
            sa.Column("template_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("name", sa.String(length=100), nullable=False),
            sa.Column("display_name", sa.String(length=255), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("data_type", sa.String(length=50), nullable=False, server_default="string"),
            sa.Column("format_pattern", sa.String(length=100), nullable=True),
            sa.Column("default_value", sa.String(length=500), nullable=True),
            sa.Column("is_required", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("validation_regex", sa.String(length=500), nullable=True),
            sa.Column("sample_value", sa.String(length=500), nullable=True),
            sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text("gen_random_uuid()")),
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
            sa.ForeignKeyConstraint(["template_id"], ["mst_notification_template.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["updated_by"], ["mst_user.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            "ix_mst_notification_template_variable_template_id",
            "mst_notification_template_variable",
            ["template_id"],
            unique=False,
        )

    if not _has_table("sys_notification"):
        op.create_table(
            "sys_notification",
            sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("recipient_email", sa.String(length=255), nullable=True),
            sa.Column("recipient_phone", sa.String(length=20), nullable=True),
            sa.Column("template_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("title", sa.String(length=255), nullable=False),
            sa.Column("message", sa.Text(), nullable=False),
            sa.Column("html_content", sa.Text(), nullable=True),
            sa.Column("category", sa.String(length=50), nullable=False, server_default="system"),
            sa.Column("priority", sa.String(length=50), nullable=False, server_default="medium"),
            sa.Column(
                "channels",
                postgresql.ARRAY(sa.String(length=50)),
                nullable=False,
                server_default=sa.text("ARRAY['in_app']::varchar[]"),
            ),
            sa.Column("status", sa.String(length=50), nullable=False, server_default="pending"),
            sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("entity_type", sa.String(length=100), nullable=True),
            sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("entity_reference", sa.String(length=100), nullable=True),
            sa.Column("action_url", sa.String(length=500), nullable=True),
            sa.Column("action_label", sa.String(length=100), nullable=True),
            sa.Column("extra_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("max_retries", sa.Integer(), nullable=False, server_default="3"),
            sa.Column("last_error", sa.Text(), nullable=True),
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text("gen_random_uuid()")),
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
            sa.ForeignKeyConstraint(["organization_id"], ["mst_organization.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["template_id"], ["mst_notification_template.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["updated_by"], ["mst_user.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["user_id"], ["mst_user.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_sys_notification_organization_id", "sys_notification", ["organization_id"], unique=False)
        op.create_index("ix_sys_notification_user_id", "sys_notification", ["user_id"], unique=False)
        op.create_index("ix_sys_notification_status", "sys_notification", ["status"], unique=False)
        op.create_index("ix_sys_notification_org_user", "sys_notification", ["organization_id", "user_id"], unique=False)
        op.create_index("ix_sys_notification_entity", "sys_notification", ["entity_type", "entity_id"], unique=False)

    if not _has_table("sys_notification_preference"):
        op.create_table(
            "sys_notification_preference",
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("category", sa.String(length=50), nullable=False),
            sa.Column("email_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("sms_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("push_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("in_app_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("whatsapp_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("digest_mode", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("digest_frequency", sa.String(length=50), nullable=True),
            sa.Column("quiet_hours_start", sa.String(length=10), nullable=True),
            sa.Column("quiet_hours_end", sa.String(length=10), nullable=True),
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text("gen_random_uuid()")),
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
            sa.ForeignKeyConstraint(["organization_id"], ["mst_organization.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["updated_by"], ["mst_user.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["user_id"], ["mst_user.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            "ix_sys_notification_preference_user_org_category",
            "sys_notification_preference",
            ["user_id", "organization_id", "category"],
            unique=True,
        )

    if not _has_table("sys_notification_log"):
        op.create_table(
            "sys_notification_log",
            sa.Column("notification_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("channel", sa.String(length=50), nullable=False),
            sa.Column("status", sa.String(length=50), nullable=False),
            sa.Column("attempt_number", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("attempted_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.Column("response_code", sa.String(length=50), nullable=True),
            sa.Column("response_message", sa.Text(), nullable=True),
            sa.Column("provider", sa.String(length=100), nullable=True),
            sa.Column("provider_message_id", sa.String(length=255), nullable=True),
            sa.Column("cost", sa.Float(), nullable=True),
            sa.Column("currency", sa.String(length=3), nullable=True),
            sa.Column("extra_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text("gen_random_uuid()")),
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
            sa.ForeignKeyConstraint(["notification_id"], ["sys_notification.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["updated_by"], ["mst_user.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_sys_notification_log_notification_id", "sys_notification_log", ["notification_id"], unique=False)


def downgrade() -> None:
    for index_name, table_name in [
        ("ix_sys_notification_log_notification_id", "sys_notification_log"),
        ("ix_sys_notification_preference_user_org_category", "sys_notification_preference"),
        ("ix_sys_notification_entity", "sys_notification"),
        ("ix_sys_notification_org_user", "sys_notification"),
        ("ix_sys_notification_status", "sys_notification"),
        ("ix_sys_notification_user_id", "sys_notification"),
        ("ix_sys_notification_organization_id", "sys_notification"),
        ("ix_mst_notification_template_variable_template_id", "mst_notification_template_variable"),
        ("ix_mst_notification_template_org_code", "mst_notification_template"),
    ]:
        if _has_table(table_name):
            op.drop_index(index_name, table_name=table_name)

    for table_name in [
        "sys_notification_log",
        "sys_notification_preference",
        "sys_notification",
        "mst_notification_template_variable",
        "mst_notification_template",
    ]:
        if _has_table(table_name):
            op.drop_table(table_name)
