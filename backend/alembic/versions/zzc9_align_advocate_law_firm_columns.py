"""Align advocate and law firm tables with ORM models.

Revision ID: zzc9_align_advocate_law_firm_columns
Revises: zzc8_add_period_tracking_deadline_date
Create Date: 2026-05-14
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "zzc9_align_advocate_law_firm_columns"
down_revision = "zzc8_add_period_tracking_deadline_date"
branch_labels = None
depends_on = None


def _has_column(table: str, column: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if table not in insp.get_table_names():
        return False
    return column in {col["name"] for col in insp.get_columns(table)}


def _add_column_if_missing(table: str, column: sa.Column) -> None:
    if not _has_column(table, column.name):
        op.add_column(table, column)


def upgrade() -> None:
    _add_column_if_missing("mst_law_firm", sa.Column("district", sa.String(100)))
    _add_column_if_missing("mst_law_firm", sa.Column("bank_name", sa.String(100)))
    _add_column_if_missing("mst_law_firm", sa.Column("bank_branch", sa.String(100)))
    _add_column_if_missing(
        "mst_law_firm",
        sa.Column("is_empaneled", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    _add_column_if_missing("mst_law_firm", sa.Column("empanelment_expiry", sa.Date()))
    _add_column_if_missing("mst_law_firm", sa.Column("empanelment_category", sa.String(50)))
    _add_column_if_missing("mst_law_firm", sa.Column("default_fee_structure", sa.String(50)))
    _add_column_if_missing(
        "mst_law_firm",
        sa.Column("total_cases_handled", sa.Integer(), nullable=False, server_default="0"),
    )
    _add_column_if_missing(
        "mst_law_firm",
        sa.Column("cases_won", sa.Integer(), nullable=False, server_default="0"),
    )
    _add_column_if_missing(
        "mst_law_firm",
        sa.Column(
            "total_recovery_amount",
            sa.Numeric(18, 2),
            nullable=False,
            server_default="0",
        ),
    )
    _add_column_if_missing("mst_law_firm", sa.Column("specializations", postgresql.JSONB()))
    _add_column_if_missing("mst_law_firm", sa.Column("remarks", sa.Text()))

    if _has_column("mst_law_firm", "contract_expiry_date"):
        op.execute("""
            UPDATE mst_law_firm
            SET empanelment_expiry = contract_expiry_date
            WHERE empanelment_expiry IS NULL
            """)
    if _has_column("mst_law_firm", "fee_structure_type"):
        op.execute("""
            UPDATE mst_law_firm
            SET default_fee_structure = fee_structure_type
            WHERE default_fee_structure IS NULL
            """)

    _add_column_if_missing("mst_advocate", sa.Column("salutation", sa.String(10)))
    _add_column_if_missing("mst_advocate", sa.Column("first_name", sa.String(100)))
    _add_column_if_missing("mst_advocate", sa.Column("middle_name", sa.String(100)))
    _add_column_if_missing("mst_advocate", sa.Column("last_name", sa.String(100)))
    _add_column_if_missing("mst_advocate", sa.Column("full_name", sa.String(300)))
    _add_column_if_missing("mst_advocate", sa.Column("enrollment_date", sa.Date()))
    _add_column_if_missing("mst_advocate", sa.Column("bank_name", sa.String(100)))
    _add_column_if_missing("mst_advocate", sa.Column("default_fee_structure", sa.String(50)))
    _add_column_if_missing("mst_advocate", sa.Column("fee_per_appearance", sa.Numeric(12, 2)))
    _add_column_if_missing("mst_advocate", sa.Column("hourly_rate", sa.Numeric(12, 2)))
    _add_column_if_missing("mst_advocate", sa.Column("success_fee_percentage", sa.Numeric(5, 2)))
    _add_column_if_missing(
        "mst_advocate",
        sa.Column("is_empaneled", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    _add_column_if_missing("mst_advocate", sa.Column("empanelment_date", sa.Date()))
    _add_column_if_missing("mst_advocate", sa.Column("years_of_experience", sa.Integer()))
    _add_column_if_missing("mst_advocate", sa.Column("courts_practiced", postgresql.JSONB()))
    _add_column_if_missing("mst_advocate", sa.Column("remarks", sa.Text()))

    if _has_column("mst_advocate", "name"):
        op.execute("""
            UPDATE mst_advocate
            SET full_name = COALESCE(full_name, name),
                first_name = COALESCE(first_name, split_part(name, ' ', 1)),
                last_name = COALESCE(NULLIF(last_name, ''), split_part(name, ' ', array_length(string_to_array(name, ' '), 1)))
            WHERE name IS NOT NULL
            """)
    if _has_column("mst_advocate", "fee_structure_type"):
        op.execute("""
            UPDATE mst_advocate
            SET default_fee_structure = fee_structure_type
            WHERE default_fee_structure IS NULL
            """)
    if _has_column("mst_advocate", "appearance_fee"):
        op.execute("""
            UPDATE mst_advocate
            SET fee_per_appearance = appearance_fee
            WHERE fee_per_appearance IS NULL
            """)
    if _has_column("mst_advocate", "success_fee_percent"):
        op.execute("""
            UPDATE mst_advocate
            SET success_fee_percentage = success_fee_percent
            WHERE success_fee_percentage IS NULL
            """)


def downgrade() -> None:
    for table, columns in {
        "mst_law_firm": [
            "district",
            "bank_name",
            "bank_branch",
            "is_empaneled",
            "empanelment_expiry",
            "empanelment_category",
            "default_fee_structure",
            "total_cases_handled",
            "cases_won",
            "total_recovery_amount",
            "specializations",
            "remarks",
        ],
        "mst_advocate": [
            "salutation",
            "first_name",
            "middle_name",
            "last_name",
            "full_name",
            "enrollment_date",
            "bank_name",
            "default_fee_structure",
            "fee_per_appearance",
            "hourly_rate",
            "success_fee_percentage",
            "is_empaneled",
            "empanelment_date",
            "years_of_experience",
            "courts_practiced",
            "remarks",
        ],
    }.items():
        for column in columns:
            if _has_column(table, column):
                op.drop_column(table, column)
