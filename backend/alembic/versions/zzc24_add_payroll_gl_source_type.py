"""Add payroll GL source type.

Revision ID: zzc24_add_payroll_gl_source_type
Revises: zzc23_lms_accounting_bridge_fields
Create Date: 2026-05-18
"""

from alembic import op


revision = "zzc24_add_payroll_gl_source_type"
down_revision = "zzc23_lms_accounting_bridge_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE gl_entry_source_type ADD VALUE IF NOT EXISTS 'PAYROLL';")


def downgrade() -> None:
    # PostgreSQL enum values cannot be removed safely in-place.
    pass
