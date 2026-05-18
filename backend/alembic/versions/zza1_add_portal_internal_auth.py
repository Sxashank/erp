"""Add internal-actor auth fields to portal_user.

Scheme borrowers continue to use the OTP flow. Internal actors such as
lenders, SMFCL reviewers/approvers, ministry viewers, and scheme admins
need invitation, password, password-reset, and MFA state on the shared
portal_user table.
"""

import sqlalchemy as sa

from alembic import op

revision = "zza1_add_portal_internal_auth"
down_revision = "zza0_add_portal_actor_role"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("portal_user", sa.Column("password_hash", sa.String(length=255), nullable=True))
    op.add_column(
        "portal_user",
        sa.Column("password_changed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column("portal_user", sa.Column("mfa_secret", sa.String(length=100), nullable=True))
    op.add_column("portal_user", sa.Column("invited_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "portal_user",
        sa.Column(
            "invited_by",
            sa.UUID(),
            sa.ForeignKey("mst_user.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "portal_user",
        sa.Column("invite_token_hash", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "portal_user",
        sa.Column("invite_token_expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "portal_user",
        sa.Column("activated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "portal_user",
        sa.Column("reset_token_hash", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "portal_user",
        sa.Column("reset_token_expires_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("portal_user", "reset_token_expires_at")
    op.drop_column("portal_user", "reset_token_hash")
    op.drop_column("portal_user", "activated_at")
    op.drop_column("portal_user", "invite_token_expires_at")
    op.drop_column("portal_user", "invite_token_hash")
    op.drop_column("portal_user", "invited_by")
    op.drop_column("portal_user", "invited_at")
    op.drop_column("portal_user", "mfa_secret")
    op.drop_column("portal_user", "password_changed_at")
    op.drop_column("portal_user", "password_hash")
