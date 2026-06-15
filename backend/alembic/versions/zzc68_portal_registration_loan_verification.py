"""Add loan-verification fields to borrower portal registration.

Revision ID: zzc68_portal_registration_loan_verification
Revises: zzc67_iif_claim_period_uniqueness
Create Date: 2026-05-27
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "zzc68_portal_registration_loan_verification"
down_revision = "zzc67_iif_claim_period_uniqueness"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "portal_user",
        sa.Column("registration_requested_loan_account_number", sa.String(length=80), nullable=True),
    )
    op.add_column(
        "portal_user",
        sa.Column("registration_requested_sanctioned_amount", sa.Numeric(20, 2), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("portal_user", "registration_requested_sanctioned_amount")
    op.drop_column("portal_user", "registration_requested_loan_account_number")
