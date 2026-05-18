"""Add DMS linkage for scheme-portal application documents.

New scheme-portal uploads must use the shared DMS as the source of truth
for file bytes, versioning, access logs, and history. The LOS
application-document table remains as a business-side checklist / review
index, but now links to the underlying DMS document row.
"""

import sqlalchemy as sa

from alembic import op

revision = "zza2_add_scheme_portal_dms_linkage"
down_revision = "zza1_add_portal_internal_auth"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "los_application_document",
        sa.Column("dms_document_id", sa.UUID(), nullable=True),
    )
    op.create_foreign_key(
        "fk_los_application_document_dms_document",
        "los_application_document",
        "dms_document",
        ["dms_document_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_los_application_document_dms_document_id",
        "los_application_document",
        ["dms_document_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_los_application_document_dms_document_id",
        table_name="los_application_document",
    )
    op.drop_constraint(
        "fk_los_application_document_dms_document",
        "los_application_document",
        type_="foreignkey",
    )
    op.drop_column("los_application_document", "dms_document_id")
