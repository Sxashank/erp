"""Add actor_role to portal_user for integrated scheme portal access.

Borrower self-registration remains the default path, so existing rows
are backfilled to ``scheme_borrower``. Lender / SMFCL / ministry users
can then be provisioned explicitly against the same portal surface.
"""

import sqlalchemy as sa

from alembic import op

revision = "zza0_add_portal_actor_role"
down_revision = "zz9_portal_align"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "portal_user",
        sa.Column(
            "actor_role",
            sa.String(length=50),
            nullable=False,
            server_default="scheme_borrower",
        ),
    )
    op.execute("UPDATE portal_user SET actor_role = 'scheme_borrower' " "WHERE actor_role IS NULL")
    op.alter_column("portal_user", "actor_role", server_default=None)


def downgrade() -> None:
    op.drop_column("portal_user", "actor_role")
