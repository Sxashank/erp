"""Add organization scope to legal cases.

Revision ID: zzc7_add_legal_case_organization_id
Revises: zzc6_add_compliance_is_active_columns
Create Date: 2026-05-14
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "zzc7_add_legal_case_organization_id"
down_revision = "zzc6_add_compliance_is_active_columns"
branch_labels = None
depends_on = None


def _has_column(table: str, column: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if table not in insp.get_table_names():
        return False
    return column in {col["name"] for col in insp.get_columns(table)}


def _has_index(table: str, index: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if table not in insp.get_table_names():
        return False
    return index in {idx["name"] for idx in insp.get_indexes(table)}


def upgrade() -> None:
    if not _has_column("col_legal_case", "organization_id"):
        op.add_column(
            "col_legal_case",
            sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=True),
        )

    op.execute("""
        UPDATE col_legal_case lc
        SET organization_id = la.organization_id
        FROM lms_loan_account la
        WHERE lc.loan_account_id = la.id
          AND lc.organization_id IS NULL
        """)

    op.alter_column("col_legal_case", "organization_id", nullable=False)

    if not _has_index("col_legal_case", "ix_col_legal_case_org"):
        op.create_index(
            "ix_col_legal_case_org",
            "col_legal_case",
            ["organization_id"],
        )

    op.create_foreign_key(
        "fk_col_legal_case_org",
        "col_legal_case",
        "mst_organization",
        ["organization_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint("fk_col_legal_case_org", "col_legal_case", type_="foreignkey")
    if _has_index("col_legal_case", "ix_col_legal_case_org"):
        op.drop_index("ix_col_legal_case_org", table_name="col_legal_case")
    if _has_column("col_legal_case", "organization_id"):
        op.drop_column("col_legal_case", "organization_id")
