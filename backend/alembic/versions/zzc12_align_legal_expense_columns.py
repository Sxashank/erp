"""Align legal expense tables with ORM models.

Revision ID: zzc12_align_legal_expense_columns
Revises: zzc11_align_legal_notice_columns
Create Date: 2026-05-14
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "zzc12_align_legal_expense_columns"
down_revision = "zzc11_align_legal_notice_columns"
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
    table = "txn_legal_expense"
    for column in [
        sa.Column("legal_case_id", postgresql.UUID(as_uuid=True)),
        sa.Column("expense_reference", sa.String(50)),
        sa.Column("gst_applicable", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("cgst_rate", sa.Numeric(5, 2)),
        sa.Column("cgst_amount", sa.Numeric(12, 2)),
        sa.Column("sgst_rate", sa.Numeric(5, 2)),
        sa.Column("sgst_amount", sa.Numeric(12, 2)),
        sa.Column("igst_rate", sa.Numeric(5, 2)),
        sa.Column("igst_amount", sa.Numeric(12, 2)),
        sa.Column("total_gst", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("gross_amount", sa.Numeric(12, 2)),
        sa.Column("payee_name", sa.String(200)),
        sa.Column("payee_pan", sa.String(10)),
        sa.Column("payee_gstin", sa.String(15)),
        sa.Column("invoice_number", sa.String(50)),
        sa.Column("invoice_date", sa.Date()),
        sa.Column("invoice_document_path", sa.String(500)),
        sa.Column("approved_by_id", postgresql.UUID(as_uuid=True)),
        sa.Column("approved_by_name", sa.String(200)),
        sa.Column("approval_date", sa.DateTime()),
        sa.Column("rejection_reason", sa.Text()),
        sa.Column("payment_date", sa.Date()),
        sa.Column("payment_mode", sa.String(50)),
        sa.Column("payment_reference", sa.String(100)),
        sa.Column("is_recoverable", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("amount_recovered", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("recovery_status", sa.String(50)),
        sa.Column("remarks", sa.Text()),
    ]:
        _add_column_if_missing(table, column)

    if _has_column(table, "case_id"):
        op.execute("""
            UPDATE txn_legal_expense
            SET legal_case_id = case_id
            WHERE legal_case_id IS NULL
            """)
    if _has_column(table, "expense_number"):
        op.execute("""
            UPDATE txn_legal_expense
            SET expense_reference = expense_number
            WHERE expense_reference IS NULL
            """)
    if _has_column(table, "gst_amount"):
        op.execute("""
            UPDATE txn_legal_expense
            SET total_gst = COALESCE(gst_amount, 0),
                igst_amount = COALESCE(igst_amount, gst_amount),
                gst_applicable = COALESCE(gst_applicable, gst_amount > 0)
            WHERE gst_amount IS NOT NULL
            """)
    if _has_column(table, "gst_rate"):
        op.execute("""
            UPDATE txn_legal_expense
            SET igst_rate = COALESCE(igst_rate, gst_rate)
            WHERE gst_rate IS NOT NULL
            """)
    if _has_column(table, "total_amount"):
        op.execute("""
            UPDATE txn_legal_expense
            SET gross_amount = COALESCE(gross_amount, total_amount)
            WHERE total_amount IS NOT NULL
            """)
    op.execute("""
        UPDATE txn_legal_expense
        SET gross_amount = COALESCE(gross_amount, base_amount + COALESCE(total_gst, 0)),
            net_payable = COALESCE(net_payable, COALESCE(gross_amount, base_amount + COALESCE(total_gst, 0)) - COALESCE(tds_amount, 0))
        """)
    if _has_column(table, "approved_by"):
        op.execute("""
            UPDATE txn_legal_expense
            SET approved_by_id = approved_by
            WHERE approved_by_id IS NULL
            """)
    if _has_column(table, "approved_at"):
        op.execute("""
            UPDATE txn_legal_expense
            SET approval_date = approved_at
            WHERE approval_date IS NULL
            """)
    if _has_column(table, "paid_date"):
        op.execute("""
            UPDATE txn_legal_expense
            SET payment_date = paid_date
            WHERE payment_date IS NULL
            """)


def downgrade() -> None:
    for column in [
        "legal_case_id",
        "expense_reference",
        "gst_applicable",
        "cgst_rate",
        "cgst_amount",
        "sgst_rate",
        "sgst_amount",
        "igst_rate",
        "igst_amount",
        "total_gst",
        "gross_amount",
        "payee_name",
        "payee_pan",
        "payee_gstin",
        "invoice_number",
        "invoice_date",
        "invoice_document_path",
        "approved_by_id",
        "approved_by_name",
        "approval_date",
        "rejection_reason",
        "payment_date",
        "payment_mode",
        "payment_reference",
        "is_recoverable",
        "amount_recovered",
        "recovery_status",
        "remarks",
    ]:
        if _has_column("txn_legal_expense", column):
            op.drop_column("txn_legal_expense", column)
