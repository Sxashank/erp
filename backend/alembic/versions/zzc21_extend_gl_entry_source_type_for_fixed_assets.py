"""Extend GL entry source enum for fixed-assets postings.

Revision ID: zzc21_extend_gl_entry_source_type_for_fixed_assets
Revises: zzc20_add_fixed_asset_depreciation_book_columns
Create Date: 2026-05-17
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "zzc21_extend_gl_entry_source_type_for_fixed_assets"
down_revision = "zzc20_add_fixed_asset_depreciation_book_columns"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TYPE gl_entry_source_type ADD VALUE IF NOT EXISTS 'FIXED_ASSET_CAPITALIZE';
        """
    )
    op.execute(
        """
        ALTER TYPE gl_entry_source_type ADD VALUE IF NOT EXISTS 'FIXED_ASSET_DISPOSAL';
        """
    )
    op.execute(
        """
        ALTER TYPE gl_entry_source_type ADD VALUE IF NOT EXISTS 'FIXED_ASSET_REVALUATION';
        """
    )
    op.execute(
        """
        ALTER TYPE gl_entry_source_type ADD VALUE IF NOT EXISTS 'FIXED_ASSET_IMPAIRMENT';
        """
    )


def downgrade() -> None:
    # PostgreSQL enum values cannot be removed safely in-place.
    pass
