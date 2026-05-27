"""Make loan product rate and repayment terms master-driven.

Revision ID: zzc59_product_terms_master_text
Revises: zzc58_product_category_master_text
Create Date: 2026-05-26
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "zzc59_product_terms_master_text"
down_revision: str | None = "zzc58_product_category_master_text"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "los_loan_product",
        "interest_type",
        existing_nullable=False,
        type_=sa.String(length=80),
        existing_type=sa.Enum(name="interesttype"),
        postgresql_using="interest_type::text",
    )
    op.alter_column(
        "los_loan_product",
        "day_count_convention",
        existing_nullable=False,
        type_=sa.String(length=50),
        existing_type=sa.Enum(name="daycountconvention"),
        postgresql_using="day_count_convention::text",
    )
    op.alter_column(
        "los_loan_product",
        "default_repayment_frequency",
        existing_nullable=False,
        type_=sa.String(length=80),
        existing_type=sa.Enum(name="repaymentfrequency"),
        postgresql_using="default_repayment_frequency::text",
    )
    op.alter_column(
        "los_loan_product",
        "default_repayment_mode",
        existing_nullable=False,
        type_=sa.String(length=80),
        existing_type=sa.Enum(name="repaymentmode"),
        postgresql_using="default_repayment_mode::text",
    )
    op.alter_column(
        "los_loan_product",
        "rate_reset_frequency",
        existing_nullable=True,
        type_=sa.String(length=80),
        existing_type=sa.Enum(name="rateresetfrequency"),
        postgresql_using="rate_reset_frequency::text",
    )


def downgrade() -> None:
    op.alter_column(
        "los_loan_product",
        "rate_reset_frequency",
        existing_nullable=True,
        type_=sa.Enum(name="rateresetfrequency"),
        existing_type=sa.String(length=80),
        postgresql_using="rate_reset_frequency::rateresetfrequency",
    )
    op.alter_column(
        "los_loan_product",
        "default_repayment_mode",
        existing_nullable=False,
        type_=sa.Enum(name="repaymentmode"),
        existing_type=sa.String(length=80),
        postgresql_using="default_repayment_mode::repaymentmode",
    )
    op.alter_column(
        "los_loan_product",
        "default_repayment_frequency",
        existing_nullable=False,
        type_=sa.Enum(name="repaymentfrequency"),
        existing_type=sa.String(length=80),
        postgresql_using="default_repayment_frequency::repaymentfrequency",
    )
    op.alter_column(
        "los_loan_product",
        "day_count_convention",
        existing_nullable=False,
        type_=sa.Enum(name="daycountconvention"),
        existing_type=sa.String(length=50),
        postgresql_using="day_count_convention::daycountconvention",
    )
    op.alter_column(
        "los_loan_product",
        "interest_type",
        existing_nullable=False,
        type_=sa.Enum(name="interesttype"),
        existing_type=sa.String(length=80),
        postgresql_using="interest_type::interesttype",
    )
