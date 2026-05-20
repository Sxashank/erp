"""Add missing court contact columns.

Revision ID: zzc46_add_missing_court_contact_columns
Revises: zzc45_align_legal_master_contracts
Create Date: 2026-05-18
"""

from alembic import op


revision = "zzc46_add_missing_court_contact_columns"
down_revision = "zzc45_align_legal_master_contracts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE IF EXISTS mst_court ADD COLUMN IF NOT EXISTS mobile VARCHAR(20)")


def downgrade() -> None:
    op.execute("ALTER TABLE IF EXISTS mst_court DROP COLUMN IF EXISTS mobile")
