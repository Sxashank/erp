"""Align legal notice table with ORM model.

Revision ID: zzc11_align_legal_notice_columns
Revises: zzc10_add_advocate_website
Create Date: 2026-05-14
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "zzc11_align_legal_notice_columns"
down_revision = "zzc10_add_advocate_website"
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
    table = "txn_legal_notice"
    for column in [
        sa.Column("legal_case_id", postgresql.UUID(as_uuid=True)),
        sa.Column("borrower_name", sa.String(200)),
        sa.Column("borrower_address", sa.Text()),
        sa.Column("co_borrower_names", sa.Text()),
        sa.Column("guarantor_names", sa.Text()),
        sa.Column("loan_account_number", sa.String(50)),
        sa.Column("principal_outstanding", sa.Numeric(18, 2)),
        sa.Column("interest_outstanding", sa.Numeric(18, 2)),
        sa.Column("penal_outstanding", sa.Numeric(18, 2), server_default="0"),
        sa.Column("other_charges", sa.Numeric(18, 2), server_default="0"),
        sa.Column("total_amount_demanded", sa.Numeric(18, 2)),
        sa.Column("future_interest_rate", sa.Numeric(8, 4)),
        sa.Column("security_description", sa.Text()),
        sa.Column("security_address", sa.Text()),
        sa.Column("security_value", sa.Numeric(18, 2)),
        sa.Column("act_reference", sa.String(200)),
        sa.Column("section_reference", sa.String(100)),
        sa.Column("notice_content", sa.Text()),
        sa.Column("language", sa.String(20), server_default="ENGLISH"),
        sa.Column("approved_by_id", postgresql.UUID(as_uuid=True)),
        sa.Column("approved_by_name", sa.String(200)),
        sa.Column("approval_date", sa.DateTime()),
        sa.Column("document_path", sa.String(500)),
        sa.Column("document_hash", sa.String(64)),
        sa.Column("remarks", sa.Text()),
    ]:
        _add_column_if_missing(table, column)

    if _has_column(table, "case_id"):
        op.execute("""
            UPDATE txn_legal_notice
            SET legal_case_id = case_id
            WHERE legal_case_id IS NULL
            """)
    if _has_column(table, "notice_body"):
        op.execute("""
            UPDATE txn_legal_notice
            SET notice_content = notice_body
            WHERE notice_content IS NULL
            """)
    if _has_column(table, "amount_demanded"):
        op.execute("""
            UPDATE txn_legal_notice
            SET total_amount_demanded = amount_demanded
            WHERE total_amount_demanded IS NULL
            """)
    if _has_column(table, "approved_by"):
        op.execute("""
            UPDATE txn_legal_notice
            SET approved_by_id = approved_by
            WHERE approved_by_id IS NULL
            """)
    if _has_column(table, "approved_at"):
        op.execute("""
            UPDATE txn_legal_notice
            SET approval_date = approved_at
            WHERE approval_date IS NULL
            """)


def downgrade() -> None:
    for column in [
        "legal_case_id",
        "borrower_name",
        "borrower_address",
        "co_borrower_names",
        "guarantor_names",
        "loan_account_number",
        "principal_outstanding",
        "interest_outstanding",
        "penal_outstanding",
        "other_charges",
        "total_amount_demanded",
        "future_interest_rate",
        "security_description",
        "security_address",
        "security_value",
        "act_reference",
        "section_reference",
        "notice_content",
        "language",
        "approved_by_id",
        "approved_by_name",
        "approval_date",
        "document_path",
        "document_hash",
        "remarks",
    ]:
        if _has_column("txn_legal_notice", column):
            op.drop_column("txn_legal_notice", column)
