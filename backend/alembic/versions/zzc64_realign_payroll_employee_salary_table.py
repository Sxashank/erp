"""Realign legacy payroll employee salary table with the current service model.

Revision ID: zzc64_realign_payroll_employee_salary_table
Revises: zzc63_realign_fixed_asset_verification_tables
Create Date: 2026-05-26
"""

from alembic import op
import sqlalchemy as sa

revision = "zzc64_realign_payroll_employee_salary_table"
down_revision = "zzc63_realign_fixed_asset_verification_tables"
branch_labels = None
depends_on = None


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def _column_names(table_name: str) -> set[str]:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return {column["name"] for column in inspector.get_columns(table_name)}


def upgrade() -> None:
    if not _table_exists("payroll_employee_salary"):
        return

    cols = _column_names("payroll_employee_salary")
    with op.batch_alter_table("payroll_employee_salary") as batch_op:
        if "annual_ctc" not in cols:
            batch_op.add_column(sa.Column("annual_ctc", sa.Numeric(18, 2), nullable=True))
        if "annual_gross" not in cols:
            batch_op.add_column(sa.Column("annual_gross", sa.Numeric(18, 2), nullable=True))
        if "annual_net" not in cols:
            batch_op.add_column(sa.Column("annual_net", sa.Numeric(18, 2), nullable=True))
        if "monthly_ctc" not in cols:
            batch_op.add_column(sa.Column("monthly_ctc", sa.Numeric(18, 2), nullable=True))
        if "monthly_gross" not in cols:
            batch_op.add_column(sa.Column("monthly_gross", sa.Numeric(18, 2), nullable=True))
        if "monthly_basic" not in cols:
            batch_op.add_column(sa.Column("monthly_basic", sa.Numeric(18, 2), nullable=True))
        if "monthly_net" not in cols:
            batch_op.add_column(sa.Column("monthly_net", sa.Numeric(18, 2), nullable=True))
        if "revision_reason" not in cols:
            batch_op.add_column(sa.Column("revision_reason", sa.String(length=200), nullable=True))

    op.execute("""
        UPDATE payroll_employee_salary
        SET
            monthly_ctc = COALESCE(monthly_ctc, ctc),
            monthly_gross = COALESCE(monthly_gross, gross_salary),
            monthly_basic = COALESCE(monthly_basic, gross_salary),
            monthly_net = COALESCE(monthly_net, net_salary),
            annual_ctc = COALESCE(annual_ctc, ctc * 12),
            annual_gross = COALESCE(annual_gross, gross_salary * 12),
            annual_net = COALESCE(annual_net, net_salary * 12),
            revision_reason = COALESCE(revision_reason, remarks)
        """)

    with op.batch_alter_table("payroll_employee_salary") as batch_op:
        batch_op.alter_column(
            "annual_ctc",
            existing_type=sa.Numeric(18, 2),
            nullable=False,
        )
        batch_op.alter_column(
            "annual_gross",
            existing_type=sa.Numeric(18, 2),
            nullable=False,
        )
        batch_op.alter_column(
            "monthly_ctc",
            existing_type=sa.Numeric(18, 2),
            nullable=False,
        )
        batch_op.alter_column(
            "monthly_gross",
            existing_type=sa.Numeric(18, 2),
            nullable=False,
        )
        batch_op.alter_column(
            "monthly_basic",
            existing_type=sa.Numeric(18, 2),
            nullable=False,
        )
        batch_op.alter_column(
            "gross_salary",
            existing_type=sa.Numeric(18, 2),
            nullable=True,
        )
        batch_op.alter_column(
            "net_salary",
            existing_type=sa.Numeric(18, 2),
            nullable=True,
        )
        batch_op.alter_column(
            "ctc",
            existing_type=sa.Numeric(18, 2),
            nullable=True,
        )


def downgrade() -> None:
    if not _table_exists("payroll_employee_salary"):
        return

    cols = _column_names("payroll_employee_salary")
    with op.batch_alter_table("payroll_employee_salary") as batch_op:
        if "ctc" in cols:
            batch_op.alter_column(
                "ctc",
                existing_type=sa.Numeric(18, 2),
                nullable=False,
            )
        if "net_salary" in cols:
            batch_op.alter_column(
                "net_salary",
                existing_type=sa.Numeric(18, 2),
                nullable=False,
            )
        if "gross_salary" in cols:
            batch_op.alter_column(
                "gross_salary",
                existing_type=sa.Numeric(18, 2),
                nullable=False,
            )
        if "revision_reason" in cols:
            batch_op.drop_column("revision_reason")
        if "monthly_net" in cols:
            batch_op.drop_column("monthly_net")
        if "monthly_basic" in cols:
            batch_op.drop_column("monthly_basic")
        if "monthly_gross" in cols:
            batch_op.drop_column("monthly_gross")
        if "monthly_ctc" in cols:
            batch_op.drop_column("monthly_ctc")
        if "annual_net" in cols:
            batch_op.drop_column("annual_net")
        if "annual_gross" in cols:
            batch_op.drop_column("annual_gross")
        if "annual_ctc" in cols:
            batch_op.drop_column("annual_ctc")
