"""Make lending application, sanction and account policy terms master-driven.

Revision ID: zzc60_lending_policy_terms_text
Revises: zzc59_product_terms_master_text
Create Date: 2026-05-26
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "zzc60_lending_policy_terms_text"
down_revision: str | None = "zzc59_product_terms_master_text"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _to_text(table: str, column: str, enum_name: str) -> None:
    op.alter_column(
        table,
        column,
        existing_nullable=False,
        type_=sa.String(length=80),
        existing_type=sa.Enum(name=enum_name),
        postgresql_using=f"{column}::text",
    )


def _nullable_to_text(table: str, column: str, enum_name: str) -> None:
    op.alter_column(
        table,
        column,
        existing_nullable=True,
        type_=sa.String(length=80),
        existing_type=sa.Enum(name=enum_name),
        postgresql_using=f"{column}::text",
    )


def _to_enum(table: str, column: str, enum_name: str) -> None:
    op.alter_column(
        table,
        column,
        existing_nullable=False,
        type_=sa.Enum(name=enum_name),
        existing_type=sa.String(length=80),
        postgresql_using=f"{column}::{enum_name}",
    )


def _nullable_to_enum(table: str, column: str, enum_name: str) -> None:
    op.alter_column(
        table,
        column,
        existing_nullable=True,
        type_=sa.Enum(name=enum_name),
        existing_type=sa.String(length=80),
        postgresql_using=f"{column}::{enum_name}",
    )


def upgrade() -> None:
    for column, enum_name in (
        ("preferred_interest_type", "interesttype"),
        ("preferred_repayment_frequency", "repaymentfrequency"),
        ("preferred_repayment_mode", "repaymentmode"),
    ):
        _to_text("los_loan_application", column, enum_name)

    for column, enum_name in (
        ("interest_type", "interesttype"),
        ("repayment_frequency", "repaymentfrequency"),
        ("repayment_mode", "repaymentmode"),
    ):
        _to_text("los_loan_sanction", column, enum_name)
        _to_text("lms_loan_account", column, enum_name)

    _nullable_to_text("los_loan_sanction", "rate_reset_frequency", "rateresetfrequency")
    _nullable_to_text("lms_loan_account", "rate_reset_frequency", "rateresetfrequency")

    for column, enum_name in (
        ("security_category", "securitycategory"),
        ("security_type", "securitytype"),
        ("charge_type", "chargetype"),
    ):
        _to_text("los_loan_security", column, enum_name)


def downgrade() -> None:
    for column, enum_name in (
        ("charge_type", "chargetype"),
        ("security_type", "securitytype"),
        ("security_category", "securitycategory"),
    ):
        _to_enum("los_loan_security", column, enum_name)

    _nullable_to_enum("lms_loan_account", "rate_reset_frequency", "rateresetfrequency")
    _nullable_to_enum("los_loan_sanction", "rate_reset_frequency", "rateresetfrequency")

    for column, enum_name in (
        ("repayment_mode", "repaymentmode"),
        ("repayment_frequency", "repaymentfrequency"),
        ("interest_type", "interesttype"),
    ):
        _to_enum("lms_loan_account", column, enum_name)
        _to_enum("los_loan_sanction", column, enum_name)

    for column, enum_name in (
        ("preferred_repayment_mode", "repaymentmode"),
        ("preferred_repayment_frequency", "repaymentfrequency"),
        ("preferred_interest_type", "interesttype"),
    ):
        _to_enum("los_loan_application", column, enum_name)
