"""Make loan product category master-driven.

Revision ID: zzc58_product_category_master_text
Revises: zzc57_lending_ssot_master_consolidation
Create Date: 2026-05-26
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "zzc58_product_category_master_text"
down_revision: str | None = "zzc57_lending_ssot_master_consolidation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "los_loan_product",
        "category",
        existing_nullable=False,
        type_=sa.String(length=80),
        existing_type=sa.Enum(name="productcategory"),
        postgresql_using="category::text",
    )


def downgrade() -> None:
    op.alter_column(
        "los_loan_product",
        "category",
        existing_nullable=False,
        type_=sa.Enum(name="productcategory"),
        existing_type=sa.String(length=80),
        postgresql_using="category::productcategory",
    )
